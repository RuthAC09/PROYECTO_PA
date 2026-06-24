import pandas as pd
import os
import glob
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt

# =====================================================================
# 1. CONFIGURACIÓN DE LA INTERFAZ DE LA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Huella Ecológica Regional - MINAM",
    page_icon="🌱",
    layout="wide"
)

# =====================================================================
# 2. DICCIONARIOS Y FUNCIONES DE SOPORTE
# =====================================================================
# Sin Callao por no ser departamento conforme a lo solicitado
REGIONES_PERU = {
    # COSTA
    'TUMBES': 'Costa', 'PIURA': 'Costa', 'LAMBAYEQUE': 'Costa', 
    'LA LIBERTAD': 'Costa', 'ANCASH': 'Costa', 'LIMA': 'Costa', 
    'ICA': 'Costa', 'AREQUIPA': 'Costa', 'MOQUEGUA': 'Costa', 
    'TACNA': 'Costa',
    
    # SIERRA
    'CAJAMARCA': 'Sierra', 'PASCO': 'Sierra', 'JUNIN': 'Sierra', 
    'HUANUCO': 'Sierra', 'HUANCAVELICA': 'Sierra', 'AYACUCHO': 'Sierra', 
    'APURIMAC': 'Sierra', 'CUSCO': 'Sierra', 'PUNO': 'Sierra',
    
    # SELVA
    'LORETO': 'Selva', 'AMAZONAS': 'Selva', 'SAN MARTIN': 'Selva', 
    'UCAYALI': 'Selva', 'MADRE DE DIOS': 'Selva'
}

def limpiar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
     
    reemplazos = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U'}
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto

# =====================================================================
# 3. CARGA Y CONSOLIDACIÓN DE DATOS REFORZADA (CACHEADA)
# =====================================================================
@st.cache_data
def cargar_datos_detallados():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    archivos_csv = glob.glob(os.path.join(BASE_DIR, "*.csv"))
    
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
            try:
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')
            except Exception:
                continue
        
        df.columns = df.columns.str.strip()
        if df.empty:
            continue
            
        if 'Ámbito' not in df.columns:
            df.rename(columns={df.columns[0]: 'Ámbito'}, inplace=True)
            
        df = df[df['Ámbito'].notna()]
        df['Ámbito'] = df['Ámbito'].astype(str).str.strip()
        df = df[~df['Ámbito'].str.contains(r'\(Hag\)|HAG|TOTAL', case=False, na=False)]
        df = df[df['Ámbito'] != '']

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
        
        df_columnas_validas = ['Ámbito'] + [c for c in nuevos_columnas.values() if c in df.columns]
        df = df[df_columnas_validas].copy()
        
        for col in df.columns:
            if col != 'Ámbito':
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.groupby('Ámbito', as_index=False).first()
        
        df['Departamento'] = df['Ámbito'].apply(limpiar_texto)
        df['Valor'] = df['Huella Regional Per Capita'] if 'Huella Regional Per Capita' in df.columns else df.iloc[:, 1]
        df['Año'] = anio
        df['Región Natural'] = df['Departamento'].map(REGIONES_PERU)
        
        datos_historicos.append(df)
        
    if not datos_historicos:
        return None
        
    return pd.concat(datos_historicos, ignore_index=True)

df_completo = cargar_datos_detallados()

if df_completo is not None and not df_completo.empty:
    df_completo = df_completo[df_completo['Región Natural'].notna()]

# =====================================================================
# 4. MENÚ LATERAL INTERACTIVO
# =====================================================================
with st.sidebar:
    st.title("🌱 Huella Ecológica")
    st.caption("Datos oficiales del Ministerio del Ambiente")
    st.markdown("---")
    seccion = st.radio(
        "Selecciona una sección:",
        ["Resumen del Proyecto", "Análisis General por Año", "Zoom por Departamento", "Visualización Avanzada de Datos"]
    )

# =====================================================================
# 5. CONTROL DE LAS VISTAS SEGÚN LA SECCIÓN SELECCIONADA
# =====================================================================
if df_completo is None or df_completo.empty:
    st.error("❌ No se pudieron procesar los datos de tus archivos CSV. Revisa los delimitadores y la ubicación de tus archivos.")
else:
    
    # --- SECCIÓN 1: RESUMEN DEL PROYECTO ---
    if seccion == "Resumen del Proyecto":
        st.title("🌱 Eckoprint: Sistema de Gestión de Huella Ecológica")
        st.markdown("---")
        
        col_texto, col_imagen = st.columns([2, 1])
        with col_texto:
            st.subheader("¿Qué es Eckoprint?")
            st.write(
                "Eckoprint es una plataforma interactiva diseñada para la visualización, "
                "análisis y monitoreo de la **Huella Ecológica Regional en el Perú**. "
                "A través de este sistema, transformamos los registros históricos del "
                "**Ministerio del Ambiente (MINAM)** en información visual clave para "
                "entender nuestro impacto en el territorio."
            )
        with col_imagen:
            st.image("https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=500", caption="Sostenibilidad Regional", use_container_width=True)

        st.markdown("---")
        st.markdown("### 🎯 Objetivo del Estudio")
        st.info(
            "**Evaluar de manera evolutiva y geoespacial el índice de Huella Ecológica Per Cápita** "
            "en los diferentes departamentos del Perú entre los años 2009 y 2016. Con esto, buscamos "
            "identificar qué regiones presentan un consumo de recursos por encima de su biocapacidad "
            "y promover estrategias de ecoeficiencia local."
        )

        st.markdown("---")
        st.markdown("### 📊 Indicadores Históricos Nacionales (2009 - 2016)")
        
        df_historico_nacional = df_completo.groupby("Año", as_index=False)["Valor"].mean()
        df_historico_nacional.rename(columns={"Valor": "Huella Promedio Nacional (Hag)"}, inplace=True)

        # Eliminar filas donde el valor sea NaN
        df_historico_nacional = df_historico_nacional.dropna(subset=["Huella Promedio Nacional (Hag)"])
        
        if not df_historico_nacional.empty:
            df_historico_nacional = df_historico_nacional.sort_values(by="Año")
        
            huella_inicial = df_historico_nacional.iloc[0]["Huella Promedio Nacional (Hag)"]
            huella_final = df_historico_nacional.iloc[-1]["Huella Promedio Nacional (Hag)"]
            diferencia_historica = huella_final - huella_inicial
        
            c1, c2, c3 = st.columns(3)
        
            with c1:
                st.metric(
                    label=f"Huella Inicial ({int(df_historico_nacional.iloc[0]['Año'])})",
                    value=f"{huella_inicial:.3f} Hag"
                )
        
            with c2:
                st.metric(
                    label=f"Huella Final ({int(df_historico_nacional.iloc[-1]['Año'])})",
                    value=f"{huella_final:.3f} Hag",
                    delta=f"{diferencia_historica:+.3f} Hag",
                    delta_color="inverse"
                )
        
            with c3:
                idx_max = df_historico_nacional["Huella Promedio Nacional (Hag)"].idxmax()
                anio_max = int(df_historico_nacional.loc[idx_max, "Año"])
                valor_max = df_historico_nacional.loc[idx_max, "Huella Promedio Nacional (Hag)"]
        
                st.metric(
                    label=f"Año Crítico Máximo ({anio_max})",
                    value=f"{valor_max:.3f} Hag"
                )
        else:
            st.warning("No se pudieron calcular los indicadores históricos porque la columna 'Valor' quedó vacía o con datos no válidos.")

        st.markdown("---")
        col_grafica, col_info_tabla = st.columns([1.1, 1])
        
        with col_grafica:
            df_pie = df_completo.groupby("Región Natural", as_index=False)["Valor"].sum()
            fig = px.pie(
                df_pie, values='Valor', names='Región Natural', hole=0, 
                color='Región Natural', color_discrete_map={'Costa': '#3b82f6', 'Sierra': '#8b5a2b', 'Selva': '#38a169'}
            )
            fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=16)
            fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            
        with col_info_tabla:
            st.markdown("### 🔍 Interpretación del Impacto Macrorregional")
            st.write(
                "El gráfico circular revela una asimetría marcada en la distribución de la carga ambiental a nivel nacional, "
                "permitiendo identificar los focos prioritarios de intervención:"
            )
            total_valores = df_pie["Valor"].sum()
            pct_costa = (df_pie[df_pie["Región Natural"] == "Costa"]["Valor"].sum() / total_valores) * 100
            pct_sierra = (df_pie[df_pie["Región Natural"] == "Sierra"]["Valor"].sum() / total_valores) * 100
            pct_selva = (df_pie[df_pie["Región Natural"] == "Selva"]["Valor"].sum() / total_valores) * 100
            
            st.markdown(f"• 🌊 **Región Costa ({pct_costa:.1f}% acumulado):** Concentra la mayor carga debido a la densidad urbana e industrial.")
            st.markdown(f"• 🏔️ **Región Sierra ({pct_sierra:.1f}% acumulado):** Mantiene una participación intermedia vinculada a la dispersión demográfica.")
            st.markdown(f"• 🌳 **Región Selva ({pct_selva:.1f}% acumulado):** Presenta la menor incidencia histórica.")
            
            st.markdown("---")
            st.markdown("### 📅 Desglose de Participación por Año (%)")
            df_tabla_reg = df_completo.groupby(["Año", "Región Natural"])["Valor"].sum().unstack()
            df_porcentaje = df_tabla_reg.div(df_tabla_reg.sum(axis=1), axis=0) * 100
            df_porcentaje = df_porcentaje[['Costa', 'Selva', 'Sierra']]
            st.dataframe(df_porcentaje.style.format("{:.1f}%"), use_container_width=True)

    # --- SECCIÓN 2: ANÁLISIS GENERAL POR AÑO ---
    elif seccion == "Análisis General por Año":
        st.title("📈 Análisis General y Comparativa de Componentes")
        st.markdown("---")
        
        lista_anios = sorted(df_completo["Año"].unique())
        anio_seleccionado = st.selectbox("Selecciona el año que deseas analizar:", lista_anios)
        
        df_anio = df_completo[df_completo["Año"] == anio_seleccionado].sort_values(by="Valor", ascending=False)
        
        tab1, tab2 = st.tabs(["📊 Gráficos de Impacto", "📄 Tabla de Datos Completos"])
        
        with tab1:
            st.subheader(f"Huella Regional Per Cápita Total - Año {anio_seleccionado}")
            st.bar_chart(df_anio.set_index("Departamento")["Valor"])
            
            st.markdown("---")
            st.subheader("Comparación de Componentes Específicos de la Huella")
            
            columnas_fijas = ["Departamento", "Valor", "Año", "Región Natural", "Ámbito"]
            componentes_disponibles = [c for c in df_anio.columns if c not in columnas_fijas]
            
            if componentes_disponibles:
                componentes_elegidos = st.multiselect(
                    "Selecciona los componentes que deseas visualizar y contrastar:", 
                    options=componentes_disponibles, 
                    default=componentes_disponibles[:3]
                )
                if componentes_elegidos:
                    st.bar_chart(df_anio.set_index("Departamento")[componentes_elegidos])
            else:
                st.info("No se encontraron componentes adicionales en este archivo.")
            
        with tab2:
            st.subheader(f"Base de Datos Completa - Año {anio_seleccionado}")
            st.dataframe(df_anio.drop(columns=['Ámbito', 'Valor'], errors='ignore'))

    # --- SECCIÓN 3: ZOOM POR DEPARTAMENTO (Código fusionado previo sin Gráfico de Torta) ---
    elif seccion == "Zoom por Departamento":
        st.title("🗺️ Análisis Macrorregional y Departamental de la Huella Ecológica")
        st.write("Esta sección desglosa los datos históricos de tu carpeta para mostrar el comportamiento de cada departamento agrupado por su región natural.")

        st.markdown("---")
        df_deptos = df_completo.groupby(['Región Natural', 'Departamento'], as_index=False)['Valor'].mean()
        df_deptos = df_deptos.sort_values(by=['Región Natural', 'Valor'], ascending=[True, False])

        st.subheader("📊 Análisis Descriptivo: Departamentos dentro de cada Región Natural")
        st.write("A continuación se muestra el aporte de cada departamento ordenado de mayor a menor impacto dentro de su respectiva zona geográfica:")

        tab1, tab2, tab3 = st.tabs(["🌊 Costa", "🏔️ Sierra", "🌳 Selva"])
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

        st.markdown("---")
        st.subheader("📈 Evolución Temporal de todos los Departamentos según su Región")
        st.write("A continuación se presentan las tendencias históricas (2009-2016) desglosadas por cada macro-región natural:")

        tab_lineas_costa, tab_lineas_sierra, tab_lineas_selva = st.tabs(["🌊 Líneas Costa", "🏔️ Líneas Sierra", "🌳 Líneas Selva"])
        config_lineas = [("Costa", tab_lineas_costa), ("Sierra", tab_lineas_sierra), ("Selva", tab_lineas_selva)]

        for nombre_reg, tab_destino in config_lineas:
            with tab_destino:
                df_filtrado_reg = df_completo[df_completo['Región Natural'] == nombre_reg]
                if not df_filtrado_reg.empty:
                    df_pivot_reg = df_filtrado_reg.pivot(index='Año', columns='Departamento', values='Valor').sort_index()
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
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.write(f"**Matriz de Datos Históricos ({nombre_reg}):**")
                    st.dataframe(df_pivot_reg, use_container_width=True)
                else:
                    st.warning(f"No hay suficientes datos temporales para mapear la región {nombre_reg}.")

    # =====================================================================
    # NUEVA INTEGRACIÓN --- SECCIÓN 4: VISUALIZACIÓN AVANZADA DE DATOS ---
    # =====================================================================
    elif seccion == "Visualización Avanzada de Datos":
        st.title("📊 Visualización de datos: Huella Ecológica por Región (2009 - 2026)")
        st.write("Analiza y compara la evolución de la huella regional per cápita y sus componentes.")
        
        st.markdown("### 🛠️ Parámetros de Selección")
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            regiones_disponibles = sorted(df_completo['Ámbito'].dropna().unique())
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
            columnas_disponibles = [col for col in columnas_graficables if col in df_completo.columns]
            if not columnas_disponibles:
                columnas_disponibles = [col for col in df_completo.columns if col not in ['Ámbito', 'Año', 'Departamento', 'Valor', 'Región Natural']]

            componente_seleccionado = st.selectbox(
                "Selecciona la variable a graficar (Zonas de Pesca, Carbono, etc.):", 
                columnas_disponibles
            )

        st.markdown("---")

        df_filtrado_vis = df_completo[df_completo['Ámbito'].isin(regiones_seleccionadas)]
        df_pivot_vis = df_filtrado_vis.pivot(index='Año', columns='Ámbito', values=componente_seleccionado).sort_index()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Evolución Temporal: {componente_seleccionado}")
            if not regiones_seleccionadas:
                st.warning("Por favor, selecciona al menos una región para generar el gráfico.")
            elif df_pivot_vis.empty or df_pivot_vis.isna().all().all():
                st.error("No hay datos numéricos suficientes para graficar esta variable.")
            else:
                fig_vis, ax_vis = plt.subplots(figsize=(10, 5))
                for region in df_pivot_vis.columns:
                    datos_region = df_pivot_vis[region].dropna()
                    ax_vis.plot(datos_region.index, datos_region.values, marker='o', label=region, linewidth=2)
                
                ax_vis.set_xlabel("Año")
                ax_vis.set_ylabel(componente_seleccionado)
                ax_vis.set_xticks(df_pivot_vis.index)
                plt.xticks(rotation=45)
                ax_vis.grid(True, linestyle='--', alpha=0.5)
                ax_vis.legend(title="Regiones", bbox_to_anchor=(1.05, 1), loc='upper left')
                st.pyplot(fig_vis)

        with col2:
            st.subheader("Datos Consolidados")
            if regiones_seleccionadas:
                st.dataframe(df_pivot_vis, use_container_width=True)
            else:
                st.write("No hay datos seleccionados.")

        st.markdown("---")
        st.subheader("Desglose Completo por Año")
        anio_seleccionado = st.slider(
            "Arrastra para cambiar el año de la tabla inferior:", 
            int(df_completo['Año'].min()), int(df_completo['Año'].max()), int(df_completo['Año'].min())
        )
        
        df_anio_vis = df_completo[df_completo['Año'] == anio_seleccionado].drop(columns=['Año', 'Departamento', 'Valor', 'Región Natural'], errors='ignore')
        st.dataframe(df_anio_vis.set_index('Ámbito'), use_container_width=True)
