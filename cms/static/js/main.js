document.addEventListener("DOMContentLoaded", () => {
    // 1. Tab Switching Logic
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const activeProjectView = document.getElementById("active-project-view");
    const emptyProjectView = document.getElementById("empty-project-view");

    window.switchTab = function(tabId) {
        tabButtons.forEach(btn => {
            if (btn.dataset.tab === tabId) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });
        tabContents.forEach(content => {
            if (content.id === tabId) {
                content.classList.add("active");
            } else {
                content.classList.remove("active");
            }
        });
    };

    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            switchTab(button.dataset.tab);
        });
    });

    // 2. Dynamic Form switching by Category
    const categorySelect = document.getElementById("categoria");
    const dynamicSections = {
        "Impressão 3D": document.getElementById("sec-impressao3d"),
        "Render": document.getElementById("sec-render"),
        "Venda": document.getElementById("sec-venda"),
        "Layout": document.getElementById("sec-layout")
    };

    function updateCategoryFields() {
        const selectedCategory = categorySelect.value;
        
        Object.keys(dynamicSections).forEach(cat => {
            const section = dynamicSections[cat];
            if (cat === selectedCategory) {
                section.style.display = "block";
                toggleRequired(section, true);
            } else {
                section.style.display = "none";
                toggleRequired(section, false);
            }
        });
    }

    function toggleRequired(section, enable) {
        // Elements with data-req should be marked as required when their section is active
        const reqFields = section.querySelectorAll("[data-req]");
        reqFields.forEach(field => {
            if (enable) {
                field.setAttribute("required", "");
            } else {
                field.removeAttribute("required");
            }
        });
    }

    categorySelect.addEventListener("change", updateCategoryFields);
    updateCategoryFields(); // Run on startup

    // 3. Profit Margin Calculation (Sales category)
    const vndCusto = document.getElementById("vnd_custo");
    const vndPreco = document.getElementById("vnd_preco");
    const outMargem = document.getElementById("out_margem");

    function calculateMargin() {
        const custo = parseFloat(vndCusto.value) || 0;
        const preco = parseFloat(vndPreco.value) || 0;
        
        if (preco > 0) {
            const marginAbs = (preco - custo).toFixed(2);
            const marginPct = (((preco - custo) / preco) * 100).toFixed(2);
            outMargem.innerHTML = `Margem de Lucro: <strong>€${marginAbs} (${marginPct}%)</strong>`;
            
            if (preco - custo >= 0) {
                outMargem.style.color = "var(--success)";
            } else {
                outMargem.style.color = "var(--danger)";
            }
        } else {
            outMargem.innerHTML = "Margem de Lucro: <strong>€0.00 (0.00%)</strong>";
            outMargem.style.color = "var(--text-secondary)";
        }
    }

    if (vndCusto && vndPreco) {
        vndCusto.addEventListener("input", calculateMargin);
        vndPreco.addEventListener("input", calculateMargin);
    }

    // 4. AJAX Load Project for Editing and Viewing
    const projectItems = document.querySelectorAll(".project-item");
    
    projectItems.forEach(item => {
        item.addEventListener("click", () => {
            // Remove active class from all and add to clicked
            projectItems.forEach(i => i.classList.remove("active"));
            item.classList.add("active");
            
            const projectId = item.dataset.id;
            loadProjectDetails(projectId);
        });
    });

    function loadProjectDetails(projectId) {
        fetch(`/project/get/${projectId}`)
            .then(res => {
                if (!res.ok) throw new Error("Erro ao carregar detalhes do projeto");
                return res.json();
            })
            .then(data => {
                // Populate Form Fields
                document.getElementById("form-id").value = data.id || "";
                document.getElementById("form-id-display").innerText = `Editando: ${data.id}`;
                document.getElementById("form-id-display").style.display = "inline-block";
                
                document.getElementById("titulo").value = data.titulo || "";
                document.getElementById("description").value = data.description || "";
                document.getElementById("tags").value = data.tags || "";
                document.getElementById("categoria").value = data.categoria || "Impressão 3D";
                document.getElementById("status").value = data.status || "Em andamento";
                document.getElementById("visibilidade").checked = data.visibilidade === "Público";
                document.getElementById("horas").value = data.horas || 0;
                
                document.getElementById("path_references").value = data.path_references || "";
                document.getElementById("path_models").value = data.path_models || "";
                document.getElementById("path_renders").value = data.path_renders || "";
                document.getElementById("path_capa").value = data.path_capa || "";
                document.getElementById("path_processo").value = data.path_processo || "";
                document.getElementById("path_galeria").value = data.path_galeria || "";

                // Populate dynamic fields depending on category
                if (data.categoria === "Impressão 3D") {
                    document.getElementById("maq_maquina").value = data.maq_maquina || "";
                    document.getElementById("maq_material").value = data.maq_material || "";
                    document.getElementById("maq_peso").value = data.maq_peso || 0;
                    document.getElementById("maq_tempo").value = data.maq_tempo || 0;
                    document.getElementById("maq_custo").value = data.maq_custo || 0;
                } else if (data.categoria === "Render") {
                    document.getElementById("rnd_softwares").value = data.rnd_softwares || "";
                    document.getElementById("rnd_vistas").value = data.rnd_vistas || 0;
                    document.getElementById("rnd_hdri").value = data.rnd_hdri || "";
                } else if (data.categoria === "Venda") {
                    document.getElementById("vnd_plataforma").value = data.vnd_plataforma || "";
                    document.getElementById("vnd_custo").value = data.vnd_custo || 0;
                    document.getElementById("vnd_preco").value = data.vnd_preco || 0;
                    calculateMargin();
                } else if (data.categoria === "Layout") {
                    document.getElementById("lay_formato").value = data.lay_formato || "";
                    document.getElementById("lay_grelha").value = data.lay_grelha || "";
                    document.getElementById("lay_tipografias").value = data.lay_tipografias || "";
                }

                updateCategoryFields();

                // Populate Internal View Tab (Private details)
                document.getElementById("view-id").innerText = data.id;
                document.getElementById("view-title").innerText = data.titulo || "Sem Título";
                document.getElementById("view-briefing").innerText = data.description || "Sem descrição disponível.";
                document.getElementById("view-tag-badge").innerText = data.tags || "#sem-tags";
                document.getElementById("view-cat-badge").innerText = data.categoria;
                document.getElementById("view-status-badge").innerText = data.status;
                
                // Status badge design
                const statusBadge = document.getElementById("view-status-badge");
                statusBadge.className = "badge";
                if (data.status === "Em andamento") {
                    statusBadge.classList.add("status-em-andamento");
                } else {
                    statusBadge.classList.add("status-finalizado");
                }

                document.getElementById("view-visibilidade").innerText = data.visibilidade;
                document.getElementById("view-hours").innerText = `${data.horas || 0} h`;

                // Render dynamic specs in Private View
                const viewSpecsContainer = document.getElementById("view-specs-content");
                let specsHtml = "";
                if (data.categoria === "Impressão 3D") {
                    specsHtml = `
                    <div class="view-spec-item">
                        <span class="view-spec-label">Impressora</span>
                        <span class="view-spec-val">${data.maq_maquina || 'N/A'}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Material</span>
                        <span class="view-spec-val">${data.maq_material || 'N/A'}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Peso</span>
                        <span class="view-spec-val">${data.maq_peso || 0} g</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Tempo</span>
                        <span class="view-spec-val">${data.maq_tempo || 0} h</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Custo</span>
                        <span class="view-spec-val">€${(data.maq_custo || 0).toFixed(2)}</span>
                    </div>`;
                } else if (data.categoria === "Render") {
                    specsHtml = `
                    <div class="view-spec-item">
                        <span class="view-spec-label">Softwares</span>
                        <span class="view-spec-val">${data.rnd_softwares || 'N/A'}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Vistas</span>
                        <span class="view-spec-val">${data.rnd_vistas || 0}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Setup/HDRI</span>
                        <span class="view-spec-val">${data.rnd_hdri || 'N/A'}</span>
                    </div>`;
                } else if (data.categoria === "Venda") {
                    specsHtml = `
                    <div class="view-spec-item">
                        <span class="view-spec-label">Plataforma</span>
                        <span class="view-spec-val">${data.vnd_plataforma || 'N/A'}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Custo Total</span>
                        <span class="view-spec-val">€${(data.vnd_custo || 0).toFixed(2)}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Preço de Venda</span>
                        <span class="view-spec-val">€${(data.vnd_preco || 0).toFixed(2)}</span>
                    </div>
                    <div class="view-spec-item col-6">
                        <span class="view-spec-label">Margem de Lucro</span>
                        <span class="view-spec-val" style="color: ${data.vnd_margem_abs >= 0 ? 'var(--success)' : 'var(--danger)'}">
                            €${(data.vnd_margem_abs || 0).toFixed(2)} (${data.vnd_margem_pct || 0}%)
                        </span>
                    </div>`;
                } else if (data.categoria === "Layout") {
                    specsHtml = `
                    <div class="view-spec-item">
                        <span class="view-spec-label">Formato</span>
                        <span class="view-spec-val">${data.lay_formato || 'N/A'}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Grelha</span>
                        <span class="view-spec-val">${data.lay_grelha || 'N/A'}</span>
                    </div>
                    <div class="view-spec-item">
                        <span class="view-spec-label">Tipografias</span>
                        <span class="view-spec-val">${data.lay_tipografias || 'N/A'}</span>
                    </div>`;
                }
                viewSpecsContainer.innerHTML = specsHtml;

                // Render Paths in Private View
                document.getElementById("view-path-ref").innerText = data.path_references || "Não definido";
                document.getElementById("view-path-models").innerText = data.path_models || "Não definido";
                document.getElementById("view-path-renders").innerText = data.path_renders || "Não definido";

                // Images Previews
                updateImagePreview("view-img-capa", data.path_capa);
                updateImagePreview("view-img-processo", data.path_processo);
                updateImagePreview("view-img-galeria", data.path_galeria);

                // Show view panel, hide empty state
                emptyProjectView.style.display = "none";
                activeProjectView.style.display = "block";
                
                // Show view action buttons (like Publish/Generate)
                const actionPublishBtn = document.getElementById("btn-publish-action");
                if (actionPublishBtn) {
                    actionPublishBtn.style.display = "inline-flex";
                    actionPublishBtn.onclick = () => { publishProject(data.id); };
                }
            })
            .catch(err => {
                showToast("Erro ao buscar detalhes do projeto: " + err.message, "danger");
            });
    }

    function updateImagePreview(elementId, path) {
        const previewContainer = document.getElementById(elementId);
        if (path) {
            // In a real local server, absolute windows paths can't be rendered directly due to security,
            // but we can load them if Flask serves them or if we show a placeholder indicating it's registered.
            // Let's create an img element or display the path. To make it beautiful, we try to load the local file.
            // In our Flask server, we will register an endpoint `/local-image?path=...` to display any image on disk safely!
            previewContainer.innerHTML = `<img src="/local-image?path=${encodeURIComponent(path)}" class="image-preview-element" alt="Preview" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500';">`;
        } else {
            previewContainer.innerHTML = `<div class="image-preview-placeholder">Ficheiro não selecionado</div>`;
        }
    }

    // 5. Reset Form for New Project Creation
    const btnNewProject = document.getElementById("btn-new-project");
    if (btnNewProject) {
        btnNewProject.addEventListener("click", () => {
            projectItems.forEach(i => i.classList.remove("active"));
            
            // Reset main input fields
            document.getElementById("form-id").value = "";
            document.getElementById("form-id-display").innerText = "Novo Projeto";
            document.getElementById("form-id-display").style.display = "none";
            document.getElementById("form-project").reset();
            
            // Reset Margin Output
            outMargem.innerHTML = "Margem de Lucro: <strong>€0.00 (0.00%)</strong>";
            outMargem.style.color = "var(--text-secondary)";
            
            // Select first category and display fields
            categorySelect.value = "Impressão 3D";
            updateCategoryFields();

            // Set tab to edit form
            switchTab("edit-tab");
        });
    }

    // 6. Project HTML Generation and Git Publish Action
    function publishProject(projectId) {
        showToast("Gerando páginas web e atualizando Portfólio...", "info");
        
        fetch(`/project/publish/${projectId}`, { method: "POST" })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast("Sucesso! Páginas geradas e Git sync iniciado no background.", "success");
                } else {
                    showToast("Erro: " + data.message, "danger");
                }
            })
            .catch(err => {
                showToast("Erro de rede ao publicar projeto.", "danger");
            });
    }

    // 7. Dynamic Toast Notifications
    window.showToast = function(message, type = "info") {
        // Remove existing toasts
        const existing = document.querySelectorAll(".toast");
        existing.forEach(t => t.remove());

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        
        let icon = "⚡";
        if (type === "success") icon = "✅";
        if (type === "danger") icon = "❌";
        if (type === "info") icon = "ℹ️";
        
        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        document.body.appendChild(toast);

        // Auto remove toast
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(20px)";
            toast.style.transition = "all 0.5s ease";
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    };
});
