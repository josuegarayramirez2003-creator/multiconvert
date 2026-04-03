from flask import Flask, render_template, request, send_file
from PIL import Image
import os
import zipfile

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================== RUTAS ====================

# Ruta principal
@app.route('/')
def home():
    return render_template('index.html')

# Ruta de subida y conversión
@app.route('/upload', methods=['POST'])
def upload():
    archivos = request.files.getlist('imagenes')
    formato = request.form.get('formato')
    modo = request.form.get('modo')

    if not archivos or archivos[0].filename == '':
        return "No se seleccionaron archivos", 400

    rutas_convertidas = []

    for archivo in archivos:
        # Guardar archivo original temporalmente
        ruta_original = os.path.join(UPLOAD_FOLDER, archivo.filename)
        archivo.save(ruta_original)

        # Abrir imagen
        img = Image.open(ruta_original)
        nombre_sin_ext = os.path.splitext(archivo.filename)[0]

        # Convertir según el formato elegido
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

        # Eliminar el archivo original si es diferente al convertido
        if ruta_original != nueva_ruta:
            try:
                os.remove(ruta_original)
            except:
                pass

    # Descarga individual o en ZIP
    if modo == 'individual' and len(rutas_convertidas) == 1:
        return send_file(rutas_convertidas[0], as_attachment=True)
    else:
        zip_path = os.path.join(UPLOAD_FOLDER, 'resultado.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for ruta in rutas_convertidas:
                zipf.write(ruta, os.path.basename(ruta))
        
        return send_file(zip_path, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
