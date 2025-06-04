from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright
import markdownify
import tempfile
import os

app = Flask(__name__)

def create_context(p):
    return p.chromium.launch(headless=True, args=["--no-sandbox"]).new_context(
        viewport={"width": 1280, "height": 1600},
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
    )

def slow_scroll(page, step=500, pause=500):
    page_height = page.evaluate("() => document.body.scrollHeight")
    for pos in range(0, page_height, step):
        page.evaluate(f"window.scrollTo(0, {pos})")
        page.wait_for_timeout(pause)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)

@app.route('/scrape')
def scrape():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    with sync_playwright() as p:
        context = create_context(p)
        page = context.new_page()
        page.goto(url, wait_until="networkidle")

        # Scroll doucement toute la page pour forcer le rendu complet
        slow_scroll(page)

        try:
            page.wait_for_selector("main", timeout=10000)
            html = page.locator("main").inner_html()
        except:
            html = page.content()

        context.close()

        markdown = markdownify.markdownify(html, heading_style="ATX")
        return jsonify({'url': url, 'markdown': markdown})

@app.route('/screenshot')
def screenshot():
    url = request.args.get('url')
    fullpage = request.args.get('full', 'true').lower() == 'true'

    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    with sync_playwright() as p:
        context = create_context(p)
        page = context.new_page()
        page.goto(url, wait_until="networkidle")

        slow_scroll(page)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            page.screenshot(path=tmp.name, full_page=fullpage)
            tmp_path = tmp.name

        context.close()

        return send_file(tmp_path, mimetype='image/png', as_attachment=False)

@app.route('/')
def index():
    return '''
        <h2>🧠 SmartScraper API</h2>
        <ul>
            <li><code>/scrape?url=https://example.com</code> → retourne du Markdown propre</li>
            <li><code>/screenshot?url=https://example.com&full=true</code> → retourne une capture nette et complète</li>
        </ul>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
