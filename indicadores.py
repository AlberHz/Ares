import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def mostrar_dashboard(df_codigos, df_data):
    # --- CSS DE ALTO NIVEL (Diseño Enterprise) ---
    st.markdown("""
        <style>
        .stMetric {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border-left: 5px solid #1E88E5;
        }
        .stExpander {
            border: 1px solid #e6e9ef;
            border-radius: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            background-color: #fafafa;
        }
        [data-testid="stMetricValue"] { font-size: 28px; color: #1e293b; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("# 🛡️ Auditoría de Movimiento y Clasificación ABC")
    st.divider()

    # --- 1. PROCESAMIENTO TÉCNICO DE DATOS ---
    df = df_codigos.copy()
    
    # 1.1. Extraer Salidas Reales (Suma de columna CANTIDAD en pestaña DATA)
    df_salidas = df_data[(df_data['TIPO_1'] == 'NS') & 
                         (df_data['TIPO_2'].astype(str).isin(['22', '93', 'TD']))].copy()
    
    resumen_salidas = df_salidas.groupby('CODIGO')['CANTIDAD'].sum().reset_index()
    resumen_salidas.rename(columns={'CANTIDAD': 'TOTAL_SALIDAS'}, inplace=True)

    # 1.2. Demanda Mensual (Promedio mensual según tu lógica del Main)
    ventas_mensuales = df_salidas.groupby(['CODIGO', df_salidas['FECHA'].dt.to_period('M')])['CANTIDAD'].sum().reset_index()
    promedios_finales = ventas_mensuales[ventas_mensuales['CANTIDAD'] > 0].groupby('CODIGO')['CANTIDAD'].mean()

    # 1.3. Unificar todo en el Maestro
    df = pd.merge(df, resumen_salidas, on='CODIGO', how='left').fillna({'TOTAL_SALIDAS': 0})
    df['DEMANDA_MES'] = df['CODIGO'].map(promedios_finales).fillna(0)

    # --- 2. CÁLCULOS CRÍTICOS ---
    # ROTACIÓN = TOTAL_SALIDAS / DEMANDA_MES
    df['ROTACION'] = df.apply(
        lambda x: x['TOTAL_SALIDAS'] / x['DEMANDA_MES'] if x['DEMANDA_MES'] > 0 else 0, axis=1
    )

    # ABC GENERAL basado en el TOTAL DE SALIDAS (Para los gráficos superiores)
    df = df.sort_values(by='TOTAL_SALIDAS', ascending=False)
    total_gral = df['TOTAL_SALIDAS'].sum()
    if total_gral > 0:
        df['%_ACUM'] = 100 * df['TOTAL_SALIDAS'].cumsum() / total_gral
    else:
        df['%_ACUM'] = 0

    def categorizar_abc(p):
        if p <= 80: return 'A'
        elif p <= 95: return 'B'
        return 'C'
    df['ABC'] = df['%_ACUM'].apply(categorizar_abc)

    # RECONSTRUCCIÓN DE ESTADO
    if 'ESTADO' not in df.columns:
        def definir_estado(row):
            lt_meses = row['LEAD_TIME'] / 30.44
            cob_v = row['STOCK_ACTUAL'] / row['DEMANDA_MES'] if row['DEMANDA_MES'] > 0 else 0
            if row['DEMANDA_MES'] == 0: return "⚪ SIN ROTACIÓN"
            if cob_v > (lt_meses * 3): return "📦 SOBRESTOCK"
            if cob_v <= (lt_meses + 1): return "⚠️ VIGILAR"
            return "✅ OK"
        df['ESTADO'] = df.apply(definir_estado, axis=1)

    # --- 3. DASHBOARD: VISUALIZACIONES PRINCIPALES ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 Distribución por Estado")
        fig_estado = px.pie(df, names='ESTADO', hole=0.6,
                            color='ESTADO', color_discrete_map={
                                "🚨 LANZAR OC": "#ef4444", "⚠️ VIGILAR": "#f59e0b", 
                                "📦 SOBRESTOCK": "#3b82f6", "✅ OK": "#10b981", "⚪ SIN ROTACIÓN": "#94a3b8"
                            })
        fig_estado.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_estado, use_container_width=True)

    with c2:
        st.subheader("🏆 ABC por Familia (% Total Salidas)")
        df_fam_sal = df.groupby('FAMILIA')['TOTAL_SALIDAS'].sum().reset_index()
        fig_fam = px.pie(df_fam_sal, names='FAMILIA', values='TOTAL_SALIDAS', hole=0.6)
        fig_fam.update_traces(textinfo='percent')
        st.plotly_chart(fig_fam, use_container_width=True)

    # --- 4. DESGLOSABLE DE ABC POR FAMILIA (ABC POR ROTACIÓN) ---
    st.markdown("## 🔍 Desglose de Movimiento por Familia")
    st.info("💡 En este desglose, la clasificación ABC se calcula bajo el criterio de **Rotación**.")
    
    lista_familias = sorted(df['FAMILIA'].unique().tolist())
    
    for fam in lista_familias:
        # Filtrar familia y ordenar por Rotación para el nuevo ABC
        df_sub = df[df['FAMILIA'] == fam].copy()
        df_sub = df_sub.sort_values(by='ROTACION', ascending=False)
        
        # Calcular ABC interno de la familia por Rotación
        total_rot_fam = df_sub['ROTACION'].sum()
        if total_rot_fam > 0:
            df_sub['%_ACUM_ROT'] = 100 * df_sub['ROTACION'].cumsum() / total_rot_fam
        else:
            df_sub['%_ACUM_ROT'] = 0
            
        df_sub['ABC_ROTACION'] = df_sub['%_ACUM_ROT'].apply(categorizar_abc)
        
        with st.expander(f"📁 Familia: {fam}"):
            k1, k2, k3 = st.columns(3)
            k1.metric("Items Analizados", len(df_sub))
            k2.metric("Total Salidas (u)", f"{df_sub['TOTAL_SALIDAS'].sum():,.0f}")
            k3.metric("Rotación Media", f"{df_sub['ROTACION'].mean():.2f}x")
            
            st.write("**Top Códigos clasificados por Rotación:**")
            
            # Tabla usando el ABC recalculado por Rotación
            tabla_view = df_sub[['CODIGO', 'DESCRIPCION', 'ABC_ROTACION', 'ESTADO', 'TOTAL_SALIDAS', 'DEMANDA_MES', 'ROTACION']].copy()
            
            st.dataframe(
                tabla_view.style.map(lambda x: 'background-color: #10b981; color: white; font-weight: bold' if x == 'A' else
                                     ('background-color: #f59e0b; color: black; font-weight: bold' if x == 'B' else ''), subset=['ABC_ROTACION'])
                .format({'TOTAL_SALIDAS': "{:,.0f}", 'DEMANDA_MES': "{:,.1f}", 'ROTACION': "{:.2f}x"}),
                use_container_width=True
            )

    # --- 5. EXPORTACIÓN ---
    st.divider()
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte de Auditoría Maestro",
        data=csv_data,
        file_name="auditoria_ares_maestra.csv",
        mime="text/csv"
    )