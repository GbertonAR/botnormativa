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

    const data = {
        ciudadano_presente: ciudadanoPresente,
        provincia_id: provinciaId,
        municipio_id: municipioId
        // ... otros datos que quieras enviar ...
    };

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
        // Aquí puedes manejar la respuesta del servidor, por ejemplo, mostrar un mensaje al usuario
    })
    .catch(error => {
        console.error('Error al enviar los datos:', error);
    });
}