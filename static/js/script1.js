
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("consultaForm");
    const consultaInput = document.getElementById("consulta");
    const respuestaDiv = document.getElementById("respuesta");
    const ejemploDiv = document.getElementById("ejemplo");

    if (!form) {
        console.error("❌ Error: No se encontró el formulario 'consultaForm' en el DOM.");
        return;
    }

    if (!consultaInput) {
        console.error("❌ Error: No se encontró el input 'consulta' en el DOM.");
        return;
    }

    if (!respuestaDiv) {
        console.warn("⚠️ Advertencia: No se encontró el div con id 'respuesta'. Puede que no se muestre la respuesta.");
    }

    if (!ejemploDiv) {
        console.warn("⚠️ Advertencia: No se encontró el div con id 'ejemplo'. Puede que no se muestre el ejemplo.");
    }

    console.log("✅ Input 'consulta' encontrado correctamente.");

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const consulta = consultaInput.value.trim();

        if (consulta === "") {
            respuestaDiv.innerHTML = "<p class='error'>Por favor, ingrese una consulta.</p>";
            return;
        }

        respuestaDiv.innerHTML = "<p class='cargando'>Procesando consulta...</p>";

        fetch("/api/consulta", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ consulta: consulta })
        })
        .then(response => response.json())
        .then(data => {
            respuestaDiv.innerHTML = `<p class='respuesta'>${data.respuesta}</p>`;
            ejemploDiv.innerHTML = `<h3>Ejemplo de respuesta:</h3><p class='ejemplo-texto'>${generarEjemplo(consulta)}</p>`;
        })
        .catch(error => {
            respuestaDiv.innerHTML = "<p class='error'>Hubo un error al procesar la consulta.</p>";
            console.error("Error:", error);
        });
    });

    function generarEjemplo(consulta) {
        const consultaLower = consulta.toLowerCase();
        if (consultaLower.includes("licencia")) {
            return "Ejemplo: Si la consulta es sobre una licencia, la respuesta podría ser: 'Según la Disposición N° XXXX, la renovación de la licencia se realiza cada 5 años...'";
        } else if (consultaLower.includes("normativa")) {
            return "Ejemplo: Para una consulta sobre normativas: 'El Decreto N° XXXX establece que...'";
        } else {
            return "Ejemplo: 'Según la normativa vigente, el proceso indicado es...'";
        }
    }
})

function generarEjemplo(consulta) {
    const consultaLower = consulta.toLowerCase();
    if (consultaLower.includes("licencia")) {
        return "Ejemplo: Si la consulta es sobre una licencia, la respuesta podría ser: 'Según la Disposición N° XXXX, la renovación de la licencia se realiza cada 5 años...'";
    } else if (consultaLower.includes("normativa")) {
        return "Ejemplo: Para una consulta sobre normativas: 'El Decreto N° XXXX establece que...'";
        } else {
            return "Ejemplo: 'Según la normativa vigente, el proceso indicado es...'";
            }
}