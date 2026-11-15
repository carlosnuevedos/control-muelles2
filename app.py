# 1. Fecha, Matrícula y Carretillero
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_registro = st.date_input("Fecha del Registro", value=datetime.now())
    carretillero = st.selectbox("Carretillero", LISTA_CARRETILLEROS)

# Extraer matrículas existentes desde la Columna B (índice 1)
matriculas_guardadas = []
if not st.session_state.df_registros.empty:
    matriculas_guardadas = sorted(st.session_state.df_registros.iloc[:, 1].dropna().astype(str).str.strip().unique().tolist())

with col_f2:
    tipo_ingreso_mat = st.radio(
        "Matrícula:", 
        ["Seleccionar existente", "Escribir nueva"], 
        horizontal=True, 
        label_visibility="collapsed",
        key="tipo_radio_mat"  # <-- Clave única para el radio
    )
    
    if tipo_ingreso_mat == "Seleccionar existente":
        if matriculas_guardadas:
            matricula = st.selectbox("Matrícula del Vehículo", matriculas_guardadas, key="select_mat_existente")
        else:
            st.info("No hay matrículas guardadas aún.")
            matricula = ""
    else:
        matricula = st.text_input("Escribe la nueva matrícula", key="input_nueva_mat").strip().upper()