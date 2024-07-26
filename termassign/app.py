from flask import Flask, redirect, render_template_string, request, url_for
import boto3
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)

S3_BUCKET = 'input-textract-jahnavi'

s3_client = boto3.client('s3')
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Cute Image Upload to S3</title>
    <!-- Bootstrap CSS CDN -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&family=Indie+Flower&display=swap" rel="stylesheet">
    <style>
        html, body {
            height: 100%;
            margin: 0;
            background-color: #f0f9ff;
            font-family: 'Roboto', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background-color: #ffffff;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            width: auto;
        }
        .header {
            background-color: #ffddf4;
            color: #333;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            font-family: 'Indie Flower', cursive;
        }
        h1, h2 {
            font-family: 'Indie Flower', cursive;
        }
        .btn-primary {
            background-color: #ff85a2;
            border: none;
            border-radius: 20px;
        }
        .btn-primary:hover {
            background-color: #ff65a3;
        }
        .custom-file-input {
            border-radius: 20px;
        }
        .custom-file-label {
            background-color: #ffddf4;
            border-radius: 20px;
        }
        .footer {
            text-align: center;
            padding: 20px;
            font-family: 'Indie Flower', cursive;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Upload Your Cute Images to S3!</h1>
        <p>Join us on a fluffy cloud adventure and store your precious documents safely in the sky.</p>
    </div>
    <h2>Try It Out 🚀</h2>
    <p>Choose an image to upload and watch the magic happen.</p>
    <form method="post" action="/upload" enctype="multipart/form-data">
        <div class="custom-file mb-3">
            <input type="file" class="custom-file-input" name="image_file" accept="image/*" id="image_file">
            <label class="custom-file-label" for="image_file">Select file...</label>
        </div>
        <button type="submit" class="btn btn-primary">Upload to Cloud</button>
    </form>
    <div class="footer">
        <p>Made with ❤️ and a sprinkle of cloud dust.</p>
    </div>
</div>
<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"></script>
<script>
$(".custom-file-input").on("change", function() {
  var fileName = $(this).val().split("\\\\").pop();
  $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});
</script>
</body>
</html>
"""

@app.route('/')
def index():
    """Renders the main page with the upload form."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    if 'image_file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['image_file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and file.filename.endswith(tuple(['.png', '.jpg', '.jpeg'])):
        filename = secure_filename(file.filename)
        try:
            s3_client.upload_fileobj(file.stream, S3_BUCKET, filename)
            # Redirect to a new URL for processing
            return redirect(url_for('process_file', filename=filename))
        except Exception as e:
            return str(e)
    return redirect(url_for('index'))

@app.route('/process_file/<filename>')
def process_file(filename):
    try:
        api_gateway_url = get_api_url('JahnaviAPIGateway', 'prod')
        api_endpoint = f"{api_gateway_url}/textract-polly"
        headers = {'Content-Type': 'application/json'}
        data = {"input_bucket": S3_BUCKET, "input_bucket_file": filename}
        response = requests.post(api_endpoint, json=data, headers=headers)
        
        if response.status_code == 200:
            return render_template_string(SUCCESS_TEMPLATE)
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
