from flask import Flask
from .canje_app import canje_bp  # Importa el Blueprint

app = Flask(__name__)
# ... otras configuraciones de la aplicación (por ejemplo, configuración de la base de datos) ...

# Registra el Blueprint 'canje_bp'
app.register_blueprint(canje_bp) # Puedes especificar el url_prefix aquí si lo deseas

# ... el resto de tu código de la aplicación (otras rutas de la app principal, inicialización de la base de datos, etc.) ...

if __name__ == '__main__':
    app.run(debug=True)