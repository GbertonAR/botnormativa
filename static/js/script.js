document.getElementById("consultaForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Evitar recargar la página

    let numeroNorma = document.getElementById("numero_norma").value;
    let pregunta = document.getElementById("pregunta").value;

    if (!numeroNorma || !pregunta) return;

    // Crear la tarjeta con la consulta
    let card = document.createElement("div");
    card.classList.add("card");
    card.innerHTML = `
        <strong>Norma ${numeroNorma}</strong>
        <p>${pregunta}</p>
        <div class="card-content">
            <p><strong>Respuesta:</strong> Procesando...</p>
        </div>
    `;

    // Agregar funcionalidad para expandir la tarjeta
    card.addEventListener("click", function () {
        let content = this.querySelector(".card-content");
        content.style.display = content.style.display === "none" ? "block" : "none";
    });

    // Agregar la tarjeta al resultado
    document.getElementById("resultado").appendChild(card);

    // Simular una respuesta después de 2 segundos
    setTimeout(() => {
        card.querySelector(".card-content").innerHTML = `<p><strong>Respuesta:</strong> Ejemplo de respuesta a la consulta sobre la Norma ${numeroNorma}.</p>`;
    }, 2000);

    // Limpiar campos
    document.getElementById("numero_norma").value = "";
    document.getElementById("pregunta").value = "";
});
