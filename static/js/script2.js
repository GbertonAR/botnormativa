fetch('/normativas')
    .then(response => response.json())
    .then(normativas => {
        const normativasList = document.getElementById('normativas-list');
        normativas.forEach(normativa => {
            const li = document.createElement('li');
            li.textContent = normativa.titulo;
            li.addEventListener('click', () => {
                fetch(`/articulos/${normativa.id}`)
                    .then(response => response.json())
                    .then(articulos => {
                        const articulosContainer = document.getElementById('articulos-container');
                        articulosContainer.innerHTML = '';
                        articulos.forEach(articulo => {
                            const p = document.createElement('p');
                            p.textContent = articulo.contenido;
                            articulosContainer.appendChild(p);
                        });
                    });
            });
            normativasList.appendChild(li);
        });
    });