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

st.title("🍔 Mi Escondite en la Amazonía - Gestor de Pedidos y Caja")

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
    else:
        st.header("Registrar Nuevo Pedido")
        st.markdown("<div id='formulario'></div>", unsafe_allow_html=True)

        if 'pedido_temp' not in st.session_state:
            st.session_state.pedido_temp = {
                "nombre": "",
                "seleccion": {},
                "total": 0.0,
                "estado": "En proceso",
                "metodo_pago": "Efectivo"
            }

        if 'pedido_guardado' not in st.session_state:
            st.session_state.pedido_guardado = False

        nombre = st.text_input("Nombre del Pedido (ej. Berta Coello, Mesa 1)", value=st.session_state.pedido_temp["nombre"])
        total = 0.0
        seleccion = {}

        for cat, items in MENU.items():
            st.subheader(cat)
            cols = st.columns(3)
            i = 0
            for producto, precio in items.items():
                with cols[i % 3]:
                    key_unica = f"{cat}_{producto}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}" if st.session_state.pedido_guardado else f"{cat}_{producto}_{i}"
                    cant_anterior = st.session_state.pedido_temp["seleccion"].get(f"{cat} - {producto}", 0)
                    cant = st.number_input(f"{producto} (${precio:.2f})", min_value=0, value=cant_anterior, step=1, key=key_unica)
                    if cant > 0:
                        seleccion[f"{cat} - {producto}"] = cant
                        total += cant * precio
                i += 1

        st.markdown("---")
        st.write(f"**Total del pedido: ${total:.2f}**")
        estado = st.selectbox("Estado inicial", ESTADOS, index=ESTADOS.index(st.session_state.pedido_temp["estado"]))
        metodo_pago = st.selectbox("Método de pago", METODOS_PAGO, index=METODOS_PAGO.index(st.session_state.pedido_temp.get("metodo_pago", "Efectivo")))

        if st.button("Revisar Pedido antes de guardar"):
            if not nombre.strip():
                st.error("❌ Debes poner un nombre al pedido.")
            elif total == 0:
                st.error("❌ Agrega al menos un producto.")
            else:
                st.session_state.pedido_temp = {
                    "nombre": nombre.strip(),
                    "seleccion": seleccion,
                    "total": total,
                    "estado": estado,
                    "metodo_pago": metodo_pago
                }
                st.session_state.pedido_guardado = False
                st.rerun()

        if st.session_state.pedido_temp["total"] > 0 and st.session_state.pedido_temp["nombre"]:
            st.markdown("### 🔍 Resumen del pedido - Verifica antes de guardar")
            detalle_lista = [f"{c}x {p}" for p, c in st.session_state.pedido_temp["seleccion"].items()]
            detalle_str = " | ".join(detalle_lista) if detalle_lista else "Sin items"

            st.markdown(f"""
            **Nombre**: {st.session_state.pedido_temp["nombre"]}
            **Detalle**: {detalle_str}
            **Total**: ${st.session_state.pedido_temp["total"]:.2f}
            **Estado**: {st.session_state.pedido_temp["estado"]}
            **Método de pago**: {st.session_state.pedido_temp["metodo_pago"]}
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar y guardar definitivamente", type="primary"):
                    df = cargar_pedidos()
                    nuevo_id = int(df['ID'].max() + 1) if not df.empty else 1
                    nuevo_pedido = pd.DataFrame([{
                        'ID': nuevo_id,
                        'Nombre_Orden': st.session_state.pedido_temp["nombre"],
                        'Fecha': now_ec,
                        'Detalle': detalle_str,
                        'Total': round(st.session_state.pedido_temp["total"], 2),
                        'Estado': st.session_state.pedido_temp["estado"],
                        'Metodo_Pago': st.session_state.pedido_temp["metodo_pago"]
                    }])
                    df = pd.concat([df, nuevo_pedido], ignore_index=True)
                    guardar_pedidos(df)

                    st.session_state.pedido_guardado = True
                    st.session_state.nuevo_id_guardado = nuevo_id
                    st.session_state.detalle_guardado = detalle_str
                    st.rerun()

            with col2:
                if st.button("✏️ Corregir"):
                    st.markdown("<script>window.location.hash = '#formulario';</script>", unsafe_allow_html=True)
                    st.rerun()

        if st.session_state.get('pedido_guardado', False):
            st.success("🎉 ¡PEDIDO GUARDADO CON ÉXITO!")
            st.balloons()
            st.markdown(f"""
            **¡El pedido se registró correctamente!**
            - **ID del pedido**: #{st.session_state.nuevo_id_guardado}
            - **Cliente/Nombre**: {st.session_state.pedido_temp["nombre"]}
            - **Items**: {st.session_state.detalle_guardado}
            - **Total cobrado**: ${st.session_state.pedido_temp["total"]:.2f}
            - **Método de pago**: {st.session_state.pedido_temp["metodo_pago"]}
            - **Estado**: {st.session_state.pedido_temp["estado"]}
            """)
            st.info("El formulario está listo para el siguiente pedido.")

            if st.button("Registrar nuevo pedido"):
                st.session_state.pedido_temp = {"nombre": "", "seleccion": {}, "total": 0.0, "estado": "En proceso", "metodo_pago": "Efectivo"}
                st.session_state.pedido_guardado = False
                st.rerun()

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

    # REPORTE Y BOTÓN DE DESCARGA SIEMPRE VISIBLE
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

    # BOTÓN SEPARADO PARA CERRAR Y REINICIAR
    st.markdown("### ⚠️ Cerrar Caja y Reiniciar Día")
    st.warning("Esto eliminará los pedidos, gastos y la apertura de caja del día seleccionado. Después necesitarás abrir caja nuevamente para registrar pedidos.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Preparar cierre y limpieza"):
            st.session_state.confirmar_cierre = True
    with col2:
        if st.session_state.get('confirmar_cierre', False):
            if st.button("🔥 CONFIRMAR CIERRE Y LIMPIAR TODO"):
                # Borrar datos del día seleccionado
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
