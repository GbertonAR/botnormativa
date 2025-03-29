document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("consultaForm");
    const consultaInput = document.getElementById("consulta");
    const chatBox = document.getElementById("chat-box");

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const consulta = consultaInput.value.trim();

        if (consulta === "") {
            return;
        }

        // Mostrar mensaje del usuario
        addMessage(consulta, 'user');

        // Mostrar mensaje de "procesando"
        addMessage('Procesando consulta...', 'bot');

        // Limpiar el campo de entrada
        consultaInput.value = '';

        // Realizar la consulta a la API
        fetch("/api/consulta", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ consulta: consulta })
        })
        .then(response => response.json())
        .then(data => {
            // Procesar la respuesta de la API
            if (data && data.tipo && data.fecha && data.numero && data.contenido) {
                // Mostrar la respuesta en el chat
                const respuesta = `
                    <h3>Respuesta:</h3>
                    <p><strong>Tipo:</strong> ${data.tipo}</p>
                    <p><strong>Fecha:</strong> ${data.fecha}</p>
                    <p><strong>Número:</strong> ${data.numero}</p>
                    <p><strong>Contenido:</strong> ${data.contenido}</p>
                `;
                addMessage(respuesta, 'bot');
                addQuickActions();  // Añadir botones de acción rápida
            } else {
                addMessage('No se encontró información relevante.', 'bot');
            }
        })
        .catch(error => {
            console.error("Error en la solicitud:", error);
            addMessage('Ocurrió un error. Intente nuevamente.', 'bot');
        });
    });

    // Función para agregar mensaje al chat
    function addMessage(message, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", `${sender}-message`);
        messageDiv.innerHTML = message;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;  // Desplazar hacia abajo al último mensaje
    }

    // Función para agregar botones de acción rápida
    function addQuickActions() {
        const actionsDiv = document.createElement("div");
        actionsDiv.classList.add("quick-actions");

        const reformulateButton = document.createElement("button");
        reformulateButton.textContent = "Reformular pregunta";
        reformulateButton.addEventListener("click", function () {
            consultaInput.focus();
        });

        const moreDetailsButton = document.createElement("button");
        moreDetailsButton.textContent = "Mostrar más detalles";
        moreDetailsButton.addEventListener("click", function () {
            alert("Mostrar más detalles de la normativa.");
        });

        actionsDiv.appendChild(reformulateButton);
        actionsDiv.appendChild(moreDetailsButton);

        chatBox.appendChild(actionsDiv);
    }
});
