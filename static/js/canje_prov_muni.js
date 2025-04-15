document.addEventListener('DOMContentLoaded', function() {
    const provinciaSelect = document.getElementById('provincia');
    const municipioSelect = document.getElementById('municipio');

    // Cargar provincias al cargar la página
    fetch('/canje/provincias')
        .then(response => response.json())
        .then(data => {
            data.forEach(provincia => {
                const option = document.createElement('option');
                option.value = provincia.id;
                option.textContent = provincia.nombre;
                provinciaSelect.appendChild(option);
            });
        });

    // Cargar municipios al cambiar la provincia seleccionada
    provinciaSelect.addEventListener('change', function() {
        const provinciaId = this.value;
        municipioSelect.innerHTML = '<option value="">Seleccione un municipio</option>'; // Limpiar municipios
        municipioSelect.disabled = true; // Deshabilitar hasta que se carguen los municipios

        if (provinciaId) {
            fetch(`/canje/municipios/${provinciaId}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(municipio => {
                        const option = document.createElement('option');
                        option.value = municipio.id;
                        option.textContent = municipio.nombre;
                        municipioSelect.appendChild(option);
                    });
                    municipioSelect.disabled = false; // Habilitar después de cargar los municipios
                });
        }
    });
});

// *** AÑADE ESTA FUNCIÓN AQUÍ (OPCIÓN RECOMENDADA) ***
function cambiarColorBoton(botonId, nuevoColor) {
    const boton = document.getElementById(botonId + '_button'); // MODIFICACIÓN PARA CONCATENAR '_button'
    if (boton) {
        boton.style.backgroundColor = nuevoColor;
    } else {
        console.error(`No se encontró el botón con el ID: ${botonId}_button`); // MODIFICACIÓN DEL MENSAJE
    }
}


function enviarDatos() {
    const ciudadanoPresente = document.querySelector('input[name="ciudadano_presente"]:checked').value;
    const provinciaId = document.getElementById('provincia').value;
    const municipioId = document.getElementById('municipio').value;

    // Datos extraídos del dorso del DNI (si los tienes almacenados)
    const nombre = document.getElementById('nombre_leido').textContent;
    const apellidos = document.getElementById('apellidos_leido').textContent;
    const dni = document.getElementById('numero_documento_leido').textContent;

    // Rutas o nombres de archivo de las imágenes cargadas
    const frente_dni_imagen = datosDocumentos['preview_frente_dni'] ? datosDocumentos['preview_frente_dni'].filename : null;
    const dorso_dni_imagen = datosDocumentos['preview_dorso_dni'] ? datosDocumentos['preview_dorso_dni'].filename : null;
    const licencia_frente_imagen = datosDocumentos['preview_licencia_municipal_frente'] ? datosDocumentos['preview_licencia_municipal_frente'].filename : null;
    const licencia_dorso_imagen = datosDocumentos['preview_licencia_municipal_dorso'] ? datosDocumentos['preview_licencia_municipal_dorso'].filename : null;
    const psicofisico_imagen = datosDocumentos['preview_psicofisico'] ? datosDocumentos['preview_psicofisico'].filename : null;
    const certificado_curso_imagen = datosDocumentos['preview_certificado_curso'] ? datosDocumentos['preview_certificado_curso'].filename : null;
    const licencia_linti_imagen = datosDocumentos['preview_licencia_linti'] ? datosDocumentos['preview_licencia_linti'].filename : null;
    const certificado_legalidad_imagen = datosDocumentos['preview_certificado_legalidad'] ? datosDocumentos['preview_certificado_legalidad'].filename : null;

    const data = {
        ciudadano_presente: ciudadanoPresente,
        provincia_id: provinciaId, // Asegúrate que coincida con el nombre de la columna en DB
        municipio_id: municipioId,   // Asegúrate que coincida con el nombre de la columna en DB
        nombre: nombre,
        apellido: apellidos,
        dni: dni,
        frente_dni_imagen: frente_dni_imagen,
        dorso_dni_imagen: dorso_dni_imagen,
        licencia_frente_imagen: licencia_frente_imagen,
        licencia_dorso_imagen: licencia_dorso_imagen,
        linti_imagen: licencia_linti_imagen,
        curso_certificado_imagen: certificado_curso_imagen,
        psicofisico_certificado_imagen: psicofisico_imagen, // Asumiendo que 'psicofisico' guarda el filename
        legalidad_certificado_imagen: certificado_legalidad_imagen, // Asumiendo que 'certificado_legalidad' guarda el filename
        // ... y así sucesivamente para todos los campos de tu tabla DatosDeCanje ...
    };

    console.log('Datos a enviar:', data); // Para debugging

    fetch('/canje/guardar_datos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log('Respuesta del servidor:', result);
        // Aquí puedes manejar la respuesta del servidor
    })
    .catch(error => {
        console.error('Error al enviar los datos:', error);
    });
}