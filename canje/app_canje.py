from flask import Flask
from .canje_app import canje_bp  # Importa el Blueprint
#import config  # Asegúrate de que config.py esté en el mismo directorio o en el PYTHONPATH


app = Flask(__name__)

# Asumiendo que tienes un archivo config.py en el mismo directorio 'canje'
from .config_canje import MAIL_ACCOUNTS as config_canje  # Importa la clase Config
# ... otras configuraciones de la aplicación (por ejemplo, configuración de la base de datos) ...
#app.config.from_object(config_canje)
app.config['MAIL_ACCOUNTS'] = config_canje
print("Claves en config_canje:", config_canje.keys())

# Registra el Blueprint 'canje_bp'
app.register_blueprint(canje_bp) # Puedes especificar el url_prefix aquí si lo deseas

# ... el resto de tu código de la aplicación (otras rutas de la app principal, inicialización de la base de datos, etc.) ...

if __name__ == '__main__':
    app.run(debug=True)