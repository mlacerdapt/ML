import os
import json
import shutil
import subprocess
import threading
import mimetypes
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-ml-gestor'

# Absolute directories relative to app.py
CMS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CMS_DIR)
DB_DIR = os.path.join(ROOT_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'portfolio_data.json')
PROJETOS_DIR = os.path.join(ROOT_DIR, 'projetos')

# Standard CV details to seed the database
DEFAULT_CV = {
    'nome': 'Marcelo Lacerda',
    'titulo': 'Engenheiro de Software & Designer 3D',
    'email': 'marcelo.lacerda@exemplo.com',
    'github': 'github.com/mlacerdapt',
    'localizacao': 'Porto, Portugal',
    'avatar': 'https://api.dicebear.com/7.x/identicon/svg?seed=mlacerda',
    'resumo': 'Engenheiro de Software Sénior com mais de 8 anos de experiência no desenvolvimento de aplicações eficientes e automatizações industriais. Paralelamente, atuo no design de réplicas físicas e virtuais de monumentos, combinando modelação tridimensional precisa, fabrico digital via impressão 3D e renderização fotorrealista.',
    'skills': 'Python & Flask, SQL & SQLite, Tailwind CSS, Impressão 3D, Slicing (Cura/PrusaSlicer), Modelação (Blender), Renderização (Cycles/V-Ray), Layout & Grelhas',
    'experiencias': [
        {
            'date': '2023 - Presente',
            'role': 'Engenheiro de Software Sénior',
            'company': 'ENERCON',
            'desc': 'Desenvolvimento de sistemas internos, integrações de banco de dados e automações para logística de distribuição e controlo de materiais tridimensionais.'
        },
        {
            'date': '2020 - 2023',
            'role': 'Especialista em Modelação e Impressão 3D',
            'company': 'ML Smart Designs',
            'desc': 'Criação de maquetes físicas de alta precisão baseadas em monumentos históricos e modelos arquitetónicos neorromânicos, utilizando filamentos especiais e fatiamento avançado.'
        }
    ],
    'educacao': [
        {
            'date': '2014 - 2019',
            'role': 'Licenciatura em Engenharia de Computadores',
            'company': 'Universidade do Porto',
            'desc': 'Foco em desenvolvimento de software corporativo, banco de dados relacional e arquitetura de sistemas distribuídos.'
        }
    ]
}

# Ensure directory structure
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PROJETOS_DIR, exist_ok=True)

# Helper to load central JSON db
def load_db():
    if not os.path.exists(DB_PATH):
        initial_db = {'curriculo': DEFAULT_CV}
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, indent=4, ensure_ascii=False)
        return initial_db
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
            if 'curriculo' not in db:
                db['curriculo'] = DEFAULT_CV
                with open(DB_PATH, 'w', encoding='utf-8') as sf:
                    json.dump(db, sf, indent=4, ensure_ascii=False)
            return db
    except Exception as e:
        print(f"Error loading database: {e}")
        return {'curriculo': DEFAULT_CV}

# Helper to save central JSON db
def save_db(data):
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving database: {e}")

# Dynamic ID Generator (Format: ML-[CAT]-[YY][SEQ])
def get_next_id(category):
    db = load_db()
    category_map = {
        "Impressão 3D": "3DP",
        "Render": "RND",
        "Venda": "VND",
        "Layout": "LYT"
    }
    cat_code = category_map.get(category, "PRJ")
    year_suffix = datetime.now().strftime("%y")  # e.g., "26"
    prefix = f"ML-{cat_code}-{year_suffix}"
    
    seq = 1
    for pid in db.keys():
        if pid == 'curriculo': continue
        if pid.startswith(prefix):
            try:
                num_part = pid.split("-")[-1]  # e.g., "26001"
                seq_str = num_part[2:]         # e.g., "001"
                seq_part = int(seq_str)
                if seq_part >= seq:
                    seq = seq_part + 1
            except (ValueError, IndexError):
                pass
                
    return f"{prefix}{seq:03d}"

# Git worker thread target
def git_sync_worker(project_id):
    print(f"[{datetime.now()}] Thread: Starting Git synchronization for {project_id}...")
    try:
        # 1. Pull changes
        p_pull = subprocess.run(['git', 'pull', 'origin', 'main'], cwd=ROOT_DIR, capture_output=True, text=True)
        if p_pull.returncode != 0:
            print(f"Git pull warnings/errors: {p_pull.stderr}")
            
        # 2. Add files
        subprocess.run(['git', 'add', '.'], cwd=ROOT_DIR, check=True)
        
        # 3. Commit
        commit_msg = f"Update ML portfolio database / curriculum: {project_id}"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=ROOT_DIR, check=True)
        
        # 4. Push
        p_push = subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT_DIR, capture_output=True, text=True)
        if p_push.returncode == 0:
            print(f"[{datetime.now()}] Thread: Git sync successful!")
        else:
            print(f"[{datetime.now()}] Thread: Git push failed: {p_push.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] Thread: Git command failed. Error details: {e}")
    except Exception as e:
        print(f"[{datetime.now()}] Thread: General Git syncing exception: {e}")

# Triggers git sync in background
def start_git_sync(project_id):
    thread = threading.Thread(target=git_sync_worker, args=(project_id,))
    thread.daemon = True
    thread.start()

# Reconstructs CV HTML layout from JSON data
def compile_cv_html(cv):
    avatar_src = cv.get('avatar') or "https://api.dicebear.com/7.x/identicon/svg?seed=mlacerda"
    nome = cv.get('nome') or "Marcelo Lacerda"
    titulo = cv.get('titulo') or "Engenheiro de Software & Designer 3D"
    
    contacts_html = ""
    if cv.get('email'):
        contacts_html += f'<li class="contact-item">📧 {cv.get("email")}</li>'
    if cv.get('github'):
        contacts_html += f'<li class="contact-item">🔗 {cv.get("github")}</li>'
    if cv.get('localizacao'):
        contacts_html += f'<li class="contact-item">📍 {cv.get("localizacao")}</li>'
        
    skills_html = ""
    skills_list = [s.strip() for s in cv.get('skills', '').split(',') if s.strip()]
    for skill in skills_list:
        skills_html += f'<span class="skill-tag">{skill}</span>'
        
    exp_html = ""
    for exp in cv.get('experiencias', []):
        if not exp.get('role') and not exp.get('company'): continue
        exp_html += f"""
                            <div class="timeline-item">
                                <div class="timeline-dot"></div>
                                <div class="timeline-date">{exp.get('date', '')}</div>
                                <div class="timeline-role">{exp.get('role', '')}</div>
                                <div class="timeline-company">{exp.get('company', '')}</div>
                                <p class="timeline-desc">{exp.get('desc', '')}</p>
                            </div>"""
        
    edu_html = ""
    for edu in cv.get('educacao', []):
        if not edu.get('role') and not edu.get('company'): continue
        edu_html += f"""
                            <div class="timeline-item">
                                <div class="timeline-dot"></div>
                                <div class="timeline-date">{edu.get('date', '')}</div>
                                <div class="timeline-role">{edu.get('role', '')}</div>
                                <div class="timeline-company">{edu.get('company', '')}</div>
                                <p class="timeline-desc">{edu.get('desc', '')}</p>
                            </div>"""
        
    cv_html = f"""<div class="cv-grid">
                <!-- Sidebar: Informações Pessoais e Competências -->
                <aside class="cv-sidebar">
                    <div class="flex flex-col items-center">
                        <img class="profile-avatar" src="{avatar_src}" alt="{nome}">
                        <h2 class="profile-name">{nome}</h2>
                        <div class="profile-title">{titulo}</div>
                    </div>
                    
                    <div>
                        <h3 class="cv-section-title">Contacto</h3>
                        <div class="smart-divider"></div>
                        <ul class="contact-list">
                            {contacts_html}
                        </ul>
                    </div>
                    
                    <div>
                        <h3 class="cv-section-title">Competências</h3>
                        <div class="smart-divider"></div>
                        <div class="skills-container">
                            {skills_html}
                        </div>
                    </div>
                </aside>
                
                <!-- Conteúdo Principal: Experiência e Educação -->
                <main class="cv-main">
                    <div>
                        <h3 class="cv-section-title">Resumo Profissional</h3>
                        <div class="smart-divider"></div>
                        <p class="text-charcoal text-sm leading-relaxed text-justify mb-8">
                            {cv.get('resumo', '')}
                        </p>
                    </div>
                    
                    <div>
                        <h3 class="cv-section-title">Experiência Profissional</h3>
                        <div class="smart-divider"></div>
                        <div class="timeline">
                            {exp_html}
                        </div>
                    </div>
                    
                    <div class="mt-8">
                        <h3 class="cv-section-title">Formação</h3>
                        <div class="smart-divider"></div>
                        <div class="timeline">
                            {edu_html}
                        </div>
                    </div>
                </main>
            </div>"""
    return cv_html

# Rebuilds root index.html grid mapping all Public projects and CV
def rebuild_master_hub():
    db = load_db()
    public_projects = []
    
    for pid, pdata in db.items():
        if pid == 'curriculo': continue
        if pdata.get('visibilidade') == 'Público':
            public_projects.append((pid, pdata))
            
    # Sort projects descending: newer first
    public_projects.sort(key=lambda x: x[0], reverse=True)
    
    cards_html = ""
    for pid, pdata in public_projects:
        proj_dir = os.path.join(PROJETOS_DIR, pid)
        img_dir = os.path.join(proj_dir, 'img')
        capa_rel_path = ""
        
        if os.path.exists(img_dir):
            for file in os.listdir(img_dir):
                if file.startswith('capa'):
                    capa_rel_path = f"projetos/{pid}/img/{file}"
                    break
                    
        badge_html = ""
        if pdata.get('status') == 'Em andamento':
            badge_html = '<span class="card-badge">Em Andamento</span>'
            
        tags_html = ""
        tags = pdata.get('tags', '')
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            for tag in tag_list:
                if not tag.startswith('#'):
                    tag = f"#{tag}"
                tags_html += f'<span class="tag">{tag}</span>'
                
        cards_html += f"""
        <div class="portfolio-card" data-category="{pdata.get('categoria')}">
            <div class="card-image-container">
                {badge_html}
                <img src="{capa_rel_path if capa_rel_path else 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500'}" alt="{pdata.get('titulo')}" loading="lazy">
            </div>
            <div class="card-content">
                <span class="card-category">{pdata.get('categoria')}</span>
                <h3 class="card-title">{pdata.get('titulo')}</h3>
                <p class="card-description">{pdata.get('description', '')[:120]}...</p>
                <div class="card-tags">{tags_html}</div>
                <a href="projetos/{pid}/index.html" class="card-button">Ver Projeto</a>
            </div>
        </div>
        """
        
    cv_data = db.get('curriculo', DEFAULT_CV)
    cv_html = compile_cv_html(cv_data)
    
    root_index_path = os.path.join(ROOT_DIR, 'index.html')
    
    # Try updating root index using start/end markers
    if os.path.exists(root_index_path):
        try:
            with open(root_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            start_marker = "<!-- PORTFOLIO_GRID_START -->"
            end_marker = "<!-- PORTFOLIO_GRID_END -->"
            
            cv_start_marker = "<!-- CURRICULO_START -->"
            cv_end_marker = "<!-- CURRICULO_END -->"
            
            patched = False
            
            # Patch grid
            if start_marker in content and end_marker in content:
                parts = content.split(start_marker)
                rest = parts[1].split(end_marker)
                content = parts[0] + start_marker + "\n" + cards_html + "\n" + end_marker + rest[1]
                patched = True
                
            # Patch CV
            if cv_start_marker in content and cv_end_marker in content:
                parts = content.split(cv_start_marker)
                rest = parts[1].split(cv_end_marker)
                content = parts[0] + cv_start_marker + "\n" + cv_html + "\n" + cv_end_marker + rest[1]
                patched = True
                
            if patched:
                with open(root_index_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("Master Hub index.html updated successfully with grid cards and CV.")
                return
        except Exception as e:
            print(f"Error patching index.html: {e}")
            
    # Default index fallback if not existing
    write_default_master_index(cards_html)

# Writes default main hub layout index.html
def write_default_master_index(cards_html):
    root_index_path = os.path.join(ROOT_DIR, 'index.html')
    # Default full html setup is already handled on root index creation
    # Rebuild hub only runs compile updates when projects are modified.

# Client Page html generator engine
def generate_client_page(project_id, project_data):
    proj_dir = os.path.join(PROJETOS_DIR, project_id)
    img_dir = os.path.join(proj_dir, 'img')
    os.makedirs(img_dir, exist_ok=True)
    
    # Copy files into local projects/ID/img/ preserving extensions
    images_mapping = {}
    for img_key in ['capa', 'processo', 'galeria']:
        src_path = project_data.get(f'path_{img_key}')
        if src_path and os.path.exists(src_path) and os.path.isfile(src_path):
            ext = os.path.splitext(src_path)[1]
            dest_filename = f"{img_key}{ext}"
            dest_path = os.path.join(img_dir, dest_filename)
            try:
                shutil.copy2(src_path, dest_path)
                images_mapping[img_key] = f"img/{dest_filename}"
            except Exception as e:
                print(f"Error copying project image {img_key}: {e}")
                images_mapping[img_key] = ""
        else:
            images_mapping[img_key] = ""
            
    # Read the base template html
    template_path = os.path.join(CMS_DIR, 'templates/project_template.html')
    if not os.path.exists(template_path):
        return False, "Base project HTML template file is missing in templates folder."
        
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        cat = project_data.get('categoria')
        
        # 1. Determine location / subtitle spec
        location_text = "Portfólio Marcelo Lacerda"
        if cat == "Impressão 3D":
            location_text = project_data.get('maq_maquina', 'Impressora 3D')
        elif cat == "Render":
            location_text = project_data.get('rnd_softwares', 'Render Engine')
        elif cat == "Venda":
            location_text = f"Disponível em {project_data.get('vnd_plataforma', 'Loja')}"
        elif cat == "Layout":
            location_text = project_data.get('lay_formato', 'Layout Digital')
            
        # 2. Determine metrics
        metrics = []
        if cat == "Impressão 3D":
            metrics = [
                { "number": f"{project_data.get('maq_peso', 0)}g", "label": "Peso do material consumido" },
                { "number": f"{project_data.get('maq_tempo', 0)}h", "label": "Tempo de impressão física" },
                { "number": f"€{project_data.get('maq_custo', 0.0):.2f}", "label": "Custo estimado de fabricação" }
            ]
        elif cat == "Render":
            metrics = [
                { "number": f"{project_data.get('rnd_vistas', 0)}", "label": "Vistas em alta resolução" },
                { "number": "Render", "label": project_data.get('rnd_hdri', 'Iluminação Física') },
                { "number": "Tools", "label": project_data.get('rnd_softwares', 'Blender / V-Ray') }
            ]
        elif cat == "Venda":
            metrics = [
                { "number": f"€{project_data.get('vnd_preco', 0.0):.2f}", "label": "Preço final de venda" },
                { "number": f"€{project_data.get('vnd_custo', 0.0):.2f}", "label": "Custo total de fabricação" },
                { "number": f"{project_data.get('vnd_margem_pct', 0.0)}%", "label": "Margem de lucro calculada" }
            ]
        elif cat == "Layout":
            metrics = [
                { "number": "Formato", "label": project_data.get('lay_formato', 'N/A') },
                { "number": "Grelha", "label": project_data.get('lay_grelha', 'N/A') },
                { "number": "Fontes", "label": project_data.get('lay_tipografias', 'N/A') }
            ]
            
        # 3. Determine milestones
        milestones = [
            {
                "num": "01",
                "title": "Conceito & Briefing",
                "text": "Definição do escopo, recolha de referências e planeamento das especificações do projeto.",
                "image": images_mapping.get('capa', '')
            },
            {
                "num": "02",
                "title": "Desenvolvimento Técnico",
                "text": "Execução da modelação 3D, fatiamento, configurações de render ou grelha de layout.",
                "image": images_mapping.get('processo', '')
            },
            {
                "num": "03",
                "title": "Produção & Acabamento",
                "text": "Impressão física da peça, pós-processamento, composição ou renderização final.",
                "image": images_mapping.get('galeria', '')
            },
            {
                "num": "04",
                "title": "Exposição & Entrega",
                "text": "Validação das métricas de qualidade, registo fotográfico e publicação no portfólio.",
                "image": images_mapping.get('capa', '')
            }
        ]
        
        # Filter milestones images - if some image is missing, reuse capa
        for m in milestones:
            if not m["image"]:
                m["image"] = images_mapping.get('capa', '') or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500"
                
        # 4. Gallery mapping
        gallery = []
        if images_mapping.get('capa'):
            gallery.append({ "url": images_mapping.get('capa'), "caption": "Imagem de Capa e Apresentação", "tag": "Capa", "spansLarge": True })
        if images_mapping.get('processo'):
            gallery.append({ "url": images_mapping.get('processo'), "caption": "Processo de Trabalho e Slicing/Wireframe", "tag": "Processo", "spansLarge": False })
        if images_mapping.get('galeria'):
            gallery.append({ "url": images_mapping.get('galeria'), "caption": "Resultado Final e Galeria", "tag": "Resultado Final", "spansLarge": False })
            
        # If gallery is empty, place placeholders
        if not gallery:
            gallery.append({ "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200", "caption": "Apresentação Geral do Projeto", "tag": "Projeto", "spansLarge": True })
            
        # Check status and set serial number
        serial_number = f"ID: {project_id}"
        if project_data.get('status') == 'Em andamento':
            serial_number += " [EM ANDAMENTO]"
            
        config = {
            "hero": {
                "title": project_data.get('titulo', ''),
                "subtitle": project_data.get('description', '')[:120] + "...",
                "category": project_data.get('categoria', ''),
                "serialNumber": serial_number,
                "locationText": location_text,
                "bgImage": images_mapping.get('capa', '') or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200"
            },
            "about": {
                "title": "Sobre o Trabalho",
                "description": project_data.get('description', ''),
                "image": images_mapping.get('processo', '') or images_mapping.get('capa', '') or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200",
                "metrics": metrics
            },
            "milestones": milestones,
            "gallery": gallery,
            "mapsIframeUrl": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2993.676644123!2d-8.625843!3d41.157943!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xd2465adc!2sPorto!5e0!3m2!1spt!2spt",
            "instagramPost": {
                "authorHandle": "@mlacerdapt",
                "authorAvatar": "https://api.dicebear.com/7.x/identicon/svg?seed=mlacerdapt",
                "likesCount": f"Curtido por {project_data.get('horas', 0)}h investidas no projeto",
                "captionText": f"Concluí mais um trabalho de {project_data.get('categoria')}: {project_data.get('titulo')}. Excelente resultado!",
                "tags": " ".join([f"#{t.strip().replace('#','')}" for t in project_data.get('tags', '').split(',') if t.strip()]),
                "date": datetime.now().strftime("%d DE %B DE %Y").upper()
            }
        }
        
        config_json_str = json.dumps(config, indent=4, ensure_ascii=False)
        html_content = html_content.replace('{{MONUMENT_CONFIG_JSON}}', config_json_str)
        
        # Write output file
        out_file_path = os.path.join(proj_dir, 'index.html')
        with open(out_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Rebuild Master Hub
        rebuild_master_hub()
        return True, "Project client web pages successfully created."
    except Exception as e:
        print(f"Error generating client HTML: {e}")
        return False, str(e)

# ROUTE: Dashboard Main
@app.route('/')
def index():
    db = load_db()
    # Filter projects (omit 'curriculo' key!)
    projects_db = {k: v for k, v in db.items() if k != 'curriculo'}
    sorted_db = dict(sorted(projects_db.items(), key=lambda x: x[0], reverse=True))
    return render_template('index.html', projetos=sorted_db, curriculo=db.get('curriculo', DEFAULT_CV))

# ROUTE: AJAX details lookup
@app.route('/project/get/<project_id>')
def get_project(project_id):
    db = load_db()
    if project_id in db:
        return jsonify(db[project_id])
    return jsonify({'error': f'Project {project_id} not found in database.'}), 404

# ROUTE: Save project metadata
@app.route('/project/save', methods=['POST'])
def save_project():
    db = load_db()
    project_id = request.form.get('id')
    categoria = request.form.get('categoria')
    
    is_new = not project_id
    if is_new:
        project_id = get_next_id(categoria)
        
    pdata = {
        'id': project_id,
        'titulo': request.form.get('titulo'),
        'description': request.form.get('description'),
        'tags': request.form.get('tags'),
        'categoria': categoria,
        'status': request.form.get('status'),
        'visibilidade': request.form.get('visibilidade', 'Privado'),
        'horas': float(request.form.get('horas', 0.0) or 0.0),
        'path_references': request.form.get('path_references'),
        'path_models': request.form.get('path_models'),
        'path_renders': request.form.get('path_renders'),
        'path_capa': request.form.get('path_capa'),
        'path_processo': request.form.get('path_processo'),
        'path_galeria': request.form.get('path_galeria'),
    }
    
    # Process dynamic data category details
    if categoria == "Impressão 3D":
        pdata.update({
            'maq_maquina': request.form.get('maq_maquina'),
            'maq_material': request.form.get('maq_material'),
            'maq_peso': float(request.form.get('maq_peso', 0.0) or 0.0),
            'maq_tempo': float(request.form.get('maq_tempo', 0.0) or 0.0),
            'maq_custo': float(request.form.get('maq_custo', 0.0) or 0.0)
        })
    elif categoria == "Render":
        pdata.update({
            'rnd_softwares': request.form.get('rnd_softwares'),
            'rnd_vistas': int(request.form.get('rnd_vistas', 0) or 0),
            'rnd_hdri': request.form.get('rnd_hdri')
        })
    elif categoria == "Venda":
        custo = float(request.form.get('vnd_custo', 0.0) or 0.0)
        preco = float(request.form.get('vnd_preco', 0.0) or 0.0)
        margem_abs = round(preco - custo, 2)
        margem_pct = round((margem_abs / preco * 100), 2) if preco > 0 else 0.0
        pdata.update({
            'vnd_plataforma': request.form.get('vnd_plataforma'),
            'vnd_custo': custo,
            'vnd_preco': preco,
            'vnd_margem_abs': margem_abs,
            'vnd_margem_pct': margem_pct
        })
    elif categoria == "Layout":
        pdata.update({
            'lay_formato': request.form.get('lay_formato'),
            'lay_grelha': request.form.get('lay_grelha'),
            'lay_tipografias': request.form.get('lay_tipografias')
        })
        
    db[project_id] = pdata
    save_db(db)
    
    # If project visibility is Public, generate static page and sync with Git repository
    if pdata['visibilidade'] == 'Público':
        success, err = generate_client_page(project_id, pdata)
        if success:
            start_git_sync(project_id)
            
    return redirect(url_for('index'))

# ROUTE: Save CV metadata
@app.route('/curriculo/save', methods=['POST'])
def save_cv():
    db = load_db()
    
    curriculo = {
        'nome': request.form.get('nome'),
        'titulo': request.form.get('titulo'),
        'email': request.form.get('email'),
        'github': request.form.get('github'),
        'localizacao': request.form.get('localizacao'),
        'avatar': request.form.get('avatar'),
        'resumo': request.form.get('resumo'),
        'skills': request.form.get('skills'),
        'experiencias': [
            {
                'date': request.form.get('exp1_date'),
                'role': request.form.get('exp1_role'),
                'company': request.form.get('exp1_company'),
                'desc': request.form.get('exp1_desc')
            },
            {
                'date': request.form.get('exp2_date'),
                'role': request.form.get('exp2_role'),
                'company': request.form.get('exp2_company'),
                'desc': request.form.get('exp2_desc')
            },
            {
                'date': request.form.get('exp3_date'),
                'role': request.form.get('exp3_role'),
                'company': request.form.get('exp3_company'),
                'desc': request.form.get('exp3_desc')
            }
        ],
        'educacao': [
            {
                'date': request.form.get('edu1_date'),
                'role': request.form.get('edu1_role'),
                'company': request.form.get('edu1_company'),
                'desc': request.form.get('edu1_desc')
            },
            {
                'date': request.form.get('edu2_date'),
                'role': request.form.get('edu2_role'),
                'company': request.form.get('edu2_company'),
                'desc': request.form.get('edu2_desc')
            }
        ]
    }
    
    # Filter empty rows
    curriculo['experiencias'] = [e for e in curriculo['experiencias'] if e['date'] or e['role'] or e['company']]
    curriculo['educacao'] = [ed for ed in curriculo['educacao'] if ed['date'] or ed['role'] or ed['company']]
    
    db['curriculo'] = curriculo
    save_db(db)
    
    # Rebuild root and sync git in background
    rebuild_master_hub()
    start_git_sync("curriculum-update")
    
    return redirect(url_for('index'))

# ROUTE: Manual publish and compile trigger
@app.route('/project/publish/<project_id>', methods=['POST'])
def publish_project(project_id):
    db = load_db()
    if project_id not in db:
        return jsonify({'success': False, 'message': 'Projeto não encontrado.'}), 404
        
    pdata = db[project_id]
    
    # Enforce Visibilidade to Público to allow rendering
    pdata['visibilidade'] = 'Público'
    db[project_id] = pdata
    save_db(db)
    
    success, err = generate_client_page(project_id, pdata)
    if success:
        start_git_sync(project_id)
        return jsonify({'success': True, 'message': 'Página gerada e sincronização iniciada.'})
    else:
        return jsonify({'success': False, 'message': f'Falha ao gerar página: {err}'}), 500

# ROUTE: Safe local disk file image server
@app.route('/local-image')
def local_image():
    img_path = request.args.get('path')
    if not img_path or not os.path.exists(img_path) or not os.path.isfile(img_path):
        return "Image not found on disk", 404
        
    mime_type, _ = mimetypes.guess_type(img_path)
    if not mime_type:
        mime_type = 'image/jpeg'
    return send_file(img_path, mimetype=mime_type)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
