document.addEventListener("DOMContentLoaded", () => {
    // Lógica para Redes Sociais Dinâmicas no Formulário
    window.addSocialLinkRow = function(platform = "Instagram", url = "") {
        const container = document.getElementById("social-links-container");
        if (!container) return;
        const row = document.createElement("div");
        row.className = "social-link-row";
        row.style.cssText = "display: flex; gap: 10px; margin-bottom: 8px; align-items: center; width: 100%;";
        row.innerHTML = `
            <select name="social_plataforma[]" style="flex: 1; min-width: 120px; padding: 12px 14px;">
                <option value="Instagram" ${platform === 'Instagram' ? 'selected' : ''}>Instagram</option>
                <option value="Facebook" ${platform === 'Facebook' ? 'selected' : ''}>Facebook</option>
                <option value="X" ${platform === 'X' ? 'selected' : ''}>X (Twitter)</option>
                <option value="Behance" ${platform === 'Behance' ? 'selected' : ''}>Behance</option>
                <option value="Pinterest" ${platform === 'Pinterest' ? 'selected' : ''}>Pinterest</option>
                <option value="YouTube" ${platform === 'YouTube' ? 'selected' : ''}>YouTube</option>
                <option value="LinkedIn" ${platform === 'LinkedIn' ? 'selected' : ''}>LinkedIn</option>
                <option value="Outro" ${platform === 'Outro' ? 'selected' : ''}>Outro</option>
            </select>
            <input type="text" name="social_url[]" value="${url}" placeholder="https://..." style="flex: 2;">
            <button type="button" class="btn-remove-social" style="background: var(--danger); color: white; border: none; padding: 12px 16px; border-radius: 2px; cursor: pointer; font-weight: bold; line-height: 1;">✕</button>
        `;
        row.querySelector(".btn-remove-social").onclick = () => row.remove();
        container.appendChild(row);
    };

    const btnAddSocial = document.getElementById("btn-add-social");
    if (btnAddSocial) {
        btnAddSocial.addEventListener("click", () => {
            addSocialLinkRow();
        });
    }

    // Lógica para Experiências Dinâmicas no Currículo
    window.addExperienceRow = function(date = "", role = "", company = "", desc = "") {
        const container = document.getElementById("cv-experiencias-container");
        if (!container) return;
        const row = document.createElement("div");
        row.className = "cv-experience-row";
        row.style.cssText = "background: var(--bg-base); border: 1px solid var(--border-color); border-radius: 4px; padding: 20px; position: relative;";
        row.innerHTML = `
            <button type="button" class="btn-remove-experience" style="position: absolute; right: 10px; top: 10px; background: var(--danger); color: white; border: none; padding: 6px 12px; border-radius: 2px; cursor: pointer; font-size: 0.75rem; font-weight: bold; transition: var(--transition-smart);">Remover</button>
            <div class="form-grid">
                <div class="form-group col-4">
                    <label>Período</label>
                    <input type="text" name="exp_date[]" value="${date}" placeholder="Ex: 2023 - Presente">
                </div>
                <div class="form-group col-8">
                    <label>Empresa</label>
                    <input type="text" name="exp_company[]" value="${company}" placeholder="Ex: ENERCON">
                </div>
                <div class="form-group col-12">
                    <label>Cargo / Função</label>
                    <input type="text" name="exp_role[]" value="${role}" placeholder="Ex: Software Engineer">
                </div>
                <div class="form-group col-12">
                    <label>Descrição das Atividades</label>
                    <textarea name="exp_desc[]" style="min-height: 70px;">${desc}</textarea>
                </div>
            </div>
        `;
        row.querySelector(".btn-remove-experience").onclick = () => row.remove();
        container.appendChild(row);
    };

    const btnAddExperience = document.getElementById("btn-add-experience");
    if (btnAddExperience) {
        btnAddExperience.addEventListener("click", () => {
            addExperienceRow();
        });
    }

    // Associar eventos aos botões de remoção das experiências já existentes (geradas pelo Jinja)
    const existingRemoveBtns = document.querySelectorAll("#cv-experiencias-container .btn-remove-experience");
    existingRemoveBtns.forEach(btn => {
        btn.onclick = (e) => {
            e.target.closest(".cv-experience-row").remove();
        };
    });

    // ==========================================================================
    // GESTOR DINÂMICO DE COMPETÊNCIAS POR CATEGORIA (CLASSIFICAÇÃO 0 A 5)
    // ==========================================================================
    const skillsContainer = document.getElementById("cv-skills-builder-container");
    const btnAddSkillCategory = document.getElementById("btn-add-skill-category");

    window.addSkillCategory = function(categoryName = "", items = []) {
        if (!skillsContainer) return;
        const categoryId = "cat-" + Date.now() + "-" + Math.random().toString(36).substr(2, 5);
        const card = document.createElement("div");
        card.className = "cv-skill-category-block";
        card.dataset.id = categoryId;
        card.style.cssText = "background: var(--bg-base); border: 1px solid var(--border-color); border-radius: 4px; padding: 20px; position: relative; display: flex; flex-direction: column; gap: 15px; margin-bottom: 15px;";
        
        card.innerHTML = `
            <button type="button" class="btn-remove-category" style="position: absolute; right: 10px; top: 10px; background: var(--danger); color: white; border: none; padding: 6px 12px; border-radius: 2px; cursor: pointer; font-size: 0.75rem; font-weight: bold; transition: var(--transition-smart);">Remover Categoria</button>
            <div class="form-group col-12" style="width: calc(100% - 140px); margin-bottom: 10px;">
                <label style="font-size: 0.72rem; font-weight: 800; color: var(--text-secondary); text-transform: uppercase;">Nome da Categoria</label>
                <input type="text" class="cat-name-input" value="${categoryName}" placeholder="Ex: Automação, Web Dev & Ciência de Dados" required style="width: 100%;">
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px; width: 100%;">
                <label style="font-size: 0.72rem; font-weight: 800; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 4px; display: block;">Competências e Avaliação (0 a 5)</label>
                <div class="skills-rows-list" style="display: flex; flex-direction: column; gap: 8px; width: 100%;">
                    <!-- Skill rows go here -->
                </div>
            </div>
            
            <button type="button" class="btn-add-skill-row btn-secondary" style="align-self: flex-start; padding: 8px 16px; font-size: 0.8rem; display: flex; align-items: center; gap: 6px; font-weight: bold;">
                ➕ Adicionar Competência
            </button>
        `;
        
        const removeBtn = card.querySelector(".btn-remove-category");
        removeBtn.onclick = () => card.remove();
        
        const addRowBtn = card.querySelector(".btn-add-skill-row");
        const rowsList = card.querySelector(".skills-rows-list");
        
        addRowBtn.onclick = () => {
            addSkillRow(rowsList);
        };
        
        skillsContainer.appendChild(card);
        
        // Render initial skill items
        if (items && items.length > 0) {
            items.forEach(item => {
                addSkillRow(rowsList, item.name, item.desc, item.level);
            });
        } else {
            // Add at least one empty row by default
            addSkillRow(rowsList);
        }
    };

    window.addSkillRow = function(container, name = "", desc = "", level = 4.0) {
        const row = document.createElement("div");
        row.className = "skill-row-item";
        row.style.cssText = "display: flex; gap: 10px; align-items: center; width: 100%; flex-wrap: wrap; margin-bottom: 8px;";
        
        row.innerHTML = `
            <input type="text" class="skill-name-input" value="${name}" placeholder="Competência (Ex: Python & Flask)" style="flex: 2; min-width: 150px;" required>
            <input type="text" class="skill-desc-input" value="${desc}" placeholder="Descrição opcional (Ex: APIs e Web Apps)" style="flex: 3; min-width: 200px;">
            <div style="display: flex; align-items: center; gap: 8px; flex: 1.2; min-width: 140px;">
                <input type="range" class="skill-level-input" min="0" max="5" step="0.5" value="${level}" style="width: 100%; height: auto; padding: 0; cursor: pointer;" oninput="this.nextElementSibling.innerText = parseFloat(this.value).toFixed(1)">
                <span class="level-value-display" style="font-size: 0.85rem; font-weight: 800; width: 25px; text-align: right;">${parseFloat(level).toFixed(1)}</span>
            </div>
            <button type="button" class="btn-remove-skill-row" style="background: var(--danger); color: white; border: none; padding: 10px 14px; border-radius: 2px; cursor: pointer; font-weight: bold; height: 44px; display: flex; align-items: center; justify-content: center;">✕</button>
        `;
        
        row.querySelector(".btn-remove-skill-row").onclick = () => row.remove();
        container.appendChild(row);
    };

    // Load initial data
    const initialSkillsDataEl = document.getElementById("initial-skills-data");
    if (initialSkillsDataEl) {
        try {
            const initialSkills = JSON.parse(initialSkillsDataEl.textContent);
            if (initialSkills && initialSkills.length > 0) {
                initialSkills.forEach(cat => {
                    addSkillCategory(cat.category, cat.items);
                });
            } else {
                // Add a default category on startup if database is empty
                addSkillCategory();
            }
        } catch (e) {
            console.error("Erro ao carregar dados iniciais de competências:", e);
            addSkillCategory();
        }
    }

    if (btnAddSkillCategory) {
        btnAddSkillCategory.onclick = () => {
            addSkillCategory();
        };
    }

    // Form Cv submit serialization logic
    const formCv = document.getElementById("form-cv");
    if (formCv) {
        formCv.addEventListener("submit", (e) => {
            const skillsData = [];
            const categoryBlocks = document.querySelectorAll(".cv-skill-category-block");
            categoryBlocks.forEach(block => {
                const categoryName = block.querySelector(".cat-name-input").value.trim();
                const skillRows = block.querySelectorAll(".skill-row-item");
                const items = [];
                skillRows.forEach(row => {
                    const name = row.querySelector(".skill-name-input").value.trim();
                    const desc = row.querySelector(".skill-desc-input").value.trim();
                    const level = parseFloat(row.querySelector(".skill-level-input").value) || 0.0;
                    if (name) {
                        items.push({ name, desc, level });
                    }
                });
                if (categoryName || items.length > 0) {
                    skillsData.push({ category: categoryName, items });
                }
            });
            document.getElementById("skills_json").value = JSON.stringify(skillsData);
        });
    }

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
                
                // Carregar mapa e redes sociais
                document.getElementById("link_mapa").value = data.link_mapa || "";
                const socialContainer = document.getElementById("social-links-container");
                if (socialContainer) {
                    socialContainer.innerHTML = "";
                    if (data.social_links && data.social_links.length > 0) {
                        data.social_links.forEach(link => {
                            addSocialLinkRow(link.plataforma, link.url);
                        });
                    }
                }

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
                const pathRefEl = document.getElementById("view-path-ref");
                if (data.path_references) {
                    if (data.path_references.match(/\.(jpeg|jpg|gif|png|webp)$/i)) {
                        const isSimpleName = !data.path_references.includes("/") && !data.path_references.includes("\\");
                        const imageUrl = isSimpleName 
                            ? `/projetos/${data.id}/img/${data.path_references}` 
                            : `/local-image?path=${encodeURIComponent(data.path_references)}`;
                        pathRefEl.innerHTML = `<a href="${imageUrl}" target="_blank" style="color: var(--accent); text-decoration: underline; font-weight: bold;">${data.path_references} 🖼️</a>`;
                    } else {
                        pathRefEl.innerText = data.path_references;
                    }
                } else {
                    pathRefEl.innerText = "Não definido";
                }
                document.getElementById("view-path-models").innerText = data.path_models || "Não definido";
                document.getElementById("view-path-renders").innerText = data.path_renders || "Não definido";

                // Render Map and Social Links in Private View
                document.getElementById("view-link-mapa").innerText = data.link_mapa || "Não definido";
                const viewSocialLinks = document.getElementById("view-social-links");
                if (viewSocialLinks) {
                    viewSocialLinks.innerHTML = "";
                    if (data.social_links && data.social_links.length > 0) {
                        data.social_links.forEach(link => {
                            const badge = document.createElement("a");
                            badge.href = link.url;
                            badge.target = "_blank";
                            badge.className = "badge badge-category";
                            badge.style.cssText = "text-decoration: none; display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; margin-right: 4px; margin-bottom: 4px;";
                            badge.innerText = `${link.plataforma} 🔗`;
                            viewSocialLinks.appendChild(badge);
                        });
                    } else {
                        viewSocialLinks.innerHTML = "<span style='font-size: 0.78rem; color: var(--text-secondary);'>Nenhuma rede social associada.</span>";
                    }
                }

                // Images Previews
                updateImagePreview("view-img-capa", data.path_capa);
                updateImagePreview("view-img-processo", data.path_processo);
                updateImagePreview("view-img-galeria", data.path_galeria);

                // Show view panel, hide empty state
                emptyProjectView.style.display = "none";
                activeProjectView.style.display = "block";
                
                // Show view action buttons (like Publish/Generate and Preview)
                const actionPublishBtn = document.getElementById("btn-publish-action");
                if (actionPublishBtn) {
                    actionPublishBtn.style.display = "inline-flex";
                    actionPublishBtn.onclick = () => { publishProject(data.id); };
                }
                const actionPreviewBtn = document.getElementById("btn-preview-action");
                if (actionPreviewBtn) {
                    actionPreviewBtn.href = `/projetos/${data.id}/index.html`;
                    actionPreviewBtn.style.display = "inline-flex";
                }
                
                // Load local thumbnail gallery for this project
                loadLocalImages(data.id);
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
            
            // Limpar redes sociais e link do mapa
            const socialContainer = document.getElementById("social-links-container");
            if (socialContainer) socialContainer.innerHTML = "";
            document.getElementById("link_mapa").value = "";
            
            // Mostrar sugestão do guia
            showToast("Novo projeto iniciado! Siga a metodologia no separador '💡 Guia de Orientação'.", "info");
            
            // Hide local image gallery container
            const galleryContainer = document.getElementById("local-img-gallery-container");
            if (galleryContainer) galleryContainer.style.display = "none";
            
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

    // Helper to fetch and display thumbnails from the project's local img/ directory
    function loadLocalImages(projectId) {
        const galleryContainer = document.getElementById("local-img-gallery-container");
        const galleryGrid = document.getElementById("local-img-gallery-grid");
        if (!projectId) {
            galleryContainer.style.display = "none";
            return;
        }
        
        fetch(`/project/images/${projectId}`)
            .then(res => res.json())
            .then(files => {
                if (!files || files.length === 0) {
                    galleryContainer.style.display = "none";
                    return;
                }
                
                galleryContainer.style.display = "block";
                galleryGrid.innerHTML = "";
                
                files.forEach(file => {
                    const card = document.createElement("div");
                    card.style.cssText = "display: flex; flex-direction: column; align-items: center; gap: 6px; background: white; border: 1px solid var(--border-color); border-radius: 2px; padding: 8px; width: 140px; position: relative; box-shadow: 0 2px 6px rgba(0,0,0,0.03);";
                    
                    card.innerHTML = `
                        <img src="${file.url}" style="width: 120px; height: 80px; object-fit: cover; border-radius: 2px; border: 1px solid var(--border-color);" alt="Thumbnail" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500';">
                        <span style="font-size: 0.65rem; color: var(--text-primary); text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; width: 120px;" title="${file.name}">${file.name}</span>
                        <span style="font-size: 0.55rem; color: var(--text-secondary); margin-top: -4px;">${file.size_mb} MB</span>
                        <div style="display: flex; gap: 4px; margin-top: 4px; width: 100%;">
                            <button type="button" class="btn-assign-capa" style="flex: 1; font-size: 0.52rem; padding: 4px 0; background: var(--accent); color: white; border: none; border-radius: 2px; cursor: pointer; font-weight: bold;" title="Definir como Capa">Capa</button>
                            <button type="button" class="btn-assign-proc" style="flex: 1; font-size: 0.52rem; padding: 4px 0; background: var(--text-secondary); color: white; border: none; border-radius: 2px; cursor: pointer; font-weight: bold;" title="Definir como Processo">Proc.</button>
                            <button type="button" class="btn-assign-gal" style="flex: 1; font-size: 0.52rem; padding: 4px 0; background: var(--accent-mustard); color: var(--text-primary); border: none; border-radius: 2px; cursor: pointer; font-weight: bold;" title="Definir como Galeria">Gal.</button>
                            <button type="button" class="btn-assign-ref" style="flex: 1; font-size: 0.52rem; padding: 4px 0; background: #6B7280; color: white; border: none; border-radius: 2px; cursor: pointer; font-weight: bold;" title="Definir como Referência">Ref.</button>
                        </div>
                    `;
                    
                    // Bind button clicks to assign paths using simple filenames
                    card.querySelector(".btn-assign-capa").onclick = () => {
                        document.getElementById("path_capa").value = file.name;
                        showToast(`Definido "${file.name}" como Imagem de Capa!`, "success");
                    };
                    card.querySelector(".btn-assign-proc").onclick = () => {
                        document.getElementById("path_processo").value = file.name;
                        showToast(`Definido "${file.name}" como Imagem de Processo!`, "success");
                    };
                    card.querySelector(".btn-assign-gal").onclick = () => {
                        document.getElementById("path_galeria").value = file.name;
                        showToast(`Definido "${file.name}" como Imagem de Galeria!`, "success");
                    };
                    card.querySelector(".btn-assign-ref").onclick = () => {
                        document.getElementById("path_references").value = file.name;
                        showToast(`Definido "${file.name}" como Referência!`, "success");
                    };
                    
                    galleryGrid.appendChild(card);
                });
            })
            .catch(err => {
                console.error("Erro ao carregar galeria de miniaturas locais:", err);
                galleryContainer.style.display = "none";
            });
    }

    // 8. Sidebar Search Filter
    const searchInput = document.getElementById("sidebar-search");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const query = searchInput.value.toLowerCase().trim();
            const items = document.querySelectorAll(".project-item");
            
            items.forEach(item => {
                const id = item.dataset.id.toLowerCase();
                const tags = (item.dataset.tags || "").toLowerCase();
                const title = item.querySelector(".project-item-title").textContent.toLowerCase();
                const status = item.querySelector(".project-item-status").textContent.toLowerCase();
                const category = item.querySelector(".project-item-meta span").textContent.toLowerCase();
                
                // Matches if search query is found in ID, tags, title, status, or category
                const matches = id.includes(query) || 
                                tags.includes(query) || 
                                title.includes(query) || 
                                status.includes(query) || 
                                category.includes(query);
                                
                if (matches) {
                    item.style.display = "flex";
                } else {
                    item.style.display = "none";
                }
            });
        });
    }
});
