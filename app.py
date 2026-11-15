import streamlit as st
from datetime import datetime
import pandas as pd
import requests
import json
import time

# Configuración de la página web
st.set_page_config(page_title="Control de Muelles - Almacén", page_icon="🚛", layout="centered")

st.title("🚛 Registro de Carga y Descarga en Muelle (Online)")
st.write("Conectado a Google Sheets mediante Google Apps Script.")

# --- CONFIGURACIÓN DE URL DE APPS SCRIPT ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbw9oPFCuuCOcMTIpbIQZipYlpmyrWtfSmjKQdpae3beI3D9Pp-iZTbMfRypXtzXAtOSNQ/exec"

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

# --- FUNCIÓN PARA CARGAR DATOS DESDE GOOGLE SHEETS AL INICIAR ---
def cargar_registros_desde_sheets():
    try:
        # Hacemos una petición GET (o POST con acción leer) al Apps Script
        response = requests.post(WEB_APP_URL, json={"action": "leer"})
        if response.status_code == 200:
            data = response.json()
            if "rows" in data and len(data["rows"]) > 0:
                # Convertimos los datos devueltos en un DataFrame de pandas
                df = pd.DataFrame(data["rows"])
                # Aseguramos que tenga las columnas correctas
                if list(df.columns) != COLS_NECESARIAS and len(df.columns) == len(COLS_NECESARIAS):
                    df.columns = COLS_NECESARIAS
                return df
    except Exception as e:
        pass
    
    # Si falla o está vacío, devolvemos un DataFrame vacío con la estructura
    return pd.DataFrame(columns=COLS_NECESARIAS)

# Inicializar historial en memoria sincronizado con Sheets
if "df_registros" not in st.session_state:
    st.session_state.df_registros = cargar_registros_desde_sheets()

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

# Ancla invisible arriba del todo para el scroll automático
st.markdown("<div id='top-section'></div>", unsafe_allow_html=True)

st.subheader("Nuevo Registro de Vehículo")

# 1. Fecha, Matrícula y Carretillero
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_registro = st.date_input("Fecha del Registro", value=datetime.now())
    carretillero = st.selectbox("Carretillero", LISTA_CARRETILLEROS)

# Extraer matrículas existentes desde los datos cargados de Google Sheets
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

    t_lleg_d = (d_llegada_h * 60) + d_llegada_m
    t_ini_d = (d_inicio_h * 60) + d_inicio_m
    t_fin_d = (d_fin_h * 60) + d_fin_m
    if t_ini_d < t_lleg_d or t_fin_d < t_ini_d:
        st.error("⚠️ [Descarga] Incongruencia horaria: La llegada debe ser anterior al inicio, y el inicio anterior al fin.")

st.divider()

# ==========================================
# BLOQUE 2: CARGA (CON LANZADERAS INTELIGENTES P / M)
# ==========================================
activar_carga = st.checkbox("📤 Registrar CARGA de mercancía")

albaran_carga = ""
pallets_carga = 33
c_llegada_h = 9
c_llegada_m = 0

if activar_carga:
    st.markdown("#### Tiempos y Referencia de Carga (Lanzadera)")
    
    col_tc1, col_tc2, col_tc3 = st.columns(3)
    with col_tc1:
        tipo_lanzadera = st.selectbox("Tipo de Referencia", ["P (Lanzadera)", "M (Lanzadera)", "Albarán Personalizado"], key="tipo_lanz")
    
    str_fecha_ddmmaa = fecha_registro.strftime("%d%m%y")
    df_actual = st.session_state.df_registros
    
    if tipo_lanzadera in ["P (Lanzadera)", "M (Lanzadera)"]:
        letra_prefijo = "P" if tipo_lanzadera.startswith("P") else "M"
        
        # Calcular el número secuencial basándose en los datos ya cargados de Google Sheets para esa fecha
        siguiente_num = 1
        if not df_actual.empty and "Fecha Registro" in df_actual.columns and "Albarán" in df_actual.columns:
            filtro_fecha = df_actual["Fecha Registro"] == fecha_registro.strftime("%Y-%m-%d")
            filtro_op = df_actual["Operación"] == "Carga"
            subset = df_actual[filtro_fecha & filtro_op]
            prefijo_buscado = f"{letra_prefijo}{str_fecha_ddmmaa}-"
            coincidencias = subset[subset["Albarán"].str.startswith(prefijo_buscado, na=False)]
            siguiente_num = len(coincidencias) + 1
            
        sugerencia_codigo = f"{letra_prefijo}{str_fecha_ddmmaa}-{siguiente_num}"
        
        with col_tc2:
            albaran_carga = st.text_input("Código de Lanzadera", value=sugerencia_codigo, key="alb_lanzadera")
    else:
        with col_tc2:
            albaran_carga = st.text_input("Nº de Albarán Personalizado", key="alb_custom")

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

                # 1. Enviar a Google Sheets vía Web App
                response = requests.post(WEB_APP_URL, json={"action": "update", "rows": nuevos_datos})
                
                if response.status_code == 200:
                    df_nuevo = pd.DataFrame(nuevos_datos, columns=COLS_NECESARIAS)
                    st.session_state.df_registros = pd.concat([st.session_state.df_registros, df_nuevo], ignore_index=True)
                    
                    st.success(f"✅ ¡Guardado y sincronizado en Google Sheets para **{matricula.upper()}**! (Carretillero: {carretillero} | Turno: {turno_calc})")
                    st.balloons()
                    
                    st.markdown("""
                        <script>
                            const mediaQuery = window.parent.document.querySelector('.main');
                            if (mediaQuery) {
                                mediaQuery.scrollTo({top: 0, behavior: 'smooth'});
                            }
                        </script>
                    """, unsafe_allow_html=True)
                    
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"❌ Error al conectar con Google Sheets (Código {response.status_code}): {response.text}")
                
            except Exception as e:
                st.error(f"❌ Error al procesar el guardado: {e}")

st.divider()
st.subheader("📊 Historial de Registros (Cargados desde Google Sheets)")
if not st.session_state.df_registros.empty:
    st.dataframe(st.session_state.df_registros, use_container_width=True)
else:
    st.info("Aún no hay registros en la hoja de cálculo.")