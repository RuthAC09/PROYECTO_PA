import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Configuración de la página web
st.set_page_config(page_title="Análisis por Regiones y Departamentos", layout="wide")

st.title("Análisis Macrorregional y Departamental de la Huella Ecológica")
st.write("Esta sección desglosa los datos históricos de tu carpeta para mostrar el comportamiento de cada departamento agrupado por su región natural.")

# --- DICCIONARIO DE MAPEADO GEOGRÁFICO ---
REGIONES_PERU = {
    # Costa
    "TUMBES": "Costa", "PIURA": "Costa", "LAMBAYEQUE": "Costa", "LA LIBERTAD": "Costa",
    "ANCASH": "Costa", "LIMA": "Costa", "ICA": "Costa", "AREQUIPA": "Costa", 
    "MOQUEGUA": "Costa", "TACNA": "Costa",
    # Sierra
    "CAJAMARCA": "Sierra", "HUANUCO": "Sierra", "PASCO": "Sierra", "JUNIN": "Sierra",
    "HUANCAVELICA": "Sierra", "AYACUCHO": "Sierra", "APURIMAC": "Sierra", 
    "CUSCO": "Sierra", "PUNO": "Sierra",
    # Selva
    "AMAZONAS": "Selva", "LORETO": "Selva", "SAN MARTIN": "Selva", 
    "UCAYALI": "Selva", "MADRE DE DIOS": "Selva"
}

# Función para limpiar texto (quitar tildes y asegurar mayúsculas)
def limpiar_texto(texto):
    texto = str(texto).upper().strip()
    replacements = (("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"))
    for a, b in replacements:
        texto = texto.replace(a, b)
    return texto

# --- 1. CARGA AUTOMÁTICA DE DATOS ---
@st.cache_data
def cargar_datos_detallados():
    archivos_csv = ["2009.csv", "2010.csv", "2011.csv", "2012.csv", "2013.csv", "2014.csv", "2015.csv", "2016.csv"]
    datos_historicos = []
    
    for archivo in archivos_csv:
        try:
            anio = int(archivo.replace(".csv", ""))
        except ValueError:
            continue 
        
        try:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8')
        except Exception:
            try:
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')
            except Exception:
                continue
        
        df.columns = df.columns.str.strip()
        if len(df.columns) < 2:
            continue
            
        # Detectar columna de ubicación
        col_ambito = None
        for col in df.columns:
            if col.lower() in ['ámbito', 'ambito', 'region', 'región', 'departamento']:
                col_ambito = col
                break
        if col_ambito is None:
            col_ambito = df.columns[0]
            
        df.rename(columns={col_ambito: 'Ámbito'}, inplace=True)
        df = df[df['Ámbito'].notna()]
        
        # Detectar columna numérica de Huella / Cultivos
        col_seleccionada = None
        for col in df.columns:
            col_min = col.lower()
            if "per capita" in col_min or "per cápita" in col_min or "huella" in col_min or "cultivos" in col_min:
                col_seleccionada = col
                break
        if col_seleccionada is None:
            col_seleccionada = df.columns[-1]
            
        df_limpio = pd.DataFrame()
        df_limpio['Departamento'] = df['Ámbito'].apply(limpiar_texto)
        df_limpio['Valor'] = df[col_seleccionada]
        
        # Eliminar filas de ruido o totales
        df_limpio = df_limpio[~df_limpio['Departamento'].str.contains('HAG|TOTAL', na=False)]
        
        if df_limpio['Valor'].dtype == 'object':
            df_limpio['Valor'] = df_limpio['Valor'].astype(str).str.replace(',', '.', regex=False).str.strip()
        df_limpio['Valor'] = pd.to_numeric(df_limpio['Valor'], errors='coerce')
        
        df_limpio = df_limpio.groupby('Departamento', as_index=False).first()
        df_limpio['Región Natural'] = df_limpio['Departamento'].map(REGIONES_PERU)
        df_limpio['Año'] = anio
        
        datos_historicos.append(df_limpio)
        
    if not datos_historicos:
        return None
    return pd.concat(datos_historicos, ignore_index=True)

df_completo = cargar_datos_detallados()

if df_completo is None or df_completo.empty:
    st.error("❌ No se pudieron procesar los datos de tus archivos CSV.")
else:
    # Filtrar solo registros que pertenecen a la Costa, Sierra o Selva de forma válida
    df_completo = df_completo[df_completo['Región Natural'].notna()]

    # --- 2. PARTICIPACIÓN TOTAL POR REGIÓN NATURAL (PRIMERO QUE TODO) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Distribución Porcentual General por Regiones Naturales")
    
    df_pastel = df_completo.groupby('Región Natural', as_index=False)['Valor'].sum()
    
    if not df_pastel.empty:
        colores_dict_pastel = {'Costa': "#A5CEFD", 'Sierra': "#FFB16D", 'Selva': "#CBF69B"}
        colores_pie = [colores_dict_pastel[r] for r in df_pastel['Región Natural']]
        
        # Uso de columnas: Gráfico a la izquierda, Explicación extendida a la derecha
        col_grafico, col_explicacion = st.columns([4, 5])
        
        with col_grafico:
            fig_pie, ax_pie = plt.subplots(figsize=(4.5, 4.5))
            ax_pie.pie(
                df_pastel['Valor'], 
                labels=df_pastel['Región Natural'], 
                colors=colores_pie, 
                autopct='%1.1f%%',
                startangle=140,
                textprops={'fontsize': 11, 'fontweight': 'bold'}
            )
            ax_pie.axis('equal')
            st.pyplot(fig_pie)
            
        with col_explicacion:
            st.markdown("### Interpretación del Impacto Macrorregional")
            st.write(
                "El gráfico circular revela una asimetría marcada en la distribución de la carga ambiental "
                "a nivel nacional, permitiendo identificar los focos prioritarios de intervención:"
            )
            
            # Extraer porcentajes dinámicos globales para la explicación rápida
            total_valor = df_pastel['Valor'].sum()
            pct_dict = {row['Región Natural']: (row['Valor'] / total_valor) * 100 for _, row in df_pastel.iterrows()}
            
            st.write(f"* **Región Costa ({pct_dict.get('Costa', 0):.1f}% acumulado):** Concentra la mayor carga debido a la densidad urbana e industrial.")
            st.write(f"* **Región Sierra ({pct_dict.get('Sierra', 0):.1f}% acumulado):** Mantiene una participación intermedia vinculada a la dispersión demográfica.")
            st.write(f"* **Región Selva ({pct_dict.get('Selva', 0):.1f}% acumulado):** Presenta la menor incidencia histórica.")
            
            # --- CÁLCULO DE PORCENTAJES ANUALES ---
            st.markdown("#### Desglose de Participación por Año (%)")
            
            # Agrupamos por Año y Región, sumamos, y calculamos el porcentaje relativo de cada año
            df_anual = df_completo.groupby(['Año', 'Región Natural'])['Valor'].sum().unstack(fill_value=0)
            df_pct_anual = df_anual.div(df_anual.sum(axis=1), axis=0) * 100
            df_pct_anual = df_pct_anual.round(1)  # Redondear a un decimal
            
            # Mostrar la matriz de porcentajes anuales de forma limpia
            st.dataframe(df_pct_anual, use_container_width=True)
            
    else:
        st.warning("No se pudieron generar los datos para el gráfico de pastel.")

    # --- 3. CÁLCULO DE PROMEDIOS HISTÓRICOS Y ANÁLISIS DESCRIPTIVO ---
    st.markdown("---")
    df_deptos = df_completo.groupby(['Región Natural', 'Departamento'], as_index=False)['Valor'].mean()
    df_deptos = df_deptos.sort_values(by=['Región Natural', 'Valor'], ascending=[True, False])

    st.subheader("Análisis Descriptivo: Departamentos dentro de cada Región Natural")
    st.write("A continuación se muestra el aporte de cada departamento ordenado de mayor a menor impacto dentro de su respectiva zona geográfica:")

    tab1, tab2, tab3 = st.tabs(["Costa", "Sierra", "Selva"])
    regiones_tabs = [("Costa", tab1, '#4A90E2'), ("Sierra", tab2, '#8B572A'), ("Selva", tab3, '#417505')]

    for nombre_reg, tab, color_graf in regiones_tabs:
        with tab:
            df_reg_actual = df_deptos[df_deptos['Región Natural'] == nombre_reg]
            
            if not df_reg_actual.empty:
                col_izq, col_der = st.columns([3, 2])
                
                with col_izq:
                    st.write(f"**Distribución del Impacto en la {nombre_reg}:**")
                    fig, ax = plt.subplots(figsize=(7, 3.5))
                    ax.barh(df_reg_actual['Departamento'], df_reg_actual['Valor'], color=color_graf, edgecolor='black', alpha=0.8)
                    ax.set_xlabel("Índice / Valor Promedio Histórico")
                    ax.invert_yaxis()
                    ax.grid(axis='x', linestyle='--', alpha=0.5)
                    st.pyplot(fig)
                    
                with col_der:
                    st.write("**Tabla de posiciones interna:**")
                    df_tabla_reg = df_reg_actual[['Departamento', 'Valor']].copy()
                    df_tabla_reg['Valor'] = df_tabla_reg['Valor'].round(3)
                    st.dataframe(df_tabla_reg, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No se encontraron datos para la región {nombre_reg}.")

    # --- 4. EVOLUCIÓN TEMPORAL DE TODOS LOS DEPARTAMENTOS POR REGIÓN NATURAL ---
    st.markdown("---")
    st.subheader("Evolución Temporal de todos los Departamentos según su Región")
    st.write("A continuación se presentan las tendencias históricas (2009-2016) desglosadas por cada macro-región natural:")

    tab_lineas_costa, tab_lineas_sierra, tab_lineas_selva = st.tabs(["Costa", "Sierra", "Selva"])
    
    config_lineas = [
        ("Costa", tab_lineas_costa),
        ("Sierra", tab_lineas_sierra),
        ("Selva", tab_lineas_selva)
    ]

    for nombre_reg, tab_destino in config_lineas:
        with tab_destino:
            df_filtrado_reg = df_completo[df_completo['Región Natural'] == nombre_reg]
            
            if not df_filtrado_reg.empty:
                df_pivot_reg = df_filtrado_reg.pivot(index='Año', columns='Departamento', values='Valor').sort_index()
                
                # Graficar a ancho completo
                fig_line, ax_line = plt.subplots(figsize=(10, 4.5))
                for depto in df_pivot_reg.columns:
                    ax_line.plot(df_pivot_reg.index, df_pivot_reg[depto], marker='o', linewidth=2.5, label=depto)
                
                ax_line.set_title(f"Tendencia Anual - Departamentos de la {nombre_reg}", fontsize=12, fontweight='bold')
                ax_line.set_xlabel("Año")
                ax_line.set_ylabel("Valor registrado")
                ax_line.set_xticks(df_pivot_reg.index)
                ax_line.grid(True, linestyle='--', alpha=0.5)
                ax_line.legend(title="Departamentos", loc='upper left', bbox_to_anchor=(1.01, 1))
                
                st.pyplot(fig_line, use_container_width=True)
                
                # Mostrar la tabla de datos abajo del gráfico
                st.markdown("<br>", unsafe_allow_html=True)
                st.write(f"**Matriz de Datos Históricos ({nombre_reg}):**")
                st.dataframe(df_pivot_reg, use_container_width=True)
            else:
                st.warning(f"No hay suficientes datos temporales para mapear la región {nombre_reg}.")