from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright
import markdownify
import tempfile
import os

app = Flask(__name__)

@app.route('/scrape')
def scrape():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # Supprime les bannières de cookies (iubenda, OneTrust, Didomi…)
        page.evaluate("""
            // iubenda
            const iubenda = document.getElementById('iubenda-cs-banner');
            if (iubenda) iubenda.remove();

            // autres bannières courantes
            ['cookie-banner', 'cookie-consent', 'onetrust-banner-sdk'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.remove();
            });

            ['didomi-popup', 'axeptio_overlay', 'cc-window'].forEach(cls => {
                document.querySelectorAll('.' + cls).forEach(e => e.remove());
            });
        """)

        # Essaye de scraper le contenu principal
        try:
            page.wait_for_selector("main", timeout=10000)
            html = page.locator("main").inner_html()
        except:
            html = page.content()

        browser.close()

        markdown = markdownify.markdownify(html, heading_style="ATX")
        return jsonify({'url': url, 'markdown': markdown})


@app.route('/screenshot')
def screenshot():
    url = request.args.get('url')
    fullpage = request.args.get('full', 'true').lower() == 'true'

    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # Supprime les bannières cookies
        page.evaluate("""
            const iubenda = document.getElementById('iubenda-cs-banner');
            if (iubenda) iubenda.remove();

            ['cookie-banner', 'cookie-consent', 'onetrust-banner-sdk'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.remove();
            });

            ['didomi-popup', 'axeptio_overlay', 'cc-window'].forEach(cls => {
                document.querySelectorAll('.' + cls).forEach(e => e.remove());
            });
        """)

        # Scroll léger pour déclencher les lazy images ou animations
        page.mouse.wheel(0, 200)
        page.wait_for_timeout(500)
        page.mouse.wheel(0, -100)
        page.wait_for_timeout(500)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            page.screenshot(path=tmp.name, full_page=fullpage)
            tmp_path = tmp.name

        browser.close()

        return send_file(tmp_path, mimetype='image/png', as_attachment=False)


@app.route('/')
def index():
    return '''
        <h2>🧠 SmartScraper API</h2>
        <ul>
            <li><code>/scrape?url=https://example.com</code> → retourne un contenu Markdown structuré dans du JSON</li>
            <li><code>/screenshot?url=https://example.com&full=true</code> → retourne une image PNG (capture de la page)</li>
        </ul>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
