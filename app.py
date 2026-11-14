import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import time

# Configuración de la página web
st.set_page_config(page_title="Control de Muelles - Almacén", page_icon="🚛", layout="centered")

st.title("🚛 Registro de Carga y Descarga en Muelle (Online)")
st.write("Conectado a Google Sheets mediante Google Apps Script.")

# --- CONFIGURACIÓN DE URL DE APPS SCRIPT ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbw6ASYyy6hW6gdjqjVSnrgvneo0-3wh2UhM4Hi5yi9bWk2_O3iRqTYX2EF3Pph5ymq3Cw/exec"

# Lista de carretilleros disponibles
LISTA_CARRETILLEROS = [
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

# Inicializar historial en memoria de la sesión (sin archivos Excel locales)
if "df_registros" not in st.session_state:
    st.session_state.df_registros = pd.DataFrame(columns=COLS_NECESARIAS)

# Función para calcular el turno según la hora y minuto
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

st.subheader("Nuevo Registro de Vehículo")

# 1. Fecha, Matrícula y Carretillero
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_registro = st.date_input("Fecha del Registro", value=datetime.now())
    carretillero = st.selectbox("Carretillero", LISTA_CARRETILLEROS)

matriculas_guardadas = []
if not st.session_state.df_registros.empty and "Matrícula" in st.session_state.df_registros.columns:
    matriculas_guardadas = sorted(st.session_state.df_registros["Matrícula"].dropna().unique().tolist())

with col_f2:
    tipo_ingreso_mat = st.radio("Matrícula:", ["Seleccionar existente", "Escribir nueva"], horizontal=True, label_visibility="collapsed")
    if tipo_ingreso_mat == "Seleccionar existente" and matriculas_guardadas:
        matricula = st.selectbox("Matrícula del Vehículo", matriculas_guardadas)
    else:
        matricula = st.text_input("Escribe la nueva matrícula").strip().upper()

st.divider()

# ==========================================
# BLOQUE 1: DESCARGA
# ==========================================
activar_descarga = st.checkbox("📥 Registrar DESCARGA de mercancía")

albaran_descarga = ""
pallets_descarga = 1
d_llegada_h = d_llegada_m = d_inicio_h = d_inicio_m = d_fin_h = d_fin_m = 8

if activar_descarga:
    st.markdown("#### Tiempos de Descarga")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        albaran_descarga = st.text_input("Nº de Albarán (Descarga)", key="alb_desc")
    with col_d2:
        pallets_descarga = st.number_input("Pallets Descargados", min_value=1, max_value=200, value=1, key="p_desc")
    
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

# ==========================================
# BLOQUE 2: CARGA
# ==========================================
activar_carga = st.checkbox("📤 Registrar CARGA de mercancía")

albaran_carga = ""
pallets_carga = 1
c_llegada_h = 9
c_llegada_m = 0

if activar_carga:
    st.markdown("#### Tiempos de Carga")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        albaran_carga = st.text_input("Nº de Albarán / Pedido (Carga)", key="alb_carg")
    with col_c2:
        pallets_carga = st.number_input("Pallets Cargados", min_value=1, max_value=200, value=1, key="p_carg")
    
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
        c_inicio_m = st.selectbox("Minutos Inicio (Carga)", lista_minutos, index=0, key="ci_m")
        
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

incidencias = st.text_area("Incidencias Generales (opcional)", placeholder="Ej: Retraso en documentación, mercancía dañada...")

submitted = st.button("Guardar Registros")

if submitted:
    if not matricula:
        st.error("Por favor, introduce o selecciona una matrícula.")
    elif not activar_descarga and not activar_carga:
        st.warning("Debes marcar al menos una opción: Descarga o Carga.")
    else:
        error_horario = False
        if activar_descarga and (t_ini_d < t_lleg_d or t_fin_d < t_ini_d):
            error_horario = True
        if activar_carga and (t_ini_c < t_lleg_c or t_fin_c < t_ini_c):
            error_horario = True

        if error_horario:
            st.error("❌ No se puede guardar: Revisa los avisos en rojo de los horarios seleccionados.")
        else:
            try:
                nuevos_datos = []
                
                if activar_descarga:
                    min_esp_d = t_ini_d - t_lleg_d
                    min_op_d = t_fin_d - t_ini_d
                    
                    # Si hay carga posterior, dejamos Min. Totales vacío ("") para evitar duplicidades al sumar
                    if activar_carga:
                        min_tot_d = "" 
                    else:
                        min_tot_d = t_fin_d - t_lleg_d

                    turno_calc = calcular_turno(d_llegada_h, d_llegada_m)
                    
                    nuevos_datos.append([
                        fecha_registro.strftime("%Y-%m-%d"),
                        matricula.upper(),
                        albaran_descarga if albaran_descarga else "S/A",
                        "Descarga",
                        f"{d_llegada_h:02d}:{d_llegada_m:02d}",
                        f"{d_inicio_h:02d}:{d_inicio_m:02d}",
                        f"{d_fin_h:02d}:{d_fin_m:02d}",
                        int(min_esp_d),
                        int(min_op_d),
                        min_tot_d if min_tot_d == "" else int(min_tot_d),
                        int(pallets_descarga),
                        carretillero,
                        turno_calc,
                        incidencias if incidencias else "Ninguna"
                    ])

                if activar_carga:
                    if activar_descarga:
                        min_esp_c = 0
                        hora_llegada_str = f"{d_fin_h:02d}:{d_fin_m:02d} (Post-Descarga)"
                        turno_calc = calcular_turno(d_fin_h, d_fin_m)
                        # Minutos totales globales desde la llegada inicial de la descarga hasta el fin de la carga
                        min_tot_c = t_fin_c - t_lleg_d
                    else:
                        min_esp_c = t_ini_c - t_lleg_c
                        hora_llegada_str = f"{c_llegada_h:02d}:{c_llegada_m:02d}"
                        turno_calc = calcular_turno(c_llegada_h, c_llegada_m)
                        min_tot_c = t_fin_c - t_lleg_c
                    
                    min_op_c = t_fin_c - t_ini_c
                    
                    nuevos_datos.append([
                        fecha_registro.strftime("%Y-%m-%d"),
                        matricula.upper(),
                        albaran_carga if albaran_carga else "S/A",
                        "Carga",
                        hora_llegada_str,
                        f"{c_inicio_h:02d}:{c_inicio_m:02d}",
                        f"{c_fin_h:02d}:{c_fin_m:02d}",
                        int(min_esp_c),
                        int(min_op_c),
                        int(min_tot_c),
                        int(pallets_carga),
                        carretillero,
                        turno_calc,
                        incidencias if incidencias else "Ninguna"
                    ])

                # 1. Enviar a Google Sheets vía Web App (Fuente de verdad oficial)
                response = requests.post(WEB_APP_URL, json={"action": "update", "rows": nuevos_datos})
                
                if response.status_code == 200:
                    # 2. Actualizar la tabla visual en memoria de la sesión
                    df_nuevo = pd.DataFrame(nuevos_datos, columns=COLS_NECESARIAS)
                    st.session_state.df_registros = pd.concat([st.session_state.df_registros, df_nuevo], ignore_index=True)
                    
                    st.success(f"✅ ¡Guardado y sincronizado en Google Sheets para **{matricula.upper()}**! (Carretillero: {carretillero} | Turno: {turno_calc})")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Error al conectar con Google Sheets (Código {response.status_code}): {response.text}")
                
            except Exception as e:
                st.error(f"❌ Error al procesar el guardado: {e}")

st.divider()
st.subheader("📊 Historial de Registros (Sesión actual)")
if not st.session_state.df_registros.empty:
    st.dataframe(st.session_state.df_registros, use_container_width=True)
else:
    st.info("Aún no hay registros en esta sesión. ¡Haz el primero arriba!")