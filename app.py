from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from readability import Document
import markdownify

app = Flask(__name__)

@app.route("/scrape", methods=["GET"])
def scrape():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        page.goto(url, timeout=60000)
        html = page.content()
        browser.close()

    doc = Document(html)
    content_html = doc.summary()
    markdown = markdownify.markdownify(content_html, heading_style="ATX")

    return jsonify({"url": url, "markdown": markdown})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
