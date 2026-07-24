import streamlit as st
import sqlite3
import hashlib
from datetime import date
import urllib.parse

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SERVIHOGAR",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E3A8A; font-weight: 800; }
    .sub-title { text-align: center; color: #4B5563; font-size: 14px; margin-bottom: 20px; }
    .card { background-color: #FFFFFF; padding: 15px; border-radius: 12px; border: 1px solid #E5E7EB; margin-bottom: 10px; }
    .badge-cert { background-color: #DBEAFE; color: #1E40AF; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
    .badge-status { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: bold; }
    .msg-box { background-color: #F3F4F6; border-left: 4px solid #1E3A8A; padding: 12px; margin-bottom: 10px; border-radius: 4px; }
    .doc-box { background-color: #F9FAFB; border: 1px dashed #CBD5E1; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. BASE DE DATOS LOCAL (SQLite)
# -----------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect('servihogar_app.db')
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            categoria TEXT DEFAULT 'N/A',
            tarifa REAL DEFAULT 0.0,
            foto BLOB,
            cv BLOB,
            cv_nombre TEXT,
            estado_tramite TEXT DEFAULT 'En Revisión',
            certificado INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla de Contratos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleador TEXT NOT NULL,
            empleado TEXT NOT NULL,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            estado TEXT DEFAULT 'SOLICITADO'
        )
    ''')

    # Tabla de Notificaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Crear usuario ADMINISTRADOR maestro si no existe
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (username, password, rol, nombre, email, telefono, estado_tramite, certificado)
            VALUES ('admin', ?, 'admin', 'Administrador SERVIHOGAR', 'admin@servihogar.com', '0000000000', 'Activo', 1)
        ''', (pwd_hash,))
        
    conn.commit()
    conn.close()

init_db()

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generar_link_whatsapp(telefono, nombre):
    mensaje = f"🎉 *¡Hola {nombre}!* Tu solicitud en *SERVIHOGAR* ha sido APROBADA y CERTIFICADA. Tu perfil ya está activo en el catálogo."
    mensaje_url = urllib.parse.quote(mensaje)
    tel_limpio = ''.join(filter(str.isdigit, str(telefono)))
    return f"https://api.whatsapp.com/send?phone={tel_limpio}&text={mensaje_url}"

# -----------------------------------------------------------------------------
# 2. CONTROL DE SESIÓN
# -----------------------------------------------------------------------------
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = 'login'
if 'usuario_logueado' not in st.session_state:
    st.session_state.usuario_logueado = None
if 'empleado_sel' not in st.session_state:
    st.session_state.empleado_sel = None

# -----------------------------------------------------------------------------
# PANTALLA 1: LOGIN Y REGISTRO
# -----------------------------------------------------------------------------
if st.session_state.pantalla == 'login':
    st.markdown("<h1 class='main-title'>SERVIHOGAR</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Plataforma de Empleo Certificado</p>", unsafe_allow_html=True)

    tab_login, tab_reg_empleador, tab_reg_empleado = st.tabs(["🔑 Iniciar Sesión", "🏠 Reg. Empleador", "👷‍♂️ Reg. Trabajador"])

    # LOGIN
    with tab_login:
        with st.form("form_login"):
            user = st.text_input("Usuario:")
            pwd = st.text_input("Contraseña:", type="password")
            submit_login = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit_login:
                conn = sqlite3.connect('servihogar_app.db')
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, rol, nombre, email, estado_tramite, certificado FROM usuarios WHERE username = ? AND password = ?", (user, hash_pass(pwd)))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    st.session_state.usuario_logueado = {
                        "id": row[0], "username": row[1], "rol": row[2], "nombre": row[3], "email": row[4], "estado_tramite": row[5], "certificado": row[6]
                    }
                    if row[2] == 'admin':
                        st.session_state.pantalla = 'panel_admin'
                    elif row[2] == 'empleador':
                        st.session_state.pantalla = 'catalogo'
                    else:
                        st.session_state.pantalla = 'panel_empleado'
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    # REGISTRO EMPLEADOR
    with tab_reg_empleador:
        st.subheader("Crear Cuenta de Empleador / Empresa")
        with st.form("form_reg_empleador"):
            emp_nombre = st.text_input("Nombre / Razón Social:")
            emp_email = st.text_input("Correo:")
            emp_phone = st.text_input("Teléfono:")
            emp_user = st.text_input("Nombre de Usuario:")
            emp_pass = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Registrarme", use_container_width=True):
                if emp_nombre and emp_user and emp_pass:
                    try:
                        conn = sqlite3.connect('servihogar_app.db')
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (username, password, rol, nombre, email, telefono) VALUES (?, ?, 'empleador', ?, ?, ?)",
                                       (emp_user, hash_pass(emp_pass), emp_nombre, emp_email, emp_phone))
                        conn.commit()
                        conn.close()
                        st.success("¡Cuenta creada! Puedes iniciar sesión.")
                    except:
                        st.error("El usuario ya existe.")

    # REGISTRO TRABAJADOR
    with tab_reg_empleado:
        st.subheader("Postularme como Trabajador")
        with st.form("form_reg_trabajador"):
            tra_nombre = st.text_input("Nombre Completo:")
            tra_email = st.text_input("Correo:")
            tra_phone = st.text_input("Teléfono / WhatsApp:")
            tra_cat = st.selectbox("Categoría:", ["Limpieza Doméstica", "Carpintería", "Electricidad", "Jardinería", "Plomería", "Pintura"])
            tra_tarifa = st.number_input("Tarifa por hora ($):", min_value=1.0, value=10.0)
            tra_foto = st.file_uploader("Foto de perfil (JPG/PNG):", type=["jpg", "jpeg", "png"])
            tra_cv = st.file_uploader("Currículum (PDF/Word):", type=["pdf", "doc", "docx"])
            tra_user = st.text_input("Usuario:")
            tra_pass = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Enviar Postulación", use_container_width=True):
                if tra_nombre and tra_user and tra_pass and tra_foto and tra_cv:
                    try:
                        conn = sqlite3.connect('servihogar_app.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO usuarios (username, password, rol, nombre, email, telefono, categoria, tarifa, foto, cv, cv_nombre, estado_tramite, certificado)
                            VALUES (?, ?, 'empleado', ?, ?, ?, ?, ?, ?, ?, ?, 'En Revisión de Documentos', 0)
                        ''', (tra_user, hash_pass(tra_pass), tra_nombre, tra_email, tra_phone, tra_cat, tra_tarifa, tra_foto.read(), tra_cv.read(), tra_cv.name))
                        
                        uid = cursor.lastrowid
                        cursor.execute("INSERT INTO notificaciones (usuario_id, titulo, mensaje, fecha) VALUES (?, ?, ?, ?)",
                                       (uid, '🎉 ¡Bienvenido!', 'Tu solicitud está en revisión por el Administrador.', str(date.today())))
                        conn.commit()
                        conn.close()
                        st.success("¡Registro enviado! Revisa tus mensajes al iniciar sesión.")
                    except:
                        st.error("El usuario ya existe.")
                else:
                    st.warning("Completa todos los campos y adjunta los archivos.")


# -----------------------------------------------------------------------------
# PANTALLA 2: PANEL DE ADMINISTRACIÓN COMPLETO (VISOR DE DOCUMENTOS)
# -----------------------------------------------------------------------------
elif st.session_state.pantalla == 'panel_admin':
    usr = st.session_state.usuario_logueado
    st.markdown("<h2 style='color:#1E3A8A;'>🛡️ Panel del Administrador</h2>", unsafe_allow_html=True)
    st.caption("Gestión Integral y Auditoría de Documentos")

    # MÉTRICAS RÁPIDAS
    conn = sqlite3.connect('servihogar_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='empleado' AND certificado=0")
    num_pendientes = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='empleado' AND certificado=1")
    num_certificados = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM contratos")
    num_contratos = cursor.fetchone()[0]
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Pendientes", num_pendientes)
    col_m2.metric("Certificados", num_certificados)
    col_m3.metric("Contratos", num_contratos)

    st.write("---")

    tab_aprobar, tab_usuarios, tab_contratos_admin = st.tabs([
        "📋 Aprobar y Ver Documentos", 
        "👥 Modificar / Borrar Usuarios", 
        "📄 Ver Todos los Contratos"
    ])

    # 1. VISOR DE DOCUMENTOS Y APROBACIÓN
    with tab_aprobar:
        st.subheader("Solicitudes e Expedientes por Revisar")
        cursor.execute("SELECT id, nombre, email, telefono, categoria, cv_nombre, foto, cv FROM usuarios WHERE rol='empleado' AND certificado=0")
        pendientes = cursor.fetchall()
        
        if not pendientes:
            st.info("No hay trámites pendientes de revisión.")
        else:
            for p in pendientes:
                p_id, p_nom, p_em, p_tel, p_cat, p_cv_nom, p_foto, p_cv_data = p
                with st.expander(f"📁 Expediente: {p_nom} ({p_cat})"):
                    st.write(f"**Correo:** {p_em} | **Teléfono:** {p_tel}")
                    
                    # VISUALIZACIÓN DE ARCHIVOS SUBIDOS
                    st.markdown("<div class='doc-box'>", unsafe_allow_html=True)
                    col_doc1, col_doc2 = st.columns([1, 2])
                    
                    with col_doc1:
                        if p_foto:
                            st.image(p_foto, caption="Foto de Perfil Subida", width=120)
                        else:
                            st.warning("Sin foto de perfil.")
                            
                    with col_doc2:
                        st.write(f"📄 **Documento CV:** {p_cv_nom if p_cv_nom else 'No adjuntado'}")
                        if p_cv_data:
                            st.download_button(
                                label="📥 Descargar Currículum",
                                data=p_cv_data,
                                file_name=p_cv_nom if p_cv_nom else "curriculum.pdf",
                                mime="application/octet-stream",
                                key=f"dl_{p_id}"
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"✅ Aprobar y Certificar", key=f"ap_{p_id}", use_container_width=True):
                            cursor.execute("UPDATE usuarios SET certificado=1, estado_tramite='Aprobado y Certificado' WHERE id=?", (p_id,))
                            cursor.execute("INSERT INTO notificaciones (usuario_id, titulo, mensaje, fecha) VALUES (?, ?, ?, ?)",
                                           (p_id, '✅ ¡Certificación Aprobada!', 'Tu perfil ha sido verificado y ya está visible en el catálogo.', str(date.today())))
                            conn.commit()
                            
                            wa_url = generar_link_whatsapp(p_tel, p_nom)
                            st.success(f"¡{p_nom} ha sido Aprobado!")
                            st.markdown(f"[📲 **Notificar por WhatsApp a {p_nom}**]({wa_url})", unsafe_allow_html=True)
                            st.rerun()
                    with c2:
                        if st.button(f"❌ Rechazar Documentos", key=f"rej_{p_id}", use_container_width=True):
                            cursor.execute("UPDATE usuarios SET estado_tramite='Rechazado - Documentación Incompleta' WHERE id=?", (p_id,))
                            conn.commit()
                            st.warning("Solicitud rechazada.")
                            st.rerun()

    # 2. AUDITORÍA GENERAL DE USUARIOS (TODOS LOS PERFILES Y SUS ARCHIVOS)
    with tab_usuarios:
        st.subheader("Directorio General de Usuarios")
        cursor.execute("SELECT id, username, nombre, rol, categoria, tarifa, certificado, email, telefono, cv_nombre, foto, cv FROM usuarios WHERE rol != 'admin'")
        todos_usuarios = cursor.fetchall()
        
        for u in todos_usuarios:
            u_id, u_user, u_nom, u_rol, u_cat, u_tar, u_cert, u_em, u_tel, u_cv_nom, u_foto, u_cv_data = u
            
            with st.expander(f"👤 [{u_rol.upper()}] {u_nom} (@{u_user})"):
                # Mostrar archivos cargados
                if u_rol == "empleado":
                    col_u1, col_u2 = st.columns([1, 2])
                    with col_u1:
                        if u_foto:
                            st.image(u_foto, width=80)
                    with col_u2:
                        st.write(f"**Correo:** {u_em} | **Tel:** {u_tel}")
                        if u_cv_data:
                            st.download_button(
                                label="📥 Descargar CV de usuario",
                                data=u_cv_data,
                                file_name=u_cv_nom if u_cv_nom else "cv.pdf",
                                mime="application/octet-stream",
                                key=f"dl_gen_{u_id}"
                            )
                
                # Formulario de Edición y Eliminación
                with st.form(f"form_edit_{u_id}"):
                    nuevo_nombre = st.text_input("Nombre completo:", value=u_nom)
                    nuevo_rol = st.selectbox("Rol:", ["empleado", "empleador"], index=0 if u_rol == "empleado" else 1)
                    
                    if u_rol == "empleado":
                        nueva_cat = st.selectbox("Categoría:", ["Limpieza Doméstica", "Carpintería", "Electricidad", "Jardinería", "Plomería", "Pintura"], index=0)
                        nueva_tarifa = st.number_input("Tarifa ($/hr):", value=float(u_tar))
                        nuevo_cert = st.checkbox("¿Está Certificado?", value=bool(u_cert))
                    else:
                        nueva_cat, nueva_tarifa, nuevo_cert = "N/A", 0.0, 0
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        guardar = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                    with col_b2:
                        borrar = st.form_submit_button("🗑️ Eliminar Usuario", type="primary", use_container_width=True)
                    
                    if guardar:
                        cursor.execute("""
                            UPDATE usuarios 
                            SET nombre=?, rol=?, categoria=?, tarifa=?, certificado=? 
                            WHERE id=?
                        """, (nuevo_nombre, nuevo_rol, nueva_cat, nueva_tarifa, 1 if nuevo_cert else 0, u_id))
                        conn.commit()
                        st.success("¡Datos actualizados correctamente!")
                        st.rerun()
                        
                    if borrar:
                        cursor.execute("DELETE FROM usuarios WHERE id=?", (u_id,))
                        conn.commit()
                        st.warning(f"Usuario {u_nom} eliminado de la base de datos.")
                        st.rerun()

    # 3. VER CONTRATOS GENERADOS
    with tab_contratos_admin:
        st.subheader("Historial de Contratos Generados")
        cursor.execute("SELECT id, empleador, empleado, fecha, descripcion, estado FROM contratos ORDER BY id DESC")
        contratos_all = cursor.fetchall()
        
        if not contratos_all:
            st.info("No se han generado contratos aún.")
        else:
            for c in contratos_all:
                st.markdown(f"""
                    <div class='card'>
                        <b>Contrato #{c[0]}</b> - <span class='badge-status'>{c[5]}</span><br>
                        <b>Empleador:</b> {c[1]} ➔ <b>Trabajador:</b> {c[2]}<br>
                        <b>Fecha Trabajo:</b> {c[3]}<br>
                        <small><b>Detalle:</b> {c[4]}</small>
                    </div>
                """, unsafe_allow_html=True)
                
    conn.close()

    st.write("---")
    if st.button("⬅️ Cerrar Sesión Administrador"):
        st.session_state.usuario_logueado = None
        st.session_state.pantalla = 'login'
        st.rerun()


# -----------------------------------------------------------------------------
# PANTALLAS DE EMPLEADOR Y TRABAJADOR
# -----------------------------------------------------------------------------
elif st.session_state.pantalla == 'catalogo':
    usr = st.session_state.usuario_logueado
    st.markdown(f"<h3 style='color:#1E3A8A;'>Bienvenido, {usr['nombre']}</h3>", unsafe_allow_html=True)
    cat_sel = st.selectbox("Filtrar por categoría:", ["Todas", "Limpieza Doméstica", "Carpintería", "Electricidad", "Jardinería", "Plomería", "Pintura"])
    
    conn = sqlite3.connect('servihogar_app.db')
    cursor = conn.cursor()
    if cat_sel == "Todas":
        cursor.execute("SELECT id, nombre, categoria, tarifa, foto FROM usuarios WHERE rol='empleado' AND certificado=1")
    else:
        cursor.execute("SELECT id, nombre, categoria, tarifa, foto FROM usuarios WHERE rol='empleado' AND certificado=1 AND categoria=?", (cat_sel,))
    trabajadores = cursor.fetchall()
    conn.close()

    st.write("---")
    for t in trabajadores:
        t_id, t_nom, t_cat, t_tar, t_foto = t
        col1, col2 = st.columns([1, 3])
        with col1:
            if t_foto:
                st.image(t_foto, width=70)
            else:
                st.write("👤")
        with col2:
            st.markdown(f"**{t_nom}** <span class='badge-cert'>✓ Certificado SERVIHOGAR</span>", unsafe_allow_html=True)
            st.caption(f"Categoría: {t_cat} | Tarifa: ${t_tar}/hr")
            if st.button(f"Contratar", key=f"btn_{t_id}"):
                st.session_state.empleado_sel = {"id": t_id, "nombre": t_nom, "categoria": t_cat, "tarifa": t_tar}
                st.session_state.pantalla = 'contrato'
                st.rerun()

    if st.button("⬅️ Cerrar Sesión"):
        st.session_state.usuario_logueado = None
        st.session_state.pantalla = 'login'
        st.rerun()

elif st.session_state.pantalla == 'contrato':
    emp = st.session_state.empleado_sel
    usr = st.session_state.usuario_logueado
    st.markdown("<h2 style='color:#1E3A8A;'>Acuerdo de Servicio Digital</h2>", unsafe_allow_html=True)
    st.info(f"**Contratante:** {usr['nombre']}\n\n**Empleado:** {emp['nombre']} ({emp['categoria']})")

    with st.form("form_contrato_app"):
        fecha_trabajo = st.date_input("Fecha requerida:", min_value=date.today())
        desc_trabajo = st.text_area("Descripción de las labores:")
        acepta = st.checkbox("Acepto los términos de servicio de SERVIHOGAR.")
        
        if st.form_submit_button("✍️ Firmar y Notificar al Empleado", use_container_width=True):
            if desc_trabajo and acepta:
                conn = sqlite3.connect('servihogar_app.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO contratos (empleador, empleado, fecha, descripcion) VALUES (?, ?, ?, ?)",
                               (usr['nombre'], emp['nombre'], str(fecha_trabajo), desc_trabajo))
                conn.commit()
                conn.close()
                st.session_state.pantalla = 'exito'
                st.rerun()

    if st.button("Volver al Catálogo"):
        st.session_state.pantalla = 'catalogo'
        st.rerun()

elif st.session_state.pantalla == 'exito':
    st.balloons()
    st.success("🎉 ¡Solicitud de Contrato Generada con Éxito!")
    if st.button("Volver al Catálogo", use_container_width=True):
        st.session_state.pantalla = 'catalogo'
        st.rerun()

elif st.session_state.pantalla == 'panel_empleado':
    usr = st.session_state.usuario_logueado
    st.markdown(f"<h3 style='color:#1E3A8A;'>Hola, {usr['nombre']}</h3>", unsafe_allow_html=True)
    
    conn = sqlite3.connect('servihogar_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT estado_tramite, certificado, foto, cv_nombre FROM usuarios WHERE id=?", (usr['id'],))
    u_info = cursor.fetchone()
    estado_actual, es_cert, foto_data, cv_nombre = u_info
    
    st.markdown(f"**Estatus de tu Trámite:** <span class='badge-status'>⏳ {estado_actual}</span>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("📩 Mensajes de SERVIHOGAR")
    cursor.execute("SELECT titulo, mensaje, fecha FROM notificaciones WHERE usuario_id=? ORDER BY id DESC", (usr['id'],))
    mensajes = cursor.fetchall()
    for m in mensajes:
        st.markdown(f"<div class='msg-box'><small>{m[2]}</small><h5>{m[0]}</h5><p>{m[1]}</p></div>", unsafe_allow_html=True)

    st.subheader("📬 Solicitudes de Contrato Recibidas")
    cursor.execute("SELECT id, empleador, fecha, descripcion, estado FROM contratos WHERE empleado=?", (usr['nombre'],))
    mis_contratos = cursor.fetchall()
    conn.close()

    for c in mis_contratos:
        st.markdown(f"<div class='card'><b>Empleador:</b> {c[1]}<br><b>Fecha:</b> {c[2]}<br><b>Detalle:</b> {c[3]}</div>", unsafe_allow_html=True)

    if st.button("⬅️ Cerrar Sesión"):
        st.session_state.usuario_logueado = None
        st.session_state.pantalla = 'login'
        st.rerun()
