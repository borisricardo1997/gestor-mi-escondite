import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

DATA_FILE = 'pedidos_mi_escondite.csv'

MENU = {
    "Hamburguesas": {
        "Italiana": 2.50,
        "Francesa": 3.25,
        "Española": 3.25,
        "Americana": 3.25,
        "4 Estaciones": 3.25,
        "Mexicana": 3.25,
        "Especial": 3.25,
        "Suprema": 3.75,
        "Papi Burguer": 2.75,
        "A su gusto (Jumbo)": 5.50,
        "Triple Burguer": 6.00,
        "Doble Burguer": 4.50
    },
    "Hot Dogs": {
        "Especial Mixto": 2.25,
        "Especial de Pollo": 2.25,
        "Hot Dog con salame": 2.25,
        "Mix Dog - Jumbo": 2.25,
        "Champi Dog": 2.25,
        "Hot Dog con cebolla": 1.75
    },
    "Papas Fritas": {
        "Salchipapa (1.50)": 1.50,
        "Salchipapa (1.75)": 1.75,
        "Papi carne": 2.50,
        "Papi Pollo": 2.50,
        "Salchipapa especial": 3.75,
        "Papa Mix": 3.75,
        "Papa Wlady": 5.00
    },
    "Sanduches": {
        "Cubano": 2.25,
        "Vegetariano": 2.25,
        "Sanduche de Pollo": 2.25
    },
    "Bebidas": {
        "Colas Coca Pequeña": 0.75,
        "Cola Sabores Pequeña": 0.50,
        "Cola Inka Grande": 1.00,
        "Fuze Tea mediano": 1.00,
        "Fuze Tea Grande": 1.50,
        "Coca Flaca": 1.75,
        "Cola Sabores Flaca": 1.50,
        "Jugos": 1.50,
        "Batidos": 1.75,
        "Jamaica": 0.50
    },
    "Porciones": {
        "Papas Fritas (0.50)": 0.50,
        "Papas Fritas (1.00)": 1.00,
        "Huevo Frito": 0.75,
        "Presa de Pollo": 1.50,
        "Salame": 0.75,
        "Queso": 0.75,
        "Carne": 0.75,
        "Tocino": 0.75
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
    nombre = st.text_input("Nombre del Pedido (ej. Berta Coello, Mesa 1)", "")
    if not nombre:
        st.warning("Ingresa un nombre para identificar el pedido.")

    total = 0.0
    seleccion = {}

    for cat, items in MENU.items():
        st.subheader(cat)
        cols = st.columns(3)
        i = 0
        for producto, precio in items.items():
            with cols[i % 3]:
                cant = st.number_input(f"{producto} (${precio:.2f})", min_value=0, value=0, step=1, key=f"{cat}_{producto}_{i}")
                if cant > 0:
                    seleccion[f"{cat} - {producto}"] = cant
                    total += cant * precio
            i += 1

    st.markdown("---")
    st.write(f"**Total del pedido: ${total:.2f}**")
    estado = st.selectbox("Estado inicial", ESTADOS, index=0)

    if st.button("Guardar Pedido", type="primary"):
        if not nombre.strip():
            st.error("❌ Debes poner un nombre al pedido.")
        elif total == 0:
            st.error("❌ Agrega al menos un producto.")
        else:
            df = cargar_datos()
            nuevo_id = int(df['ID'].max() + 1) if not df.empty else 1
            detalle = " | ".join([f"{c}x {p}" for p, c in seleccion.items()])
            nuevo_pedido = pd.DataFrame([{
                'ID': nuevo_id,
                'Nombre_Orden': nombre.strip(),
                'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Detalle': detalle if detalle else "Sin items",
                'Total': round(total, 2),
                'Estado': estado
            }])
            df = pd.concat([df, nuevo_pedido], ignore_index=True)
            guardar_datos(df)

            st.success("✅ ¡PEDIDO GUARDADO EXITOSAMENTE!")
            st.balloons()
            st.markdown(f"""
            **Resumen del pedido guardado:**
            - **ID**: #{nuevo_id}
            - **Nombre**: {nombre.strip()}
            - **Detalle**: {detalle if detalle else "Sin items"}
            - **Total**: ${round(total, 2)}
            - **Estado**: {estado}
            """)
            st.info("Puedes seguir registrando más pedidos o ir a 'Ver Pedidos'.")

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
                    st.success("¡Todos los registros borrados! Ahora empieza desde cero.")
                    if 'confirmar_borrado' in st.session_state:
                        del st.session_state.confirmar_borrado
                    st.rerun()

elif opcion == "Cambiar Estado":
    st.header("Cambiar Estado de Pedido")
    df = cargar_datos()
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
                nuevo_estado = st.selectbox("Nuevo estado", ESTADOS, index=ESTADOS.index(pedido['Estado']))
                if st.button("Actualizar Estado"):
                    df.loc[df['ID'] == pedido_id, 'Estado'] = nuevo_estado
                    guardar_datos(df)
                    st.success(f"¡Pedido #{pedido_id} actualizado a {nuevo_estado}!")
                    st.rerun()
