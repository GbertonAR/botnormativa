#!/bin/bash
apt-get update
#apt-get -y install tesseract-ocr libtesseract-dev

# O si necesitas paquetes de idioma (ejemplo para español):
apt-get -y install tesseract-ocr tesseract-ocr-spa

# Asegúrate de que Python pueda encontrar Tesseract (añade la ruta a PATH si es necesario)
# export PATH="$PATH:/usr/local/bin:/usr/bin:/opt/tesseract/bin"

# Resto de tus comandos de despliegue (activación de entorno virtual, instalación de requirements, etc.)
#if [ -f "$DEPLOYMENT_TARGET/requirements.txt" ]; then
#    python -m pip install -r "$DEPLOYMENT_TARGET/requirements.txt" --no-cache-dir
#fi

# Cualquier otro comando necesario para tu aplicación