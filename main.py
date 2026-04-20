import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import indicadores  # <--- IMPORTANTE


# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="ARES PERÚ - DEMANDA", layout="wide")
st.title("🛡️ PLANEACIÓN Y PREDICCiÓN DE MATERIA PRIMA")

@st.cache_data(ttl=600)
def load_and_process(file):
    # Forzamos CODIGO como string y limpieza de datos
    df_d = pd.read_excel(file, sheet_name='DATA', dtype={'CODIGO': str})
    df_c = pd.read_excel(file, sheet_name='CODIGOS', dtype={'CODIGO': str})
    df_d.columns = df_d.columns.str.strip()
    df_c.columns = df_c.columns.str.strip()
    df_d['CODIGO'] = df_d['CODIGO'].str.strip()
    df_c['CODIGO'] = df_c['CODIGO'].str.strip()
    df_d['FECHA'] = pd.to_datetime(df_d['FECHA'])
    return df_d, df_c

uploaded_file = st.file_uploader("Cargar Base de Datos (Excel)", type=["xlsx"])

if uploaded_file:
    df_data, df_codigos = load_and_process(uploaded_file)
    fecha_hoy = pd.Timestamp(datetime.now().date())

    # 2. MOTOR DE DEMANDA: PROMEDIO SIMPLE HISTÓRICO (SUMA MENSUAL)
    df_salidas = df_data[(df_data['TIPO_1'] == 'NS') & (df_data['TIPO_2'].astype(str).isin(['22', '93', 'TD']))].copy()
    
    # Agrupamos por mes/año para tener el total mensual antes de promediar
    ventas_mensuales = df_salidas.groupby(['CODIGO', df_salidas['FECHA'].dt.to_period('M')])['CANTIDAD'].sum().reset_index()
    
    # Promedio solo de meses con actividad > 0 (Lógica Excel)
    promedios_finales = ventas_mensuales[ventas_mensuales['CANTIDAD'] > 0].groupby('CODIGO')['CANTIDAD'].mean()
    desviaciones_finales = ventas_mensuales[ventas_mensuales['CANTIDAD'] > 0].groupby('CODIGO')['CANTIDAD'].std()

    # 3. SIDEBAR: SIMULACIÓN DE TRÁNSITO
    st.sidebar.header("🚢 Simulación de Tránsito")
    target_cod = st.sidebar.text_input("Código para analizar y graficar:", "").strip()
    
    st.sidebar.subheader("📦 Ingresos Programados")
    q_fab = st.sidebar.number_input("Cant. en Fabricación", min_value=0)
    f_fab = st.sidebar.date_input("Fecha Ingreso 1", value=(fecha_hoy + pd.Timedelta(days=30)).date())
    
    q_arr = st.sidebar.number_input("Cant. en Arribo", min_value=0)
    f_arr = st.sidebar.date_input("Fecha Ingreso 2", value=(fecha_hoy + pd.Timedelta(days=60)).date())

    # 4. CÁLCULOS MAESTROS (DINÁMICOS SEGÚN LEAD TIME)
    df_master = df_codigos.copy()
    df_master['DEMANDA_MES'] = df_master['CODIGO'].map(promedios_finales).fillna(0)
    df_master['DESVIACION'] = df_master['CODIGO'].map(desviaciones_finales).fillna(df_master['DEMANDA_MES'] * 0.1)

    Z = 1.65 
    df_master['SS'] = Z * df_master['DESVIACION'] * np.sqrt(df_master['LEAD_TIME']/30.44)
    
    def calcular_logica_jit(row):
        cod = row['CODIGO']
        dem_m = row['DEMANDA_MES']
        dem_d = dem_m / 30.44
        lt_meses = row['LEAD_TIME'] / 30.44
        
        # Stock Virtual (Actual + lo que viene en camino si es el código seleccionado)
        stock_v = row['STOCK_ACTUAL']
        if cod == target_cod:
            stock_v += (q_fab + q_arr)
        
        # Cobertura Virtual
        cob_v = stock_v / dem_m if dem_m > 0 else 0
        
        # Fecha de Quiebre Proyectada
        dias_quiebre = stock_v / dem_d if dem_d > 0 else 365
        f_quiebre = fecha_hoy + pd.Timedelta(days=int(dias_quiebre))
        
        # Fecha Lanzamiento Próxima OC (Punto de Reorden)
        # Se lanza cuando el stock virtual llega al SS
        dias_hasta_pedido = (stock_v - row['SS']) / dem_d if dem_d > 0 else 365
        f_pedido = fecha_hoy + pd.Timedelta(days=int(dias_hasta_pedido - row['LEAD_TIME']))
        
        # Cantidad Sugerida JIT (Llenar el hueco de LT + 2 meses, restando el stock virtual)
        sugerido = (dem_m * (lt_meses + 2) + row['SS']) - stock_v
        
        # Lógica de Estado Dinámica
        if dem_m == 0:
            estado = "⚪ SIN ROTACIÓN"
        elif cob_v > (lt_meses * 3): # SOBRESTOCK: Más de 3 veces tu tiempo de reposición
            estado = "📦 SOBRESTOCK"
        elif f_pedido.date() <= fecha_hoy.date():
            estado = "🚨 LANZAR OC"
        elif cob_v <= (lt_meses + 1): # VIGILAR: Te queda menos de tu LT + 1 mes
            estado = "⚠️ VIGILAR"
        else:
            estado = "✅ OK"
            
        return pd.Series([cob_v, f_quiebre, f_pedido, max(0, sugerido), estado])

    df_master[['COB_V', 'F_QUIEBRE', 'F_PEDIDO', 'SUGERIDO', 'ESTADO']] = df_master.apply(calcular_logica_jit, axis=1)

    # 5. FILTROS DE GESTIÓN
    st.subheader("🔍 Panel de Control y Planeamiento")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_fam = st.multiselect("Filtrar Familia:", sorted(df_master['FAMILIA'].unique()))
    with col_f2:
        sel_est = st.multiselect("Filtrar Estado:", ["🚨 LANZAR OC", "⚠️ VIGILAR", "✅ OK", "📦 SOBRESTOCK", "⚪ SIN ROTACIÓN"], 
                                 default=["🚨 LANZAR OC", "⚠️ VIGILAR", "📦 SOBRESTOCK"])

    df_filtered = df_master.copy()
    if sel_fam: df_filtered = df_filtered[df_filtered['FAMILIA'].isin(sel_fam)]
    if sel_est: df_filtered = df_filtered[df_filtered['ESTADO'].isin(sel_est)]

    # 6. TABLA DE RESULTADOS (CRONOGRAMA DE STOCK)
    meses_nombres = [(fecha_hoy + pd.DateOffset(months=i)).strftime('%b') for i in range(1, 6)]
    resumen_final = []
    
    for _, row in df_filtered.iterrows():
        stk_p = row['STOCK_ACTUAL']
        dem_m = row['DEMANDA_MES']
        proy_meses = {}
        
        for i, m_name in enumerate(meses_nombres):
            f_p = fecha_hoy + pd.DateOffset(months=i+1)
            if row['CODIGO'] == target_cod:
                if f_p.month == f_fab.month and f_p.year == f_fab.year: stk_p += q_fab
                if f_p.month == f_arr.month and f_p.year == f_arr.year: stk_p += q_arr
            stk_p = max(0, stk_p - dem_m)
            proy_meses[m_name] = int(stk_p)
            
        resumen_final.append({
            "CODIGO": row['CODIGO'], "DESCRIPCION": row['DESCRIPCION'], "STOCK": int(row['STOCK_ACTUAL']),
            "PROMEDIO": round(dem_m, 1), "LT": row['LEAD_TIME'], "COB. VIRTUAL": round(row['COB_V'], 1),
            "QUIEBRE": row['F_QUIEBRE'].date(), "PRÓX. OC": row['F_PEDIDO'].date(),
            "CANT. A COMPRAR": int(row['SUGERIDO']), "ESTADO": row['ESTADO'], **proy_meses
        })

    if resumen_final:
        st.dataframe(pd.DataFrame(resumen_final).style.map(lambda x: 
            'background-color: #ff4b4b; color: white' if x == '🚨 LANZAR OC' else 
            'background-color: #ffa500; color: white' if x == '⚠️ VIGILAR' else
            'background-color: #4b4bff; color: white' if x == '📦 SOBRESTOCK' else '', 
            subset=['ESTADO']), use_container_width=True)


    # 7. GRÁFICO DE PREDICCIÓN Y SIMULACIÓN
    if target_cod:
        st.divider()
        reg_plot = df_master[df_master['CODIGO'] == target_cod]
        if not reg_plot.empty:
            r = reg_plot.iloc[0]
            # Histórico de ventas
            df_hist = df_salidas[df_salidas['CODIGO'] == target_cod].set_index('FECHA').resample('ME')['CANTIDAD'].sum().reset_index()
            
            # Evolución de Stock (180 días)
            f_futuras = pd.date_range(start=fecha_hoy, periods=180, freq='D')
            s_evolucion = []
            s_temp = r['STOCK_ACTUAL']
            dem_diaria_plot = r['DEMANDA_MES'] / 30.44
            
            for d in f_futuras:
                if d.date() == f_fab: s_temp += q_fab
                if d.date() == f_arr: s_temp += q_arr
                s_temp = max(0, s_temp - dem_diaria_plot)
                s_evolucion.append(s_temp)

            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_hist['FECHA'], y=df_hist['CANTIDAD'], name="Venta Real (Historial)", marker_color='rgba(100, 100, 100, 0.3)'))
            fig.add_trace(go.Scatter(x=f_futuras, y=s_evolucion, name="Proyección de Stock", line=dict(color='#2ecc71', width=4)))
            
            # Marcador de Próxima OC
            f_oc_plot = r['F_PEDIDO']
            fig.add_shape(type="line", x0=f_oc_plot, x1=f_oc_plot, y0=0, y1=1, xref="x", yref="paper", line=dict(color="blue", dash="dot", width=2))
            fig.add_annotation(x=f_oc_plot, y=1.05, xref="x", yref="paper", text=f"Sugerencia OC: {f_oc_plot.date()}", showarrow=False, font=dict(color="blue"))

            fig.add_hline(y=r['SS'], line_dash="dash", line_color="orange", annotation_text="Stock Seguridad")
            
            fig.update_layout(title=f"Predicción Inteligente: {r['DESCRIPCION']} ({target_cod})", 
                              hovermode="x unified", height=500, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"El código {target_cod} no se encuentra en la base.")


    # --- AQUÍ DEBE IR LA LLAMADA, DENTRO DEL IF UPLOADED_FILE ---
    import indicadores 
    indicadores.mostrar_dashboard(df_codigos, df_data)

