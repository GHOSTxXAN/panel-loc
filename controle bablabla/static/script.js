document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector("#campo-busca");
    const resultadoContainer = document.querySelector("#resultado");

    // Função para renderizar os resultados
    const renderizarResultados = (resultados) => {
        if (resultados.length === 0) {
            resultadoContainer.innerHTML = "<p style='text-align: center;'>Nenhuma unidade encontrada.</p>";
            return;
        }

        resultadoContainer.innerHTML = resultados.map(r => `
            <div class="resultado-container">
                <div class="resultado-item"><strong>Proprietário:</strong> <span>${r.proprietario}</span></div>
                <div class="resultado-item"><strong>Unidade:</strong> <span>${r.unidade} | ${r.apartamento}</span></div>
                <div class="resultado-item"><strong>Status:</strong> ${
                    r.locado ? `<span class="status-ok">✅ LOCADO</span>` : `<span class="status-nao">❌ NÃO LOCADO</span>`
                }</div>
                ${r.locado ? `
                    <div class="resultado-item"><strong>Locatário:</strong> <span>${r.locatario}</span></div>
                    <div class="resultado-item"><strong>Período:</strong> <span class="data-periodo">${r.inicio_formatado} a ${r.fim_formatado}</span></div>
                ` : ""}
            </div>
            <hr style="margin: 20px auto; border: 0; border-top: 1px dashed #ccc; max-width: 600px;">
        `).join("");
    };

    input.addEventListener("input", async () => {
        const termo = input.value.trim();

        if (termo.length === 0) {
            // Quando a busca está vazia, recarrega a página para mostrar os resultados iniciais do Flask
            // Ou, se preferir, você pode buscar todos os locados novamente via AJAX
            window.location.reload(); 
            return;
        }

        const response = await fetch("/buscar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ termo })
        });

        const resultados = await response.json();
        renderizarResultados(resultados);
    });
});