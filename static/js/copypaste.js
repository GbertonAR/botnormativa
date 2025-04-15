async function copiarRespuesta(textoRespuesta) {
    try {
        await navigator.clipboard.writeText(textoRespuesta);
        alert('¡Respuesta copiada al portapapeles!');
    } catch (err) {
        console.error('Error al copiar al portapapeles: ', err);
        alert('No se pudo copiar al portapapeles. Por favor, selecciona y copia el texto manualmente.');
    }
}

const botonCopiar = document.getElementById('boton-copiar-respuesta');
const areaRespuesta = document.getElementById('area-respuesta');

if (botonCopiar && areaRespuesta) {
    botonCopiar.addEventListener('click', () => {
        copiarRespuesta(areaRespuesta.textContent);
    });
}

const botonGenerarPdf = document.getElementById('boton-generar-pdf');

if (botonGenerarPdf && areaRespuesta) {
    botonGenerarPdf.addEventListener('click', () => {
        const respuesta = areaRespuesta.textContent;
        const formData = new FormData();
        formData.append('respuesta', respuesta);

        fetch('/pdf/generar', { // Asegúrate de que esta sea la ruta correcta de tu backend
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'respuesta_normativa.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error al generar el PDF:', error);
            alert('No se pudo generar el PDF.');
        });
    });

    function copiarTexto() {
        let textarea = document.getElementById("respuesta");
        textarea.select();
        document.execCommand("copy");  // Método tradicional
        navigator.clipboard.writeText(textarea.value) // Método moderno
            .then(() => alert("Texto copiado"))
            .catch(err => console.error("Error al copiar: ", err));
    }
}