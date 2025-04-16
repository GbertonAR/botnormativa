#!/bin/bash
set -euo pipefail
sudo apt update
sudo add-apt-repository universe -y
sudo apt update
sudo apt install -y tesseract-ocr
sudo apt install -y tesseract-ocr-eng

# #!/bin/bash
# set -e

# echo "Ejecutando script de despliegue personalizado..."

# # Actualizar los repositorios
# echo "Actualizando repositorios..."
# sudo apt-get update

# # Instalar Tesseract OCR y paquetes de idioma español
# # echo "Instalando Tesseract OCR y paquete de idioma español..."
# # sudo apt-get -y install tesseract-ocr tesseract-ocr-spa



# echo "Tesseract OCR instalado."

# # Puedes agregar aquí cualquier otro comando que necesites ejecutar
# # DESPUÉS de que Oryx haya instalado las dependencias de Python.

# echo "Script de despliegue personalizado completado."