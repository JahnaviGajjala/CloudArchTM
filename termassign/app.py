from flask import Flask, redirect, render_template_string, request, url_for
import boto3
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)

# Update the S3 bucket name to reflect the bucket for storing input images
S3_BUCKET = 'input-rekognition-jahnavi'

s3_client = boto3.client('s3')
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Image Upload to S3</title>
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
        <h1>Upload Your Images to S3!</h1>
        <p>Join us on a fluffy cloud adventure and store your precious images safely in the sky.</p>
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

SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success</title>
</head>
<body>
    <p>IMAGE UPLOADED AND AUDIO FILE GENERATED</p>
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
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        try:
            s3_client.upload_fileobj(file.stream, S3_BUCKET, filename)
            api_gateway_url = get_api_url('JahnaviAPIGateway', 'prod')
            api_endpoint = f"{api_gateway_url}/rekognition-polly"
            headers = {'Content-Type': 'application/json'}
            data = {"input_bucket": S3_BUCKET, "input_bucket_file": filename}
            response = requests.post(api_endpoint, json=data, headers=headers)
            
            if response.status_code == 200:
                return render_template_string(SUCCESS_TEMPLATE)
            return str(response.content)
        except Exception as e:
            return str(e)
    
    return redirect(url_for('index'))

def allowed_file(filename):
    """Check if the file type is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif']

def get_api_url(api_name, stage_name):
    """Retrieve the API URL for a given API Gateway name and stage."""
    region = 'us-east-1'
    api_gateway_client = boto3.client('apigateway', region_name=region)
    response = api_gateway_client.get_rest_apis()
    
    for item in response['items']:
        if item['name'] == api_name:
            api_id = item['id']
            return f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
    
    raise ValueError(f"API Gateway '{api_name}' not found.")

if __name__ == '__main__':
    app.run(debug=True)
