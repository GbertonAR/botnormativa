#!/bin/bash
set -e

echo "Ejecutando script de despliegue personalizado..."

# Actualizar los repositorios
echo "Actualizando repositorios..."
sudo apt-get update

# Instalar Tesseract OCR y paquetes de idioma español
echo "Instalando Tesseract OCR y paquete de idioma español..."
sudo apt-get -y install tesseract-ocr tesseract-ocr-spa

echo "Tesseract OCR instalado."

# Instalar dependencias de Python desde requirements.txt
echo "Instalando dependencias de Python..."
if [ -f "$HOME/site/wwwroot/requirements.txt" ]; then
    python -m pip install -r "$HOME/site/wwwroot/requirements.txt" --no-cache-dir
fi

echo "Dependencias de Python instaladas."

# Puedes agregar aquí cualquier otro comando que necesites ejecutar
# después de la instalación de Tesseract y las dependencias.

echo "Script de despliegue personalizado completado."