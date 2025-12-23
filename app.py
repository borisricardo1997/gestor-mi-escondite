import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

DATA_FILE = 'pedidos_mi_escondite.csv'

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
        "Salchipapa (1.50)": 1.50, "Salchipapa (1.75)": 1.75, "Papi carne": 2.50, "Papi Pollo": 2.50,
        "Salchipapa especial": 3.75, "Papa Mix": 3.75, "Papa Wlady": 5.00
    },
    "Sanduches": {
        "Cubano": 2.25, "Vegetariano": 2.25, "Sanduche de Pollo": 2.25
    },
    "Bebidas": {
        "Colas Coca Pequeña": 0.75, "Cola Sabores Pequeña": 0.50, "Cola Inka Grande": 1.00,
        "Fuze Tea mediano": 1.00, "Fuze Tea Grande": 1.50, "Coca Flaca": 1.75,
        "Cola Sabores Flaca": 1.50, "Jugos": 1.50, "Batidos": 1.75, "Jamaica": 0.50
    },
    "Porciónes": {
        "Papas Fritas (0.50)": 0.50, "Papas Fritas (1.00)": 1.00, "Huevo Frito": 0.75,
        "Presa de Pollo": 1.50, "Salame": 0.75, "Queso": 0.75, "Carne": 0.75, "Tocino": 0.75
    }
}

ESTADOS = ["En proceso", "Entregado", "Pagado", "Cancelado"]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'ID' not in df.columns:
            df['ID'] = range(1, len(df) + 1)
        if 'Nombre_Orden' not in df.columns:
            df['Nombre_Orden'] = "Sin nombre"
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=['ID', 'Nombre_Orden', 'Fecha', 'Detalle', 'Total', 'Estado'])

def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)

st.title("🍔 Mi Escondite en la Amazonía - Gestor de Pedidos")

opcion = st.sidebar.selectbox("Menú", ["Registrar Pedido", "Ver Pedidos", "Cambiar Estado"])

if opcion == "Registrar Pedido":
    st.header("Registrar Nuevo Pedido")

    st.markdown("<div id='formulario'></div>", unsafe_allow_html=True)

    if 'pedido_temp' not in st.session_state:
        st.session_state.pedido_temp = {
            "nombre": "",
            "seleccion": {},
            "total": 0.0,
            "estado": "En proceso"
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
                key_unica = f"{cat}_{producto}_{datetime.now().strftime('%Y%m%d%H%M%S')}" if st.session_state.pedido_guardado else f"{cat}_{producto}_{i}"
                cant_anterior = st.session_state.pedido_temp["seleccion"].get(f"{cat} - {producto}", 0)
                cant = st.number_input(f"{producto} (${precio:.2f})", min_value=0, value=cant_anterior, step=1, key=key_unica)
                if cant > 0:
                    seleccion[f"{cat} - {producto}"] = cant
                    total += cant * precio
            i += 1

    st.markdown("---")
    st.write(f"**Total del pedido: ${total:.2f}**")
    estado = st.selectbox("Estado inicial", ESTADOS, index=ESTADOS.index(st.session_state.pedido_temp["estado"]))

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
                "estado": estado
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
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar y guardar definitivamente", type="primary"):
                df = cargar_datos()
                nuevo_id = int(df['ID'].max() + 1) if not df.empty else 1
                nuevo_pedido = pd.DataFrame([{
                    'ID': nuevo_id,
                    'Nombre_Orden': st.session_state.pedido_temp["nombre"],
                    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Detalle': detalle_str,
                    'Total': round(st.session_state.pedido_temp["total"], 2),
                    'Estado': st.session_state.pedido_temp["estado"]
                }])
                df = pd.concat([df, nuevo_pedido], ignore_index=True)
                guardar_datos(df)

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
        - **Estado**: {st.session_state.pedido_temp["estado"]}
        """)
        st.info("El formulario está listo para el siguiente pedido.")

        if st.button("Registrar nuevo pedido"):
            # Limpiar todo completamente
            st.session_state.pedido_temp = {"nombre": "", "seleccion": {}, "total": 0.0, "estado": "En proceso"}
            st.session_state.pedido_guardado = False
            st.rerun()

# (El resto del código "Ver Pedidos" y "Cambiar Estado" es el mismo de antes)

elif opcion == "Ver Pedidos":
    st.header("Registro de Pedidos")
    df = cargar_datos()
    if df.empty:
        st.info("No hay pedidos registrados aún.")
    else:
        estado_filtro = st.multiselect("Filtrar por estado", ESTADOS, default=ESTADOS)
        fecha_filtro = st.date_input("Filtrar por fecha", value=None)
        df_filtrado = df[df['Estado'].isin(estado_filtro)].copy()
        if fecha_filtro:
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']).dt.date == fecha_filtro]
        st.dataframe(df_filtrado.sort_values('ID', ascending=False))
        st.write(f"**Total mostrado: ${df_filtrado['Total'].sum():.2f}**")

        st.markdown("### 📥 Descargar respaldo")
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        st.download_button(
            label="Descargar todos los pedidos (CSV para Excel)",
            data=csv_buffer,
            file_name=f"pedidos_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

        st.markdown("### ⚠️ Limpiar todos los registros")
        st.warning("Esto eliminará TODOS los pedidos para siempre.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Preparar borrado total"):
                st.session_state.confirmar_borrado = True
        with col2:
            if st.session_state.get('confirmar_borrado', False):
                if st.button("🔥 CONFIRMAR Y BORRAR TODO"):
                    if os.path.exists(DATA_FILE):
                        os.remove(DATA_FILE)
                    st.success("¡Todos los registros borr
