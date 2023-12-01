from flask import Flask, render_template, request, jsonify, Response, session
from werkzeug.utils import secure_filename
from camera_people_detection import VideoPeopleDetection
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Needed to use sessions


# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

last_uploaded_filename = None
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(message='No file part'), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(message='No selected file'), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['uploaded_file_path'] = file_path  # Save the file path to the session
        return jsonify(message=f'File {filename} uploaded successfully'), 200
    else:
        return jsonify(message='File type not allowed'), 400

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame
               + b'\r\n\r\n')
        
@app.route("/use_webcam")
def use_webcam():
    camera = VideoPeopleDetection()
    camera.use_webcam()
    return Response(gen(camera),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

        
@app.route("/video_feed")
def video_feed():
    # Check if a file has been uploaded and saved in the session
    if 'uploaded_file_path' in session:
        # Initialize VideoPeopleDetection with the uploaded file path
        return Response(gen(VideoPeopleDetection(session['uploaded_file_path'])),
                        mimetype="multipart/x-mixed-replace; boundary=frame")
    else:
        # If no file has been uploaded, return a default message or empty feed
        return "No video uploaded yet", 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
