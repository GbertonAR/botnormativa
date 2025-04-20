document.addEventListener('DOMContentLoaded', function() {
    const procesarButton = document.getElementById('procesar_documentos_button');
    const additionalDataForm = document.getElementById('additional-data-form');

    // Inicialmente deshabilitar el botón y ocultar el formulario
    if (procesarButton) {
        procesarButton.disabled = true;
    }
    if (additionalDataForm) {
        additionalDataForm.style.display = 'none';
    }

    // Inicializa datosDocumentos en el window scope (si aún no existe)
    window.datosDocumentos = window.datosDocumentos || {};

    // Define el Proxy para interceptar cambios en window.datosDocumentos
    const datosDocumentosProxy = new Proxy(window.datosDocumentos, {
        set: function(target, property, value) {
            target[property] = value;
            console.log('datosDocumentos actualizado (Proxy):', target); // <-- Verifica este log
            if (verificarDatosDocumentosCompletos()) {
                if (procesarButton) {
                    procesarButton.disabled = false;
                }
            } else {
                if (procesarButton) {
                    procesarButton.disabled = true;
                }
            }
            return true;
        }
    });

    // Asigna el Proxy al objeto window.datosDocumentos
    window.datosDocumentos = datosDocumentosProxy;

    // Función para verificar si todos los datos del documento están presentes
    function verificarDatosDocumentosCompletos() {
        return (
            window.datosDocumentos.hasOwnProperty('certificado_legalidad') &&
            window.datosDocumentos.hasOwnProperty('dorso_dni') &&
            window.datosDocumentos.hasOwnProperty('frente_dni') &&
            window.datosDocumentos.hasOwnProperty('licencia_linti') &&
            window.datosDocumentos.hasOwnProperty('licencia_municipal_dorso') &&
            window.datosDocumentos.hasOwnProperty('licencia_municipal_frente') &&
            window.datosDocumentos.hasOwnProperty('psicofisico') &&
            window.datosDocumentos.hasOwnProperty('certificado_curso')
        );
    }

    // Evento para mostrar el formulario adicional al hacer clic en el botón de procesar
    if (procesarButton) {
        procesarButton.addEventListener('click', function() {
            if (!procesarButton.disabled && additionalDataForm) {
                additionalDataForm.style.display = 'block';
            }
        });
    }
});