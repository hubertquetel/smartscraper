from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright
from readability import Document
import markdownify
import tempfile
import os

app = Flask(__name__)

def init_browser(p):
    return p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled"
        ]
    )

def setup_page(context, url):
    page = context.new_page()
    page.goto(url, wait_until="networkidle")

    # Accepter les cookies si le bouton est détecté
    try:
        page.locator("button:has-text('Accepter')").first.click(timeout=3000)
    except:
        pass  # pas de popup cookies

    # Scroll jusqu'en bas pour forcer le chargement d’éléments lazy
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(3000)  # attendre 3s pour laisser finir les chargements
    return page

@app.route('/scrape')
def scrape():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    with sync_playwright() as p:
        browser = init_browser(p)
        context = browser.new_context(
            viewport={"width": 1280, "height": 1920},
            device_scale_factor=2,
            is_mobile=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = setup_page(context, url)

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
        browser = init_browser(p)
        context = browser.new_context(
            viewport={"width": 1280, "height": 1920},
            device_scale_factor=2,
            is_mobile=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = setup_page(context, url)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            page.screenshot(path=tmp.name, full_page=fullpage)
            tmp_path = tmp.name

        browser.close()

        return send_file(tmp_path, mimetype='image/png', as_attachment=False)

@app.route('/')
def index():
    return '''
        <h2>SmartScraper API</h2>
        <ul>
            <li><code>/scrape?url=https://example.com</code> → retourne markdown JSON</li>
            <li><code>/screenshot?url=https://example.com&full=true</code> → retourne une image PNG</li>
        </ul>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
