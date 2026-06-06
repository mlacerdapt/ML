import os
import json
import shutil
import subprocess
import threading
import mimetypes
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, send_from_directory

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
    'skills_by_category': [
        {
            'category': 'Automação, Web Dev & Ciência de Dados',
            'items': [
                {'name': 'Python & Flask', 'desc': 'Desenvolvimento de Web Apps, APIs e Sistemas de Gestão', 'level': 5},
                {'name': 'Pandas & NumPy', 'desc': 'Análise, tratamento de dados complexos e ETL', 'level': 4.5},
                {'name': 'RPA / Automatismos', 'desc': 'PyAutoGUI, Win32, extração SAP automatizada', 'level': 5}
            ]
        }
    ],
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
    titulo = cv.get('titulo') or "Técnico de Planeamento e Processos"
    
    # Render Skills grouped by category with SVG radial circular progress charts
    skills_html = ""
    categories = cv.get('skills_by_category', [])
    if categories:
        for cat in categories:
            cat_title = cat.get('category', '').strip()
            items = cat.get('items', [])
            if not cat_title and not items:
                continue
            skills_html += f'<div class="cv-skills-category-group">\n'
            skills_html += f'  <h4 class="cv-skills-category-header">{cat_title}</h4>\n'
            skills_html += f'  <div class="cv-skills-category-grid">\n'
            for item in items:
                name = item.get('name', '').strip()
                desc = item.get('desc', '').strip()
                level = float(item.get('level', 4.0))
                
                # SVG stroke-dashoffset calculation. Circumference C = 2 * pi * r = 2 * pi * 20 = 125.66. Let's use 126.
                dasharray = 126
                dashoffset = dasharray - (level / 5.0) * dasharray
                
                skills_html += f"""
                <div class="skill-radial-item">
                    <div class="skill-radial-details">
                        <div class="skill-bar-header">
                            <span class="skill-radial-name">{name}</span>
                            <span class="skill-radial-level">{level:g}/5</span>
                        </div>
                        <div class="skill-progress-wrapper">
                            <div class="skill-progress-fill" style="width: {level * 20:g}%;"></div>
                        </div>
                        {f'<div class="skill-radial-desc">{desc}</div>' if desc else ''}
                    </div>
                </div>"""
            skills_html += f'  </div>\n'
            skills_html += f'</div>\n'
    else:
        # Fallback to plain tags if skills_by_category not defined
        skills_list = [s.strip() for s in cv.get('skills', '').split(',') if s.strip()]
        skills_html += '<div class="cv-skills-list">'
        for skill in skills_list:
            skills_html += f'<span class="skill-tag">{skill}</span>'
        skills_html += '</div>'
        
    exp_html = ""
    for exp in cv.get('experiencias', []):
        if not exp.get('role') and not exp.get('company'): continue
        desc_html = exp.get('desc', '').replace('\r\n', '<br>').replace('\n', '<br>')
        exp_html += f"""
                            <div class="timeline-row-item">
                                <div class="timeline-left-date">{exp.get('date', '')}</div>
                                <div class="timeline-center-line">
                                    <div class="timeline-node-dot"></div>
                                </div>
                                <div class="timeline-right-content">
                                    <div class="timeline-title-company">
                                        <span class="timeline-role-name">{exp.get('role', '')}</span>
                                        <span class="timeline-sep">|</span>
                                        <span class="timeline-company-name">{exp.get('company', '')}</span>
                                    </div>
                                    <div class="timeline-description-text">{desc_html}</div>
                                </div>
                            </div>"""
        
    edu_html = ""
    for edu in cv.get('educacao', []):
        if not edu.get('role') and not edu.get('company'): continue
        desc_html = edu.get('desc', '').replace('\r\n', '<br>').replace('\n', '<br>')
        edu_html += f"""
                            <div class="timeline-row-item">
                                <div class="timeline-left-date">{edu.get('date', '')}</div>
                                <div class="timeline-center-line">
                                    <div class="timeline-node-dot"></div>
                                </div>
                                <div class="timeline-right-content">
                                    <div class="timeline-title-company">
                                        <span class="timeline-role-name">{edu.get('role', '')}</span>
                                        <span class="timeline-sep">|</span>
                                        <span class="timeline-company-name">{edu.get('company', '')}</span>
                                    </div>
                                    <div class="timeline-description-text">{desc_html}</div>
                                </div>
                            </div>"""
        
    cv_html = f"""<div class="cv-print-bar no-print">
                <button class="cv-print-btn" onclick="printCV()">🖨️ Imprimir / Exportar PDF</button>
                <span class="cv-print-hint">💡 Nota: Na janela de impressão, marque a opção "Gráficos de fundo" e "Cabeçalhos e rodapés" para ver cores e números de página.</span>
            </div>
            <div class="cv-modern-split">
                <!-- Left Sidebar Column (Dark/Charcoal Background below photo) -->
                <aside class="cv-split-sidebar">
                    <div class="cv-sidebar-header">
                        <h2 class="cv-name-display">{nome}</h2>
                        <div class="cv-title-display">{titulo}</div>
                    </div>
                    
                    <!-- Profile Picture container with diagonal clip-path -->
                    <div class="cv-photo-container">
                        <img class="cv-photo-img" src="{avatar_src}" alt="{nome}">
                    </div>
                    
                    <!-- Dark Area below the photo -->
                    <div class="cv-sidebar-dark-content">
                        <div class="cv-sidebar-section">
                            <h3 class="cv-sidebar-section-title">Sobre Mim</h3>
                            <p class="cv-about-text">{cv.get('resumo', '')}</p>
                        </div>
                        
                        <div class="cv-sidebar-section">
                            <h3 class="cv-sidebar-section-title">Contacto</h3>
                            <ul class="cv-contact-items-list">"""

    # Build contact items cleanly to avoid nested f-string issues
    _email = cv.get('email', '')
    _github = cv.get('github', '')
    _telefone = cv.get('telefone', '')
    _localizacao = cv.get('localizacao', '')
    _maps_url = cv.get('localizacao_maps_url', '') or (
        'https://www.google.com/maps/search/?api=1&query=' + _localizacao.replace(' ', '+')
        if _localizacao else ''
    )
    _github_clean = _github.replace('https://github.com/', '').replace('github.com/', '')
    _tel_clean = _telefone.replace(' ', '').replace('+', '').replace('-', '')

    contact_html = ''
    if _email:
        contact_html += f'<li class="contact-li">📧 <a class="contact-txt contact-link" href="mailto:{_email}">{_email}</a></li>\n'
    if _github:
        contact_html += f'<li class="contact-li">🔗 <a class="contact-txt contact-link" href="https://github.com/{_github_clean}" target="_blank" rel="noopener">{_github}</a></li>\n'
    if _telefone:
        contact_html += f'<li class="contact-li">📱 <a class="contact-txt contact-link" href="https://wa.me/{_tel_clean}" target="_blank" rel="noopener">{_telefone}</a></li>\n'
    if _localizacao:
        contact_html += f'<li class="contact-li">📍 <a class="contact-txt contact-link" href="{_maps_url}" target="_blank" rel="noopener">{_localizacao}</a></li>\n'

    # Render dynamic CV social links (redes sociais)
    for link in cv.get('social_links', []):
        plataforma = link.get('plataforma', 'Outro')
        url = link.get('url', '').strip()
        if not url:
            continue
        icon_map = {
            'linkedin': '💼',
            'github': '💻',
            'instagram': '📸',
            'behance': '🎨',
            'facebook': '👥',
            'x': '🐦',
            'youtube': '📺',
            'portfolio': '🌐',
            'outro': '🔗'
        }
        icon = icon_map.get(plataforma.lower(), '🔗')
        href = url if url.startswith(('http://', 'https://')) else f'https://{url}'
        display_text = url.replace('https://', '').replace('http://', '').replace('www.', '')
        if len(display_text) > 30:
            display_text = display_text[:27] + "..."
        contact_html += f'<li class="contact-li">{icon} <a class="contact-txt contact-link" href="{href}" target="_blank" rel="noopener">{plataforma}: {display_text}</a></li>\n'

    qr_html = ""
    if _github:
        qr_url_encoded = f"https%3A%2F%2Fgithub.com%2F{_github_clean}"
        qr_html = f"""
            <!-- QR Code block – visible ONLY in print (last page) -->
            <div class="cv-print-qr-block" id="cv-print-qr">
                <div class="cv-print-qr-inner">
                    <img
                        class="cv-qr-image"
                        src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={qr_url_encoded}&color=0058A3&bgcolor=FFFFFF&margin=6"
                        alt="QR Code – Portfólio e Currículo no GitHub"
                    >
                    <div class="cv-qr-text">
                        <p class="cv-qr-label">Portfólio &amp; Currículo Online</p>
                        <a class="cv-qr-link" href="https://github.com/{_github_clean}" target="_blank" rel="noopener">
                            github.com/{_github_clean}
                        </a>
                        <p class="cv-qr-caption">Aceda ao meu portfólio completo, projetos e currículo online no GitHub. Aponte a câmara para o QR code ou clique no link acima.</p>
                    </div>
                </div>
            </div>"""

    cv_html_part2 = f"""                                {contact_html}
                            </ul>
                        </div>
                    </div>
                </aside>
                
                <!-- Right Main Column (Light background) -->
                <main class="cv-split-main">
                    <!-- Skills Section -->
                    <section class="cv-main-section">
                        <div class="cv-section-header-styled">
                            <h3 class="cv-section-title-text">Competências</h3>
                            <div class="cv-section-header-line"></div>
                        </div>
                        <div class="cv-skills-radial-wrapper">
                            {skills_html}
                        </div>
                    </section>
                    
                    <!-- Experience Section -->
                    <section class="cv-main-section">
                        <div class="cv-section-header-styled">
                            <h3 class="cv-section-title-text">Experiência</h3>
                            <div class="cv-section-header-line"></div>
                        </div>
                        <div class="cv-timeline-vertical-styled">
                            {exp_html}
                        </div>
                    </section>
                    
                    <!-- Education Section -->
                    <section class="cv-main-section">
                        <div class="cv-section-header-styled">
                            <h3 class="cv-section-title-text">Educação</h3>
                            <div class="cv-section-header-line"></div>
                        </div>
                        <div class="cv-timeline-vertical-styled">
                            {edu_html}
                        </div>
                    </section>
                    
                    {qr_html}
                </main>
            </div>"""

    return cv_html + cv_html_part2


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

# Helper to optimize/compress images to fit GitHub limits and improve web speed
def optimize_image(file_path, max_size_mb=10):
    if not os.path.exists(file_path):
        return
        
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size <= max_size_bytes:
        return
        
    print(f"Image {file_path} size ({file_size / (1024*1024):.2f} MB) exceeds {max_size_mb}MB limit. Optimizing...")
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            # Handle alpha transparency channels for JPEG compatibility
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                # Paste using alpha channel as mask
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            # If resolution is ultra-high, scale down to fit max dimension of 2560px
            max_dimension = 2560
            width, height = img.size
            if width > max_dimension or height > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized image to {new_width}x{new_height}")
                
            # Save back in JPEG format with high optimization
            img.save(file_path, 'JPEG', quality=85, optimize=True)
            print(f"Optimized image saved. New size: {os.path.getsize(file_path) / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"Error optimizing image {file_path}: {e}")

# Client Page html generator engine
def generate_client_page(project_id, project_data):
    proj_dir = os.path.join(PROJETOS_DIR, project_id)
    img_dir = os.path.join(proj_dir, 'img')
    os.makedirs(img_dir, exist_ok=True)
    
    # Copy files into local projects/ID/img/ resolving names and extensions
    images_mapping = {}
    for img_key in ['capa', 'processo', 'galeria']:
        src_path = project_data.get(f'path_{img_key}')
        resolved_path = None
        
        if src_path:
            src_path = src_path.strip()
            # 1. Try directly as absolute/relative path
            if os.path.exists(src_path) and os.path.isfile(src_path):
                resolved_path = src_path
            # 2. If it's just a filename (no slashes), search in local work directories
            elif not os.path.isabs(src_path) and "/" not in src_path and "\\" not in src_path:
                # First, check if the file already exists in the project's own img/ directory
                candidate_img_path = os.path.join(img_dir, src_path)
                if os.path.exists(candidate_img_path) and os.path.isfile(candidate_img_path):
                    resolved_path = candidate_img_path
                else:
                    for folder_key in ['path_renders', 'path_models', 'path_references']:
                        folder_path = project_data.get(folder_key)
                        if folder_path:
                            candidate_path = os.path.join(folder_path.strip(), src_path)
                            if os.path.exists(candidate_path) and os.path.isfile(candidate_path):
                                resolved_path = candidate_path
                                break
                            
        # 3. If still not resolved, check if a file with the key name already exists in projects/ID/img/
        if not resolved_path:
            if os.path.exists(img_dir):
                for f in os.listdir(img_dir):
                    if os.path.splitext(f)[0] == img_key:
                        resolved_path = os.path.join(img_dir, f)
                        images_mapping[img_key] = f"img/{f}"
                        break
                        
        if resolved_path and not images_mapping.get(img_key):
            ext = os.path.splitext(resolved_path)[1].lower()
            # If the source file is larger than 10MB, convert/save it as .jpg for optimal compression
            file_size = os.path.getsize(resolved_path)
            if file_size > 10 * 1024 * 1024:
                ext = ".jpg"
                
            dest_filename = f"{img_key}{ext}"
            dest_path = os.path.join(img_dir, dest_filename)
            try:
                if os.path.abspath(resolved_path) != os.path.abspath(dest_path):
                    shutil.copy2(resolved_path, dest_path)
                # Optimize/Compress if it exceeds the limit
                optimize_image(dest_path, max_size_mb=10)
                images_mapping[img_key] = f"img/{dest_filename}"
            except Exception as e:
                print(f"Error copying/optimizing project image {img_key}: {e}")
                images_mapping[img_key] = ""
        elif resolved_path and images_mapping.get(img_key):
            # Optimize in place if it already existed in the destination
            dest_path = os.path.join(img_dir, os.path.basename(resolved_path))
            optimize_image(dest_path, max_size_mb=10)
        else:
            if not images_mapping.get(img_key):
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
            
        # 2. Determine metrics (private financial data is NOT included in the public page)
        metrics = []
        if cat == "Impressão 3D":
            metrics = [
                { "number": f"{project_data.get('maq_peso', 0)}g", "label": "Peso do material consumido" },
                { "number": f"{project_data.get('maq_tempo', 0)}h", "label": "Tempo de impressão física" },
                { "number": project_data.get('maq_material', 'Material utilizado') or 'Material utilizado', "label": "Material de impressão" }
            ]
        elif cat == "Render":
            metrics = [
                { "number": f"{project_data.get('rnd_vistas', 0)}", "label": "Vistas em alta resolução" },
                { "number": "Render", "label": project_data.get('rnd_hdri', 'Iluminação Física') },
                { "number": "Tools", "label": project_data.get('rnd_softwares', 'Blender / V-Ray') }
            ]
        elif cat == "Venda":
            metrics = [
                { "number": f"€{project_data.get('vnd_preco', 0.0):.2f}", "label": "Preço de venda" },
                { "number": project_data.get('vnd_plataforma', 'Loja online') or 'Loja online', "label": "Canal de venda" },
                { "number": str(int(project_data.get('horas', 0))) + "h", "label": "Horas investidas" }
            ]
        elif cat == "Layout":
            metrics = [
                { "number": "Formato", "label": project_data.get('lay_formato', 'N/A') },
                { "number": "Grelha", "label": project_data.get('lay_grelha', 'N/A') },
                { "number": "Fontes", "label": project_data.get('lay_tipografias', 'N/A') }
            ]

        # Helper: resolve milestone image from filename in img/ or fallback to capa
        def resolve_milestone_img(filename, fallback):
            if not filename:
                return fallback
            candidate = os.path.join(img_dir, filename)
            if os.path.exists(candidate):
                return f"img/{filename}"
            # Try to find by prefix (e.g. "capa" matches "capa.jpg")
            if os.path.exists(img_dir):
                for f in os.listdir(img_dir):
                    if os.path.splitext(f)[0].lower() == filename.lower().replace('img/', ''):
                        return f"img/{f}"
            return fallback or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500"

        fallback_capa = images_mapping.get('capa', '') or "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500"

        # 3. Determine milestones with per-phase image assignment
        m1_title = project_data.get('milestone1_title', '').strip() or "Conceito & Briefing"
        m1_desc = project_data.get('milestone1_desc', '').strip() or "Definição do escopo, recolha de referências e planeamento das especificações do projeto."
        m1_img = resolve_milestone_img(project_data.get('milestone1_image', ''), images_mapping.get('capa', '') or fallback_capa)

        m2_title = project_data.get('milestone2_title', '').strip() or "Desenvolvimento Técnico"
        m2_desc = project_data.get('milestone2_desc', '').strip() or "Execução da modelação 3D, fatiamento, configurações de render ou grelha de layout."
        m2_img = resolve_milestone_img(project_data.get('milestone2_image', ''), images_mapping.get('processo', '') or fallback_capa)

        m3_title = project_data.get('milestone3_title', '').strip() or "Produção & Acabamento"
        m3_desc = project_data.get('milestone3_desc', '').strip() or "Impressão física da peça, pós-processamento, composição ou renderização final."
        m3_img = resolve_milestone_img(project_data.get('milestone3_image', ''), images_mapping.get('galeria', '') or fallback_capa)

        m4_title = project_data.get('milestone4_title', '').strip() or "Exposição & Entrega"
        m4_desc = project_data.get('milestone4_desc', '').strip() or "Validação das métricas de qualidade, registo fotográfico e publicação no portfólio."
        m4_img = resolve_milestone_img(project_data.get('milestone4_image', ''), fallback_capa)

        milestones = [
            { "num": "01", "title": m1_title, "text": m1_desc, "image": m1_img },
            { "num": "02", "title": m2_title, "text": m2_desc, "image": m2_img },
            { "num": "03", "title": m3_title, "text": m3_desc, "image": m3_img },
            { "num": "04", "title": m4_title, "text": m4_desc, "image": m4_img }
        ]
                
        # 4. Gallery: include ALL local images in img/ except explicitly excluded ones
        excluded_images = project_data.get('excluded_images', [])
        image_metadata = project_data.get('image_metadata', {})
        gallery = []

        # Default captions/tags for well-known filenames (prefix match)
        default_meta = {
            'capa':    {'caption': 'Imagem de Capa e Apresentação', 'tag': 'Capa',           'spansLarge': True},
            'processo':{'caption': 'Processo de Trabalho',          'tag': 'Processo',        'spansLarge': False},
            'galeria': {'caption': 'Resultado Final',               'tag': 'Resultado Final', 'spansLarge': False},
        }

        if os.path.exists(img_dir):
            # Sort: capa first, then alphabetically
            all_files = sorted(
                [f for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))],
                key=lambda f: (0 if os.path.splitext(f)[0].lower() == 'capa' else 1, f)
            )
            is_first = True
            for fname in all_files:
                if fname in excluded_images:
                    continue
                url = f"img/{fname}"
                base = os.path.splitext(fname)[0].lower()
                # Custom metadata takes priority; fallback to default_meta by prefix
                meta_entry = image_metadata.get(fname, {})
                custom_caption = meta_entry.get('caption', '').strip()
                custom_tag = meta_entry.get('tag', '').strip()
                default = default_meta.get(base, {})
                caption = custom_caption or default.get('caption', fname)
                tag = custom_tag or default.get('tag', 'Galeria')
                spans_large = is_first  # First image always spans large
                gallery.append({'url': url, 'caption': caption, 'tag': tag, 'spansLarge': spans_large})
                is_first = False

        # If gallery is still empty, place placeholder
        if not gallery:
            gallery.append({ "url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200", "caption": "Apresentação Geral do Projeto", "tag": "Projeto", "spansLarge": True })
            
        # Check status and set serial number
        serial_number = f"ID: {project_id}"
        if project_data.get('status') == 'Em andamento':
            serial_number += " [EM ANDAMENTO]"

        # Resolve Map Link
        maps_url = project_data.get('link_mapa', '').strip()

        # Resolve Instagram Post URL
        instagram_url = ""
        for sl in project_data.get('social_links', []):
            if sl.get('plataforma') == 'Instagram':
                instagram_url = sl.get('url', '')
                break
            
        config = {
            "status": project_data.get('status', 'Em andamento'),
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
            "mapsIframeUrl": maps_url,
            "socialLinks": project_data.get('social_links', []),
            "instagramPost": {
                "authorHandle": "@mlacerdapt",
                "authorAvatar": "https://api.dicebear.com/7.x/identicon/svg?seed=mlacerdapt",
                "likesCount": f"Curtido por {project_data.get('horas', 0)}h investidas no projeto",
                "captionText": f"Concluí mais um trabalho de {project_data.get('categoria')}: {project_data.get('titulo')}. Excelente resultado!",
                "tags": " ".join([f"#{t.strip().replace('#','')}" for t in project_data.get('tags', '').split(',') if t.strip()]),
                "date": datetime.now().strftime("%d DE %B DE %Y").upper(),
                "postUrl": instagram_url
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
    active_tab = request.args.get('active_tab', 'edit-tab')
    # Filter projects (omit 'curriculo' key!)
    projects_db = {k: v for k, v in db.items() if k != 'curriculo'}
    sorted_db = dict(sorted(projects_db.items(), key=lambda x: x[0], reverse=True))
    return render_template('index.html', projetos=sorted_db, curriculo=db.get('curriculo', DEFAULT_CV), active_tab=active_tab)

# ROUTE: AJAX details lookup
@app.route('/project/get/<project_id>')
def get_project(project_id):
    db = load_db()
    if project_id in db:
        return jsonify(db[project_id])
    return jsonify({'error': f'Project {project_id} not found in database.'}), 404

# ROUTE: AJAX local project images lookup
@app.route('/project/images/<project_id>')
def get_project_images(project_id):
    proj_dir = os.path.join(PROJETOS_DIR, project_id)
    img_dir = os.path.join(proj_dir, 'img')
    if not os.path.exists(img_dir):
        return jsonify([])
        
    try:
        files = []
        for f in os.listdir(img_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                size_bytes = os.path.getsize(os.path.join(img_dir, f))
                files.append({
                    'name': f,
                    'path': os.path.join(img_dir, f),
                    'url': f"/projetos/{project_id}/img/{f}",
                    'size_mb': round(size_bytes / (1024 * 1024), 2)
                })
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ROUTE: Save project metadata
@app.route('/project/save', methods=['POST'])
def save_project():
    db = load_db()
    project_id = request.form.get('id')
    categoria = request.form.get('categoria')
    
    is_new = not project_id
    if is_new:
        project_id = get_next_id(categoria)
        
    # Parse dynamic list of social links
    social_plataformas = request.form.getlist('social_plataforma[]')
    social_urls = request.form.getlist('social_url[]')
    social_links = []
    for plat, url in zip(social_plataformas, social_urls):
        if url.strip():
            social_links.append({
                'plataforma': plat,
                'url': url.strip()
            })

    path_ref = request.form.get('path_references', '').strip() or f"projetos/{project_id}/referencias"
    path_mod = request.form.get('path_models', '').strip() or f"projetos/{project_id}/modelos"
    path_rnd = request.form.get('path_renders', '').strip() or f"projetos/{project_id}/renders"

    pdata = {
        'id': project_id,
        'titulo': request.form.get('titulo'),
        'description': request.form.get('description'),
        'tags': request.form.get('tags'),
        'categoria': categoria,
        'status': request.form.get('status'),
        'visibilidade': request.form.get('visibilidade', 'Privado'),
        'horas': float(request.form.get('horas', 0.0) or 0.0),
        'path_references': path_ref,
        'path_models': path_mod,
        'path_renders': path_rnd,
        'path_capa': request.form.get('path_capa'),
        'path_processo': request.form.get('path_processo'),
        'path_galeria': request.form.get('path_galeria'),
        'link_mapa': request.form.get('link_mapa'),
        'social_links': social_links,
        'milestone1_title': request.form.get('milestone1_title', '').strip(),
        'milestone1_desc': request.form.get('milestone1_desc', '').strip(),
        'milestone1_image': request.form.get('milestone1_image', '').strip(),
        'milestone2_title': request.form.get('milestone2_title', '').strip(),
        'milestone2_desc': request.form.get('milestone2_desc', '').strip(),
        'milestone2_image': request.form.get('milestone2_image', '').strip(),
        'milestone3_title': request.form.get('milestone3_title', '').strip(),
        'milestone3_desc': request.form.get('milestone3_desc', '').strip(),
        'milestone3_image': request.form.get('milestone3_image', '').strip(),
        'milestone4_title': request.form.get('milestone4_title', '').strip(),
        'milestone4_desc': request.form.get('milestone4_desc', '').strip(),
        'milestone4_image': request.form.get('milestone4_image', '').strip(),
        'excluded_images': request.form.getlist('excluded_images')
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
        
    # Save per-image metadata (caption and tag) for images in the project img/ folder
    proj_dir_for_meta = os.path.join(PROJETOS_DIR, project_id)
    img_dir_for_meta = os.path.join(proj_dir_for_meta, 'img')
    image_metadata = {}
    if os.path.exists(img_dir_for_meta):
        for fname in os.listdir(img_dir_for_meta):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                caption = request.form.get(f'image_caption_{fname}', '').strip()
                tag = request.form.get(f'image_tag_{fname}', '').strip()
                image_metadata[fname] = {'caption': caption, 'tag': tag}
    pdata['image_metadata'] = image_metadata

    # Automatically create local directories on the filesystem if specified and they don't exist
    for path_key in ['path_references', 'path_models', 'path_renders']:
        path_val = pdata.get(path_key)
        if path_val:
            path_val_stripped = path_val.strip()
            # If it's a simple filename (no separators), it's not a folder, so skip auto-creating
            if not os.path.isabs(path_val_stripped) and "/" not in path_val_stripped and "\\" not in path_val_stripped:
                continue
            try:
                # Expand user symbol (~), normalize path, and create directory tree
                if not os.path.isabs(path_val_stripped):
                    dir_path = os.path.abspath(os.path.join(ROOT_DIR, path_val_stripped))
                else:
                    dir_path = os.path.abspath(os.path.expanduser(path_val_stripped))
                os.makedirs(dir_path, exist_ok=True)
                print(f"Local work directory created/verified: {dir_path}")
            except Exception as e:
                print(f"Error creating local work directory for {path_key} ({path_val}): {e}")
        
    db[project_id] = pdata
    save_db(db)
    
    # Always generate client web page locally for previewing
    success, err = generate_client_page(project_id, pdata)
    
    # If project visibility is Public and generation succeeded, sync with Git repository
    if success and pdata['visibilidade'] == 'Público':
        start_git_sync(project_id)
            
    return redirect(url_for('index', active_tab='edit-tab'))

# ROUTE: Save CV metadata
@app.route('/curriculo/save', methods=['POST'])
def save_cv():
    db = load_db()
    
    # Handle profile avatar image upload
    avatar_url = request.form.get('avatar')
    avatar_file = request.files.get('avatar_file')
    if avatar_file and avatar_file.filename:
        _, ext = os.path.splitext(avatar_file.filename)
        if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            uploads_dir = os.path.join(ROOT_DIR, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            # Remove old avatar files to prevent file pollution in Git
            for old_file in os.listdir(uploads_dir):
                if old_file.startswith('profile_avatar.'):
                    try:
                        os.remove(os.path.join(uploads_dir, old_file))
                    except Exception as e:
                        print(f"Error removing old avatar file: {e}")
            filename = f"profile_avatar{ext.lower()}"
            avatar_path = os.path.join(uploads_dir, filename)
            avatar_file.save(avatar_path)
            avatar_url = f"uploads/{filename}"

    # Handle dynamic experiences
    exp_dates = request.form.getlist('exp_date[]')
    exp_roles = request.form.getlist('exp_role[]')
    exp_companies = request.form.getlist('exp_company[]')
    exp_descs = request.form.getlist('exp_desc[]')
    
    experiencias = []
    for date, role, company, desc in zip(exp_dates, exp_roles, exp_companies, exp_descs):
        if date.strip() or role.strip() or company.strip() or desc.strip():
            experiencias.append({
                'date': date.strip(),
                'role': role.strip(),
                'company': company.strip(),
                'desc': desc.strip()
            })
    
    # Handle dynamic education
    edu_dates = request.form.getlist('edu_date[]')
    edu_roles = request.form.getlist('edu_role[]')
    edu_companies = request.form.getlist('edu_company[]')
    edu_descs = request.form.getlist('edu_desc[]')
    
    educacao = []
    for date, role, company, desc in zip(edu_dates, edu_roles, edu_companies, edu_descs):
        if date.strip() or role.strip() or company.strip() or desc.strip():
            educacao.append({
                'date': date.strip(),
                'role': role.strip(),
                'company': company.strip(),
                'desc': desc.strip()
            })
    
    # Parse structured skills from hidden JSON field
    skills_json_str = request.form.get('skills_json')
    skills_by_category = []
    if skills_json_str:
        try:
            skills_by_category = json.loads(skills_json_str)
        except Exception as e:
            print(f"Error parsing skills_json: {e}")

    curriculo = {
        'nome': request.form.get('nome'),
        'titulo': request.form.get('titulo'),
        'email': request.form.get('email'),
        'github': request.form.get('github'),
        'telefone': request.form.get('telefone', '').strip(),
        'localizacao': request.form.get('localizacao'),
        'localizacao_maps_url': request.form.get('localizacao_maps_url', '').strip(),
        'avatar': avatar_url,
        'resumo': request.form.get('resumo'),
        'skills': request.form.get('skills') or "",
        'skills_by_category': skills_by_category,
        'experiencias': experiencias,
        'educacao': educacao
    }
    
    # Parse CV social links (redes sociais do currículo)
    cv_social_plataformas = request.form.getlist('cv_social_plataforma[]')
    cv_social_urls = request.form.getlist('cv_social_url[]')
    cv_social_links = []
    for plataforma, url in zip(cv_social_plataformas, cv_social_urls):
        if url.strip():
            cv_social_links.append({'plataforma': plataforma.strip(), 'url': url.strip()})
    curriculo['social_links'] = cv_social_links
    
    db['curriculo'] = curriculo
    save_db(db)
    
    # Rebuild root and sync git in background
    rebuild_master_hub()
    start_git_sync("curriculum-update")
    
    return redirect(url_for('index', active_tab='cv-tab'))

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

# ROUTE: Serve uploaded avatar/files locally
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    uploads_dir = os.path.join(ROOT_DIR, 'uploads')
    return send_from_directory(uploads_dir, filename)

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

# ROUTE: Safe local folder opener for macOS Finder
@app.route('/open-folder', methods=['POST'])
def open_folder():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'success': False, 'message': 'Caminho não fornecido.'}), 400
        
    path_val = data['path'].strip()
    if not path_val:
        return jsonify({'success': False, 'message': 'Caminho vazio.'}), 400
        
    try:
        # Resolve path relative to ROOT_DIR if relative
        if not os.path.isabs(path_val):
            resolved_path = os.path.abspath(os.path.join(ROOT_DIR, path_val))
        else:
            resolved_path = os.path.abspath(os.path.expanduser(path_val))
            
        # Ensure it exists
        os.makedirs(resolved_path, exist_ok=True)
        
        # Open in macOS Finder
        subprocess.run(['open', resolved_path], check=True)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ROUTE: Serve root css file for local previews
@app.route('/portfolio_style.css')
def serve_root_css():
    return send_file(os.path.join(ROOT_DIR, 'portfolio_style.css'))

# ROUTE: Serve i18n translation script for local previews
@app.route('/portfolio_i18n.js')
def serve_i18n_js():
    return send_file(os.path.join(ROOT_DIR, 'portfolio_i18n.js'))

# ROUTE: Serve the compiled master portfolio/curriculum hub
@app.route('/portfolio')
def serve_portfolio_hub():
    return send_file(os.path.join(ROOT_DIR, 'index.html'))

# ROUTE: Serve client pages locally for previewing
@app.route('/projetos/<path:filename>')
def serve_projetos(filename):
    return send_from_directory(PROJETOS_DIR, filename)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
