import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import time

# Configuración de la página web
st.set_page_config(page_title="Control de Muelles - Almacén", page_icon="🚛", layout="centered")

st.title("🚛 Registro de Carga y Descarga en Muelle (Online)")
st.write("Conectado a Google Sheets mediante Google Apps Script.")

# --- CONFIGURACIÓN DE URL DE APPS SCRIPT ACTUALIZADA ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyP9cpZSNJdUfEWATW0gIfot-Mg_9_wDy_LZeYY52Ln-kkrWHlQ4PhbLg1iHRcJQncj5Q/exec"

# Lista base por defecto para carretilleros
CARRETILLEROS_BASE = [
    "C. Alías", "C. Díaz", "M. José", "David", "Andreu", 
    "Raúl", "Álvaro", "Daniel", "J. A. Lara", "J. A. Vega", "Sergio", "Samuel"
]

# Columnas oficiales del registro
COLS_NECESARIAS = [
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
                if df.shape[1] >= len(COLS_NECESARIAS):
                    df = df.iloc[:, :len(COLS_NECESARIAS)]
                    df.columns = COLS_NECESARIAS
                    return df
    except Exception as e:
        pass
    
    return pd.DataFrame(columns=COLS_NECESARIAS)

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

# Ancla invisible arriba del todo para el scroll automático
st.markdown("<div id='top-section'></div>", unsafe_allow_html=True)

st.subheader("Nuevo Registro de Vehículo")

# Inicializar estados de modo si no existen
if "modo_mat" not in st.session_state:
    st.session_state.modo_mat = "Seleccionar existente"
if "modo_carr" not in st.session_state:
    st.session_state.modo_carr = "Seleccionar existente"

# Extraer matrículas existentes desde la Columna B (índice 1)
matriculas_guardadas = []
if not st.session_state.df_registros.empty:
    matriculas_guardadas = sorted(st.session_state.df_registros.iloc[:, 1].dropna().astype(str).str.strip().unique().tolist())

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

# --- DISEÑO EN 2 COLUMNAS ALINEADAS ---
col_f1, col_f2 = st.columns(2)

# FILA 1: Fecha (Izquierda) y Carretillero (Derecha) perfectamente alineados
with col_f1:
    fecha_registro = st.date_input("Fecha del Registro", value=datetime.now())

with col_f2:
    st.markdown("##### Carretillero")
    if st.session_state.modo_carr == "Seleccionar existente":
        carretillero = st.selectbox("Carretillero", carretilleros_existentes, label_visibility="collapsed", key="select_carretillero_existente")
    else:
        col_nc1, col_nc2 = st.columns([0.75, 0.25])
        with col_nc1:
            nuevo_carr = st.text_input("Nombre del nuevo carretillero", placeholder="Ej: J. Pérez", label_visibility="collapsed", key="input_nuevo_carr").strip()
        with col_nc2:
            btn_add_carr = st.button("Añadir", key="btn_guardar_nuevo_carr")
        
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
        key="radio_modo_carr"
    )
    if nuevo_modo_carr != st.session_state.modo_carr:
        st.session_state.modo_carr = nuevo_modo_carr
        st.rerun()

# FILA 2: Matrícula (Izquierda)
with col_f1:
    st.markdown("##### Matrícula del Vehículo")
    if st.session_state.modo_mat == "Seleccionar existente":
        if matriculas_guardadas:
            matricula = st.selectbox("Matrícula", matriculas_guardadas, label_visibility="collapsed", key="select_mat_existente")
        else:
            st.info("No hay matrículas guardadas.")
            matricula = ""
    else:
        matricula = st.text_input("Escribe la nueva matrícula", placeholder="Ej: 1234ABC", label_visibility="collapsed", key="input_nueva_mat").strip().upper()

    nuevo_modo_mat = st.radio(
        "Modo Matrícula", 
        ["Seleccionar existente", "Escribir nueva"], 
        index=0 if st.session_state.modo_mat == "Seleccionar existente" else 1,
        horizontal=True, 
        label_visibility="collapsed",
        key="radio_modo_mat"
    )
    if nuevo_modo_mat != st.session_state.modo_mat:
        st.session_state.modo_mat = nuevo_modo_mat
        st.rerun()

st.divider()

# ==========================================
# BLOQUE 1: DESCARGA
# ==========================================
activar_descarga = st.checkbox("📥 Registrar DESCARGA de mercancía", key="chk_descarga")

albaran_descarga = ""
pallets_descarga = 33
d_llegada_h = d_llegada_m = d_inicio_h = d_inicio_m = d_fin_h = d_fin_m = 8

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

    t_lleg_d = (d_llegada_h * 60) +