# --- Archivo para importar los modelos (ejemplo para SQLAlchemy en Flask) ---
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Provincia(db.Model):
    __tablename__ = 'provincias'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    municipios = db.relationship('Municipio', backref='provincia', lazy=True)
    canjes = db.relationship('Canje', backref='provincia', lazy=True)

    def __repr__(self):
        return f"<Provincia {self.nombre}>"

class Municipio(db.Model):
    __tablename__ = 'municipios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id'), nullable=False)
    canjes = db.relationship('Canje', backref='municipio', lazy=True)

    def __repr__(self):
        return f"<Municipio {self.nombre}>"

class Canje(db.Model):
    __tablename__ = 'DatosDeCanje'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_transaccion = db.Column(db.String(50), unique=True, nullable=False)
    fecha_hora = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    ciudadano_presente = db.Column(db.Boolean)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id'))
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipios.id'))
    nombre_ciudadano = db.Column(db.String(100))
    apellido_ciudadano = db.Column(db.String(100))
    documento_frente_dni = db.Column(db.String(255))
    documento_dorso_dni = db.Column(db.String(255))
    documento_licencia_municipal_frente = db.Column(db.String(255))
    documento_licencia_municipal_dorso = db.Column(db.String(255))
    documento_psicofisico = db.Column(db.String(255))
    documento_certificado_curso = db.Column(db.String(255))
    documento_licencia_linti = db.Column(db.String(255))
    documento_certificado_legalidad = db.Column(db.String(255))
    datos_dni_dorso = db.Column(db.JSON)

    provincia = db.relationship('Provincias', backref=db.backref('canjes', lazy=True))
    municipio = db.relationship('Municipios', backref=db.backref('canjes', lazy=True))

    def __repr__(self):
        return f"<Canje {self.codigo_transaccion}>"

# --- Ejemplo de cómo inicializar los modelos en tu aplicación Flask ---
# from flask import Flask
# from tu_archivo_de_modelos import db, Provincia, Municipio, Canje

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'tu_uri_de_base_de_datos'
# db.init_app(app)

# with app.app_context():
#     db.create_all() # Crea las tablas en la base de datos