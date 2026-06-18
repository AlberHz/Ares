# -*- coding: utf-8 -*-
"""
=============================================================================
ARES SMART INVENTORY CORE v9.0 — ENTERPRISE RESOURCE LOGISTICS ENGINE
Desarrollado bajo los Estándares Macrologísticos del MIT Center for Transportation & Logistics
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =========================================================================
# 1. CONFIGURACIÓN ESTRUCTURAL DE LA INTERFAZ EJECUTIVA
# =========================================================================
st.set_page_config(
    page_title="Ares Smart Inventory Core v9.0 — Enterprise Logistics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos CSS avanzados para entorno industrial (Tema Oscuro Profesional)
st.markdown("""
    <style>
    /* Estilos generales de la aplicación */
    .reportview-container { 
        background: #0f1116; 
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Tarjetas de Métricas Críticas (KPIs) */
    .metric-card-premium {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 20px;
        border-left: 5px solid #00ebc7;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .metric-card-alert {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 20px;
        border-left: 5px solid #ef553b;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .metric-card-warning {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 20px;
        border-left: 5px solid #fecb52;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .metric-title-executive { 
        font-size: 12px; 
        color: #94a3b8; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 0.8px; 
    }
    .metric-value-executive { 
        font-size: 30px; 
        color: #ffffff; 
        font-weight: 800; 
        padding: 6px 0; 
    }
    .metric-subtitle-executive { 
        font-size: 11px; 
        color: #00ebc7; 
        font-weight: 500; 
    }
    
    /* Separadores de sección */
    .section-divider {
        margin: 25px 0;
        border-bottom: 1px solid #2e374a;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado Corporativo Principal
st.title("Plataforma de Analisis de Inventarios")
st.markdown("""
**Plataforma de Diagnóstico para la descarga de reportes y analisis de inventarios.
""")

# =========================================================================
# 2. ALGORITMOS Y FUNCIONES MATEMÁTICAS DE LOGÍSTICA
# =========================================================================

def helper_cargar_y_limpiar_datos(file_object):
    """
    Carga de forma adaptativa archivos Excel o CSV, limpiando espacios en blanco,
    eliminando columnas fantasma sin nombre y estandarizando cabeceras a mayúsculas.
    """
    if file_object is None:
        return None
        
    try:
        if file_object.name.endswith('.csv'):
            df = pd.read_csv(file_object)
        else:
            df = pd.read_excel(file_object)
            
        # Limpieza inicial de columnas del dataframe
        df.columns = df.columns.str.strip().str.upper()
        df = df.loc[:, ~df.columns.str.contains('^UNNAMED|^$')]
        
        # Estandarizar identificador crítico si existe
        if 'CODIGO' in df.columns:
            df['CODIGO'] = df['CODIGO'].astype(str).str.strip().str.upper()
            
        return df
    except Exception as e:
        st.error(f"Error en la pre-lectura del archivo {file_object.name}: {str(e)}")
        return None


def clasificar_aging_gerencial(dias_inactivos):
    """
    Segmentación estricta del inventario de acuerdo con las curvas de obsolescencia
    y penalización financiera de capital de trabajo inmovilizado.
    """
    if pd.isna(dias_inactivos):
        return "04. INMOVILIZADO CRÍTICO (>180 días)"
        
    if dias_inactivos <= 30:
        return "01. Rotación Saludable (<30 días)"
    elif dias_inactivos <= 90:
        return "02. Alerta Preventiva (30-90 días)"
    elif dias_inactivos <= 180:
        return "03. Riesgo Estructural (90-180 días)"
    else:
        return "04. INMOVILIZADO CRÍTICO (>180 días)"


def algoritmo_abc_frecuencia(row_dataframe):
    """
    Clasificación de Pareto basada estrictamente en la frecuencia operativa de las
    salidas de almacén (Transacciones de tipo NS).
    """
    if 'FRECUENCIA_SALIDAS' not in row_dataframe or row_dataframe['FRECUENCIA_SALIDAS'] == 0:
        return 'Sin Rotación'
        
    porcentaje_acumulado = row_dataframe['%_ACUMULADO']
    
    if porcentaje_acumulado <= 0.80:
        return 'A (Alta Rotación)'
    elif porcentaje_acumulado <= 0.95:
        return 'B (Media Rotación)'
    else:
        return 'C (Baja Rotación)'


def calcular_matriz_criticidad_cruzada(row_dataframe):
    """
    Cruza la eficiencia operacional (ABC) con la permanencia en almacén (Aging) 
    para aislar de manera científica el stock muerto del surtido estratégico.
    """
    if 'CATEGORIA_ABC' not in row_dataframe or 'DIAS_INACTIVOS' not in row_dataframe:
        return "🟢 Surtido Óptimo"
        
    categoria_abc = row_dataframe['CATEGORIA_ABC']
    dias = row_dataframe['DIAS_INACTIVOS']
    stock_actual = row_dataframe.get('STOCK', 0)
    
    if categoria_abc == 'Sin Rotación' and dias > 180 and stock_actual > 0:
        return "🔴 Stock Muerto (Sin Rotación & Envejecido)"
    elif categoria_abc == 'A (Alta Rotación)' and stock_actual <= 0:
        return "⚠️ Riesgo de Quiebre Operacional"
    elif dias > 90 and stock_actual > 0 and categoria_abc in ['C (Baja Rotación)', 'Sin Rotación']:
        return "🟡 Capital Dormido en Almacén"
    else:
        return "🟢 Surtido Óptimo"

# =========================================================================
# 3. INTERFAZ DE CARGA DE ARCHIVOS FUENTE
# =========================================================================
st.markdown("### 📥 Panel de Carga de archivos de Stock Actual y Movimientos")
col_upload_left, col_upload_right = st.columns(2)

with col_upload_left:
    file_movs = st.file_uploader(
        "1. Archivo de Movimientos (Kardex Completo con Columnas: FECHA, CODIGO, CT, CANTIDAD)", 
        type=["xlsx", "csv"], 
        key="uploader_movs"
    )

with col_upload_right:
    file_stock = st.file_uploader(
        "2. Archivo de Stock Actual Base (Estructura: CODIGO, DESCRIPCIÓN, FAMILIA, STOCK)", 
        type=["xlsx", "csv"], 
        key="uploader_stock"
    )

st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

# =========================================================================
# 4. MOTOR PROCESADOR CENTRAL (DATA ENGINE PRINCIPAL)
# =========================================================================
if file_movs and file_stock:
    try:
        # Cargar los set de datos usando la función robusta de limpieza
        df_movs_raw = helper_cargar_y_limpiar_datos(file_movs)
        df_stock_raw = helper_cargar_y_limpiar_datos(file_stock)
        
        # Validaciones críticas de existencia de columnas requeridas
        columnas_movs_requeridas = ['FECHA', 'CODIGO', 'CT', 'CANTIDAD']
        columnas_stock_requeridas = ['CODIGO', 'DESCRIPCIÓN', 'FAMILIA', 'STOCK']
        
        missing_movs = [col for col in columnas_movs_requeridas if col not in df_movs_raw.columns]
        missing_stock = [col for col in columnas_stock_requeridas if col not in df_stock_raw.columns]
        
        if missing_movs:
            st.error(f"Faltan columnas esenciales en el Kardex de Movimientos: {missing_movs}")
            st.stop()
        if missing_stock:
            st.error(f"Faltan columnas esenciales en la Tabla de Stock Actual: {missing_stock}")
            st.stop()
            
        # Homologación estricta de tipos de datos en memoria para evitar fallos de merge
        df_stock_raw['CODIGO'] = df_stock_raw['CODIGO'].astype(str).str.strip().str.upper()
        df_movs_raw['CODIGO'] = df_movs_raw['CODIGO'].astype(str).str.strip().str.upper()
        
        # Forzar mayúsculas en campos categóricos de agrupación
        df_stock_raw['FAMILIA'] = df_stock_raw['FAMILIA'].fillna('SIN FAMILIA').astype(str).str.strip().str.upper()
        df_stock_raw['DESCRIPCIÓN'] = df_stock_raw['DESCRIPCIÓN'].fillna('PRODUCTO SIN DETALLE').astype(str).str.strip()
        
        # Filtrar valores espurios o nulos del catálogo maestro
        df_stock_clean = df_stock_raw[df_stock_raw['CODIGO'] != 'NAN'].copy()
        maestro_articulos_dict = df_stock_clean.drop_duplicates(subset=['CODIGO']).set_index('CODIGO')
        
        # Formatear el eje temporal del Kardex de Movimientos
        df_movs_raw['FECHA'] = pd.to_datetime(df_movs_raw['FECHA'], errors='coerce')
        df_movs_clean = df_movs_raw.dropna(subset=['FECHA', 'CODIGO', 'CT']).copy()
        
        # Fecha de corte de análisis para cálculo estricto de antigüedades (Aging)
        fecha_corte_sistema = df_movs_clean['FECHA'].max()
        
        # Desacoplar columnas descriptivas del Kardex para evitar colisiones en uniones futuras
        if 'FAMILIA' in df_movs_clean.columns:
            df_movs_clean = df_movs_clean.drop(columns=['FAMILIA'])
        if 'DESCRIPCIÓN' in df_movs_clean.columns:
            df_movs_clean = df_movs_clean.drop(columns=['DESCRIPCIÓN'])
            
        # Integrar las variables maestras oficiales a cada fila del historial transaccional
        df_movs_enriquecido = df_movs_clean.merge(
            maestro_articulos_dict[['DESCRIPCIÓN', 'FAMILIA']], 
            on='CODIGO', 
            how='left'
        )
        df_movs_enriquecido['FAMILIA'] = df_movs_enriquecido['FAMILIA'].fillna('OTRAS').astype(str).str.upper()
        df_movs_enriquecido['DESCRIPCIÓN'] = df_movs_enriquecido['DESCRIPCIÓN'].fillna('DESCONOCIDO')
        
        # Segmentar subconjunto estricto de Notas de Salida (Demand Stream Analitics)
        df_notas_salida = df_movs_enriquecido[df_movs_enriquecido['CT'] == 'NS'].copy()
        df_notas_salida['AÑO_MES_PERIOD'] = df_notas_salida['FECHA'].dt.to_period('M')
        
        # =========================================================================
        # 5. CÁLCULO DE MÉTRICAS GLOBALES INDEPENDIENTES DE FILTROS (EVITA KEYERRORS)
        # =========================================================================
        
        # 5.1. Días de Inactividad Global por SKU
        df_global_ultima_actividad = df_movs_enriquecido.groupby('CODIGO')['FECHA'].max().reset_index()
        df_global_ultima_actividad = df_global_ultima_actividad.rename(columns={'FECHA': 'FECHA_ULTIMA_ACTIVIDAD'})
        
        # 5.2. Métricas de Consumo y Coeficiente de Variación (S&OP Matrix Elements)
        df_demanda_agrupada_mes = df_notas_salida.groupby(['CODIGO', 'AÑO_MES_PERIOD'])['CANTIDAD'].sum().reset_index()
        df_metricas_cv = df_demanda_agrupada_mes.groupby('CODIGO')['CANTIDAD'].agg(['mean', 'std']).reset_index()
        df_metricas_cv = df_metricas_cv.rename(columns={'mean': 'CONSUMO_PROMEDIO_MENSUAL', 'std': 'DESVIACION_ESTANDAR_MENSUAL'})
        df_metricas_cv['CV'] = (df_metricas_cv['DESVIACION_ESTANDAR_MENSUAL'] / df_metricas_cv['CONSUMO_PROMEDIO_MENSUAL']).fillna(0.0)
        
        # 5.3. Frecuencia Absoluta de Transacciones de Salida (Para Pareto ABC)
        df_global_frecuencia_salidas = df_notas_salida.groupby('CODIGO').size().reset_index(name='FRECUENCIA_SALIDAS')

        # =========================================================================
        # 6. RECONSTRUCCIÓN REVERSIBLE DE HISTÓRICO DE CIERRES MENSUALES
        # =========================================================================
        df_movs_enriquecido['AÑO_MES_PERIOD'] = df_movs_enriquecido['FECHA'].dt.to_period('M')
        secuencia_meses_ordenados = sorted(df_movs_enriquecido['AÑO_MES_PERIOD'].dropna().unique())
        universo_total_codigos = set(df_movs_enriquecido['CODIGO'].dropna().unique()).union(set(df_stock_clean['CODIGO'].dropna().unique()))
        
        diccionario_stock_actual_almacen = df_stock_clean.set_index('CODIGO')['STOCK'].to_dict()
        registro_reconstruccion_stock = {cod: diccionario_stock_actual_almacen.get(cod, 0.0) for cod in universo_total_codigos}
        
        matriz_cierres_historicos_calculados = {}
        secuencia_meses_reversa = sorted(df_movs_enriquecido['AÑO_MES_PERIOD'].unique(), reverse=True)
        
        for periodo_mes in secuencia_meses_reversa:
            df_movimientos_del_mes = df_movs_enriquecido[df_movs_enriquecido['AÑO_MES_PERIOD'] == periodo_mes]
            resumen_transacciones_mes = df_movimientos_del_mes.groupby(['CODIGO', 'CT'])['CANTIDAD'].sum().unstack(fill_value=0.0)
            
            if 'NI' not in resumen_transacciones_mes.columns:
                resumen_transacciones_mes['NI'] = 0.0
            if 'NS' not in resumen_transacciones_mes.columns:
                resumen_transacciones_mes['NS'] = 0.0
                
            matriz_cierres_historicos_calculados[periodo_mes] = {}
            
            for codigo_sku in universo_total_codigos:
                cantidad_ingresada_ni = resumen_transacciones_mes.loc[codigo_sku, 'NI'] if codigo_sku in resumen_transacciones_mes.index else 0.0
                cantidad_salida_ns = resumen_transacciones_mes.loc[codigo_sku, 'NS'] if codigo_sku in resumen_transacciones_mes.index else 0.0
                
                # Fórmula inversa del balance de inventarios: Stock Anterior = Stock Final - Ingresos + Salidas
                stock_al_inicio_de_periodo = registro_reconstruccion_stock[codigo_sku] - cantidad_ingresada_ni + cantidad_salida_ns
                stock_al_inicio_de_periodo = max(0.0, stock_al_inicio_de_periodo)
                
                matriz_cierres_historicos_calculados[periodo_mes][codigo_sku] = stock_al_inicio_de_periodo
                registro_reconstruccion_stock[codigo_sku] = stock_al_inicio_de_periodo

        # Consolidación final del gran set de series temporales balanceadas
        registros_series_temporales_consolidados = []
        for periodo_mes in secuencia_meses_ordenados:
            df_movimientos_del_mes = df_movs_enriquecido[df_movs_enriquecido['AÑO_MES_PERIOD'] == periodo_mes]
            resumen_transacciones_mes = df_movimientos_del_mes.groupby(['CODIGO', 'CT'])['CANTIDAD'].sum().unstack(fill_value=0.0)
            
            if 'NI' not in resumen_transacciones_mes.columns:
                resumen_transacciones_mes['NI'] = 0.0
            if 'NS' not in resumen_transacciones_mes.columns:
                resumen_transacciones_mes['NS'] = 0.0
                
            for codigo_sku in universo_total_codigos:
                cantidad_ingresada_ni = resumen_transacciones_mes.loc[codigo_sku, 'NI'] if codigo_sku in resumen_transacciones_mes.index else 0.0
                cantidad_salida_ns = resumen_transacciones_mes.loc[codigo_sku, 'NS'] if codigo_sku in resumen_transacciones_mes.index else 0.0
                
                stock_inicial_mes = matriz_cierres_historicos_calculados[periodo_mes].get(codigo_sku, 0.0)
                stock_final_mes = max(0.0, stock_inicial_mes + cantidad_ingresada_ni - cantidad_salida_ns)
                
                meta_descripcion =  maestro_articulos_dict.loc[codigo_sku, 'DESCRIPCIÓN'] if codigo_sku in maestro_articulos_dict.index else 'DESCONOCIDO'
                meta_familia = maestro_articulos_dict.loc[codigo_sku, 'FAMILIA'] if codigo_sku in maestro_articulos_dict.index else 'OTRAS'
                
                registros_series_temporales_consolidados.append({
                    'AÑO_MES': periodo_mes.strftime('%Y-%m'),
                    'CODIGO': codigo_sku,
                    'DESCRIPCIÓN': meta_descripcion,
                    'FAMILIA': meta_familia,
                    'STOCK_INICIAL': stock_inicial_mes,
                    'INGRESOS': cantidad_ingresada_ni,
                    'SALIDAS': cantidad_salida_ns,
                    'STOCK_FINAL': stock_final_mes
                })
                
        df_historico_grande_maestro = pd.DataFrame(registros_series_temporales_consolidados)

        # =========================================================================
        # 7. FILTROS JERÁRQUICOS GLOBALES EN LA BARRA LATERAL (CASCADA COMPLETA)
        # =========================================================================
        st.sidebar.header("🎛️ Filtros de Control Maestro")
        
        # Filtro Nivel 1: Familias logísticas disponibles
        lista_familias_validas = sorted([f for f in df_stock_clean['FAMILIA'].unique() if f not in ['NAN', 'NONE', 'UNKNOWN']])
        opciones_familias_desplegable = ["TODAS LAS FAMILIAS"] + lista_familias_validas
        familia_seleccionada = st.sidebar.selectbox("1. Seleccionar Familia:", opciones_familias_desplegable)
        
        # Filtro Nivel 2: Códigos específicos condicionados jerárquicamente a la familia
        if familia_seleccionada != "TODAS LAS FAMILIAS":
            df_codigos_filtrados_por_familia = df_stock_clean[df_stock_clean['FAMILIA'] == familia_seleccionada]
            lista_codigos_disponibles = sorted(df_codigos_filtrados_por_familia['CODIGO'].unique())
        else:
            lista_codigos_disponibles = sorted(df_stock_clean['CODIGO'].unique())
            
        opciones_codigos_desplegable = ["TODOS LOS SKU"] + lista_codigos_disponibles
        codigo_seleccionado = st.sidebar.selectbox("2. Filtrar Código Específico (Gráficos 4 y 5):", opciones_codigos_desplegable)

        # Creación de entornos de pestañas ejecutivas de trabajo
        tab_dashboard, tab_data_pbi = st.tabs([
            "📊 Executive Health Dashboard (MIT Standards)", 
            "📥 Repositorio de Tablas Clean (Power BI)"
        ])

        # =========================================================================
        # 8. PESTAÑA 1: PANEL DE CONTROL DE ALTA FIDELIDAD (MÁXIMO DETALLE GRÁFICO)
        # =========================================================================
        with tab_dashboard:
            
            # Re-construir la matriz unificada del dashboard inyectando cálculos globales de forma segura
            df_unificado_dashboard = df_stock_clean.copy()
            
            # Realizar las uniones analíticas de datos
            df_unificado_dashboard = df_unificado_dashboard.merge(df_global_ultima_actividad, on='CODIGO', how='left')
            df_unificado_dashboard = df_unificado_dashboard.merge(df_global_frecuencia_salidas, on='CODIGO', how='left').fillna({'FRECUENCIA_SALIDAS': 0.0})
            
            # Inyección de cálculos matemáticos temporales
            df_unificado_dashboard['DIAS_INACTIVOS'] = (fecha_corte_sistema - pd.to_datetime(df_unificado_dashboard['FECHA_ULTIMA_ACTIVIDAD'])).dt.days.fillna(365).astype(int)
            df_unificado_dashboard['RANGO_AGING'] = df_unificado_dashboard['DIAS_INACTIVOS'].apply(clasificar_aging_gerencial)
            
            # Cálculo exacto de Pareto ABC corporativo
            df_unificado_dashboard = df_unificado_dashboard.sort_values(by='FRECUENCIA_SALIDAS', ascending=False).reset_index(drop=True)
            suma_total_frecuencia_operativa = df_unificado_dashboard['FRECUENCIA_SALIDAS'].sum()
            
            if suma_total_frecuencia_operativa > 0:
                df_unificado_dashboard['%_ACUMULADO'] = (df_unificado_dashboard['FRECUENCIA_SALIDAS'] / suma_total_frecuencia_operativa).cumsum()
            else:
                df_unificado_dashboard['%_ACUMULADO'] = 1.0
                
            df_unificado_dashboard['CATEGORIA_ABC'] = df_unificado_dashboard.apply(algoritmo_abc_frecuencia, axis=1)
            df_unificado_dashboard['CRITICIDAD_LOGISTICA'] = df_unificado_dashboard.apply(calcular_matriz_criticidad_cruzada, axis=1)

            # APLICACIÓN DE FILTRO GLOBAL DE FAMILIA A LA MATRIZ DEL DASHBOARD
            if familia_seleccionada != "TODAS LAS FAMILIAS":
                df_visualizacion_dashboard = df_unificado_dashboard[df_unificado_dashboard['FAMILIA'] == familia_seleccionada].copy()
            else:
                df_visualizacion_dashboard = df_unificado_dashboard.copy()

            # Conteo dinámico de SKUs para el bloque actual del filtro
            total_skus_muestra_activa = df_visualizacion_dashboard['CODIGO'].nunique()

            # Bloque de KPIs Gerenciales en la sección superior
            st.markdown(f"#### 📐 Indicadores Estructurales de la Muestra Actual ({total_skus_muestra_activa} SKUs Filtrados)")
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            
            with kpi_col1:
                total_unidades_fisicas = df_visualizacion_dashboard['STOCK'].sum()
                st.markdown(f"""
                <div class='metric-card-premium'>
                    <div class='metric-title-executive'>Capital Total de Inventario</div>
                    <div class='metric-value-executive'>{total_unidades_fisicas:,.0f}</div>
                    <div class='metric-subtitle-executive'>Unidades en Piso</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col2:
                total_skus_muertos = df_visualizacion_dashboard[df_visualizacion_dashboard['CRITICIDAD_LOGISTICA'].str.contains('🔴')]['CODIGO'].nunique()
                st.markdown(f"""
                <div class='metric-card-alert'>
                    <div class='metric-title-executive'>SKUs en Estatus Muerto</div>
                    <div class='metric-value-executive'>{total_skus_muertos}</div>
                    <div class='metric-subtitle-executive'>Inmovilizados Críticos >180 Días</div>
                </div>
                """, unsafe_allow_html=True)
                
            with kpi_col3:
                total_skus_alta_rotacion = df_visualizacion_dashboard[df_visualizacion_dashboard['CATEGORIA_ABC'] == 'A (Alta Rotación)']['CODIGO'].nunique()
                st.markdown(f"""
                <div class='metric-card-warning'>
                    <div class='metric-title-executive'>SKUs Clase A (Pareto)</div>
                    <div class='metric-value-executive'>{total_skus_alta_rotacion}</div>
                    <div class='metric-subtitle-executive'>Concentran el 80% de Salidas</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # ---------------------------------------------------------------------
            # GRÁFICO 1: MATRIZ DE PREDICTIBILIDAD S&OP (CV VS VOLUME)
            # ---------------------------------------------------------------------
            st.markdown(f"#### 🔍 1. Matriz de Predictibilidad S&OP: Variabilidad (CV) vs. Volumen de Consumo (SKUs: {total_skus_muestra_activa})")
            
            df_grafico_scatter_cv = pd.merge(
                df_metricas_cv, 
                df_visualizacion_dashboard[['CODIGO', 'DESCRIPCIÓN', 'FAMILIA']], 
                on='CODIGO', 
                how='inner'
            )
            
            df_grafico_scatter_cv['Segmento de Planificación S&OP'] = np.where(
                df_grafico_scatter_cv['CV'] <= 0.20, 'Estable (Fácil de Planificar / Predictible)',
                np.where(df_grafico_scatter_cv['CV'] <= 0.70, 'Variable (Requeres Stock de Seguridad)', 'Altamente Volátil (Efecto Látigo / Errático)')
            )
            
            fig_scatter_mit = px.scatter(
                df_grafico_scatter_cv, 
                x='CONSUMO_PROMEDIO_MENSUAL', 
                y='CV', 
                color='Segmento de Planificación S&OP',
                hover_data=['CODIGO', 'DESCRIPCIÓN'],
                labels={
                    'CONSUMO_PROMEDIO_MENSUAL': 'Volumen de Consumo Promedio Mensual (Escala Logarítmica)', 
                    'CV': 'Coeficiente de Variación (Volatilidad del SKU)'
                },
                color_discrete_map={
                    'Estable (Fácil de Planificar / Predictible)': '#00cc96', 
                    'Variable (Requeres Stock de Seguridad)': '#fecb52', 
                    'Altamente Volátil (Efecto Látigo / Errático)': '#ef553b'
                },
                log_x=True
            )
            
            # Añadir línea de umbral crítico de variabilidad industrial
            fig_scatter_mit.add_hline(y=0.50, line_dash="dash", line_color="#94a3b8", annotation_text="Límite Internacional de Predictibilidad")
            fig_scatter_mit.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                margin=dict(t=10, b=25, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
            )
            st.plotly_chart(fig_scatter_mit, width='stretch')

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # ---------------------------------------------------------------------
            # GRÁFICO 2: STOCK INMOVILIZADO Y LUEGO STOCK ABC (PARALELOS)
            # ---------------------------------------------------------------------
            st.markdown(f"#### 📊 2. Análisis Dual de Almacenes: Envejecimiento (Aging) vs. Categorización ABC (SKUs: {total_skus_muestra_activa})")
            g2_left_column, g2_right_column = st.columns(2)
            
            # Agrupar volúmenes físicos para gráficos de barras paralelos
            df_resumen_barras_aging = df_visualizacion_dashboard.groupby('RANGO_AGING', observed=False)['STOCK'].agg(['sum', 'count']).reset_index()
            df_resumen_barras_abc = df_visualizacion_dashboard.groupby('CATEGORIA_ABC', observed=False)['STOCK'].agg(['sum', 'count']).reset_index()

            with g2_left_column:
                fig_barras_aging = px.bar(
                    df_resumen_barras_aging, 
                    x='RANGO_AGING', 
                    y='sum', 
                    color='RANGO_AGING', 
                    text_auto='.0f',
                    title=f"Volumen de Inventario por Rango de Inactividad (Total Códigos: {df_resumen_barras_aging['count'].sum()})",
                    labels={'sum': 'Unidades Físicas en Almacén', 'RANGO_AGING': 'Rango Temporal de Aging'},
                    color_discrete_map={
                        "01. Rotación Saludable (<30 días)": "#00cc96", 
                        "02. Alerta Preventiva (30-90 días)": "#fecb52", 
                        "03. Riesgo Estructural (90-180 días)": "#ff9900", 
                        "04. INMOVILIZADO CRÍTICO (>180 días)": "#ef553b"
                    }
                )
                fig_barras_aging.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_barras_aging, width='stretch')
                
            with g2_right_column:
                fig_barras_abc = px.bar(
                    df_resumen_barras_abc, 
                    x='CATEGORIA_ABC', 
                    y='sum', 
                    color='CATEGORIA_ABC', 
                    text_auto='.0f',
                    title=f"Volumen de Inventario por Clasificación ABC de Frecuencia (Total Códigos: {df_resumen_barras_abc['count'].sum()})",
                    labels={'sum': 'Unidades Físicas en Almacén', 'CATEGORIA_ABC': 'Categoría Operacional de Demanda'},
                    color_discrete_sequence=['#00ebc7', '#fecb52', '#ef553b', '#6b7280']
                )
                fig_barras_abc.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_barras_abc, width='stretch')

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # ---------------------------------------------------------------------
            # GRÁFICO 3: CRUCE ENNTRE INMOVILIZADOS Y EL ABC (CONTEO SKUS)
            # ---------------------------------------------------------------------
            st.markdown(f"#### 🔀 3. Cruce Analítico de Riesgo Operativo: Intersección ABC vs. Perfil de Inactividad (SKUs: {total_skus_muestra_activa})")
            
            # Generar agregación cruzada para cuantificar el conteo exacto de códigos en riesgo
            df_agrupamiento_cruce_criticidad = df_visualizacion_dashboard.groupby(['CATEGORIA_ABC', 'CRITICIDAD_LOGISTICA']).size().reset_index(name='CANTIDAD_SKUS_UNIKOS')
            
            fig_cruce_gerencial = px.bar(
                df_agrupamiento_cruce_criticidad, 
                x='CATEGORIA_ABC', 
                y='CANTIDAD_SKUS_UNIKOS', 
                color='CRITICIDAD_LOGISTICA', 
                barmode='group', 
                text_auto=True,
                title=f"Matriz Corporativa de Surtido Estratégico y Riesgos Financieros — Filtro: {familia_seleccionada}",
                labels={
                    'CANTIDAD_SKUS_UNIKOS': 'Cantidad Exacta de Códigos (SKUs)', 
                    'CATEGORIA_ABC': 'Estatus de Rotación en Almacén'
                },
                color_discrete_map={
                    "🔴 Stock Muerto (Sin Rotación & Envejecido)": "#ef553b", 
                    "⚠️ Riesgo de Quiebre Operacional": "#fecb52", 
                    "🟡 Capital Dormido en Almacén": "#ff9900",
                    "🟢 Surtido Óptimo": "#00cc96"
                }
            )
            fig_cruce_gerencial.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
            )
            st.plotly_chart(fig_cruce_gerencial, width='stretch')

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # FILTRADO DINÁMICO AD-HOC DE LAS SERIES TEMPORALES
            df_filtros_series_temporales = df_historico_grande_maestro.copy()
            if familia_seleccionada != "TODAS LAS FAMILIAS":
                df_filtros_series_temporales = df_filtros_series_temporales[df_filtros_series_temporales['FAMILIA'] == familia_seleccionada]
            if codigo_seleccionado != "TODOS LOS SKU":
                df_filtros_series_temporales = df_filtros_series_temporales[df_filtros_series_temporales['CODIGO'] == codigo_seleccionado]

            # Conteo dinámico específico de códigos contenidos en las series temporales mostradas
            skus_en_series_temporales = df_filtros_series_temporales['CODIGO'].nunique()

            # ---------------------------------------------------------------------
            # GRÁFICO 4: STOCKS FINALES DE CADA MES Y SU VARIACIÓN
            # ---------------------------------------------------------------------
            st.markdown(f"#### 📈 4. Evolución de Cierres de Inventario y Variación Mensual MoM (SKUs en Muestra: {skus_en_series_temporales})")
            
            df_g4_agrupamiento_mes = df_filtros_series_temporales.groupby('AÑO_MES')['STOCK_FINAL'].sum().reset_index()
            df_g4_agrupamiento_mes['VARIACION_NETA_INTERMENSUAL'] = df_g4_agrupamiento_mes['STOCK_FINAL'].diff().fillna(0.0)
            
            fig_lineas_g4 = go.Figure()
            
            # Línea de tendencia principal
            fig_lineas_g4.add_trace(go.Scatter(
                x=df_g4_agrupamiento_mes['AÑO_MES'], 
                y=df_g4_agrupamiento_mes['STOCK_FINAL'], 
                mode='lines+markers+text', 
                name='Stock de Cierre de Mes',
                text=df_g4_agrupamiento_mes['STOCK_FINAL'].map(lambda val: f"{val:,.0f}"), 
                textposition="top center",
                line=dict(color='#00ebc7', width=3), 
                marker=dict(size=8)
            ))
            
            # Barras de variación intermensual
            fig_lineas_g4.add_trace(go.Bar(
                x=df_g4_agrupamiento_mes['AÑO_MES'], 
                y=df_g4_agrupamiento_mes['VARIACION_NETA_INTERMENSUAL'], 
                name='Variación Neta de Capital (MoM)',
                marker_color=np.where(df_g4_agrupamiento_mes['VARIACION_NETA_INTERMENSUAL'] >= 0, '#00cc96', '#ef553b'), 
                opacity=0.55
            ))
            
            fig_lineas_g4.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                xaxis_title="Línea de Tiempo Mensual", 
                yaxis_title="Unidades Físicas (Cierre)", 
                margin=dict(t=15, b=15, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_lineas_g4, width='stretch')

            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            # ---------------------------------------------------------------------
            # GRÁFICO 5: STOCK ACTUAL INRESO SALIDAS Y % CONSUMO
            # ---------------------------------------------------------------------
            st.markdown(f"#### 🔄 5. Balance Transaccional Integral y Tasa Mensual de Consumo de Inventario Disponible (SKUs en Muestra: {skus_en_series_temporales})")
            
            df_g5_agrupamiento_flujo = df_filtros_series_temporales.groupby('AÑO_MES')[['STOCK_INICIAL', 'INGRESOS', 'SALIDAS', 'STOCK_FINAL']].sum().reset_index()
            
            # El disponible para consumo del mes es la suma de lo que había al arrancar más lo ingresado en el mes
            df_g5_agrupamiento_flujo['INVENTARIO_DISPONIBLE_TOTAL'] = df_g5_agrupamiento_flujo['STOCK_INICIAL'] + df_g5_agrupamiento_flujo['INGRESOS']
            df_g5_agrupamiento_flujo['TASA_CONSUMO_PORCENTUAL'] = np.where(
                df_g5_agrupamiento_flujo['INVENTARIO_DISPONIBLE_TOTAL'] > 0, 
                (df_g5_agrupamiento_flujo['SALIDAS'] / df_g5_agrupamiento_flujo['INVENTARIO_DISPONIBLE_TOTAL']) * 100.0, 
                0.0
            )
            
            fig_interactivo_g5 = go.Figure()
            
            # Barras agrupadas para flujos de materiales físicos
            fig_interactivo_g5.add_trace(go.Bar(
                x=df_g5_agrupamiento_flujo['AÑO_MES'], 
                y=df_g5_agrupamiento_flujo['INGRESOS'], 
                name='Ingresos a Almacén (NI)', 
                marker_color='#00cc96'
            ))
            fig_interactivo_g5.add_trace(go.Bar(
                x=df_g5_agrupamiento_flujo['AÑO_MES'], 
                y=df_g5_agrupamiento_flujo['SALIDAS'], 
                name='Salidas de Almacén (NS)', 
                marker_color='#ef553b'
            ))
            fig_interactivo_g5.add_trace(go.Bar(
                x=df_g5_agrupamiento_flujo['AÑO_MES'], 
                y=df_g5_agrupamiento_flujo['STOCK_FINAL'], 
                name='Stock Remanente al Cierre', 
                marker_color='#3b82f6', 
                opacity=0.40
            ))
            
            # Línea de % de consumo sobre eje secundario derecho de coordenadas
            fig_interactivo_g5.add_trace(go.Scatter(
                x=df_g5_agrupamiento_flujo['AÑO_MES'], 
                y=df_g5_agrupamiento_flujo['TASA_CONSUMO_PORCENTUAL'], 
                name='% de Eficiencia de Consumo del Disponible',
                mode='lines+markers', 
                line=dict(color='#fecb52', width=3, dash='dash'), 
                yaxis='y2'
            ))
            
            fig_interactivo_g5.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                barmode='group', 
                xaxis_title="Evolución de Periodos Fiscales", 
                yaxis_title="Volumen Físico de Materiales",
                yaxis2=dict(
                    title="Tasa de Consumo Porcentual del Almacén (%)", 
                    overlaying='y', 
                    side='right', 
                    range=[0, 105], 
                    ticksuffix="%"
                ),
                margin=dict(t=25, b=25, l=10, r=10), 
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_interactivo_g5, width='stretch')

        # =========================================================================
        # 9. PESTAÑA 2: REPOSITORIO DE DATOS PUROS (POWER BI DATASOURCES)
        # =========================================================================
        with tab_data_pbi:
            st.subheader("📥 Data Warehouse Corporativo — Orígenes de Datos Limpios")
            st.markdown("Estructuras relacionales cerradas y consolidadas matemáticamente para inyección directa en Power BI.")
            
            reporte_solicitado = st.selectbox(
                "Seleccione el Modelo de Datos a Exportar:",
                [
                    "1. Reporte de Antigüedad y Días de Inactividad (Lógica Unificada)",
                    "2. Histórico de Cierres de Mes por Código y Familia",
                    "3. Matriz Transaccional Balanceada (Para Gráfico de Cascada)",
                    "4. Clasificación ABC de Rotación y Matriz de Criticidad Cruce",
                    "5. Módulo de Proyecciones Independientes (Consumos Escenarios vs Stock)"
                ]
            )
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

            if "1. Reporte de Antigüedad" in reporte_solicitado:
                st.dataframe(df_visualizacion_dashboard, width='stretch')
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer_engine:
                    df_visualizacion_dashboard.to_excel(writer_engine, index=False)
                st.download_button(
                    "📥 Descargar Fact_Aging_Dias.xlsx", 
                    data=output_excel.getvalue(), 
                    file_name="Fact_Aging_Dias.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif "2. Histórico de Cierres de Mes" in reporte_solicitado:
                df_cierres_exportar = df_historico_grande_maestro[df_historico_grande_maestro['STOCK_FINAL'] > 0][
                    ['AÑO_MES', 'CODIGO', 'DESCRIPCIÓN', 'FAMILIA', 'STOCK_FINAL']
                ].rename(columns={'STOCK_FINAL': 'STOCK_CIERRE'})
                
                st.dataframe(df_cierres_exportar, width='stretch')
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer_engine:
                    df_cierres_exportar.to_excel(writer_engine, index=False)
                st.download_button(
                    "📥 Descargar Fact_Cierre_Mes_Familias.xlsx", 
                    data=output_excel.getvalue(), 
                    file_name="Fact_Cierre_Mes_Familias.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif "3. Matriz Transaccional Balanceada" in reporte_solicitado:
                st.dataframe(df_historico_grande_maestro, width='stretch')
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer_engine:
                    df_historico_grande_maestro.to_excel(writer_engine, index=False)
                st.download_button(
                    "📥 Descargar Fact_Matriz_Waterfall.xlsx", 
                    data=output_excel.getvalue(), 
                    file_name="Fact_Matriz_Waterfall.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif "4. Clasificación ABC de Rotación" in reporte_solicitado:
                st.dataframe(df_visualizacion_dashboard, width='stretch')
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer_engine:
                    df_visualizacion_dashboard.to_excel(writer_engine, index=False)
                st.download_button(
                    "📥 Descargar Dim_Productos_ABC_Cobertura.xlsx", 
                    data=output_excel.getvalue(), 
                    file_name="Dim_Productos_ABC_Cobertura.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif "5. Módulo de Proyecciones" in reporte_solicitado:
                df_pivot_mensual_prod = df_notas_salida.groupby(['CODIGO', 'AÑO_MES_PERIOD'])['CANTIDAD'].sum().unstack(fill_value=0.0)
                df_calculo_promedios_proy = df_pivot_mensual_prod.mean(axis=1).reset_index(name='CONSUMO_PROMEDIO_NORMAL')
                
                df_calculo_promedios_proy['CONSUMO_ESCENARIO_25%'] = (df_calculo_promedios_proy['CONSUMO_PROMEDIO_NORMAL'] * 1.25).round(2)
                df_calculo_promedios_proy['CONSUMO_ESCENARIO_35%'] = (df_calculo_promedios_proy['CONSUMO_PROMEDIO_NORMAL'] * 1.35).round(2)
                
                meses_futuros_proyeccion = ['Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                registros_proyecciones_long = []
                
                for indice_fila, datos_fila in df_calculo_promedios_proy.iterrows():
                    for nombre_mes in meses_futuros_proyeccion:
                        registros_proyecciones_long.append({
                            'CODIGO': datos_fila['CODIGO'],
                            'MES_PROYECCION': nombre_mes,
                            'CONSUMO_NORMAL': round(datos_fila['CONSUMO_PROMEDIO_NORMAL'], 2),
                            'CONSUMO_MAS_25': round(datos_fila['CONSUMO_ESCENARIO_25%'], 2),
                            'CONSUMO_MAS_35': round(datos_fila['CONSUMO_ESCENARIO_35%'], 2)
                        })
                        
                df_tabla_proyecciones_final = pd.DataFrame(registros_proyecciones_long)
                
                col_split_b1, col_split_b2 = st.columns(2)
                with col_split_b1:
                    st.markdown("**Tabla 1: Inventario Base Actual**")
                    st.dataframe(df_stock_clean[['CODIGO', 'DESCRIPCIÓN', 'FAMILIA', 'STOCK']], width='stretch')
                    out_b1 = io.BytesIO()
                    with pd.ExcelWriter(out_b1, engine='openpyxl') as w_b1:
                        df_stock_clean[['CODIGO', 'DESCRIPCIÓN', 'FAMILIA', 'STOCK']].to_excel(w_b1, index=False)
                    st.download_button("📥 Descargar Archivo 1: Stock Base", data=out_b1.getvalue(), file_name="Dim_Stock_Base_Actual.xlsx")
                    
                with col_split_b2:
                    st.markdown("**Tabla 2: Escenarios de Consumo Proyectados**")
                    st.dataframe(df_tabla_proyecciones_final, width='stretch')
                    out_b2 = io.BytesIO()
                    with pd.ExcelWriter(out_b2, engine='openpyxl') as w_b2:
                        df_tabla_proyecciones_final.to_excel(w_b2, index=False)
                    st.download_button("📥 Descargar Archivo 2: Consumos Proyectados", data=out_b2.getvalue(), file_name="Fact_Consumos_Proyectados_Escenarios.xlsx")

    except Exception as error_global_sistema:
        st.error(f"❌ Error crítico detectado en el núcleo de procesamiento: {str(error_global_sistema)}")
else:
    st.info("💡 Suite Ares de Analítica Avanzada en Espera de Archivos. Cargue el Kardex de Movimientos y el Stock Base para inicializar los gráficos.")
