import pandas as pd
import os
import streamlit as st

# 1. Configuración de la interfaz de la página
st.set_page_config(
    page_title="Huella Ecológica Regional - MINAM",
    page_icon="🌱",
    layout="wide"
)

# 2. Función para cargar los archivos de manera optimizada y tolerante
@st.cache_data
def cargar_datos_anio(nombre_archivo):
    carpeta_datos = r"C:\Users\Ryzen 5\Desktop\Mi Carpeta\UPCH\2026-1 UPCH\Programacion avanzada\Proyecto\Proyecto_Huella_Ecológica\data"
    
    posibles_rutas = [
        os.path.join(carpeta_datos, nombre_archivo),
        os.path.join(carpeta_datos, f"{nombre_archivo}.csv"),
        os.path.join(carpeta_datos, nombre_archivo.capitalize()),
        os.path.join(carpeta_datos, f"{nombre_archivo.capitalize()}.csv")
    ]
    
    ruta_final = None
    for r in posibles_rutas:
        if os.path.exists(r):
            ruta_final = r
            break
            
    if ruta_final is None:
        st.error(f"No se encontró el archivo '{nombre_archivo}' dentro de la carpeta 'datos'.")
        return None
        
    try:
        df = pd.read_csv(ruta_final, encoding='utf-8', sep=';')
        df.columns = df.columns.str.strip()
        
        # Estandarizamos las columnas quitando tildes para evitar errores entre versiones de archivos
        df.columns = df.columns.str.replace('á', 'a').str.replace('é', 'e').str.replace('í', 'i').str.replace('ó', 'o').str.replace('ú', 'u')
        df.columns = df.columns.str.replace('Á', 'A').str.replace('É', 'E').str.replace('Í', 'I').str.replace('Ó', 'O').str.replace('Ú', 'U')
        
        return df
    except Exception as e:
        st.error(f"Error al abrir el archivo {nombre_archivo}: {e}")
        return None

# --- DICCIONARIO DE TUS ARCHIVOS (2009 - 2016) ---
archivos_csv = {
    "Año 2009": "huella_2009",
    "Año 2010": "huella_2010",
    "Año 2011": "huella_2011",
    "Año 2012": "huella_2012",
    "Año 2013": "huella_2013",
    "Año 2014": "huella_2014",
    "Año 2015": "huella_2015",
    "Año 2016": "huella_2016"
}

# --- MENÚ LATERAL INTERACTIVO ---
with st.sidebar:
    st.title("🌱 Huella Ecológica")
    st.caption("Datos oficiales del Ministerio del Ambiente")
    st.markdown("---")
    seccion = st.radio(
        "Selecciona una sección:",
        ["Resumen del Proyecto", "Análisis General por Año", "Zoom por Departamento"]
    )

# --- SECCIÓN 1: RESUMEN DEL PROYECTO ---
if seccion == "Resumen del Proyecto":
    st.title("🌱 Eckoprint: Sistema de Gestión de Huella Ecológica")
    st.markdown("---")
    
    # --- FILA 1: INTRODUCCIÓN Y CONTEXTO ---
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
        st.write(
            "La Huella Ecológica mide la superficie de tierra y agua ecológicamente "
            "productivas necesarias para producir los recursos consumidos y absorber "
            "los desechos generados por la población."
        )
    with col_imagen:
        st.image(
            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=500", 
            caption="Sostenibilidad Regional",
            use_container_width=True
        )

    st.markdown("---")

    # --- FILA 2: OBJETIVO DEL ESTUDIO ---
    st.markdown("### 🎯 Objetivo del Estudio")
    st.info(
        "**Evaluar de manera evolutiva y geoespacial el índice de Huella Ecológica Per Cápita** "
        "en los diferentes departamentos del Perú entre los años 2009 y 2016. Con esto, buscamos "
        "identificar qué regiones presentan un consumo de recursos por encima de su biocapacidad "
        "y promover estrategias de ecoeficiencia local."
    )

    st.markdown("---")

    # --- FILA 3: GRÁFICA COMPARATIVA HISTÓRICA ---
    st.markdown("### 📊 Evolución Histórica Nacional (2009 - 2016)")
    
    # Definimos la función aquí adentro para garantizar que exista antes de usarla
    datos_resumen = []
    col_total = "Huella Regional Per Capita (Hag)"
    
    for etiqueta_anio, nombre_arch in archivos_csv.items():
        df_anio = cargar_datos_anio(nombre_arch)
        if df_anio is not None and col_total in df_anio.columns:
            valores_numericos = pd.to_numeric(df_anio[col_total], errors='coerce')
            promedio_nacional = valores_numericos.mean()
            
            if not pd.isna(promedio_nacional):
                datos_resumen.append({
                    "Año": int(etiqueta_anio.replace("Año ", "")),
                    "Huella Promedio Nacional (Hag)": promedio_nacional
                })
                
    df_historico_nacional = pd.DataFrame(datos_resumen)
    
    if not df_historico_nacional.empty:
        df_historico_nacional = df_historico_nacional.sort_values(by="Año")
        
        # Métricas visuales
        huella_inicial = df_historico_nacional.iloc[0]["Huella Promedio Nacional (Hag)"]
        huella_final = df_historico_nacional.iloc[-1]["Huella Promedio Nacional (Hag)"]
        diferencia_historica = huella_final - huella_inicial
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="Huella Inicial (2009)", value=f"{huella_inicial:.3f} Hag")
        with c2:
            st.metric(
                label="Huella Final (2016)", 
                value=f"{huella_final:.3f} Hag",
                delta=f"{diferencia_historica:+.3f} Hag",
                delta_color="inverse"
            )
        with c3:
            fila_max = df_historico_nacional.loc
            
# --- SECCIÓN 2: ANÁLISIS GENERAL POR AÑO ---
elif seccion == "Análisis General por Año":
    st.title("📈 Análisis General y Comparativa de Componentes")
    st.markdown("---")
    
    anio_seleccionado = st.selectbox("Selecciona el año que deseas analizar:", list(archivos_csv.keys()))
    archivo_objetivo = archivos_csv[anio_seleccionado]
    
    df = cargar_datos_anio(archivo_objetivo)
    
    if df is not None:
        col_total = "Huella Regional Per Capita"
        col_ambito = "Ambito"
        
        tab1, tab2 = st.tabs(["📊 Gráficos de Impacto", "📄 Tabla de Datos Completos"])
        
        with tab1:
            st.subheader(f"Huella Regional Per Cápita Total - {anio_seleccionado}")
            df_ordenado = df.sort_values(by=col_total, ascending=False)
            st.bar_chart(df_ordenado.set_index(col_ambito)[col_total])
            
            st.markdown("---")
            st.subheader("Comparación de Componentes de la Huella")
            
            componentes_posibles = [
                "Area de Cultivos", "Area de Pastoreo", "Area de Bosques", 
                "Zonas de Pesca", "Huella de Carbono", "Areas Urbanas"
            ]
            componentes_reales = [c for c in componentes_posibles if c in df.columns]
            
            if componentes_reales:
                componentes_elegidos = st.multiselect(
                    "Componentes a visualizar en gráfico:", 
                    componentes_reales, 
                    default=componentes_reales[:3]
                )
                if componentes_elegidos:
                    st.bar_chart(df_ordenado.set_index(col_ambito)[componentes_elegidos])
            
        with tab2:
            st.subheader(f"Base de Datos Completa - {anio_seleccionado}")
            st.dataframe(df)

# --- SECCIÓN 3: ZOOM POR DEPARTAMENTO ---
elif seccion == "Zoom por Departamento":
    st.title("🗺️ Análisis Histórico Evolutivo por Departamento")
    st.markdown("---")
    
    primer_anio = list(archivos_csv.values())[0]
    df_base = cargar_datos_anio(primer_anio)
    
    if df_base is not None:
        col_ambito = "Ambito"
        col_total = "Huella Regional Per Capita"
        lista_departamentos = sorted(df_base[col_ambito].unique())
        
        dep_seleccionado = st.selectbox("Selecciona el departamento que deseas analizar:", lista_departamentos)
        
        datos_historicos = []
        
        for etiqueta_anio, nombre_arch in archivos_csv.items():
            df_anio = cargar_datos_anio(nombre_arch)
            if df_anio is not None:
                fila_dep = df_anio[df_anio[col_ambito] == dep_seleccionado]
                if not fila_dep.empty:
                    valor_huella = float(fila_dep[col_total].values[0])
                    datos_historicos.append({
                        "Año": etiqueta_anio.replace("Año ", ""),
                        "Índice de Huella Ecológica": valor_huella
                    })
        
        df_historico = pd.DataFrame(datos_historicos)
        
        if not df_historico.empty:
            st.success(f"### 📈 Evolución de la Huella Ecológica: {dep_seleccionado}")
            
            st.line_chart(df_historico.set_index("Año")["Índice de Huella Ecológica"])
            
            huella_max = df_historico["Índice de Huella Ecológica"].max()
            huella_min = df_historico["Índice de Huella Ecológica"].min()
            
            col1, col2 = st.columns(2)
            col1.metric(label="Punto Crítico Máximo", value=f"{huella_max:.3f} u")
            col2.metric(label="Punto Más Ecoeficiente (Mínimo)", value=f"{huella_min:.3f} u")
            
            st.markdown("---")
            st.subheader("📋 Resumen de datos históricos de la gráfica")
            st.dataframe(df_historico.set_index("Año"))
        else:
            st.warning("No se encontraron registros históricos suficientes para este departamento.")
    else:
        st.error("No se pudieron conectar las bases de datos para el análisis dinámico.")