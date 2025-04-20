document.addEventListener('DOMContentLoaded', function() {
    const enviarCorreoBtn = document.getElementById('enviar-correo-btn');
    const cuentaEnvioSelect = document.getElementById('cuenta-envio');
    const textoAdicionalTextarea = document.getElementById('texto-adicional');
    const modalEnviarCorreo = document.getElementById('modal-enviar-correo');

    if (enviarCorreoBtn) {
        enviarCorreoBtn.addEventListener('click', function() {
            const canjeId = this.dataset.canjeId;
            const sendFrom = cuentaEnvioSelect.value;
            const additionalText = textoAdicionalTextarea.value;

            fetch(`/canje/procesar_y_enviar_mail/${canjeId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ send_from: sendFrom, additional_text: additionalText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('¡Éxito!', data.success, 'success').then(() => {
                        modalEnviarCorreo.style.display = 'none';
                        textoAdicionalTextarea.value = '';
                        // Opcional: Recargar la página o actualizar el estado del canje en la UI
                    });
                } else if (data.error) {
                    Swal.fire('¡Error!', data.error, 'error');
                }
            })
            .catch(error => {
                Swal.fire('¡Error de conexión!', 'Hubo un problema al comunicarse con el servidor.', 'error');
            });
        });
    }
});