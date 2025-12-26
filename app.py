import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
from zoneinfo import ZoneInfo

DATA_FILE_PEDIDOS = 'pedidos_mi_escondite.csv'
DATA_FILE_GASTOS = 'gastos_mi_escondite.csv'
DATA_FILE_CAJA = 'caja_mi_escondite.csv'

TZ_EC = ZoneInfo("America/Guayaquil")

MENU = {
    "Hamburguesas": {
        "Italiana": 2.50, "Francesa": 3.25, "Española": 3.25, "Americana": 3.25, "4 Estaciones": 3.25,
        "Mexicana": 3.25, "Especial": 3.25, "Suprema": 3.75, "Papi Burguer": 2.75, "A su gusto (Jumbo)": 5.50,
        "Triple Burguer": 6.00, "Doble Burguer": 4.50
    },
    "Hot Dogs": {
        "Especial Mixto": 2.25, "Especial de Pollo": 2.25, "Hot Dog con salame": 2.25,
        "Mix Dog - Jumbo": 2.25, "Champi Dog": 2.25, "Hot Dog con cebolla": 1.75
    },
    "Papas Fritas": {
        "Salchipapa": 2.00, "Papi carne": 2.50, "Papi Pollo": 2.50,
        "Salchipapa especial": 3.75, "Papa Mix": 3.75, "Papa Wlady": 5.00
    },
    "Sanduches": {
        "Cubano": 2.25, "Vegetariano": 2.25, "Sanduche de Pollo": 2.25
    },
    "Bebidas": {
        "Colas Coca Pequeña": 0.75, "Cola Sabores Pequeña": 0.50, "Cola Inka Grande": 1.00,
        "Fuze Tea mediano": 1.00, "Fuze Tea Grande": 1.50, "Coca Flaca": 1.75,
        "Cola Sabores Flaca": 1.50, "Jugos": 1.50, "Batidos": 1.75, "Botella de Agua": 0.75, "Jamaica": 0.75
    },
    "Porciónes": {
        "Papas Fritas (0.50)": 0.50, "Papas Fritas (1.00)": 1.00, "Huevo Frito": 0.75,
        "Presa de Pollo": 1.50, "Pollo desmenuzado": 0.75, "Salame": 0.75, "Queso": 0.75, "Carne": 0.75, "Tocino": 0.75
    }
}

ESTADOS = ["En proceso", "Entregado", "Pagado", "Cancelado"]
METODOS_PAGO = ["Efectivo", "Transferencia De Una", "Transferencia Jardín Azuayo", "Transferencia JEP"]

def cargar_pedidos():
    if os.path.exists(DATA_FILE_PEDIDOS):
        df = pd.read_csv(DATA_FILE_PEDIDOS)
        if 'ID' not in df.columns:
            df['ID'] = range(1, len(df) + 1)
        if 'Nombre_Orden' not in df.columns:
            df['Nombre_Orden'] = "Sin nombre"
        if 'Metodo_Pago' not in df.columns:
            df['Metodo_Pago'] = "Efectivo"
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=['ID', 'Nombre_Orden', 'Fecha', 'Detalle', 'Total', 'Estado', 'Metodo_Pago'])

def guardar_pedidos(df):
    df.to_csv(DATA_FILE_PEDIDOS, index=False)

def cargar_gastos():
    if os.path.exists(DATA_FILE_GASTOS):
        df = pd.read_csv(DATA_FILE_GASTOS)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=['Fecha', 'Descripción', 'Monto'])

def guardar_gastos(df):
    df.to_csv(DATA_FILE_GASTOS, index=False)

def cargar_caja():
    if os.path.exists(DATA_FILE_CAJA):
        df = pd.read_csv(DATA_FILE_CAJA)
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=['Fecha', 'Inicial'])

def guardar_caja(df):
    df.to_csv(DATA_FILE_CAJA, index=False)

st.set_page_config(page_title="Mi Escondite", layout="centered")
st.markdown("<h1 style='text-align: center; color: #FF4500;'>🍔 Mi Escondite en la Amazonía</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Gestor de Pedidos y Caja</p>", unsafe_allow_html=True)

opcion = st.sidebar.selectbox("Menú", ["Apertura de Caja", "Registrar Pedido", "Ver Pedidos", "Registrar Gasto", "Cierre de Caja", "Historial de Cierres", "Cambiar Estado"])

now_ec = datetime.now(TZ_EC)
fecha_hoy = now_ec.date()

df_caja = cargar_caja()
apertura_hoy = df_caja[pd.to_datetime(df_caja['Fecha']).dt.date == fecha_hoy]
caja_abierta = not apertura_hoy.empty

if opcion == "Apertura de Caja":
    st.header("Apertura de Caja")
    if caja_abierta:
        st.success(f"Caja ya abierta hoy con inicial ${apertura_hoy['Inicial'].iloc[0]:.2f}.")
    else:
        inicial = st.number_input("Valor inicial en caja ($)", min_value=0.0, step=0.01)
        if st.button("Abrir Caja"):
            nuevo_apertura = pd.DataFrame([{
                'Fecha': now_ec,
                'Inicial': round(inicial, 2)
            }])
            df_caja = pd.concat([df_caja, nuevo_apertura], ignore_index=True)
            guardar_caja(df_caja)
            st.success(f"¡Caja abierta con inicial ${inicial:.2f}! Ahora puedes registrar pedidos.")
            st.rerun()

elif opcion == "Registrar Pedido":
    if not caja_abierta:
        st.error("🚫 La caja no está abierta hoy. Ve a 'Apertura de Caja' para iniciar el día.")
        st.stop()

    st.header("Registrar Pedido Rápido")

    # Carrito en session_state
    if 'carrito' not in st.session_state:
        st.session_state.carrito = {}

    # Resumen fijo arriba
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        nombre = st.text_input("Cliente / Mesa", placeholder="Ej. Mesa 3, Juan", value="")
    with col2:
        total = sum(st.session_state.carrito.get(key, 0) * precio for cat in MENU for key, precio in [(f"{cat} - {p}", precio) for p, precio in MENU[cat].items()])
        st.markdown(f"<h3 style='color: #FF4500;'>Total: ${total:.2f}</h3>", unsafe_allow_html=True)
    with col3:
        metodo_pago = st.selectbox("Método de Pago", METODOS_PAGO)

    # Pestañas por categoría
    tabs = st.tabs(list(MENU.keys()))

    for tab, categoria in zip(tabs, MENU.keys()):
        with tab:
            items = MENU[categoria]
            cols = st.columns(3)
            for idx, (producto, precio) in enumerate(items.items()):
                col = cols[idx % 3]
                key = f"{categoria} - {producto}"
                cantidad = st.session_state.carrito.get(key, 0)
                with col:
                    st.markdown(f"<h4 style='color: #000000; margin-bottom: 5px;'>{producto}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #FF4500; font-weight: bold; margin-top: 0;'>${precio:.2f}</p>", unsafe_allow_html=True)
                    col_btn = st.columns([1, 2, 1])
                    with col_btn[0]:
                        if cantidad > 0:
                            if st.button("➖", key=f"menos_{key}"):
                                st.session_state.carrito[key] = cantidad - 1
                                if st.session_state.carrito[key] == 0:
                                    del st.session_state.carrito[key]
                                st.rerun()
                    with col_btn[1]:
                        st.markdown(f"<h2 style='text-align: center; color: #FF4500; margin: 0;'>{cantidad}</h2>", unsafe_allow_html=True)
                    with col_btn[2]:
                        if st.button("➕", key=f"mas_{key}", type="primary"):
                            st.session_state.carrito[key] = cantidad + 1
                            st.rerun()

    # Resumen y guardar con revisión
    st.markdown("### Resumen del Pedido")
    if st.session_state.carrito:
        detalle = []
        total = 0
        for key, cant in st.session_state.carrito.items():
            cat, prod = key.split(" - ", 1)
            precio = next(precio for c, items in MENU.items() if c == cat for p, precio in items.items() if p == prod)
            total += cant * precio
            detalle.append(f"{cant}x {prod}")
        st.write(" | ".join(detalle))
        st.markdown(f"<h3 style='color: #FF4500;'>Total: ${total:.2f}</h3>", unsafe_allow_html=True)

        if st.button("Revisar Pedido antes de guardar"):
            if not nombre:
                st.error("Ingresa un nombre o mesa.")
            elif total == 0:
                st.error("Agrega al menos un producto.")
            else:
                st.session_state.pedido_temp = {
                    "nombre": nombre,
                    "detalle": " | ".join(detalle),
                    "total": total,
                    "estado": "En proceso",
                    "metodo_pago": metodo_pago
                }
                st.rerun()

        if 'pedido_temp' in st.session_state:
            st.markdown("### 🔍 Confirma el pedido")
            st.markdown(f"""
            **Cliente/Mesa**: {st.session_state.pedido_temp["nombre"]}
            **Detalle**: {st.session_state.pedido_temp["detalle"]}
            **Total**: ${st.session_state.pedido_temp["total"]:.2f}
            **Pago**: {st.session_state.pedido_temp["metodo_pago"]}
            """)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Guardar Pedido", type="primary"):
                    df = cargar_pedidos()
                    nuevo_id = int(df['ID'].max() + 1) if not df.empty else 1
                    nuevo_pedido = pd.DataFrame([{
                        'ID': nuevo_id,
                        'Nombre_Orden': st.session_state.pedido_temp["nombre"],
                        'Fecha': now_ec,
                        'Detalle': st.session_state.pedido_temp["detalle"],
                        'Total': st.session_state.pedido_temp["total"],
                        'Estado': "En proceso",
                        'Metodo_Pago': st.session_state.pedido_temp["metodo_pago"]
                    }])
                    df = pd.concat([df, nuevo_pedido], ignore_index=True)
                    guardar_pedidos(df)
                    st.success("🎉 ¡PEDIDO GUARDADO CON ÉXITO!")
                    st.balloons()
                    st.markdown(f"""
                    **¡El pedido se registró correctamente!**
                    - **ID del pedido**: #{nuevo_id}
                    - **Cliente/Mesa**: {st.session_state.pedido_temp["nombre"]}
                    - **Detalle**: {st.session_state.pedido_temp["detalle"]}
                    - **Total cobrado**: ${st.session_state.pedido_temp["total"]:.2f}
                    - **Método de pago**: {st.session_state.pedido_temp["metodo_pago"]}
                    """)
                    st.info("El formulario está listo para el siguiente pedido.")
                    st.session_state.carrito = {}
                    if 'pedido_temp' in st.session_state:
                        del st.session_state.pedido_temp
            with col2:
                if st.button("✏️ Corregir"):
                    if 'pedido_temp' in st.session_state:
                        del st.session_state.pedido_temp
                    st.rerun()

        # Botón adicional para registrar nuevo pedido (limpia todo, incluyendo nombre)
        if st.button("🆕 Registrar Nuevo Pedido"):
            st.session_state.carrito = {}
            if 'pedido_temp' in st.session_state:
                del st.session_state.pedido_temp
            st.rerun()
    else:
        st.info("🛒 Agrega productos para comenzar el pedido.")

elif opcion == "Registrar Gasto":
    st.header("Registrar Gasto")
    descripcion = st.text_input("Descripción del gasto")
    monto = st.number_input("Monto del gasto ($)", min_value=0.01, step=0.01)
    if st.button("Guardar Gasto"):
        if not descripcion.strip():
            st.error("Debes poner una descripción.")
        else:
            df = cargar_gastos()
            nuevo_gasto = pd.DataFrame([{
                'Fecha': now_ec,
                'Descripción': descripcion.strip(),
                'Monto': round(monto, 2)
            }])
            df = pd.concat([df, nuevo_gasto], ignore_index=True)
            guardar_gastos(df)
            st.success(f"¡Gasto de ${monto:.2f} registrado!")
            st.balloons()
    df = cargar_gastos()
    if not df.empty:
        st.markdown("### 📥 Descargar gastos")
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        st.download_button(
            label="Descargar todos los gastos (CSV)",
            data=csv_buffer,
            file_name=f"gastos_{now_ec.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

elif opcion == "Cierre de Caja":
    st.header("Cierre de Caja")
    fecha_cierre = st.date_input("Seleccionar fecha para cierre", value=now_ec.date())
    df_pedidos = cargar_pedidos()
    df_gastos = cargar_gastos()
    df_caja = cargar_caja()
    apertura_dia = df_caja[pd.to_datetime(df_caja['Fecha']).dt.date == fecha_cierre]
    inicial = apertura_dia['Inicial'].iloc[0] if not apertura_dia.empty else 0.00
    pedidos_dia = df_pedidos[pd.to_datetime(df_pedidos['Fecha']).dt.date == fecha_cierre]
    gastos_dia = df_gastos[pd.to_datetime(df_gastos['Fecha']).dt.date == fecha_cierre]
    ventas_pagadas = pedidos_dia[pedidos_dia['Estado'] == 'Pagado']
    ventas_efectivo = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Efectivo']['Total'].sum()
    ventas_deuna = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Transferencia De Una']['Total'].sum()
    ventas_jardin = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Transferencia Jardín Azuayo']['Total'].sum()
    ventas_jep = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Transferencia JEP']['Total'].sum()
    total_gastos = gastos_dia['Monto'].sum()
    caja_final = inicial + ventas_efectivo - total_gastos
    ganancia_neta = (ventas_efectivo + ventas_deuna + ventas_jardin + ventas_jep) - total_gastos
    st.markdown(f"### Resumen del día {fecha_cierre.strftime('%d/%m/%Y')}")
    st.write(f"**Inicial en caja**: ${inicial:.2f}")
    st.write(f"**Ventas en efectivo**: ${ventas_efectivo:.2f}")
    st.write(f"**Transferencia De Una**: ${ventas_deuna:.2f}")
    st.write(f"**Transferencia Jardín Azuayo**: ${ventas_jardin:.2f}")
    st.write(f"**Transferencia JEP**: ${ventas_jep:.2f}")
    st.write(f"**Total ventas**: ${ventas_efectivo + ventas_deuna + ventas_jardin + ventas_jep:.2f}")
    st.write(f"**Gastos**: ${total_gastos:.2f}")
    st.write(f"**Ganancia neta**: ${ganancia_neta:.2f}")
    st.write(f"**Caja final en efectivo**: ${caja_final:.2f}")
    if not pedidos_dia.empty:
        st.subheader("Pedidos del día")
        st.dataframe(pedidos_dia[['ID', 'Nombre_Orden', 'Detalle', 'Total', 'Metodo_Pago', 'Estado']])
    if not gastos_dia.empty:
        st.subheader("Gastos del día")
        st.dataframe(gastos_dia)
    st.markdown("### 📥 Reporte de Cierre - Descargar")
    reporte = pd.DataFrame({
        'Concepto': ['Inicial', 'Ventas Efectivo', 'Transferencia De Una', 'Transferencia Jardín Azuayo', 'Transferencia JEP', 'Gastos', 'Ganancia Neta', 'Caja Final Efectivo'],
        'Monto': [inicial, ventas_efectivo, ventas_deuna, ventas_jardin, ventas_jep, total_gastos, ganancia_neta, caja_final]
    })
    csv_buffer = io.BytesIO()
    reporte.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)
    st.download_button(
        label="DESCARGAR REPORTE DE CIERRE DE CAJA",
        data=csv_buffer,
        file_name=f"cierre_caja_{fecha_cierre.strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        type="primary"
    )
    st.markdown("### ⚠️ Cerrar Caja y Reiniciar Día")
    st.warning("Esto eliminará los pedidos, gastos y la apertura de caja del día seleccionado. Después necesitarás abrir caja nuevamente para registrar pedidos.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Preparar cierre y limpieza"):
            st.session_state.confirmar_cierre = True
    with col2:
        if st.session_state.get('confirmar_cierre', False):
            if st.button("🔥 CONFIRMAR CIERRE Y LIMPIAR TODO"):
                df_pedidos = df_pedidos[pd.to_datetime(df_pedidos['Fecha']).dt.date != fecha_cierre]
                guardar_pedidos(df_pedidos)
                df_gastos = df_gastos[pd.to_datetime(df_gastos['Fecha']).dt.date != fecha_cierre]
                guardar_gastos(df_gastos)
                df_caja = df_caja[pd.to_datetime(df_caja['Fecha']).dt.date != fecha_cierre]
                guardar_caja(df_caja)
                st.success("¡Caja cerrada y día limpiado completamente! Para registrar nuevos pedidos, debes abrir caja nuevamente.")
                if 'confirmar_cierre' in st.session_state:
                    del st.session_state.confirmar_cierre
                st.rerun()

elif opcion == "Historial de Cierres":
    st.header("Historial de Cierres de Caja")
    st.info("Selecciona una fecha para ver o descargar el reporte histórico.")
    fecha_hist = st.date_input("Fecha del cierre", value=now_ec.date())
    df_pedidos = cargar_pedidos()
    df_gastos = cargar_gastos()
    df_caja = cargar_caja()
    apertura_dia = df_caja[pd.to_datetime(df_caja['Fecha']).dt.date == fecha_hist]
    inicial = apertura_dia['Inicial'].iloc[0] if not apertura_dia.empty else 0.00
    pedidos_dia = df_pedidos[pd.to_datetime(df_pedidos['Fecha']).dt.date == fecha_hist]
    gastos_dia = df_gastos[pd.to_datetime(df_gastos['Fecha']).dt.date == fecha_hist]
    ventas_pagadas = pedidos_dia[pedidos_dia['Estado'] == 'Pagado']
    ventas_efectivo = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Efectivo']['Total'].sum()
    ventas_deuna = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Transferencia De Una']['Total'].sum()
    ventas_jardin = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Transferencia Jardín Azuayo']['Total'].sum()
    ventas_jep = ventas_pagadas[ventas_pagadas['Metodo_Pago'] == 'Transferencia JEP']['Total'].sum()
    total_gastos = gastos_dia['Monto'].sum()
    caja_final = inicial + ventas_efectivo - total_gastos
    ganancia_neta = (ventas_efectivo + ventas_deuna + ventas_jardin + ventas_jep) - total_gastos
    st.markdown(f"### Reporte histórico del {fecha_hist.strftime('%d/%m/%Y')}")
    st.write(f"**Inicial**: ${inicial:.2f}")
    st.write(f"**Ventas Efectivo**: ${ventas_efectivo:.2f}")
    st.write(f"**Transferencia De Una**: ${ventas_deuna:.2f}")
    st.write(f"**Transferencia Jardín Azuayo**: ${ventas_jardin:.2f}")
    st.write(f"**Transferencia JEP**: ${ventas_jep:.2f}")
    st.write(f"**Total ventas**: ${ventas_efectivo + ventas_deuna + ventas_jardin + ventas_jep:.2f}")
    st.write(f"**Gastos**: ${total_gastos:.2f}")
    st.write(f"**Ganancia neta**: ${ganancia_neta:.2f}")
    st.write(f"**Caja final**: ${caja_final:.2f}")
    reporte_hist = pd.DataFrame({
        'Concepto': ['Inicial', 'Ventas Efectivo', 'Transferencia De Una', 'Transferencia Jardín Azuayo', 'Transferencia JEP', 'Gastos', 'Ganancia Neta', 'Caja Final'],
        'Monto': [inicial, ventas_efectivo, ventas_deuna, ventas_jardin, ventas_jep, total_gastos, ganancia_neta, caja_final]
    })
    csv_hist = io.BytesIO()
    reporte_hist.to_csv(csv_hist, index=False, encoding='utf-8')
    csv_hist.seek(0)
    st.download_button(
        label="📥 Descargar Reporte Histórico",
        data=csv_hist,
        file_name=f"reporte_historico_{fecha_hist.strftime('%Y-%m-%d')}.csv",
        mime="text/csv"
    )

elif opcion == "Ver Pedidos":
    st.header("Registro de Pedidos")
    df = cargar_pedidos()
    if df.empty:
        st.info("No hay pedidos registrados aún.")
    else:
        estado_filtro = st.multiselect("Filtrar por estado", ESTADOS, default=ESTADOS)
        metodo_filtro = st.multiselect("Filtrar por método de pago", METODOS_PAGO, default=METODOS_PAGO)
        fecha_filtro = st.date_input("Filtrar por fecha", value=None)
        df_filtrado = df[df['Estado'].isin(estado_filtro) & df['Metodo_Pago'].isin(metodo_filtro)].copy()
        if fecha_filtro:
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']).dt.date == fecha_filtro]
        st.dataframe(df_filtrado.sort_values('ID', ascending=False))
        st.write(f"**Total mostrado: ${df_filtrado['Total'].sum():.2f}**")
        st.markdown("### 📥 Descargar respaldo")
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        st.download_button(
            label="Descargar todos los pedidos (CSV)",
            data=csv_buffer,
            file_name=f"pedidos_{now_ec.strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

elif opcion == "Cambiar Estado":
    st.header("Cambiar Estado de Pedido")
    df = cargar_pedidos()
    if df.empty:
        st.info("No hay pedidos para modificar.")
    else:
        busqueda = st.text_input("Buscar por nombre o ID")
        filtrado = df[df['Nombre_Orden'].str.contains(busqueda, case=False, na=False) | df['ID'].astype(str).str.contains(busqueda)]
        if filtrado.empty:
            st.warning("No se encontró ningún pedido.")
        else:
            opciones = [f"#{row['ID']} - {row['Nombre_Orden']} ({row['Estado']})" for _, row in filtrado.iterrows()]
            seleccionado = st.selectbox("Selecciona el pedido", opciones)
            if seleccionado:
                pedido_id = int(seleccionado.split(" - ")[0][1:])
                pedido = df[df['ID'] == pedido_id].iloc[0]
                st.info(f"Detalle: {pedido['Detalle']}")
                st.info(f"Total: ${pedido['Total']:.2f}")
                st.info(f"Método de pago: {pedido['Metodo_Pago']}")
                nuevo_estado = st.selectbox("Nuevo estado", ESTADOS, index=ESTADOS.index(pedido['Estado']))
                if st.button("Actualizar Estado"):
                    df.loc[df['ID'] == pedido_id, 'Estado'] = nuevo_estado
                    guardar_pedidos(df)
                    st.success(f"¡Pedido #{pedido_id} actualizado a {nuevo_estado}!")
                    st.rerun()
