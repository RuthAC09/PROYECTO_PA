import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Configuración de la página web de Streamlit
st.set_page_config(page_title="Dashboard Huella Ecológica", layout="wide")

st.title("Visualización de datos: Huella Ecológica por Región (2009 - 2026)")
st.write("Analiza y compara la evolución de la huella regional per cápita y sus componentes.")

# --- 1. CARGA Y CONSOLIDACIÓN DE DATOS REFORZADA ---
@st.cache_data
def cargar_datos():
    archivos_csv = glob.glob("*.csv")
    if not archivos_csv:
        return None

    datos_historicos = []
    for archivo in archivos_csv:
        nombre_base = os.path.basename(archivo)
        
        try:
            numeros = ''.join(filter(str.isdigit, nombre_base))
            if not numeros:
                continue
            anio = int(numeros)
        except ValueError:
            continue 
        
        try:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8')
        except Exception:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')
        
        # 1.1 Limpiar espacios en blanco de los encabezados
        df.columns = df.columns.str.strip()
        
        # 1.2 Forzar el nombre de la primera columna a 'Ámbito'
        if 'Ámbito' not in df.columns:
            df.rename(columns={df.columns[0]: 'Ámbito'}, inplace=True)
            
        # 1.3 Eliminar filas basura que contienen unidades desalineadas como (Hag)"
        df = df[df['Ámbito'].notna()]
        df['Ámbito'] = df['Ámbito'].astype(str).str.strip()
        df = df[~df['Ámbito'].str.contains(r'\(Hag\)', case=False, na=False)]
        df = df[df['Ámbito'] != '']

        # 1.4 Mapeo estricto para unificar columnas duplicadas con o sin "(Hag)"
        nuevos_columnas = {}
        for col in df.columns:
            if col == 'Ámbito':
                continue
            
            col_normalizada = col.lower()
            if "cultivos" in col_normalizada:
                nuevos_columnas[col] = "Área de Cultivos"
            elif "pastoreo" in col_normalizada:
                nuevos_columnas[col] = "Área de Pastoreo"
            elif "bosques" in col_normalizada:
                nuevos_columnas[col] = "Área de Bosques"
            elif "pesca" in col_normalizada:
                nuevos_columnas[col] = "Zonas de Pesca"
            elif "carbono" in col_normalizada:
                nuevos_columnas[col] = "Huella de Carbono"
            elif "urbanas" in col_normalizada or "urbana" in col_normalizada:
                nuevos_columnas[col] = "Áreas Urbanas"
            elif "per capita" in col_normalizada or "per cápita" in col_normalizada:
                nuevos_columnas[col] = "Huella Regional Per Capita"
                
        df.rename(columns=nuevos_columnas, inplace=True)
        
        # 1.5 Agrupar por 'Ámbito' en caso de que la unificación haya dejado duplicados en el mismo archivo
        # Esto combina los datos fragmentados (como las columnas que estaban separadas en 2010)
        df_columnas_validas = ['Ámbito'] + [c for c in nuevos_columnas.values() if c in df.columns]
        df = df[df_columnas_validas].copy()
        
        # 1.6 Limpieza de números y conversión de decimales (comas a puntos)
        for col in df.columns:
            if col != 'Ámbito':
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Consolidar filas duplicadas de la región combinando los valores numéricos válidos (no nulos)
        df = df.groupby('Ámbito', as_index=False).first()
        
        df['Año'] = anio
        datos_historicos.append(df)
        
    if not datos_historicos:
        return None
        
    return pd.concat(datos_historicos, ignore_index=True)

# Ejecutar la función de carga
df_total = cargar_datos()

if df_total is None:
    st.error("❌ No se encontraron archivos CSV válidos en la carpeta actual.")
else:
    # --- 2. FILTROS DENTRO DE LA PÁGINA ---
    st.markdown("### 🛠️ Parámetros de Selección")
    
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        regiones_disponibles = sorted(df_total['Ámbito'].dropna().unique())
        regiones_seleccionadas = st.multiselect(
            "Selecciona las regiones a comparar:",
            options=regiones_disponibles,
            default=[regiones_disponibles[0]] if regiones_disponibles else []
        )
        
    with col_filtro2:
        columnas_graficables = [
            'Huella Regional Per Capita', 'Área de Cultivos', 
            'Área de Pastoreo', 'Área de Bosques', 
            'Zonas de Pesca', 'Huella de Carbono', 'Áreas Urbanas'
        ]
        columnas_disponibles = [col for col in columnas_graficables if col in df_total.columns]
        
        if not columnas_disponibles:
            columnas_disponibles = [col for col in df_total.columns if col not in ['Ámbito', 'Año']]

        componente_seleccionado = st.selectbox(
            "Selecciona la variable a graficar (Zonas de Pesca, Carbono, etc.):", 
            columnas_disponibles
        )

    st.markdown("---")

    # --- 3. PROCESAMIENTO DE DATOS FILTRADOS ---
    df_filtrado = df_total[df_total['Ámbito'].isin(regiones_seleccionadas)]
    
    # Crear tabla pivotada para el gráfico de líneas
    df_pivot = df_filtrado.pivot(index='Año', columns='Ámbito', values=componente_seleccionado).sort_index()

    # --- 4. DISEÑO VISUAL DE GRÁFICOS Y TABLAS ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Evolución Temporal: {componente_seleccionado}")
        if not regiones_seleccionadas:
            st.warning("Por favor, selecciona al menos una región para generar el gráfico.")
        elif df_pivot.empty or df_pivot.isna().all().all():
            st.error("No hay datos numéricos suficientes para graficar esta variable.")
        else:
            fig, ax = plt.subplots(figsize=(10, 5))
            for region in df_pivot.columns:
                datos_region = df_pivot[region].dropna()
                ax.plot(datos_region.index, datos_region.values, marker='o', label=region, linewidth=2)
            
            ax.set_xlabel("Año")
            ax.set_ylabel(componente_seleccionado)
            ax.set_xticks(df_pivot.index)
            plt.xticks(rotation=45)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(title="Regiones", bbox_to_anchor=(1.05, 1), loc='upper left')
            
            st.pyplot(fig)

    with col2:
        st.subheader("Datos Consolidados")
        if regiones_seleccionadas:
            st.dataframe(df_pivot, use_container_width=True)
        else:
            st.write("No hay datos seleccionados.")

    # --- 5. SLIDER DE CONTROL TEMPORAL ---
    st.markdown("---")
    st.subheader("Desglose Completo por Año")
    anio_seleccionado = st.slider("Arrastra para cambiar el año de la tabla inferior:", 
                                  int(df_total['Año'].min()), int(df_total['Año'].max()), int(df_total['Año'].min()))
    
    df_anio = df_total[df_total['Año'] == anio_seleccionado].drop(columns=['Año'])
    st.dataframe(df_anio.set_index('Ámbito'), use_container_width=True)