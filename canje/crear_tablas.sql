-- Script para crear la tabla Provincias
CREATE TABLE IF NOT EXISTS Provincias (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT UNIQUE NOT NULL
);

-- Script para crear la tabla Municipios
CREATE TABLE IF NOT EXISTS Municipios (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Nombre TEXT NOT NULL,
    Id_Provincia INTEGER NOT NULL,
    Mail_Institucional TEXT,
    FOREIGN KEY (Id_Provincia) REFERENCES Provincias(ID)
);

-- Script para crear la tabla DatosDeCanje (con las columnas que discutimos)
CREATE TABLE IF NOT EXISTS DatosDeCanje (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_ingreso DATE NOT NULL,
    estado VARCHAR(20) NOT NULL,
    dni VARCHAR(20),
    apellido VARCHAR(100),
    nombre VARCHAR(100),
    psicofisico_apellido VARCHAR(100),
    psicofisico_nombre VARCHAR(100),
    psicofisico_categoria VARCHAR(50),
    psicofisico_f_examen DATE,
    psicofisico_f_dictamen DATE,
    psicofisico_dni VARCHAR(20),
    psicofisico_imagen VARCHAR(255),
    curso_nombre VARCHAR(100),
    curso_apellido VARCHAR(100),
    curso_dni VARCHAR(20),
    curso_imagen VARCHAR(255),
    legalidad_nombre VARCHAR(100),
    legalidad_apellido VARCHAR(100),
    legalidad_dni VARCHAR(20),
    legalidad_imagen VARCHAR(255),
    provincia VARCHAR(100),
    municipio VARCHAR(100),
    ciudadano_presencial VARCHAR(10),
    frente_dni_imagen VARCHAR(255),
    dorso_dni_imagen VARCHAR(255),
    licencia_frente_imagen VARCHAR(255),
    licencia_dorso_imagen VARCHAR(255),
    linti_imagen VARCHAR(255),
    curso_certificado_imagen VARCHAR(255),
    psicofisico_certificado_imagen VARCHAR(255),
    legalidad_certificado_imagen VARCHAR(255)
);