/**
 * portfolio_i18n.js
 * Client-side language switcher: PT 🇵🇹 | EN 🇬🇧 | ES 🇪🇸
 * Uses the free Google Translate (gtx) endpoint — no API key required.
 * Caches translations in sessionStorage per language to avoid re-fetching.
 */

(function () {
    'use strict';

    // ── Static UI label translations (instant, no API needed) ────────────────
    const UI_LABELS = {
        pt: {
            'tab-portfolio-label': 'Portfólio',
            'tab-curriculo-label': 'Currículo',
            'filter-all': 'Todos',
            'filter-3d': 'Impressão 3D',
            'filter-render': 'Renders',
            'filter-venda': 'Artigos de Venda',
            'filter-layout': 'Layout Gráfico',
            'footer-tagline': 'Coleção de Criações 3D & Layouts',
            'footer-copy': '© 2026 Marcelo Lacerda. Todos os direitos reservados.',
            'print-btn': '🖨️ Imprimir / Exportar PDF',
            'btn-ver-projeto': 'Ver Projeto',
            'translating': 'A traduzir…',
            'cv-sidebar-sobre': 'Sobre Mim',
            'cv-sidebar-contacto': 'Contacto',
            'cv-section-edu': 'Educação',
            'cv-section-exp': 'Experiência',
            'cv-section-skills': 'Competências',
        },
        en: {
            'tab-portfolio-label': 'Portfolio',
            'tab-curriculo-label': 'Résumé',
            'filter-all': 'All',
            'filter-3d': '3D Printing',
            'filter-render': 'Renders',
            'filter-venda': 'Sales Items',
            'filter-layout': 'Graphic Layout',
            'footer-tagline': 'Collection of 3D Creations & Layouts',
            'footer-copy': '© 2026 Marcelo Lacerda. All rights reserved.',
            'print-btn': '🖨️ Print / Export PDF',
            'btn-ver-projeto': 'View Project',
            'translating': 'Translating…',
            'cv-sidebar-sobre': 'About Me',
            'cv-sidebar-contacto': 'Contact',
            'cv-section-edu': 'Education',
            'cv-section-exp': 'Experience',
            'cv-section-skills': 'Skills',
        },
        es: {
            'tab-portfolio-label': 'Portafolio',
            'tab-curriculo-label': 'Currículum',
            'filter-all': 'Todos',
            'filter-3d': 'Impresión 3D',
            'filter-render': 'Renders',
            'filter-venda': 'Artículos de Venta',
            'filter-layout': 'Diseño Gráfico',
            'footer-tagline': 'Colección de Creaciones 3D & Diseños',
            'footer-copy': '© 2026 Marcelo Lacerda. Todos los derechos reservados.',
            'print-btn': '🖨️ Imprimir / Exportar PDF',
            'btn-ver-projeto': 'Ver Proyecto',
            'translating': 'Traduciendo…',
            'cv-sidebar-sobre': 'Sobre Mí',
            'cv-sidebar-contacto': 'Contacto',
            'cv-section-edu': 'Educación',
            'cv-section-exp': 'Experiencia',
            'cv-section-skills': 'Competencias',
        }
    };

    // Selectors for UI labels (static, translate instantly)
    const UI_SELECTORS = {
        'tab-portfolio-label': 'button[onclick*="tab-portfolio"]',
        'tab-curriculo-label': 'button[onclick*="tab-curriculo"]',
        'filter-all':    '.filter-btn[data-filter="all"]',
        'filter-3d':     '.filter-btn[data-filter="Impressão 3D"]',
        'filter-render': '.filter-btn[data-filter="Render"]',
        'filter-venda':  '.filter-btn[data-filter="Venda"]',
        'filter-layout': '.filter-btn[data-filter="Layout"]',
        'footer-tagline': '.museum-footer-tagline',
        'footer-copy':    '.portfolio-footer p',
        'print-btn':      '.cv-print-btn',
        'cv-sidebar-sobre':    '.cv-sidebar-section-title:first-of-type',
        'cv-section-edu':      '.cv-section-title-text:nth-of-type(1)',
    };

    // ── State ────────────────────────────────────────────────────────────────
    let currentLang = 'pt';
    const STORAGE_KEY_PREFIX = 'i18n_cache_';
    const ORIGINAL_KEY = 'i18n_originals';

    // ── Translate text via Google Translate free endpoint ────────────────────
    async function gTranslate(text, targetLang, sourceLang = 'pt') {
        if (!text || text.trim().length < 2) return text;
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`;
        try {
            const res = await fetch(url);
            const data = await res.json();
            // Response structure: [[["translated","original",null,null,1],...], ...]
            return data[0].map(seg => seg[0]).join('');
        } catch (e) {
            console.warn('Translation failed for:', text, e);
            return text; // fallback: keep original
        }
    }

    // ── Collect all translatable text nodes in the page ──────────────────────
    function getTranslatableNodes() {
        const nodes = [];
        const skipTags = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'CODE', 'PRE', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'SVG', 'PATH', 'CIRCLE']);
        const skipClasses = ['contact-link', 'tag', 'card-category', 'badge', 'lang-btn', 'lang-bar'];

        function walk(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent.trim();
                if (text.length > 1 && !/^[\d\s\W]+$/.test(text)) {
                    nodes.push(node);
                }
                return;
            }
            if (node.nodeType !== Node.ELEMENT_NODE) return;
            if (skipTags.has(node.tagName)) return;
            if (skipClasses.some(c => node.classList && node.classList.contains(c))) return;
            // Skip elements that contain actual URLs or emails
            if (node.tagName === 'A') {
                const href = node.getAttribute('href') || '';
                if (href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('https://wa.me')) return;
            }
            // Skip the lang-bar entirely
            if (node.id === 'lang-bar') return;
            for (const child of node.childNodes) {
                walk(child);
            }
        }

        walk(document.body);
        return nodes;
    }

    // Safe storage helper with in-memory fallback to prevent SecurityError on file:// protocol
    const storageCache = {};
    const safeStorage = {
        getItem(key) {
            try {
                return sessionStorage.getItem(key);
            } catch (e) {
                return storageCache[key] || null;
            }
        },
        setItem(key, value) {
            try {
                sessionStorage.setItem(key, value);
            } catch (e) {
                storageCache[key] = value;
            }
        }
    };

    // ── Save originals (Portuguese) on first call ─────────────────────────────
    function saveOriginals(nodes) {
        if (safeStorage.getItem(ORIGINAL_KEY)) return; // already saved
        const originals = nodes.map(n => n.textContent);
        safeStorage.setItem(ORIGINAL_KEY, JSON.stringify(originals));
    }

    // ── Restore original Portuguese text ─────────────────────────────────────
    function restoreOriginals(nodes) {
        const raw = safeStorage.getItem(ORIGINAL_KEY);
        if (!raw) return;
        const originals = JSON.parse(raw);
        nodes.forEach((node, i) => {
            if (originals[i] !== undefined) {
                node.textContent = originals[i];
            }
        });
    }

    // ── Apply cached translation ──────────────────────────────────────────────
    function applyCachedTranslation(nodes, lang) {
        const cacheKey = STORAGE_KEY_PREFIX + lang;
        const cached = safeStorage.getItem(cacheKey);
        if (!cached) return false;
        const translations = JSON.parse(cached);
        if (translations.length !== nodes.length) return false; // stale cache
        nodes.forEach((node, i) => {
            if (translations[i]) node.textContent = translations[i];
        });
        return true;
    }

    // ── Translate all nodes in batches ────────────────────────────────────────
    async function translateNodes(nodes, lang) {
        const cacheKey = STORAGE_KEY_PREFIX + lang;
        const BATCH_SIZE = 10; // translate 10 nodes per request to avoid URL length limits
        const results = new Array(nodes.length).fill('');

        for (let i = 0; i < nodes.length; i += BATCH_SIZE) {
            const batch = nodes.slice(i, i + BATCH_SIZE);
            await Promise.all(batch.map(async (node, j) => {
                const translated = await gTranslate(node.textContent, lang);
                results[i + j] = translated;
                node.textContent = translated; // apply immediately as we go
            }));
        }

        safeStorage.setItem(cacheKey, JSON.stringify(results));
    }

    // ── Apply instant UI label translations ───────────────────────────────────
    function applyUILabels(lang) {
        const labels = UI_LABELS[lang] || UI_LABELS['pt'];

        // Update all cv-sidebar-section-title elements
        const sidebarTitles = document.querySelectorAll('.cv-sidebar-section-title');
        const sidebarKeys = ['cv-sidebar-sobre', 'cv-sidebar-contacto'];
        sidebarTitles.forEach((el, i) => {
            if (sidebarKeys[i] && labels[sidebarKeys[i]]) el.textContent = labels[sidebarKeys[i]];
        });

        // Update cv section titles
        const sectionTitles = document.querySelectorAll('.cv-section-title-text');
        const sectionKeys = ['cv-section-edu', 'cv-section-exp', 'cv-section-skills'];
        sectionTitles.forEach((el, i) => {
            if (sectionKeys[i] && labels[sectionKeys[i]]) el.textContent = labels[sectionKeys[i]];
        });

        // Update other UI elements
        const uiMap = {
            'button[onclick*="tab-portfolio"]': labels['tab-portfolio-label'],
            'button[onclick*="tab-curriculo"]': labels['tab-curriculo-label'],
            '.filter-btn[data-filter="all"]': labels['filter-all'],
            '.filter-btn[data-filter="Impressão 3D"]': labels['filter-3d'],
            '.filter-btn[data-filter="Render"]': labels['filter-render'],
            '.filter-btn[data-filter="Venda"]': labels['filter-venda'],
            '.filter-btn[data-filter="Layout"]': labels['filter-layout'],
            '.museum-footer-tagline': labels['footer-tagline'],
            '.portfolio-footer p': labels['footer-copy'],
            '.cv-print-btn': labels['print-btn'],
        };

        Object.entries(uiMap).forEach(([sel, text]) => {
            const el = document.querySelector(sel);
            if (el && text) el.textContent = text;
        });

        // Project "Ver Projeto" buttons
        document.querySelectorAll('.card-button').forEach(btn => {
            btn.textContent = labels['btn-ver-projeto'];
        });
    }

    // ── Show / hide loading overlay ───────────────────────────────────────────
    function setLoading(visible, lang) {
        let overlay = document.getElementById('i18n-loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'i18n-loading-overlay';
            overlay.innerHTML = `
                <div class="i18n-spinner"></div>
                <span id="i18n-loading-text">A traduzir…</span>
            `;
            document.body.appendChild(overlay);
        }
        if (visible) {
            const label = UI_LABELS[lang]?.translating || 'Translating…';
            document.getElementById('i18n-loading-text').textContent = label;
            overlay.classList.add('visible');
        } else {
            overlay.classList.remove('visible');
        }
    }

    // ── Main language switch function ─────────────────────────────────────────
    window.switchLang = async function(lang) {
        if (lang === currentLang) return;

        // Update active button state
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });

        // Always apply UI labels instantly
        applyUILabels(lang);

        const nodes = getTranslatableNodes();

        if (lang === 'pt') {
            // Restore originals — no API call needed
            restoreOriginals(nodes);
            // Re-apply PT UI labels (already done above)
        } else {
            // Try cache first
            const fromCache = applyCachedTranslation(nodes, lang);
            if (!fromCache) {
                // Save originals before first translation
                restoreOriginals(nodes); // ensure we start from PT
                const freshNodes = getTranslatableNodes();
                saveOriginals(freshNodes);
                setLoading(true, lang);
                try {
                    await translateNodes(freshNodes, lang);
                } finally {
                    setLoading(false, lang);
                }
            }
        }

        currentLang = lang;

        // Update html lang attribute
        const langMap = { pt: 'pt-BR', en: 'en', es: 'es' };
        document.documentElement.lang = langMap[lang] || lang;

        // Persist chosen language
        try { localStorage.setItem('portfolio_lang', lang); } catch(e) {}
    };

    // ── Init on DOMContentLoaded ──────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        // Try restoring last language choice
        let savedLang = 'pt';
        try { savedLang = localStorage.getItem('portfolio_lang') || 'pt'; } catch(e) {}

        // Save originals right away (before any translation)
        const nodes = getTranslatableNodes();
        saveOriginals(nodes);

        if (savedLang !== 'pt') {
            switchLang(savedLang);
        }
    });
})();
