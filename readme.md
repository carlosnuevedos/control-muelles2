# 🚛 Registro de Actividad - Azentis Persán La Red

Aplicación web desarrollada en **Streamlit (Python)** y conectada a **Google Sheets** mediante **Google Apps Script**, diseñada para optimizar y agilizar el registro diario de operaciones logísticas en el centro de trabajo de Azentis Persán La Red.

---

## 🚀 Características Principales

La aplicación cuenta con un diseño corporativo adaptado y se divide en **5 módulos operativos principales**:

1. **Control Lanzaderas:** 
   - Gestión y control de entradas/salidas de vehículos.
   - Registro independiente o combinado de **Descargas** y **Cargas** con cálculo automático de tiempos de espera, operación y totales.
   - Autogeneración de referencias de albarán (formato `P/M-DDMMYY-X`).
   - Control de matrículas existentes y selección dinámica de carretilleros.

2. **Cargas de Cliente:**
   - Registro de salidas de transporte de cliente.
   - Control de horarios (picada, comienzo, fin), cálculo de tiempos de operación/espera, pallets, etiquetas y turnos automáticos.

3. **Producción:**
   - Registro de actividad de producción por carretillero.
   - Control de pallets de **Maquilado** y **Chequeo** junto con sus tiempos empleados respectivos.

4. **Reubicaciones, Compactaciones y NCT's:**
   - Sección modular controlada por checkboxes independientes.
   - Registro simultáneo de reubicaciones de pallets, compactaciones de stock (con control de tiempos) y gestión dinámica de múltiples **NCT's** (pedidos, carretillero, cajas y tiempos).

5. **Preparación Cargas:**
   - Registro segmentado en Cargas de Cliente, Mailing y Persán.
   - Control de pallets preparados, operarios implicados, tiempos de operación y control opcional de reenfardados/reetiquetados.

---

## 🛠️ Tecnologías Utilizadas

- **Frontend / Interfaz:** [Streamlit](https://streamlit.io/) (Python) con estilos CSS personalizados y diseño adaptativo.
- **Backend / Persistencia:** [Google Sheets API](https://workspace.google.com/intl/es/products/sheets/) gestionada a través de un Web App en **Google Apps Script** para lectura y escritura masiva ultrarrápida.
- **Procesamiento de Datos:** Pandas y Python estándar para el manejo de estructuras y fechas.
- **Gestión de Estado:** `st.session_state` optimizado para limpieza automática de formularios, desplazamiento automático al inicio (scroll-top) tras cada guardado y gestión dinámica de carretilleros.

---

## ⚙️ Estructura del Proyecto

```text
control-muelles-lared/
│
├── app.py                     # Código principal de la aplicación Streamlit
├── Código.gs                  # Script backend alojado en Google Apps Script (Web App)
├── requirements.txt           # Dependencias de Python (streamlit, pandas, requests, pillow)
├── AZENTIS-SIN-FONDO.png      # Logotipo corporativo principal
├── Lanzadera.png              # Icono para módulo de Lanzaderas
├── Clientes.png               # Icono para módulo de Cargas de Cliente
├── Pallet.png                 # Icono para módulo de Producción
├── Carretilla.png             # Icono para módulo de Reubicaciones y NCTs
└── Cargas.png                 # Icono para módulo de Preparación de Cargas
📦 Instalación y Configuración Local
Clonar el repositorio:

Bash
git clone [https://github.com/tu-usuario/control-muelles-lared.git](https://github.com/tu-usuario/control-muelles-lared.git)
cd control-muelles-lared
Instalar las dependencias de Python:

Bash
pip install -r requirements.txt
Configurar las credenciales y URLs:

Asegúrate de tener los recursos gráficos (iconos y logo) en el directorio raíz del proyecto.

Verifica que la constante WEB_APP_URL en app.py apunta correctamente a tu despliegue activo de Google Apps Script.

Ejecutar la aplicación:

Bash
streamlit run app.py
⚡ Backend (Google Apps Script)
El backend optimizado en Google Apps Script (Código.gs) utiliza:

Lectura en memoria masiva (getValues()) para evitar cuellos de botella en bucles celda por celda.

Algoritmo de inserción segura que localiza la primera fila libre a partir de la fila 5 de forma instantánea y sin conflictos de arrays.

Automatización de metadatos (cálculo de mes, semana ISO y día de la semana) a partir de la fecha introducida.