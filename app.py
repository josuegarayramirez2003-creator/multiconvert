from flask import Flask, render_template, request, send_file, after_this_request
from PIL import Image, UnidentifiedImageError
import os
import zipfile
import tempfile
import shutil
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'

# ==================== CONFIGURACIÓN ====================
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB (ajusta según necesites)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== RUTAS ====================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # Soporte mejorado para móviles y navegadores
    archivos = request.files.getlist('imagenes')
    if not archivos or (len(archivos) == 1 and archivos[0].filename == ''):
        archivo_unico = request.files.get('imagenes')
        if archivo_unico and archivo_unico.filename != '':
            archivos = [archivo_unico]
        else:
            return "No se seleccionaron archivos", 400

    formato = request.form.get('formato')
    modo = request.form.get('modo', 'zip')

    if formato not in ['jpg', 'png']:
        return "Formato no válido (usa jpg o png)", 400

    converted_files = []
    temp_files_to_cleanup = []

    try:
        for archivo in archivos:
            if not archivo or not archivo.filename or not allowed_file(archivo.filename):
                continue

            filename = secure_filename(archivo.filename)
            temp_id = str(uuid.uuid4())
            ruta_original = os.path.join(app.config['UPLOAD_FOLDER'], f"{temp_id}_{filename}")
            
            archivo.save(ruta_original)
            temp_files_to_cleanup.append(ruta_original)

            try:
                img = Image.open(ruta_original)
            except UnidentifiedImageError:
                continue  # Imagen inválida

            nombre_sin_ext = os.path.splitext(filename)[0]

            if formato == 'jpg':
                img = img.convert('RGB')
                nuevo_nombre = f"{nombre_sin_ext}.jpg"
                nueva_ruta = os.path.join(app.config['UPLOAD_FOLDER'], f"{temp_id}_{nuevo_nombre}")
                img.save(nueva_ruta, 'JPEG', quality=85, optimize=True)
            else:  # png
                nuevo_nombre = f"{nombre_sin_ext}.png"
                nueva_ruta = os.path.join(app.config['UPLOAD_FOLDER'], f"{temp_id}_{nuevo_nombre}")
                img.save(nueva_ruta, 'PNG', optimize=True, compress_level=6)

            converted_files.append((nueva_ruta, nuevo_nombre))
            temp_files_to_cleanup.append(nueva_ruta)

            # Eliminar original
            if os.path.exists(ruta_original):
                try:
                    os.remove(ruta_original)
                except:
                    pass

        if not converted_files:
            return "Ningún archivo válido pudo procesarse", 400

        # Descarga individual
        if modo == 'individual' and len(converted_files) == 1:
            file_path, download_name = converted_files[0]
            
            @after_this_request
            def cleanup(response):
                for f in temp_files_to_cleanup:
                    try:
                        if os.path.exists(f):
                            os.remove(f)
                    except:
                        pass
                return response
            
            return send_file(file_path, as_attachment=True, download_name=download_name)

        # Crear ZIP
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f"convertidas_{uuid.uuid4()}.zip")
        temp_files_to_cleanup.append(zip_path)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, download_name in converted_files:
                zipf.write(file_path, download_name)

        @after_this_request
        def cleanup(response):
            for f in temp_files_to_cleanup:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except:
                    pass
            return response

        return send_file(zip_path, as_attachment=True, download_name='imagenes_convertidas.zip')

    except Exception as e:
        # Limpieza en caso de error
        for f in temp_files_to_cleanup:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        return f"Error procesando las imágenes: {str(e)}", 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
