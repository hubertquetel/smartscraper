from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from readability import Document
import markdownify

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

        # Attendre que le contenu principal soit chargé
        try:
            page.wait_for_selector('.fund-details-section', timeout=10000)
        except:
            print("⚠️ Le contenu n’a pas été trouvé à temps.")

        html = page.locator('main').inner_html()
        browser.close()

        # Extraction du contenu principal en markdown
        doc = Document(html)
        simplified_html = doc.summary()
        markdown = markdownify.markdownify(simplified_html, heading_style="ATX")

        return jsonify({'url': url, 'markdown': markdown})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
