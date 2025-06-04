from flask import Flask, request, jsonify, send_file
from playwright.sync_api import sync_playwright
from readability import Document
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

        try:
            page.wait_for_selector("main", timeout=10000)
            html = page.locator("main").inner_html()
        except:
            html = page.content()

        browser.close()

        # PAS DE readability, on markdownifie directement le HTML extrait
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

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            page.screenshot(path=tmp.name, full_page=fullpage)
            tmp_path = tmp.name

        browser.close()

        return send_file(tmp_path, mimetype='image/png', as_attachment=False)

# Optional index
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
