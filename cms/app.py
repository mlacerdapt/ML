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

# Ensure directory structure
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(PROJETOS_DIR, exist_ok=True)

# Helper to load central JSON db
def load_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading database: {e}")
        return {}

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
        commit_msg = f"Update ML portfolio project: {project_id}"
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

# Rebuilds root index.html grid mapping all Public projects
def rebuild_master_hub():
    db = load_db()
    public_projects = []
    
    for pid, pdata in db.items():
        if pdata.get('visibilidade') == 'Público':
            public_projects.append((pid, pdata))
            
    # Sort projects descending: newer first
    public_projects.sort(key=lambda x: x[0], reverse=True)
    
    cards_html = ""
    for pid, pdata in public_projects:
        # Lookup relative path to cover image inside public folder structure
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
        
    root_index_path = os.path.join(ROOT_DIR, 'index.html')
    
    # Try updating root index using start/end markers
    if os.path.exists(root_index_path):
        try:
            with open(root_index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            start_marker = "<!-- PORTFOLIO_GRID_START -->"
            end_marker = "<!-- PORTFOLIO_GRID_END -->"
            
            if start_marker in content and end_marker in content:
                parts = content.split(start_marker)
                rest = parts[1].split(end_marker)
                new_content = parts[0] + start_marker + "\n" + cards_html + "\n" + end_marker + rest[1]
                with open(root_index_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("Master Hub index.html updated successfully with grid cards.")
                return
        except Exception as e:
            print(f"Error patching index.html: {e}")
            
    # Default index fallback if not existing or no markers found
    write_default_master_index(cards_html)

# Writes default main hub layout index.html
def write_default_master_index(cards_html):
    root_index_path = os.path.join(ROOT_DIR, 'index.html')
    default_html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ML Portfólio</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="portfolio_style.css">
</head>
<body>
    <div class="portfolio-wrapper">
        <header class="portfolio-header">
            <h1 class="portfolio-logo">ML Portfólio</h1>
            <p class="portfolio-subtitle">Galeria de Impressões 3D, Renders, Designs e Artigos</p>
            
            <!-- Category Filters UI -->
            <div class="filters-container">
                <button class="filter-btn active" data-filter="all">Todos</button>
                <button class="filter-btn" data-filter="Impressão 3D">Impressão 3D</button>
                <button class="filter-btn" data-filter="Render">Renders</button>
                <button class="filter-btn" data-filter="Venda">Artigos de Venda</button>
                <button class="filter-btn" data-filter="Layout">Layout Gráfico</button>
            </div>
        </header>
        
        <main class="portfolio-container">
            <div class="portfolio-grid">
                <!-- PORTFOLIO_GRID_START -->
                {cards_html}
                <!-- PORTFOLIO_GRID_END -->
            </div>
        </main>
        
        <footer class="portfolio-footer">
            <p>&copy; 2026 ML Portfólio. Todos os direitos reservados. Gerado por ML Gestor.</p>
        </footer>
    </div>
    
    <script>
        // Filters implementation
        document.addEventListener("DOMContentLoaded", () => {{
            const filterBtns = document.querySelectorAll(".filter-btn");
            const cards = document.querySelectorAll(".portfolio-card");
            
            filterBtns.forEach(btn => {{
                btn.addEventListener("click", () => {{
                    filterBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    
                    const filter = btn.dataset.filter;
                    cards.forEach(card => {{
                        if (filter === "all" || card.dataset.category === filter) {{
                            card.style.display = "flex";
                        }} else {{
                            card.style.display = "none";
                        }}
                    }});
                }});
            }});
        }});
    </script>
</body>
</html>"""
    try:
        with open(root_index_path, 'w', encoding='utf-8') as f:
            f.write(default_html)
        print("Default Master Hub index.html created.")
    except Exception as e:
        print(f"Error creating default index.html: {e}")

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
            
        spec_html = ""
        cat = project_data.get('categoria')
        
        # Build specification grids depending on category
        if cat == "Impressão 3D":
            spec_html = f"""
            <div class="specs-grid">
                <div class="spec-item"><span>Máquina</span><strong>{project_data.get('maq_maquina', 'N/A')}</strong></div>
                <div class="spec-item"><span>Material</span><strong>{project_data.get('maq_material', 'N/A')}</strong></div>
                <div class="spec-item"><span>Peso</span><strong>{project_data.get('maq_peso', 0)}g</strong></div>
                <div class="spec-item"><span>Tempo de Impressão</span><strong>{project_data.get('maq_tempo', 0)}h</strong></div>
                <div class="spec-item"><span>Custo Estimado</span><strong>€{project_data.get('maq_custo', 0.0):.2f}</strong></div>
            </div>"""
        elif cat == "Render":
            spec_html = f"""
            <div class="specs-grid">
                <div class="spec-item"><span>Softwares</span><strong>{project_data.get('rnd_softwares', 'N/A')}</strong></div>
                <div class="spec-item"><span>Vistas</span><strong>{project_data.get('rnd_vistas', 0)}</strong></div>
                <div class="spec-item"><span>Setup/HDRI</span><strong>{project_data.get('rnd_hdri', 'N/A')}</strong></div>
            </div>"""
        elif cat == "Venda":
            spec_html = f"""
            <div class="specs-grid">
                <div class="spec-item"><span>Plataforma</span><strong>{project_data.get('vnd_plataforma', 'N/A')}</strong></div>
                <div class="spec-item"><span>Custo de Fabricação</span><strong>€{project_data.get('vnd_custo', 0.0):.2f}</strong></div>
                <div class="spec-item"><span>Preço de Venda</span><strong>€{project_data.get('vnd_preco', 0.0):.2f}</strong></div>
                <div class="spec-item"><span>Margem de Lucro</span><strong>€{project_data.get('vnd_margem_abs', 0.0):.2f} ({project_data.get('vnd_margem_pct', 0.0)}%)</strong></div>
            </div>"""
        elif cat == "Layout":
            spec_html = f"""
            <div class="specs-grid">
                <div class="spec-item"><span>Formato</span><strong>{project_data.get('lay_formato', 'N/A')}</strong></div>
                <div class="spec-item"><span>Grelha</span><strong>{project_data.get('lay_grelha', 'N/A')}</strong></div>
                <div class="spec-item"><span>Tipografia</span><strong>{project_data.get('lay_tipografias', 'N/A')}</strong></div>
            </div>"""
            
        badge_html = ""
        if project_data.get('status') == "Em andamento":
            badge_html = '<div class="badge-status-inprogress">Em Andamento</div>'
            
        replacements = {
            '{{ID}}': project_id,
            '{{TITLE}}': project_data.get('titulo', ''),
            '{{DESCRIPTION}}': project_data.get('description', ''),
            '{{TAGS}}': project_data.get('tags', ''),
            '{{CATEGORY}}': project_data.get('categoria', ''),
            '{{STATUS}}': project_data.get('status', ''),
            '{{HOURS}}': str(project_data.get('horas', 0)),
            '{{SPECIFICATIONS}}': spec_html,
            '{{STATUS_BADGE}}': badge_html,
            '{{IMAGE_CAPA}}': images_mapping.get('capa', ''),
            '{{IMAGE_PROCESSO}}': images_mapping.get('processo', ''),
            '{{IMAGE_GALERIA}}': images_mapping.get('galeria', ''),
        }
        
        # Replace template placeholders
        for k, v in replacements.items():
            html_content = html_content.replace(k, v)
            
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
    # Sort projects list by ID descending
    sorted_db = dict(sorted(db.items(), key=lambda x: x[0], reverse=True))
    return render_template('index.html', projetos=sorted_db)

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
