from flask import Flask, render_template, request, send_file, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from PIL import Image
import zipfile

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================== CONFIGURACIÓN DE LOGIN ====================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'   # Si intentas acceder a rutas protegidas, te manda aquí

USERS = {
    "admin": {"password": "1234"}
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# ==================== RUTAS ====================

# Ruta de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USERS and USERS[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect('/')  

        else:
            return "Usuario o contraseña incorrectos", 401

    return render_template('login.html')


# Ruta de Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# Ruta principal → YA NO requiere login
@app.route('/')
def home():
    return render_template('index.html')


# Ruta de subida y conversión (mantengo protegida con login)
@app.route('/upload', methods=['POST'])
def upload():
    archivos = request.files.getlist('imagenes')
    formato = request.form.get('formato')
    modo = request.form.get('modo')

    if not archivos or archivos[0].filename == '':
        return "No se seleccionaron archivos", 400

    rutas_convertidas = []

    for archivo in archivos:
        ruta_original = os.path.join(UPLOAD_FOLDER, archivo.filename)
        archivo.save(ruta_original)

        img = Image.open(ruta_original)
        nombre_sin_ext = os.path.splitext(archivo.filename)[0]

        if formato == 'jpg':
            img = img.convert('RGB')
            nuevo_nombre = nombre_sin_ext + '.jpg'
            nueva_ruta = os.path.join(UPLOAD_FOLDER, nuevo_nombre)
            img.save(nueva_ruta, 'JPEG', quality=50, optimize=True)
        else:  # png
            nuevo_nombre = nombre_sin_ext + '.png'
            nueva_ruta = os.path.join(UPLOAD_FOLDER, nuevo_nombre)
            img.save(nueva_ruta, 'PNG', optimize=True)

        rutas_convertidas.append(nueva_ruta)

        # Limpiar archivo original si es diferente
        if ruta_original != nueva_ruta:
            try:
                os.remove(ruta_original)
            except:
                pass

    # Descarga
    if modo == 'individual' and len(rutas_convertidas) == 1:
        return send_file(rutas_convertidas[0], as_attachment=True)
    else:
        zip_path = os.path.join(UPLOAD_FOLDER, 'resultado.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for ruta in rutas_convertidas:
                zipf.write(ruta, os.path.basename(ruta))

        return send_file(zip_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)