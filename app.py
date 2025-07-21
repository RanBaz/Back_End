import logging
from flask import Flask, request, jsonify
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import uuid
import mimetypes

# ------------------- Setup Logging -------------------
LOG_FILE = 'app.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,  # Can be changed to DEBUG for more verbose logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Also show logs in the console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# ------------------- Initialize Flask -------------------
app = Flask(__name__)

# Create downloads folder if not exists
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ------------------- File Download Function -------------------
def download_file(url):
    try:
        logging.info(f"Starting download for: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        # If no filename or extension, use content-type to guess
        if not filename or '.' not in filename:
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            ext = mimetypes.guess_extension(content_type) or '.bin'
            filename = f"{uuid.uuid4()}{ext}"

        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        logging.info(f"Downloaded and saved to: {filepath}")

        return {
            'url': url,
            'status': 'success',
            'filename': filename,
            'saved_path': os.path.abspath(filepath)
        }

    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")
        return {
            'url': url,
            'status': 'error',
            'error': str(e)
        }

# ------------------- API Route -------------------
@app.route('/download', methods=['POST'])
def download_files():
    data = request.get_json()
    urls = data.get('urls', [])

    if not urls or not isinstance(urls, list):
        logging.warning("Invalid input: missing or incorrect 'urls' format")
        return jsonify({'error': 'Please provide a list of URLs under "urls"'}), 400

    logging.info(f"Received {len(urls)} URLs for download")
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(download_file, urls))

    return jsonify({'results': results})

# ------------------- Run App -------------------
if __name__ == '__main__':
    logging.info("Starting Flask app on http://127.0.0.1:5000")
    app.run(debug=True)
