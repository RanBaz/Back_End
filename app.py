# Import required libraries
from flask import Flask, request, jsonify  # Flask for API creation
import os  # For file/directory operations
import requests  # For downloading files via HTTP
from concurrent.futures import ThreadPoolExecutor  # For concurrent/multithreaded downloads
from urllib.parse import urlparse  # To parse URLs and extract filenames
import uuid  # To generate unique filenames when necessary
import mimetypes  # To guess file extensions from content types

# Initialize Flask app
app = Flask(__name__)

# Define folder where files will be downloaded
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Create folder if it doesn't exist

# Function to download a single file
def download_file(url):
    try:
        # Make a GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception if the status code is not 200

        # Parse the URL to extract the filename
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        # If filename is missing or has no extension
        if not filename or '.' not in filename:
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            ext = mimetypes.guess_extension(content_type) or '.bin'  # Guess extension or use .bin
            filename = f"{uuid.uuid4()}{ext}"  # Use UUID to create unique filename

        # Create the full path to save the file
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)

        # Write file content to disk
        with open(filepath, 'wb') as f:
            f.write(response.content)

        # Return success info
        return {
            'url': url,
            'status': 'success',
            'filename': filename,
            'saved_path': os.path.abspath(filepath)
        }
    except Exception as e:
        # If any error occurs, return the error message
        return {'url': url, 'status': 'error', 'error': str(e)}

# Define the API route for downloading multiple files
@app.route('/download', methods=['POST'])
def download_files():
    # Parse JSON from request body
    data = request.get_json()
    urls = data.get('urls', [])  # Extract list of URLs

    # Validate input
    if not urls or not isinstance(urls, list):
        return jsonify({'error': 'Please provide a list of URLs under "urls"'}), 400

    # Use ThreadPoolExecutor to download files concurrently
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(download_file, urls))

    # Return the results
    return jsonify({'results': results})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
