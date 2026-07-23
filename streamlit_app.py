import streamlit as st
import pandas as pd
from datetime import date

# Configuración de la página para dispositivos móviles
st.set_page_config(
    page_title="SERVIHOGAR",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para mejorar el diseño en móviles
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #1E3A8A;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #4B5563;
        font-size: 14px;
        margin-bottom: 25px;
    }
    .card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        margin-bottom: 15px;
    }
    .badge-cert {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Datos simulados de empleados
if 'empleados' not in st.session_state:
    st.session_state.empleados = [
        {"id": 1, "nombre": "Juan Pérez", "categoria": "Electricidad", "tarifa": 15.0, "calif": "⭐ 4.8", "cert": True},
        {"id": 2, "nombre": "María Gómez", "categoria": "Limpieza Doméstica", "tarifa": 12.0, "calif": "⭐ 5.0", "cert": True},
        {"id": 3, "nombre": "Carlos Ruiz", "categoria": "Plomería", "tarifa": 18.0, "calif": "⭐ 4.7", "cert": True},
        {"id": 4, "nombre": "Ana Martínez", "categoria": "Jardinería", "tarifa": 14.0, "calif": "⭐ 4.9", "cert": True},
    ]

# Estado de navegación
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = 'login'
if 'empleado_sel' not in st.session_state:
    st.session_state.empleado_sel = None


# -----------------------------------------------------------------------------
# PANTALLA 1: LOGIN Y ELECCIÓN DE ROL
# -----------------------------------------------------------------------------
if st.session_state.pantalla == 'login':
    st.markdown("<h1 class='main-title'>SERVIHOGAR</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Conectando talento certificado con tu hogar</p>", unsafe_allow_html=True)

    st.subheader("¿Cómo deseas ingresar?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Busco Contratar", use_container_width=True):
            st.session_state.pantalla = 'catalogo'
            st.rerun()
            
    with col2:
        if st.button("👷‍♂️ Ofrecer Servicios", use_container_width=True):
            st.info("Formulario de registro para trabajadores en revisión.")


# -----------------------------------------------------------------------------
# PANTALLA 2: CATÁLOGO DE EMPLEADOS POR CATEGORÍA
# -----------------------------------------------------------------------------
elif st.session_state.pantalla == 'catalogo':
    st.markdown("<h2 style='color:#1E3A8A;'>Catálogo SERVIHOGAR</h2>", unsafe_allow_html=True)
    
    # Filtro por Categorías
    categorias = ["Todas", "Electricidad", "Limpieza Doméstica", "Plomería", "Jardinería"]
    cat_seleccionada = st.selectbox("Selecciona una categoría:", categorias)

    # Filtrar lista
    if cat_seleccionada == "Todas":
        empleados_filtrados = st.session_state.empleados
    else:
        empleados_filtrados = [e for e in st.session_state.empleados if e['categoria'] == cat_seleccionada]

    st.write("---")

    # Renderizar catálogo
    for emp in empleados_filtrados:
        with st.container():
            st.markdown(f"""
                <div class='card'>
                    <h4>{emp['nombre']} <span class='badge-cert'>✓ Certificado</span></h4>
                    <p><b>Categoría:</b> {emp['categoria']} | {emp['calif']}<br>
                    <b>Tarifa:</b> ${emp['tarifa']}/hora</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Contratar a {emp['nombre']}", key=f"btn_{emp['id']}", use_container_width=True):
                st.session_state.empleado_sel = emp
                st.session_state.pantalla = 'contrato'
                st.rerun()

    if st.button("⬅️ Cerrar Sesión", type="secondary"):
        st.session_state.pantalla = 'login'
        st.rerun()


# -----------------------------------------------------------------------------
# PANTALLA 3: ACUERDO DE SERVICIO / CONTRATO
# -----------------------------------------------------------------------------
elif st.session_state.pantalla == 'contrato':
    emp = st.session_state.empleado_sel
    st.markdown("<h2 style='color:#1E3A8A;'>Contrato de Servicio Digital</h2>", unsafe_allow_html=True)
    st.caption("Respaldo Oficial SERVIHOGAR")

    st.success(f"**Profesional:** {emp['nombre']} ({emp['categoria']})\n\n**Tarifa:** ${emp['tarifa']}/hora")

    # Formulario del contrato
    with st.form("form_contrato"):
        nombre_empleador = st.text_input("Nombre de la Empresa o Contratante:")
        fecha_req = st.date_input("Fecha requerida del servicio:", min_value=date.today())
        descripcion = st.text_area("Descripción detallada del trabajo:")
        
        acepta_terminos = st.checkbox("Acepto las políticas de garantía y contratación de SERVIHOGAR.")
        
        submitted = st.form_submit_button("✍️ Firmar y Enviar Solicitud", use_container_width=True)
        
        if submitted:
            if not nombre_empleador or not descripcion:
                st.error("Por favor completa todos los campos requeridos.")
            elif not acepta_terminos:
                st.warning("Debes aceptar los términos del contrato.")
            else:
                st.session_state.datos_contrato = {
                    "empleador": nombre_empleador,
                    "empleado": emp['nombre'],
                    "fecha": fecha_req,
                    "tarifa": emp['tarifa']
                }
                st.session_state.pantalla = 'exito'
                st.rerun()

    if st.button("Cancel y Volver al Catálogo"):
        st.session_state.pantalla = 'catalogo'
        st.rerun()


# -----------------------------------------------------------------------------
# PANTALLA 4: CONFIRMACIÓN Y NOTIFICACIÓN
# -----------------------------------------------------------------------------
elif st.session_state.pantalla == 'exito':
    st.balloons()
    datos = st.session_state.get('datos_contrato', {})
    
    st.success("🎉 ¡Solicitud Enviada con Éxito!")
    st.markdown(f"""
        **Resumen del Acuerdo:**
        - **Contratante:** {datos.get('empleador')}
        - **Profesional Notificado:** {datos.get('empleado')}
        - **Fecha Agendada:** {datos.get('fecha')}
        - **Monto Base:** ${datos.get('tarifa')}/hora
        
        *SERVIHOGAR ha notificado directamente al trabajador informándole que su solicitud fue aceptada.*
    """)
    
    if st.button("Volver al Inicio", use_container_width=True):
        st.session_state.pantalla = 'login'
        st.rerun()
