Pythonimport streamlit as st
import pandas as pd
from datetime import datetime
import os
import io  # <-- Nuevo para descarga

DATA_FILE = 'pedidos_mi_escondite.csv'

MENU = {
    "Hamburguesas": {"Italiana": 2.25, "Francesa": 3.00, "Española": 3.00, "Americana": 3.00, "4 Estaciones": 3.00,
        "Mexicana": 3.00, "Especial": 3.00, "Suprema": 3.50, "Papi Burguer": 2.50, "A su gusto (Jumbo)": 5.00,
        "Triple Burguer": 6.00, "Doble Burguer": 4.50},
    "Hot Dogs": {"Especial Mixto": 2.25, "Especial de Pollo": 2.25, "Hot Dog con salame": 2.25,
                 "Mix Dog - Jumbo": 2.25, "Champi Dog": 2.25, "Hot Dog con cebolla": 1.75},
    "Papas Fritas": {"Salchipapa (1.50)": 1.50, "Salchipapa (1.75)": 1.75, "Papi carne": 2.25, "Papi Pollo": 2.25,
                     "Salchipapa especial": 3.25, "Papa Mix": 3.25, "Papa Wlady": 5.00},
    "Sanduches": {"Cubano": 2.00, "Vegetariano": 2.00, "Sanduche de Pollo": 2.00},
    "Bebidas": {"Colas Pequeñas": 0.75, "Jugos": 1.50, "Batidos": 1.75, "Jamaica": 0.50},
    "Porciónes": {"Papas Fritas (0.50)": 0.50, "Papas Fritas (1.00)": 1.00, "Huevo Frito": 0.50, "Presa de Pollo": 1.50}
}

ESTADOS = ["En proceso", "Entregado", "Pagado", "Cancelado"]

def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'ID' not in df.columns:
            df['ID'] = range(1, len(df) + 1)
        if 'Nombre_Orden' not in df.columns:
            df['Nombre_Orden'] = "Sin nombre"
        return df
    return pd.DataFrame(columns=['ID', 'Nombre_Orden', 'Fecha', 'Detalle', 'Total', 'Estado'])

def guardar_datos(df):
    df.to_csv(DATA_FILE, index=False)

st.title("🍔 Mi Escondite en la Amazonía - Gestor de Pedidos")

opcion = st.sidebar.selectbox("Menú", ["Registrar Pedido", "Ver Pedidos", "Cambiar Estado"])

if opcion == "Registrar Pedido":
    st.header("Registrar Nuevo Pedido")
    nombre = st.text_input("Nombre del Pedido (ej. Berta Coello, Mesa 1)", "")
    if not nombre:
        st.warning("Ingresa un nombre para identificar el pedido después.")

    total = 0.0
    seleccion = {}

    for cat, items in MENU.items():
        st.subheader(cat)
        cols = st.columns(3)
        i = 0
        for producto, precio in items.items():
            with cols[i % 3]:
                cant = st.number_input(f"{producto} (${precio:.2f})", min_value=0, value=0, step=1)
                if cant > 0:
                    seleccion[f"{cat} - {producto}"] = cant
                    total += cant * precio
            i += 1

    st.write(f"**Total: ${total:.2f}**")
    estado = st.selectbox("Estado inicial", ESTADOS, index=0)

    if st.button("Guardar Pedido"):
        if not nombre:
            st.error("Debes poner un nombre al pedido.")
        elif total == 0:
            st.error("Agrega al menos un producto.")
        else:
            df = cargar_datos()
            nuevo_id = df['ID'].max() + 1 if not df.empty else 1
            detalle = " | ".join([f"{c}x {p}" for p, c in seleccion.items()])
            nuevo = pd.DataFrame({
                'ID': [nuevo_id],
                'Nombre_Orden': [nombre],
                'Fecha': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'Detalle': [detalle],
                'Total': [round(total, 2)],
                'Estado': [estado]
            })
            df = pd.concat([df, nuevo], ignore_index=True)
            guardar_datos(df)
            st.success(f"Pedido guardado: #{nuevo_id} - {nombre} ({estado})")

elif opcion == "Ver Pedidos":
    st.header("Registro de Pedidos")
    df = cargar_datos()
    if df.empty:
        st.info("No hay pedidos.")
    else:
        estado_filtro = st.multiselect("Filtrar por estado", ESTADOS, default=ESTADOS)
        fecha_filtro = st.date_input("Filtrar por fecha", value=None)
        df_filtrado = df[df['Estado'].isin(estado_filtro)]
        if fecha_filtro:
            df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['Fecha']).dt.date == fecha_filtro]
        st.dataframe(df_filtrado.sort_values('ID', ascending=False))
        st.write(f"**Total mostrado: ${df_filtrado['Total'].sum():.2f}**")

elif opcion == "Cambiar Estado":
    st.header("Modificar Estado de Pedido")
    df = cargar_datos()
    if df.empty:
        st.info("No hay pedidos.")
    else:
        busqueda = st.text_input("Buscar por nombre o ID (ej. Berta)")
        filtrado = df[df['Nombre_Orden'].str.contains(busqueda, case=False) | df['ID'].astype(str).str.contains(busqueda)]
        if filtrado.empty:
            st.warning("No encontrado.")
        else:
            opciones = [f"#{row['ID']} - {row['Nombre_Orden']} ({row['Estado']})" for _, row in filtrado.iterrows()]
            seleccionado = st.selectbox("Selecciona", opciones)
            if seleccionado:
                pedido_id = int(seleccionado.split(" - ")[0][1:])
                pedido = df[df['ID'] == pedido_id].iloc[0]
                st.write(f"Detalle: {pedido['Detalle']}")
                st.write(f"Total: ${pedido['Total']:.2f}")
                nuevo_estado = st.selectbox("Nuevo estado", ESTADOS)
                if st.button("Actualizar"):
                    df.loc[df['ID'] == pedido_id, 'Estado'] = nuevo_estado
                    guardar_datos(df)
                    st.success(f"Actualizado a {nuevo_estado}!")

                    st.rerun()
                    # === NUEVO: BOTÓN DE DESCARGA ===
        st.markdown("### Descargar datos")
        # Convertir a CSV en memoria
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        
        st.download_button(
            label="📥 Descargar todos los pedidos como CSV (abre en Excel)",
            data=csv_buffer,
            file_name=f"pedidos_mi_escondite_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
        # === FIN NUEVO ===

Abajo haz Commit changes (mensaje: "Agregado botón de descarga diaria").

En minutos, la app se actualizará sola y verás un botón azul "Descargar todos los pedidos como CSV".
Al hacer clic, descarga un archivo con fecha del día, que abres directo en Excel.
Forma 2: Manual (sin cambiar código)
Si no quieres tocar el código:

Abre la app en tu celular o PC.
Ve a "Ver Pedidos".
Selecciona todo el contenido de la tabla (con el mouse o dedo).
Copia y pega en una hoja de Google Sheets o Excel.
O toma captura de pantalla diaria.

Pero la Forma 1 con el botón es mucho mejor y profesional.
Recomendación para tu negocio

Usa el botón nuevo para descargar al final de cada día.
Guárdalo en una carpeta en tu celular/PC o en Google Drive.
Así tienes respaldo diario de ingresos (ventas = suma de Total en "Pagado").

¿Quieres que agregue también un módulo simple de egresos/gastos (para restar compras, sueldos, etc. y ver ganancia diaria)? Dime y lo hacemos rápido.
¡Ya tienes todo para manejar ingresos profesionalmente! 💰📊3,7sFast
