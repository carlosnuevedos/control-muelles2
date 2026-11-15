import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import time
from PIL import Image
import io
import base64

# --- FUNCIÓN PARA CONVERTIR IMÁGENES A BASE64 ---
def convertir_imagen_a_base64(ruta_imagen):
    try:
        with Image.open(ruta_imagen) as img:
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        return ""

# Cargar logo principal y los iconos de las secciones en Base64
logo_base64 = convertir_imagen_a_base64("AZENTIS-SIN-FONDO.png")
icono_lanzadera_base64 = convertir_imagen_a_base64("Lanzadera.png")
icono_clientes_base64 = convertir_imagen_a_base64("Clientes.png")

# Configuración de la página web (Título de la pestaña y favicon corporativo)
st.set_page_config(
    page_title="Control de Muelles - Azentis Persán La Red", 
    page_icon="AZENTIS-SIN-FONDO.png" if logo_base64 else "🚛", 
    layout="centered"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        h1, h2, h3 {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 700;
        }
        
        /* Estilo para que los iconos actúen como elementos fijos sin interactividad */
        .logo-icono {
            width: 75px;
            height: auto;
            pointer-events: none;
            user-select: none;
        }
        
        .seccion-icono {
            width: 32px;
            height: auto;
            vertical-align: middle;
            margin-right: 10px;
            pointer-events: none;
            user-select: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA CORPORATIVA CON LOGO HTML FIJO Y TÍTULO LIMPIO ---
col_logo, col_titulo = st.columns([0.16, 0.84])

with col_logo:
    if logo_base64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_base64}" class="logo-icono">', 
            unsafe_allow_html=True
        )
    else:
        st.write("🚛")

with col_titulo:
    st.markdown("<h2 style='padding-top: 2px; margin-bottom: 0px;'>Control de Muelles y Cargas</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #555555; font-weight: 500; margin-top: 2px;'>Azentis Persán La Red • Conectado a Google Sheets</p>", unsafe_allow_html=True)

st.divider()

# --- CONFIGURACIÓN DE URL DE APPS SCRIPT ACTUALIZADA ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyP9cpZSNJdUfEWATW0gIfot-Mg_9_wDy_LZeYY52Ln-kkrWHlQ4PhbLg1iHRcJQncj5Q/exec"

# Lista base por defecto para carretilleros
CARRETILLEROS_BASE = [
    "C. Alías", "C. Díaz", "M. José", "David", "Andreu", 
    "Raúl", "Álvaro", "Daniel", "J. A. Lara", "J. A. Vega", "Sergio", "Samuel"
]

# Columnas oficiales para Lanzaderas
COLS_NECESARIAS_LANZADERAS = [
    "Fecha Registro", "Matrícula", "Albarán", "Operación",
    "Hora Llegada", "Hora Inicio", "Hora Fin", 
    "Min. Espera", "Min. Operación", "Min. Totales",
    "Pallets", "Carretillero", "Turno", "Incidencias"
]

# --- FUNCIÓN PARA CARGAR DESDE GOOGLE SHEETS ---
def cargar_registros_desde_sheets():
    try:
        url_fresca = f"{WEB_APP_URL}?nocache={time.time()}"
        response = requests.post(url_fresca, json={"action": "leer"})
        if response.status_code == 200:
            data = response.json()
            if "rows" in data and len(data["rows"]) > 1:
                rows = data["rows"]
                data_rows = rows[1:] # Omitir cabecera
                
                df = pd.DataFrame(data_rows)
                if df.shape[1] >= len(COLS_NECESARIAS_LANZADERAS):
                    df = df.iloc[:, :len(COLS_NECESARIAS_LANZADERAS)]
                    df.columns = COLS_NECESARIAS_LANZADERAS
                    return df
    except Exception as e:
        pass
    
    return pd.DataFrame(columns=COLS_NECESARIAS_LANZADERAS)

# Cargar de Google Sheets al iniciar la sesión en memoria
if "df_registros" not in st.session_state:
    st.session_state.df_registros = cargar_registros_desde_sheets()

# Función para calcular el turno según la hora y minuto de INICIO
def calcular_turno(hora, minuto):
    total_minutos = (hora * 60) + minuto
    if 360 <= total_minutos <= 835:
        return "Mañana"
    elif 840 <= total_minutos <= 1315:
        return "Tarde"
    else:
        return "Noche"

# Listas para los desplegables de hora y minutos
lista_horas = list(range(0, 24))
lista_minutos = list(range(0, 60, 5))

# Ancla invisible arriba del todo
st.markdown("<div id='top-section'></div>", unsafe_allow_html=True)

# ==========================================
# SELECTOR DE MODO / APARTADO PRINCIPAL
# ==========================================
st.sidebar.title("Navegación")
modo_app = st.sidebar.radio("Selecciona el apartado:", ["Control Lanzaderas", "Cargas de Cliente"])

# Gestión dinámica de carretilleros
carretilleros_existentes = list(CARRETILLEROS_BASE)
if not st.session_state.df_registros.empty and len(st.session_state.df_registros.columns) > 11:
    col_carretilleros_historico = st.session_state.df_registros.iloc[:, 11].dropna().astype(str).str.strip().unique().tolist()
    for c in col_carretilleros_historico:
        if c and c not in carretilleros_existentes:
            carretilleros_existentes.append(c)

if "carretilleros_extra" not in st.session_state:
    st.session_state.carretilleros_extra = []

for c in st.session_state.carretilleros_extra:
    if c not in carretilleros_existentes:
        carretilleros_existentes.append(c)

carretilleros_existentes = sorted(carretilleros_existentes)


# ==============================================================================
# SECCIÓN 1: CONTROL DE LANZADERAS
# ==============================================================================
if modo_app == "Control Lanzaderas":
    if icono_lanzadera_base64:
        st.markdown(
            f"<h3 style='display: flex; align-items: center;'><img src='data:image/png;base64,{icono_lanzadera_base64}' class='seccion-icono'> Nuevo Registro de Vehículo (Lanzaderas)</h3>", 
            unsafe_allow_html=True
        )
    else:
        st.subheader("🚛 Nuevo Registro de Vehículo (Lanzaderas)")

    if "modo_mat" not in st.session_state:
        st.session_state.modo_mat = "Seleccionar existente"
    if "modo_carr" not in st.session_state:
        st.session_state.modo_carr = "Seleccionar existente"

    matriculas_guardadas = []
    if not st.session_state.df_registros.empty:
        matriculas_guardadas = sorted(st.session_state.df_registros.iloc[:, 1].dropna().astype(str).str.strip().unique().tolist())

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        fecha_registro = st.date_input("Fecha del Registro", value=datetime.now(), key="f_lanz")

    with col_f2:
        st.markdown('<p style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: inherit;">Carretillero</p>', unsafe_allow_html=True)
        
        if st.session_state.modo_carr == "Seleccionar existente":
            carretillero = st.selectbox("Carretillero", carretilleros_existentes, label_visibility="collapsed", key="select_carretillero_existente_lanz")
        else:
            col_nc1, col_nc2 = st.columns([0.75, 0.25])
            with col_nc1:
                nuevo_carr = st.text_input("Nombre del nuevo carretillero", placeholder="Ej: J. Pérez", label_visibility="collapsed", key="input_nuevo_carr_lanz").strip()
            with col_nc2:
                btn_add_carr = st.button("Añadir", key="btn_guardar_nuevo_carr_lanz")
            
            if btn_add_carr:
                if nuevo_carr:
                    if nuevo_carr not in st.session_state.carretilleros_extra:
                        st.session_state.carretilleros_extra.append(nuevo_carr)
                    st.success(f"¡'{nuevo_carr}' añadido!")
                    st.session_state.modo_carr = "Seleccionar existente"
                    st.rerun()
                else:
                    st.warning("Escribe un nombre.")
            
            carretillero = nuevo_carr if nuevo_carr else (carretilleros_existentes[0] if carretilleros_existentes else "")

        nuevo_modo_carr = st.radio(
            "Modo Carretillero", 
            ["Seleccionar existente", "➕ Añadir nuevo"], 
            index=0 if st.session_state.modo_carr == "Seleccionar existente" else 1,
            horizontal=True, 
            label_visibility="collapsed",
            key="radio_modo_carr_lanz"
        )
        if nuevo_modo_carr != st.session_state.modo_carr:
            st.session_state.modo_carr = nuevo_modo_carr
            st.rerun()

    with col_f1:
        st.markdown("##### Matrícula del Vehículo")
        if st.session_state.modo_mat == "Seleccionar existente":
            if matriculas_guardadas:
                matricula = st.selectbox("Matrícula", matriculas_guardadas, label_visibility="collapsed", key="select_mat_existente_lanz")
            else:
                st.info("No hay matrículas guardadas.")
                matricula = ""
        else:
            matricula = st.text_input("Escribe la nueva matrícula", placeholder="Ej: 1234ABC", label_visibility="collapsed", key="input_nueva_mat_lanz").strip().upper()

        nuevo_modo_mat = st.radio(
            "Modo Matrícula", 
            ["Seleccionar existente", "Escribir nueva"], 
            index=0 if st.session_state.modo_mat == "Seleccionar existente" else 1,
            horizontal=True, 
            label_visibility="collapsed",
            key="radio_modo_mat_lanz"
        )
        if nuevo_modo_mat != st.session_state.modo_mat:
            st.session_state.modo_mat = nuevo_modo_mat
            st.rerun()

    st.divider()

    # BLOQUE 1: DESCARGA
    activar_descarga = st.checkbox("📥 Registrar DESCARGA de mercancía", key="chk_descarga")
    albaran_descarga = ""
    pallets_descarga = 33
    d_llegada_h = d_llegada_m = d_inicio_h = d_inicio_m = d_fin_h = d_fin_m = 8

    t_lleg_d = 0
    t_ini_d = 0
    t_fin_d = 0

    if activar_descarga:
        st.markdown("#### Tiempos de Descarga")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            albaran_descarga = st.text_input("Nº de Albarán (Descarga)", key="alb_desc")
        with col_d2:
            opcion_pallets_d = st.selectbox("Pallets Descargados", ["33", "26", "Otra cantidad"], key="opt_p_desc")
            if opcion_pallets_d == "Otra cantidad":
                pallets_descarga = st.number_input("Especifica cantidad de pallets", min_value=1, max_value=200, value=33, key="p_desc_otro")
            else:
                pallets_descarga = int(opcion_pallets_d)
        
        st.write("**Horarios de Descarga:**")
        c_lh, c_lm = st.columns(2)
        with c_lh:
            d_llegada_h = st.selectbox("Hora Llegada (Descarga)", lista_horas, index=8, key="dl_h")
        with c_lm:
            d_llegada_m = st.selectbox("Minutos Llegada (Descarga)", lista_minutos, index=0, key="dl_m")
            
        c_ih, c_im = st.columns(2)
        with c_ih:
            d_inicio_h = st.selectbox("Hora Inicio (Descarga)", lista_horas, index=8, key="di_h")
        with c_im:
            d_inicio_m = st.selectbox("Minutos Inicio (Descarga)", lista_minutos, index=0, key="di_m")
            
        c_fh, c_fm = st.columns(2)
        with c_fh:
            d_fin_h = st.selectbox("Hora Fin (Descarga)", lista_horas, index=9, key="df_h")
        with c_fm:
            d_fin_m = st.selectbox("Minutos Fin (Descarga)", lista_minutos, index=0, key="df_m")

        t_lleg_d = (d_llegada_h * 60) + d_llegada_m
        t_ini_d = (d_inicio_h * 60) + d_inicio_m
        t_fin_d = (d_fin_h * 60) + d_fin_m
        if t_ini_d < t_lleg_d or t_fin_d < t_ini_d:
            st.error("⚠️ [Descarga] Incongruencia horaria: La llegada debe ser anterior al inicio, y el inicio anterior al fin.")

    st.divider()

    # BLOQUE 2: CARGA
    activar_carga = st.checkbox("📤 Registrar CARGA de mercancía", key="chk_carga")
    albaran_carga = ""
    pallets_carga = 33
    c_llegada_h = 9
    c_llegada_m = 0
    c_inicio_h = 9
    c_inicio_m = 0
    c_fin_h = 10
    c_fin_m = 0

    t_lleg_c = 0
    t_ini_c = 0
    t_fin_c = 0

    if activar_carga:
        st.markdown("#### Tiempos y Referencia de Carga (Lanzadera)")
        col_tc1, col_tc2, col_tc3 = st.columns(3)
        with col_tc1:
            tipo_lanzadera = st.selectbox("Tipo de Referencia", ["P (Lanzadera)", "M (Lanzadera)", "Albarán Personalizado"], key="tipo_lanz")
        
        str_fecha_ddmmaa = fecha_registro.strftime("%d%m%y")
        df_actual = st.session_state.df_registros
        
        if tipo_lanzadera in ["P (Lanzadera)", "M (Lanzadera)"]:
            letra_prefijo = "P" if tipo_lanzadera.startswith("P") else "M"
            siguiente_num = 1
            if not df_actual.empty:
                prefijo_buscado = f"{letra_prefijo}{str_fecha_ddmmaa}-".upper()
                conteo_coincidencias = sum(1 for _, row in df_actual.iterrows() if str(row.iloc[2]).strip().upper().startswith(prefijo_buscado))
                siguiente_num = conteo_coincidencias + 1
            sugerencia_codigo = f"{letra_prefijo}{str_fecha_ddmmaa}-{siguiente_num}"
            
            st.session_state["input_albaran_lanz"] = sugerencia_codigo
            
            with col_tc2:
                albaran_carga = st.text_input("Nº Albarán", key="input_albaran_lanz")
        else:
            with col_tc2:
                albaran_carga = st.text_input("Nº Albarán", placeholder="Ej: ALB-12345", key="input_albaran_custom")

        with col_tc3:
            opcion_pallets_c = st.selectbox("Pallets Cargados", ["33", "26", "Otra cantidad"], key="opt_p_carg")
            if opcion_pallets_c == "Otra cantidad":
                pallets_carga = st.number_input("Especifica pallets", min_value=1, max_value=200, value=33, key="p_carg_otro")
            else:
                pallets_carga = int(opcion_pallets_c)
        
        if activar_descarga:
            c_llegada_h = d_fin_h
            c_llegada_m = d_fin_m
            st.info(f"ℹ️ El camión ya está en las instalaciones (Llegada heredada de la descarga a las {c_llegada_h:02d}:{c_llegada_m:02d}).")
        else:
            st.write("**Horarios de Carga (Vehículo externo que solo carga):**")
            cl_lh, cl_lm = st.columns(2)
            with cl_lh:
                c_llegada_h = st.selectbox("Hora Llegada (Carga)", lista_horas, index=9, key="cl_h")
            with cl_lm:
                c_llegada_m = st.selectbox("Minutos Llegada (Carga)", lista_minutos, index=0, key="cl_m")
            
        ci_h, ci_im = st.columns(2)
        with ci_h:
            c_inicio_h = st.selectbox("Hora Inicio (Carga)", lista_horas, index=c_llegada_h, key="ci_h")
        with ci_im:
            c_inicio_m = st.selectbox("Minutos Inicio (Carga)", lista_minutos, index=0, key="ci_im")
            
        cf_h, cf_fm = st.columns(2)
        with cf_h:
            c_fin_h = st.selectbox("Hora Fin (Carga)", lista_horas, index=c_inicio_h + 1 if c_inicio_h < 23 else 23, key="cf_h")
        with cf_fm:
            c_fin_m = st.selectbox("Minutos Fin (Carga)", lista_minutos, index=0, key="cf_m")

        t_lleg_c = (c_llegada_h * 60) + c_llegada_m
        t_ini_c = (c_inicio_h * 60) + c_inicio_m
        t_fin_c = (c_fin_h * 60) + c_fin_m
        if t_ini_c < t_lleg_c or t_fin_c < t_ini_c:
            st.error("⚠️ [Carga] Incongruencia horaria: La hora de inicio no puede ser anterior a la de llegada, ni la de fin anterior a la de inicio.")

    incidencias = st.text_area("Incidencias Generales (opcional)", placeholder="Ej: Retraso en documentación...", key="incidencias_input_lanz")
    submitted_lanz = st.button("Guardar Registros (Lanzaderas)")

    if submitted_lanz:
        if not matricula:
            st.error("Por favor, introduce o selecciona una matrícula.")
        elif not carretillero:
            st.error("Por favor, selecciona o introduce un carretillero.")
        elif not activar_descarga and not activar_carga:
            st.warning("Debes marcar al menos una opción: Descarga o Carga.")
        else:
            error_horario = False
            if activar_descarga and (t_ini_d < t_lleg_d or t_fin_d < t_ini_d):
                error_horario = True
            if activar_carga and (t_ini_c < t_lleg_c or t_fin_c < t_ini_c):
                error_horario = True

            if error_horario:
                st.error("❌ No se puede guardar: Revisa los avisos en rojo de los horarios.")
            else:
                try:
                    nuevos_datos = []
                    texto_incidencias = incidencias.strip() if incidencias else ""
                    
                    if activar_descarga:
                        min_esp_d = t_ini_d - t_lleg_d
                        min_op_d = t_fin_d - t_ini_d
                        min_tot_d = "" if activar_carga else (t_fin_d - t_lleg_d)
                        turno_calc_d = calcular_turno(d_inicio_h, d_inicio_m)
                        nuevos_datos.append([
                            fecha_registro.strftime("%Y-%m-%d"), matricula.upper(),
                            albaran_descarga if albaran_descarga else "S/A", "Descarga",
                            f"{d_llegada_h:02d}:{d_llegada_m:02d}", f"{d_inicio_h:02d}:{d_inicio_m:02d}", f"{d_fin_h:02d}:{d_fin_m:02d}",
                            int(min_esp_d), int(min_op_d), min_tot_d if min_tot_d == "" else int(min_tot_d),
                            int(pallets_descarga), carretillero, turno_calc_d, texto_incidencias
                        ])

                    if activar_carga:
                        min_esp_c = 0 if activar_descarga else (t_ini_c - t_lleg_c)
                        hora_llegada_str = f"{d_fin_h:02d}:{d_fin_m:02d} (Post-Descarga)" if activar_descarga else f"{c_llegada_h:02d}:{c_llegada_m:02d}"
                        min_tot_c = (t_fin_c - t_lleg_d) if activar_descarga else (t_fin_c - t_lleg_c)
                        min_op_c = t_fin_c - t_inicio_c
                        turno_calc_c = calcular_turno(c_inicio_h, c_inicio_m)
                        nuevos_datos.append([
                            fecha_registro.strftime("%Y-%m-%d"), matricula.upper(),
                            albaran_carga if albaran_carga else "S/A", "Carga",
                            hora_llegada_str, f"{c_inicio_h:02d}:{c_inicio_m:02d}", f"{c_fin_h:02d}:{c_fin_m:02d}",
                            int(min_esp_c), int(min_op_c), int(min_tot_c),
                            int(pallets_carga), carretillero, turno_calc_c, texto_incidencias
                        ])

                    response = requests.post(WEB_APP_URL, json={"action": "update", "rows": nuevos_datos})
                    if response.status_code == 200:
                        st.success(f"✅ ¡Guardado en Google Sheets para **{matricula.upper()}**!")
                        st.balloons()
                        
                        # Borrar claves del estado para restablecer formulario
                        for c in ["input_nueva_mat_lanz", "alb_desc", "input_albaran_lanz", "input_albaran_custom", "chk_descarga", "chk_carga", "incidencias_input_lanz"]:
                            if c in st.session_state: del st.session_state[c]
                        st.session_state.df_registros = cargar_registros_desde_sheets()
                        
                        # TRUCO DEFINITIVO: Cambiar query_params para obligar al navegador a subir arriba al recargar
                        st.query_params["recarga"] = str(time.time())
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Error en servidor: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.divider()
    st.subheader("📊 Historial de Lanzaderas (En Memoria)")
    if not st.session_state.df_registros.empty:
        st.dataframe(st.session_state.df_registros, use_container_width=True)
    else:
        st.info("Aún no hay registros.")


# ==============================================================================
# SECCIÓN 2: CARGAS DE CLIENTE
# ==============================================================================
elif modo_app == "Cargas de Cliente":
    if icono_clientes_base64:
        st.markdown(
            f"<h3 style='display: flex; align-items: center;'><img src='data:image/png;base64,{icono_clientes_base64}' class='seccion-icono'> Nuevo Registro de Carga de Cliente</h3>", 
            unsafe_allow_html=True
        )
    else:
        st.subheader("📦 Nuevo Registro de Carga de Cliente")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fecha_cliente = st.date_input("Fecha del Registro", value=datetime.now(), key="f_cli")
        transporte = st.text_input("Número de Transporte", placeholder="Ej: TR-98765", key="num_transporte")

    with col_c2:
        st.markdown('<p style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: inherit;">Carretillero</p>', unsafe_allow_html=True)
        carretillero_cli = st.selectbox("Carretillero (Cliente)", carretilleros_existentes, label_visibility="collapsed", key="sel_carr_cli")
        
        opcion_pallets_cli = st.selectbox("Número de Pallets", ["33", "26", "24", "21", "50", "Otra cantidad"], key="opt_p_cli")
        if opcion_pallets_cli == "Otra cantidad":
            num_pallets_cli = st.number_input("Especifica número de pallets", min_value=1, max_value=200, value=33, key="p_cli_otro")
        else:
            num_pallets_cli = int(opcion_pallets_cli)

    st.markdown("#### Horarios y Control")
    
    st.write("**Hora Picada:**")
    c_ph1, c_ph2 = st.columns(2)
    with c_ph1:
        ph_h = st.selectbox("Hora Picada", lista_horas, index=8, key="ph_h")
    with c_ph2:
        ph_m = st.selectbox("Minutos Picada", lista_minutos, index=0, key="ph_m")

    st.write("**Hora Comienzo:**")
    c_ci1, c_ci2 = st.columns(2)
    with c_ci1:
        ci_h = st.selectbox("Hora Comienzo", lista_horas, index=8, key="ci_cli_h")
    with c_ci2:
        ci_m = st.selectbox("Minutos Comienzo", lista_minutos, index=0, key="ci_cli_m")

    st.write("**Hora Fin:**")
    c_cf1, c_cf2 = st.columns(2)
    with c_cf1:
        cf_h = st.selectbox("Hora Fin", lista_horas, index=9, key="cf_cli_h")
    with c_cf2:
        cf_m = st.selectbox("Minutos Fin", lista_minutos, index=0, key="cf_m")

    opcion_etiquetas = st.selectbox("¿Lleva etiquetas?", ["", "Sí", "No"], key="opt_etiquetas")

    incidencias_cli = st.text_area("Incidencias (opcional)", placeholder="Ej: Falta de stock, retraso...", key="inc_cli")

    submitted_cli = st.button("Guardar Carga de Cliente")

    if submitted_cli:
        if not transporte:
            st.error("Por favor, introduce el número de transporte.")
        else:
            t_picada = (ph_h * 60) + ph_m
            t_comienzo = (ci_h * 60) + ci_m
            t_fin = (cf_h * 60) + cf_m

            if t_comienzo < t_picada or t_fin < t_comienzo:
                st.error("⚠️ Incongruencia horaria: La hora picada debe ser anterior al comienzo, y el comienzo anterior al fin.")
            else:
                try:
                    min_operacion = t_fin - t_comienzo
                    min_espera_totales = t_fin - t_picada
                    turno_calc_cli = calcular_turno(ci_h, ci_m)
                    
                    fila_cliente = [[
                        fecha_cliente.strftime("%Y-%m-%d"),
                        transporte.strip().upper(),
                        f"{ph_h:02d}:{ph_m:02d}",
                        f"{ci_h:02d}:{ci_m:02d}",
                        f"{cf_h:02d}:{cf_m:02d}",
                        int(min_operacion),
                        int(min_espera_totales),
                        int(num_pallets_cli),
                        carretillero_cli,
                        opcion_etiquetas,
                        turno_calc_cli,
                        incidencias_cli.strip() if incidencias_cli else ""
                    ]]

                    response = requests.post(WEB_APP_URL, json={"action": "update_cliente", "rows": fila_cliente})
                    
                    if response.status_code == 200:
                        st.success(f"✅ ¡Carga de cliente **{transporte.upper()}** guardada en la pestaña 'Cargas de cliente'!")
                        st.balloons()
                        
                        claves_cli_a_borrar = ["num_transporte", "inc_cli", "opt_etiquetas", "p_cli_otro", "sel_carr_cli"]
                        for clave in claves_cli_a_borrar:
                            if clave in st.session_state:
                                del st.session_state[clave]

                        # TRUCO DEFINITIVO: Cambiar query_params para obligar al navegador a subir arriba al recargar
                        st.query_params["recarga"] = str(time.time())
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Error al conectar con Google Sheets: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")