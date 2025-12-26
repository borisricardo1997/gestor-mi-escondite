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
st.title("🍔 Mi Escondite - Gestor de Pedidos")

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

    # Inicializar carrito
    if 'carrito' not in st.session_state:
        st.session_state.carrito = {}

    # Resumen fijo arriba (responsivo)
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            nombre = st.text_input("Cliente / Mesa", placeholder="Ej. Mesa 3, Juan", help="Ingresa el nombre o número de mesa")
        with col2:
            total = sum(st.session_state.carrito.get(p, 0) * precio for cat in MENU for p, precio in MENU[cat].items() if p in [f'{cat} - {k}' for k in MENU[cat]])
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
                    st.markdown(f"<h4 style='margin: 0; color: #000000;'>{producto}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin: 0; color: #FF4500; font-weight: bold;'>${precio:.2f}</p>", unsafe_allow_html=True)
                    col_btn = st.columns([1, 2, 1])
                    with col_btn[0]:
                        if st.button("➖", key=f"menos_{key}", help="Quitar 1"):
                            if cantidad > 0:
                                st.session_state.carrito[key] = cantidad - 1
                                if st.session_state.carrito[key] == 0:
                                    del st.session_state.carrito[key]
                                st.rerun()
                    with col_btn[1]:
                        st.markdown(f"<h2 style='text-align: center; color: #FF4500; margin: 0;'>{cantidad}</h2>", unsafe_allow_html=True)
                    with col_btn[2]:
                        if st.button("➕", key=f"mas_{key}", type="primary", help="Agregar 1"):
                            st.session_state.carrito[key] = cantidad + 1
                            st.rerun()

    # Resumen y guardar
    st.markdown("### Resumen del Pedido")
    if st.session_state.carrito:
        total = 0
        detalle = []
        for key, cant in st.session_state.carrito.items():
            cat, prod = key.split(" - ", 1)
            precio = next(precio for c, items in MENU.items() if c == cat for p, precio in items.items() if p == prod)
            total += cant * precio
            detalle.append(f"{cant}x {prod}")
        st.write(" | ".join(detalle))
        st.markdown(f"<h3 style='color: #FF4500;'>Total: ${total:.2f}</h3>", unsafe_allow_html=True)

        if st.button("✅ Guardar Pedido", type="primary"):
            if not nombre:
                st.error("❌ Ingresa un nombre o mesa.")
            else:
                df = cargar_pedidos()
                nuevo_id = int(df['ID'].max() + 1) if not df.empty else 1
                nuevo_pedido = pd.DataFrame([{
                    'ID': nuevo_id,
                    'Nombre_Orden': nombre,
                    'Fecha': now_ec,
                    'Detalle': " | ".join(detalle),
                    'Total': round(total, 2),
                    'Estado': "En proceso",
                    'Metodo_Pago': metodo_pago
                }])
                df = pd.concat([df, nuevo_pedido], ignore_index=True)
                guardar_pedidos(df)
                st.success("🎉 ¡Pedido guardado con éxito!")
                st.balloons()
                st.session_state.carrito = {}
                st.rerun()
    else:
        st.info("🛒 Agrega productos al pedido para continuar.")

# (Mantén el resto del código (Registrar Gasto, Cierre de Caja, Historial, Ver Pedidos, Cambiar Estado) igual que en la versión anterior que funcionaba)

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

# (Las secciones Cierre de Caja, Historial de Cierres, Ver Pedidos y Cambiar Estado permanecen igual que en la versión anterior)

# ... (copia el resto del código que ya tenías funcionando para estas secciones)
