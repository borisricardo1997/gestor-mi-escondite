# ... (todo el código anterior hasta la sección de Cierre de Caja permanece igual)

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

                st.success("¡Caja cerrada y día limpiado! Para registrar nuevos pedidos, debes abrir caja nuevamente.")
                if 'confirmar_cierre' in st.session_state:
                    del st.session_state.confirmar_cierre
                st.rerun()

# (El resto del código permanece igual)
