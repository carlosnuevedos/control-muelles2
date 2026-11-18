import streamlit as st
from datetime import datetime, timezone, timedelta
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

# Cargar logo principal y los iconos en Base64
logo_base64 = convertir_imagen_a_base64("AZENTIS-SIN-FONDO.png")
icono_lanzadera_base64 = convertir_imagen_a_base64("Lanzadera.png")
icono_clientes_base64 = convertir_imagen_a_base64("Clientes.png")
icono_pallet_base64 = convertir_imagen_a_base64("Pallet.png")

# Configuración de la página web
st.set_page_config(
    page_title="Registro de Actividad - Azentis Persán La Red", 
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

        /* --- BOTÓN FLOTANTE MINIMALISTA BLANCO, TRANSLÚCIDO Y CON SOMBRA --- */
        .btn-flotante-arriba {
            position: fixed;
            bottom: 85px;
            right: 25px;
            background-color: rgba(255, 255, 255, 0.85);
            color: #000000 !important;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            text-align: center;
            box-shadow: 0px 6px 20px rgba(0, 0, 0, 0.25);
            z-index: 99999;
            text-decoration: none;
            font-weight: 700;
            font-size: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(6px);
            border: 1px solid rgba(0, 0, 0, 0.08);
            transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
        }
        .btn-flotante-arriba:hover {
            background-color: rgba(255, 255, 255, 1);
            transform: scale(1.08);
            box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.35);
            color: #000000 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Botón flotante para subir arriba
st.markdown(
    '<a href="#top-section" class="btn-flotante-arriba" title="Volver arriba">↑</a>',
    unsafe_allow_html=True
)

# Cabecera corporativa
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
    st.markdown("<h2 style='padding-top: 2px; margin-bottom: 0px;'>Registro de Actividad</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #555555; font-weight: 500; margin-top: 2px;'>Azentis Persán La Red • Conectado a Google Sheets</p>", unsafe_allow_html=True)

st.divider()

# --- CONFIGURACIÓN DE URL DE APPS SCRIPT ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyP9cpZSNJdUfEWATW0gIfot-Mg_9_wDy_LZeYY52Ln-kkrWHlQ4PhbLg1iHRcJQncj5Q/exec"

# LISTA BASE FIJA DE CARRETILLEROS
CARRETILLEROS_BASE = [
    "C. Alías", "C. Díaz", "M. José", "David", "Andreu", 
    "Raúl", "Álvaro", "Daniel", "J. A. Lara", "J. A. Vega", "Sergio", "Samuel"
]

# ESTRUCTURAS EXACTAS POR HOJA
COLS_NECESARIAS_LANZADERAS = [
    "Fecha Registro", "Mes", "Matrícula", "Albarán", "Operación",
    "Hora Llegada", "Hora Inicio", "Hora Fin", 
    "Min. Espera", "Min. Operación", "Min. Totales",
    "Pallets", "Carretillero", "Turno", "Incidencias", "Semana", "Día"
]

COLS_NECESARIAS_CLIENTES = [
    "Fecha Registro", "Mes", "Nº Transporte", "H. Picada", "H. Comienzo", 
    "Hora Fin", "Min. Operación", "Min. Espera totales", "Pallets", 
    "Carretillero", "¿Etiquetas?", "Turno", "Incidencia", "Semana", "Día"
]

COLS_NECESARIAS_PRODUCCION = [
    "Fecha Registro", "Mes", "Día", "Semana", "Carretillero", 
    "Pallets Maquilado", "Pallets Chequeo", "Tiempo Maquilado", "Tiempo Chequeo", "Turno"
]

COLS_NECESARIAS_REUB = [
    "Fecha Registro", "Mes", "Turno", "Semana", "Día",
    "Carretillero R.", "Nº Pallets Reub.",
    "Carretillero C.", "Nº Compact.", "Tiempo Compact",
    "Carretillero NCT", "Nº Pedido", "Nº Cajas", "Tiempo NCT"
]

# --- FUNCIONES DE LECTURA ROBUSTAS (DESDE FILA 5 -> ÍNDICE 4) ---
def procesar_filas_hoja(raw_rows, cols_esperadas):
    if not raw_rows or len(raw_rows) <= 4:
        return pd.DataFrame(columns=cols_esperadas)
    
    # Tomamos las filas desde la fila 5 en adelante (índice 4)
    datos_validos = []
    for r in raw_rows[4:]:
        if len(r) > 0 and str(r[0]).strip() != "":
            # Aseguramos que la fila tenga suficientes elementos rellenando con ""
            fila_normalizada = list(r) + [""] * (len(cols_esperadas) - len(r))
            datos_validos.append(fila_normalizada[:len(cols_esperadas)])
            
    if not datos_validos:
        return pd.DataFrame(columns=cols_esperadas)
        
    return pd.DataFrame(datos_validos, columns=cols_esperadas)

def cargar_registros_lanzaderas():
    try:
        url_fresca = f"{WEB_APP_URL}?nocache={time.time()}"
        response = requests.post(url_fresca, json={"action": "leer"})
        if response.status_code == 200:
            data = response.json()
            return procesar_filas_hoja(data.get("rows", []), COLS_NECESARIAS_LANZADERAS)
    except Exception:
        pass
    return pd.DataFrame(columns=COLS_NECESARIAS_LANZADERAS)

def cargar_registros_clientes():
    try:
        url_fresca = f"{WEB_APP_URL}?nocache={time.time()}"
        response = requests.post(url_fresca, json={"action": "leer_clientes"})
        if response.status_code == 200:
            data = response.json()
            return procesar_filas_hoja(data.get("rows", []), COLS_NECESARIAS_CLIENTES)
    except Exception:
        pass
    return pd.DataFrame(columns=COLS_NECESARIAS_CLIENTES)

def cargar_registros_produccion():
    try:
        url_fresca = f"{WEB_APP_URL}?nocache={time.time()}"
        response = requests.post(url_fresca, json={"action": "leer_produccion"})
        if response.status_code == 200:
            data = response.json()
            return procesar_filas_hoja(data.get("rows", []), COLS_NECESARIAS_PRODUCCION)
    except Exception:
        pass
    return pd.DataFrame(columns=COLS_NECESARIAS_PRODUCCION)

def cargar_registros_reub():
    try:
        url_fresca = f"{WEB_APP_URL}?nocache={time.time()}"
        response = requests.post(url_fresca, json={"action": "leer_reub"})
        if response.status_code == 200:
            data = response.json()
            return procesar_filas_hoja(data.get("rows", []), COLS_NECESARIAS_REUB)
    except Exception:
        pass
    return pd.DataFrame(columns=COLS_NECESARIAS_REUB)

# Cargar estados en memoria
if "df_registros" not in st.session_state:
    st.session_state.df_registros = cargar_registros_lanzaderas()
if "df_clientes" not in st.session_state:
    st.session_state.df_clientes = cargar_registros_clientes()
if "df_produccion" not in st.session_state:
    st.session_state.df_produccion = cargar_registros_produccion()
if "df_reub" not in st.session_state:
    st.session_state.df_reub = cargar_registros_reub()

zona_espana = timezone(timedelta(hours=1))
fecha_hoy_local = datetime.now(zona_espana).date() if hasattr(datetime, 'now') else datetime.now().date()

def calcular_turno(hora, minuto):
    total_minutos = (hora * 60) + minuto
    if 360 <= total_minutos <= 835:
        return "Mañana"
    elif 840 <= total_minutos <= 1315:
        return "Tarde"
    else:
        return "Noche"

lista_horas = list(range(0, 24))
lista_minutos = list(range(0, 60, 5))
lista_horas_prod = list(range(0, 9))
lista_minutos_15 = [0, 15, 30, 45]

st.markdown("<div id='top-section'></div>", unsafe_allow_html=True)

# ==========================================
# GESTIÓN FIJA DE CARRETILLEROS + EXTRA EN SESIÓN
# ==========================================
if "carretilleros_extra" not in st.session_state:
    st.session_state.carretilleros_extra = []

def obtener_lista_carretilleros():
    lista = list(CARRETILLEROS_BASE)
    for c in st.session_state.carretilleros_extra:
        if c not in lista:
            lista.append(c)
    return sorted(lista)

# ==========================================
# NAVEGACIÓN PRINCIPAL
# ==========================================
st.sidebar.title("Navegación")
modo_app = st.sidebar.radio(
    "Selecciona el apartado:", 
    ["Control Lanzaderas", "Cargas de Cliente", "Producción", "Reubicaciones, Compactaciones y NCT's"]
)


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
    if "modo_carr_lanz" not in st.session_state:
        st.session_state.modo_carr_lanz = "Seleccionar existente"

    carretilleros_actuales = obtener_lista_carretilleros()
    matriculas_guardadas = []
    if not st.session_state.df_registros.empty and "Matrícula" in st.session_state.df_registros.columns:
        matriculas_guardadas = sorted([
            m for m in st.session_state.df_registros["Matrícula"].dropna().astype(str).str.strip().unique().tolist()
            if m and m != "Matrícula" and m.lower() != "noviembre" and m.lower() != "octubre"
        ])

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        fecha_registro = st.date_input("Fecha del Registro", value=fecha_hoy_local, key="f_lanz")

    with col_f2:
        st.markdown('<p style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: inherit;">Carretillero</p>', unsafe_allow_html=True)
        if st.session_state.modo_carr_lanz == "Seleccionar existente":
            carretillero = st.selectbox("Carretillero", carretilleros_actuales, label_visibility="collapsed", key="select_carretillero_existente_lanz")
        else:
            col_nc1, col_nc2 = st.columns([0.75, 0.25])
            with col_nc1:
                nuevo_carr = st.text_input("Nombre", placeholder="Ej: J. Pérez", label_visibility="collapsed", key="input_nuevo_carr_lanz").strip()
            with col_nc2:
                btn_add_carr = st.button("Añadir", key="btn_guardar_nuevo_carr_lanz")
            if btn_add_carr and nuevo_carr:
                if nuevo_carr not in st.session_state.carretilleros_extra:
                    st.session_state.carretilleros_extra.append(nuevo_carr)
                st.success(f"¡'{nuevo_carr}' añadido!")
                st.session_state.modo_carr_lanz = "Seleccionar existente"
                st.rerun()
            carretillero = nuevo_carr if nuevo_carr else (carretilleros_actuales[0] if carretilleros_actuales else "")

        nuevo_modo_carr = st.radio("Modo Carretillero", ["Seleccionar existente", "➕ Añadir nuevo"], index=0 if st.session_state.modo_carr_lanz == "Seleccionar existente" else 1, horizontal=True, label_visibility="collapsed", key="radio_modo_carr_lanz")
        if nuevo_modo_carr != st.session_state.modo_carr_lanz:
            st.session_state.modo_carr_lanz = nuevo_modo_carr
            st.rerun()

    with col_f1:
        st.markdown("##### Matrícula del Vehículo")
        if st.session_state.modo_mat == "Seleccionar existente":
            matricula = st.selectbox("Matrícula", matriculas_guardadas if matriculas_guardadas else [""], label_visibility="collapsed", key="select_mat_existente_lanz")
        else:
            matricula = st.text_input("Nueva matrícula", placeholder="Ej: 1234ABC", label_visibility="collapsed", key="input_nueva_mat_lanz").strip().upper()

        nuevo_modo_mat = st.radio("Modo Matrícula", ["Seleccionar existente", "Escribir nueva"], index=0 if st.session_state.modo_mat == "Seleccionar existente" else 1, horizontal=True, label_visibility="collapsed", key="radio_modo_mat_lanz")
        if nuevo_modo_mat != st.session_state.modo_mat:
            st.session_state.modo_mat = nuevo_modo_mat
            st.rerun()

    st.divider()

    activar_descarga = st.checkbox("📥 Registrar DESCARGA de mercancía", key="chk_descarga")
    albaran_descarga = ""
    pallets_descarga = 33
    d_llegada_h = d_llegada_m = d_inicio_h = d_inicio_m = d_fin_h = d_fin_m = 8
    t_lleg_d = t_ini_d = t_fin_d = 0

    if activar_descarga:
        st.markdown("#### Tiempos de Descarga")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            albaran_descarga = st.text_input("Nº de Albarán (Descarga)", key="alb_desc")
        with col_d2:
            opcion_pallets_d = st.selectbox("Pallets Descargados", ["33", "26", "Otra cantidad"], key="opt_p_desc")
            pallets_descarga = st.number_input("Especifica cantidad", min_value=1, max_value=200, value=33, key="p_desc_otro") if opcion_pallets_d == "Otra cantidad" else int(opcion_pallets_d)
        
        c_lh, c_lm = st.columns(2)
        with c_lh: d_llegada_h = st.selectbox("Hora Llegada", lista_horas, index=8, key="dl_h")
        with c_lm: d_llegada_m = st.selectbox("Minutos Llegada", lista_minutos, index=0, key="dl_m")
        c_ih, c_im = st.columns(2)
        with c_ih: d_inicio_h = st.selectbox("Hora Inicio", lista_horas, index=8, key="di_h")
        with c_im: d_inicio_m = st.selectbox("Minutos Inicio", lista_minutos, index=0, key="di_m")
        c_fh, c_fm = st.columns(2)
        with c_fh: d_fin_h = st.selectbox("Hora Fin", lista_horas, index=9, key="df_h")
        with c_fm: d_fin_m = st.selectbox("Minutos Fin", lista_minutos, index=0, key="df_m")

        t_lleg_d = (d_llegada_h * 60) + d_llegada_m
        t_ini_d = (d_inicio_h * 60) + d_inicio_m
        t_fin_d = (d_fin_h * 60) + d_fin_m

    st.divider()

    activar_carga = st.checkbox("📤 Registrar CARGA de mercancía", key="chk_carga")
    albaran_carga = ""
    pallets_carga = 33
    c_llegada_h = c_inicio_h = 9
    c_llegada_m = c_inicio_m = 0
    c_fin_h = 10
    c_fin_m = 0
    t_lleg_c = t_ini_c = t_fin_c = 0

    if activar_carga:
        st.markdown("#### Tiempos y Referencia de Carga")
        col_tc1, col_tc2, col_tc3 = st.columns(3)
        with col_tc1: tipo_lanzadera = st.selectbox("Tipo de Referencia", ["P (Lanzadera)", "M (Lanzadera)", "Albarán Personalizado"], key="tipo_lanz")
        
        str_fecha_ddmmaa = fecha_registro.strftime("%d%m%y")
        if tipo_lanzadera in ["P (Lanzadera)", "M (Lanzadera)"]:
            letra_prefijo = "P" if tipo_lanzadera.startswith("P") else "M"
            siguiente_num = 1
            if not st.session_state.df_registros.empty and "Albarán" in st.session_state.df_registros.columns:
                prefijo_buscado = f"{letra_prefijo}{str_fecha_ddmmaa}-".upper()
                siguiente_num = sum(1 for alb in st.session_state.df_registros["Albarán"] if str(alb).strip().upper().startswith(prefijo_buscado)) + 1
            st.session_state["input_albaran_lanz"] = f"{letra_prefijo}{str_fecha_ddmmaa}-{siguiente_num}"
            with col_tc2: albaran_carga = st.text_input("Nº Albarán", key="input_albaran_lanz")
        else:
            with col_tc2: albaran_carga = st.text_input("Nº Albarán", placeholder="Ej: ALB-12345", key="input_albaran_custom")

        with col_tc3:
            opcion_pallets_c = st.selectbox("Pallets Cargados", ["33", "26", "Otra cantidad"], key="opt_p_carg")
            pallets_carga = st.number_input("Especifica pallets", min_value=1, max_value=200, value=33, key="p_carg_otro") if opcion_pallets_c == "Otra cantidad" else int(opcion_pallets_c)

        if activar_descarga:
            c_llegada_h, c_llegada_m = d_fin_h, d_fin_m
        else:
            cl_lh, cl_lm = st.columns(2)
            with cl_lh: c_llegada_h = st.selectbox("Hora Llegada (Carga)", lista_horas, index=9, key="cl_h")
            with cl_lm: c_llegada_m = st.selectbox("Minutos Llegada (Carga)", lista_minutos, index=0, key="cl_m")

        ci_h, ci_im = st.columns(2)
        with ci_h: c_inicio_h = st.selectbox("Hora Inicio (Carga)", lista_horas, index=c_llegada_h, key="ci_h")
        with ci_im: c_inicio_m = st.selectbox("Minutos Inicio (Carga)", lista_minutos, index=0, key="ci_im")
        cf_h, cf_fm = st.columns(2)
        with cf_h: c_fin_h = st.selectbox("Hora Fin (Carga)", lista_horas, index=9, key="cf_h")
        with cf_fm: c_fin_m = st.selectbox("Minutos Fin (Carga)", lista_minutos, index=0, key="cf_fm")

        t_lleg_c = (c_llegada_h * 60) + c_llegada_m
        t_ini_c = (c_inicio_h * 60) + c_inicio_m
        t_fin_c = (c_fin_h * 60) + c_fin_m

    incidencias = st.text_area("Incidencias Generales (opcional)", key="incidencias_input_lanz")
    submitted_lanz = st.button("Guardar Registros (Lanzaderas)")

    if submitted_lanz:
        if not matricula: st.error("Introduce o selecciona una matrícula.")
        elif not carretillero: st.error("Selecciona un carretillero.")
        elif not activar_descarga and not activar_carga: st.warning("Marca al menos Descarga o Carga.")
        else:
            try:
                nuevos_datos = []
                if activar_descarga:
                    nuevos_datos.append([
                        fecha_registro.strftime("%Y-%m-%d"), matricula.upper(),
                        albaran_descarga if albaran_descarga else "S/A", "Descarga",
                        f"{d_llegada_h:02d}:{d_llegada_m:02d}", f"{d_inicio_h:02d}:{d_inicio_m:02d}", f"{d_fin_h:02d}:{d_fin_m:02d}",
                        int(t_ini_d - t_lleg_d), int(t_fin_d - t_ini_d), "" if activar_carga else int(t_fin_d - t_lleg_d),
                        int(pallets_descarga), carretillero, calcular_turno(d_inicio_h, d_inicio_m), incidencias.strip()
                    ])
                if activar_carga:
                    nuevos_datos.append([
                        fecha_registro.strftime("%Y-%m-%d"), matricula.upper(),
                        albaran_carga if albaran_carga else "S/A", "Carga",
                        f"{d_fin_h:02d}:{d_fin_m:02d} (Post-Descarga)" if activar_descarga else f"{c_llegada_h:02d}:{c_llegada_m:02d}",
                        f"{c_inicio_h:02d}:{c_inicio_m:02d}", f"{c_fin_h:02d}:{c_fin_m:02d}",
                        0 if activar_descarga else int(t_ini_c - t_lleg_c), int(t_fin_c - c_inicio_h * 60 - c_inicio_m),
                        int(t_fin_c - t_lleg_d) if activar_descarga else int(t_fin_c - t_lleg_c),
                        int(pallets_carga), carretillero, calcular_turno(c_inicio_h, c_inicio_m), incidencias.strip()
                    ])

                response = requests.post(WEB_APP_URL, json={"action": "update", "rows": nuevos_datos})
                if response.status_code == 200:
                    st.success(f"✅ ¡Guardado en Google Sheets para **{matricula.upper()}**!")
                    st.balloons()
                    for c in ["input_nueva_mat_lanz", "alb_desc", "input_albaran_lanz", "input_albaran_custom", "chk_descarga", "chk_carga", "incidencias_input_lanz"]:
                        if c in st.session_state: del st.session_state[c]
                    st.session_state.df_registros = cargar_registros_lanzaderas()
                    st.query_params["recarga"] = str(time.time())
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.divider()
    st.subheader("📊 Últimos 5 Registros (Lanzaderas)")
    if not st.session_state.df_registros.empty:
        st.dataframe(st.session_state.df_registros.tail(5), use_container_width=True)
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

    if "modo_carr_cli" not in st.session_state:
        st.session_state.modo_carr_cli = "Seleccionar existente"

    carretilleros_actuales = obtener_lista_carretilleros()

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fecha_cliente = st.date_input("Fecha del Registro", value=fecha_hoy_local, key="f_cli")
        transporte = st.text_input("Número de Transporte", placeholder="Ej: TR-98765", key="num_transporte")

    with col_c2:
        st.markdown('<p style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: inherit;">Carretillero</p>', unsafe_allow_html=True)
        if st.session_state.modo_carr_cli == "Seleccionar existente":
            carretillero_cli = st.selectbox("Carretillero (Cliente)", carretilleros_actuales, label_visibility="collapsed", key="sel_carr_cli")
        else:
            col_nc1, col_nc2 = st.columns([0.75, 0.25])
            with col_nc1:
                nuevo_carr_cli = st.text_input("Nombre", placeholder="Ej: J. Pérez", label_visibility="collapsed", key="input_nuevo_carr_cli").strip()
            with col_nc2:
                btn_add_carr_cli = st.button("Añadir", key="btn_guardar_nuevo_carr_cli")
            if btn_add_carr_cli and nuevo_carr_cli:
                if nuevo_carr_cli not in st.session_state.carretilleros_extra:
                    st.session_state.carretilleros_extra.append(nuevo_carr_cli)
                st.success(f"¡'{nuevo_carr_cli}' añadido!")
                st.session_state.modo_carr_cli = "Seleccionar existente"
                st.rerun()
            carretillero_cli = nuevo_carr_cli if nuevo_carr_cli else (carretilleros_actuales[0] if carretilleros_actuales else "")

        nuevo_modo_carr_cli = st.radio("Modo Carretillero (Cliente)", ["Seleccionar existente", "➕ Añadir nuevo"], index=0 if st.session_state.modo_carr_cli == "Seleccionar existente" else 1, horizontal=True, label_visibility="collapsed", key="radio_modo_carr_cli")
        if nuevo_modo_carr_cli != st.session_state.modo_carr_cli:
            st.session_state.modo_carr_cli = nuevo_modo_carr_cli
            st.rerun()

        opcion_pallets_cli = st.selectbox("Número de Pallets", ["33", "26", "24", "21", "50", "Otra cantidad"], key="opt_p_cli")
        num_pallets_cli = st.number_input("Especifica pallets", min_value=1, max_value=200, value=33, key="p_cli_otro") if opcion_pallets_cli == "Otra cantidad" else int(opcion_pallets_cli)

    st.markdown("#### Horarios y Control")
    c_ph1, c_ph2 = st.columns(2)
    with c_ph1: ph_h = st.selectbox("Hora Picada", lista_horas, index=8, key="ph_h")
    with c_ph2: ph_m = st.selectbox("Minutos Picada", lista_minutos, index=0, key="ph_m")

    c_ci1, c_ci2 = st.columns(2)
    with c_ci1: ci_h = st.selectbox("Hora Comienzo", lista_horas, index=8, key="ci_cli_h")
    with c_ci2: ci_m = st.selectbox("Minutos Comienzo", lista_minutos, index=0, key="ci_cli_m")

    c_cf1, c_cf2 = st.columns(2)
    with c_cf1: cf_h = st.selectbox("Hora Fin", lista_horas, index=9, key="cf_cli_h")
    with c_cf2: cf_m = st.selectbox("Minutos Fin", lista_minutos, index=0, key="cf_m")

    opcion_etiquetas = st.selectbox("¿Lleva etiquetas?", ["", "Sí", "No"], key="opt_etiquetas")
    incidencias_cli = st.text_area("Incidencias (opcional)", key="inc_cli")
    submitted_cli = st.button("Guardar Carga de Cliente")

    if submitted_cli:
        if not transporte: st.error("Introduce el número de transporte.")
        else:
            try:
                t_picada, t_comienzo, t_fin = (ph_h * 60) + ph_m, (ci_h * 60) + ci_m, (cf_h * 60) + cf_m
                fila_cliente = [[
                    fecha_cliente.strftime("%Y-%m-%d"), transporte.strip().upper(),
                    f"{ph_h:02d}:{ph_m:02d}", f"{ci_h:02d}:{ci_m:02d}", f"{cf_h:02d}:{cf_m:02d}",
                    int(t_fin - t_comienzo), int(t_fin - t_picada), int(num_pallets_cli),
                    carretillero_cli, opcion_etiquetas, calcular_turno(ci_h, ci_m), incidencias_cli.strip()
                ]]
                response = requests.post(WEB_APP_URL, json={"action": "update_cliente", "rows": fila_cliente})
                if response.status_code == 200:
                    st.success(f"✅ ¡Carga de cliente **{transporte.upper()}** guardada!")
                    st.balloons()
                    for c in ["num_transporte", "inc_cli", "opt_etiquetas", "p_cli_otro"]:
                        if c in st.session_state: del st.session_state[c]
                    st.session_state.df_clientes = cargar_registros_clientes()
                    st.query_params["recarga"] = str(time.time())
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.divider()
    st.subheader("📊 Últimos 5 Registros (Cargas de Cliente)")
    if not st.session_state.df_clientes.empty:
        st.dataframe(st.session_state.df_clientes.tail(5), use_container_width=True)
    else:
        st.info("Aún no hay registros de cliente.")


# ==============================================================================
# SECCIÓN 3: PRODUCCIÓN
# ==============================================================================
elif modo_app == "Producción":
    if icono_pallet_base64:
        st.markdown(
            f"<h3 style='display: flex; align-items: center;'><img src='data:image/png;base64,{icono_pallet_base64}' class='seccion-icono'> Nuevo registro de Producción</h3>", 
            unsafe_allow_html=True
        )
    else:
        st.subheader("📦 Nuevo registro de Producción")

    if "modo_carr_prod" not in st.session_state:
        st.session_state.modo_carr_prod = "Seleccionar existente"

    carretilleros_actuales = obtener_lista_carretilleros()

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        fecha_prod = st.date_input("Fecha del Registro", value=fecha_hoy_local, key="f_prod")
    with col_p2:
        st.markdown('<p style="font-size: 14px; font-weight: 600; margin-bottom: 6px; color: inherit;">Carretillero</p>', unsafe_allow_html=True)
        if st.session_state.modo_carr_prod == "Seleccionar existente":
            carretillero_prod = st.selectbox("Carretillero (Prod)", carretilleros_actuales, label_visibility="collapsed", key="sel_carr_prod")
        else:
            col_nc1, col_nc2 = st.columns([0.75, 0.25])
            with col_nc1:
                nuevo_carr_prod = st.text_input("Nombre", placeholder="Ej: J. Pérez", label_visibility="collapsed", key="input_nuevo_carr_prod").strip()
            with col_nc2:
                btn_add_carr_prod = st.button("Añadir", key="btn_guardar_nuevo_carr_prod")
            if btn_add_carr_prod and nuevo_carr_prod:
                if nuevo_carr_prod not in st.session_state.carretilleros_extra:
                    st.session_state.carretilleros_extra.append(nuevo_carr_prod)
                st.success(f"¡'{nuevo_carr_prod}' añadido!")
                st.session_state.modo_carr_prod = "Seleccionar existente"
                st.rerun()
            carretillero_prod = nuevo_carr_prod if nuevo_carr_prod else (carretilleros_actuales[0] if carretilleros_actuales else "")

        nuevo_modo_carr_prod = st.radio("Modo Carretillero (Prod)", ["Seleccionar existente", "➕ Añadir nuevo"], index=0 if st.session_state.modo_carr_prod == "Seleccionar existente" else 1, horizontal=True, label_visibility="collapsed", key="radio_modo_carr_prod")
        if nuevo_modo_carr_prod != st.session_state.modo_carr_prod:
            st.session_state.modo_carr_prod = nuevo_modo_carr_prod
            st.rerun()

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        turno_prod = st.selectbox("Turno", ["Mañana", "Tarde", "Noche"], key="sel_turno_prod")
    with col_t2:
        st.write("")

    st.markdown("#### Número de pallets")
    
    col_pal1, col_pal2 = st.columns(2)
    with col_pal1:
        pallets_maquilado = st.number_input("Pallets Maquilado", min_value=0, max_value=1000, value=0, key="num_p_maquilado")
    with col_pal2:
        pallets_chequeo = st.number_input("Pallets Chequeo", min_value=0, max_value=1000, value=0, key="num_p_chequeo")

    st.markdown("#### Tiempo Empleado")
    
    st.write("**Tiempo Maquilado:**")
    col_tm1, col_tm2 = st.columns(2)
    with col_tm1:
        tm_h = st.selectbox("Horas Maquilado", lista_horas_prod, index=0, key="tm_h")
    with col_tm2:
        tm_m = st.selectbox("Minutos Maquilado", lista_minutos, index=0, key="tm_m")

    st.write("**Tiempo Chequeo:**")
    col_tc1, col_tc2 = st.columns(2)
    with col_tc1:
        tc_h = st.selectbox("Horas Chequeo", lista_horas_prod, index=0, key="tc_h")
    with col_tc2:
        tc_m = st.selectbox("Minutos Chequeo", lista_minutos, index=0, key="tc_m")

    minutos_maquilado_totales = (tm_h * 60) + tm_m
    minutos_chequeo_totales = (tc_h * 60) + tc_m

    submitted_prod = st.button("Guardar Registro de Producción")

    if submitted_prod:
        try:
            fila_produccion = [[
                fecha_prod.strftime("%Y-%m-%d"),
                carretillero_prod,
                int(pallets_maquilado),
                int(pallets_chequeo),
                int(minutos_maquilado_totales),
                int(minutos_chequeo_totales),
                turno_prod
            ]]

            response = requests.post(WEB_APP_URL, json={"action": "update_produccion", "rows": fila_produccion})
            
            if response.status_code == 200:
                st.success("✅ ¡Registro de Producción guardado correctamente!")
                st.balloons()
                
                for clave in ["num_p_maquilado", "num_p_chequeo", "tm_h", "tm_m", "tc_h", "tc_m"]:
                    if clave in st.session_state:
                        del st.session_state[clave]

                st.session_state.df_produccion = cargar_registros_produccion()
                st.query_params["recarga"] = str(time.time())
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"❌ Error al conectar con Google Sheets: {response.text}")
        except Exception as e:
            st.error(f"❌ Error al procesar: {e}")

    st.divider()
    st.subheader("📊 Últimos 5 Registros (Producción)")
    if not st.session_state.df_produccion.empty:
        st.dataframe(st.session_state.df_produccion.tail(5), use_container_width=True)
    else:
        st.info("Aún no hay registros en Producción.")


# ==============================================================================
# SECCIÓN 4: REUBICACIONES, COMPACTACIONES Y NCT'S
# ==============================================================================
elif modo_app == "Reubicaciones, Compactaciones y NCT's":
    st.subheader("🔄 Reubicaciones, Compactaciones y NCT's")

    carretilleros_actuales = obtener_lista_carretilleros()

    # --- SECCIÓN GENERAL ---
    st.markdown("#### Datos Generales")
    col_gen1, col_gen2 = st.columns(2)
    with col_gen1:
        fecha_reub = st.date_input("Fecha del Registro", value=fecha_hoy_local, key="f_reub")
    with col_gen2:
        turno_reub = st.selectbox("Turno", ["Mañana", "Tarde", "Noche"], key="sel_turno_reub")

    st.divider()

    # --- SUBAPARTADO 1: REUBICACIONES ---
    st.markdown("#### 1. Reubicaciones")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        carrs_reub = st.multiselect(
            "Carretillero(s) Reubicaciones", 
            carretilleros_actuales, 
            placeholder="Selecciona uno o varios",
            key="multi_carr_reub"
        )
    with col_r2:
        num_pallets_reub = st.number_input("Nº de Pallets", min_value=0, max_value=1000, value=0, key="num_p_reub")

    st.divider()

    # --- SUBAPARTADO 2: COMPACTACIONES ---
    st.markdown("#### 2. Compactaciones")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        carrs_comp = st.multiselect(
            "Carretillero(s) Compactaciones", 
            carretilleros_actuales, 
            placeholder="Selecciona uno o varios",
            key="multi_carr_comp"
        )
    with col_c2:
        num_compactaciones = st.number_input("Nº de Compactaciones", min_value=0, max_value=1000, value=0, key="num_comp")

    st.write("**Tiempo en Operación (Compactaciones):**")
    col_tc_h, col_tc_m = st.columns(2)
    with col_tc_h:
        comp_h = st.selectbox("Horas (Compact.)", lista_horas_prod, index=0, key="comp_h")
    with col_tc_m:
        comp_m = st.selectbox("Minutos (Compact.)", lista_minutos_15, index=0, key="comp_m")

    minutos_compact_totales = (comp_h * 60) + comp_m

    st.divider()

    # --- SUBAPARTADO 3: NCT'S ---
    st.markdown("#### 3. NCT's")
    if "num_ncts" not in st.session_state:
        st.session_state.num_ncts = 1

    datos_ncts = []
    for i in range(st.session_state.num_ncts):
        if st.session_state.num_ncts > 1:
            st.markdown(f"**NCT #{i + 1}**")
        
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            pedido_nct = st.text_input("Nº de Pedido", placeholder="Ej: PED-1234", key=f"ped_nct_{i}")
        with col_n2:
            carr_nct = st.selectbox("Carretillero", [""] + carretilleros_actuales, key=f"carr_nct_{i}")
        with col_n3:
            cajas_nct = st.number_input("Nº de Cajas", min_value=0, max_value=5000, value=0, key=f"cajas_nct_{i}")

        col_nh, col_nm = st.columns(2)
        with col_nh:
            nct_h = st.selectbox("Horas Operación (NCT)", lista_horas_prod, index=0, key=f"nct_h_{i}")
        with col_nm:
            nct_m = st.selectbox("Minutos Operación (NCT)", lista_minutos_15, index=0, key=f"nct_m_{i}")

        minutos_nct_totales = (nct_h * 60) + nct_m

        datos_ncts.append({
            "pedido": pedido_nct.strip(),
            "carretillero": carr_nct,
            "cajas": int(cajas_nct),
            "tiempo": int(minutos_nct_totales)
        })

        if i < st.session_state.num_ncts - 1:
            st.markdown("---")

    col_btn_nct1, col_btn_nct2 = st.columns([0.4, 0.6])
    with col_btn_nct1:
        if st.button("➕ Añadir nueva NCT", key="btn_add_nct"):
            st.session_state.num_ncts += 1
            st.rerun()
    with col_btn_nct2:
        if st.session_state.num_ncts > 1:
            if st.button("➖ Quitar última NCT", key="btn_del_nct"):
                st.session_state.num_ncts -= 1
                st.rerun()

    # Opción rápida para añadir un nuevo carretillero a la lista
    with st.expander("➕ ¿Necesitas añadir un carretillero nuevo a la lista?"):
        col_ex1, col_ex2 = st.columns([0.75, 0.25])
        with col_ex1:
            nuevo_carr_general = st.text_input("Nombre del carretillero", placeholder="Ej: F. Gómez", key="input_nuevo_carr_gen").strip()
        with col_ex2:
            st.write("")
            btn_add_gen = st.button("Añadir", key="btn_guardar_nuevo_gen")
        if btn_add_gen and nuevo_carr_general:
            if nuevo_carr_general not in st.session_state.carretilleros_extra:
                st.session_state.carretilleros_extra.append(nuevo_carr_general)
                st.success(f"¡'{nuevo_carr_general}' añadido a los desplegables!")
                st.rerun()

    st.divider()

    submitted_reub = st.button("Guardar Registro (Reub, Comp y NCT's)")

    if submitted_reub:
        try:
            str_carrs_reub = ", ".join(carrs_reub)
            str_carrs_comp = ", ".join(carrs_comp)
            fecha_str = fecha_reub.strftime("%Y-%m-%d")

            filas_a_enviar = []

            primera_nct = datos_ncts[0]
            tiene_nct_0 = bool(primera_nct["pedido"] or primera_nct["carretillero"] or primera_nct["cajas"] > 0 or primera_nct["tiempo"] > 0)

            filas_a_enviar.append([
                fecha_str,
                turno_reub,
                str_carrs_reub,
                int(num_pallets_reub) if (str_carrs_reub or num_pallets_reub > 0) else "",
                str_carrs_comp,
                int(num_compactaciones) if (str_carrs_comp or num_compactaciones > 0) else "",
                int(minutos_compact_totales) if (str_carrs_comp or num_compactaciones > 0 or minutos_compact_totales > 0) else "",
                primera_nct["carretillero"] if tiene_nct_0 else "",
                primera_nct["pedido"] if tiene_nct_0 else "",
                primera_nct["cajas"] if tiene_nct_0 else "",
                primera_nct["tiempo"] if tiene_nct_0 else ""
            ])

            for extra_nct in datos_ncts[1:]:
                if extra_nct["pedido"] or extra_nct["carretillero"] or extra_nct["cajas"] > 0 or extra_nct["tiempo"] > 0:
                    filas_a_enviar.append([
                        fecha_str,
                        turno_reub,
                        "", "", "", "", "",
                        extra_nct["carretillero"],
                        extra_nct["pedido"],
                        extra_nct["cajas"],
                        extra_nct["tiempo"]
                    ])

            response = requests.post(WEB_APP_URL, json={"action": "update_reub", "rows": filas_a_enviar})

            if response.status_code == 200:
                st.success("✅ ¡Registro guardado correctamente en Google Sheets!")
                st.balloons()

                claves_limpiar = ["multi_carr_reub", "num_p_reub", "multi_carr_comp", "num_comp", "comp_h", "comp_m"]
                for i in range(st.session_state.num_ncts):
                    claves_limpiar.extend([f"ped_nct_{i}", f"carr_nct_{i}", f"cajas_nct_{i}", f"nct_h_{i}", f"nct_m_{i}"])
                for c in claves_limpiar:
                    if c in st.session_state:
                        del st.session_state[c]
                st.session_state.num_ncts = 1

                st.session_state.df_reub = cargar_registros_reub()
                st.query_params["recarga"] = str(time.time())
                time.sleep(0.5)
                st.rerun()
            else:
                st.error(f"❌ Error al conectar con Google Sheets: {response.text}")
        except Exception as e:
            st.error(f>❌ Error al procesar: {e}")

    st.divider()
    st.subheader("📊 Últimos 5 Registros (Reub, Comp y NCT's)")
    if not st.session_state.df_reub.empty:
        st.dataframe(st.session_state.df_reub.tail(5), use_container_width=True)
    else:
        st.info("Aún no hay registros en este apartado.")