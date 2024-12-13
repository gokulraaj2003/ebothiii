from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from gtts import gTTS  # Import gTTS for Text-to-Speech conversion
from src.gradio_demo import SadTalker
import uuid
import time

app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set static folder for storing generated videos
STATIC_FOLDER = './static/generated_videos'
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Ensure files and form data are included in the request
        if 'source_image' not in request.files:
            return jsonify({"status": "error", "message": "Source image is missing"}), 400
        if 'text' not in request.form:
            return jsonify({"status": "error", "message": "Text is missing"}), 400

        # Retrieve and save uploaded image
        source_image = request.files['source_image']
        source_image_path = os.path.join(UPLOAD_FOLDER, secure_filename(source_image.filename))
        source_image.save(source_image_path)

        # Retrieve text from form
        text = request.form['text']

        # Convert text to speech (audio)
        audio_filename = "generated_audio.mp3"
        audio_file_path = os.path.join(UPLOAD_FOLDER, audio_filename)
        tts = gTTS(text=text, lang='en')  # Language can be set as per requirement
        tts.save(audio_file_path)

        # Retrieve additional parameters
        preprocess = request.form.get('preprocess', 'crop')  # Default is 'crop'
        still_mode = request.form.get('still_mode', 'false').lower() == 'true'
        use_enhancer = request.form.get('use_enhancer', 'false').lower() == 'true'
        batch_size = int(request.form.get('batch_size', 1))
        size = int(request.form.get('size', 256))
        pose_style = int(request.form.get('pose_style', 0))
        exp_scale = float(request.form.get('exp_scale', 1.0))
        use_blink = request.form.get('use_blink', 'true').lower() == 'true'

        # Initialize SadTalker
        sad_talker = SadTalker()

        # Call the test method
        result_path = sad_talker.test(
            source_image=source_image_path,
            driven_audio=audio_file_path,
            preprocess=preprocess,
            still_mode=still_mode,
            use_enhancer=use_enhancer,
            batch_size=batch_size,
            size=size,
            pose_style=pose_style,
            exp_scale=exp_scale,
            use_blink=use_blink
        )

        # Generate a unique filename using UUID and timestamp
        unique_filename = f"video_{uuid.uuid4().hex}_{int(time.time())}.mp4"
        result_file_path = os.path.join(STATIC_FOLDER, unique_filename)

        # Move the generated video to static folder
        os.rename(result_path, result_file_path)  # Assuming result_path is the generated video file path

        # Return the video path for frontend to display
        video_url = f"/static/generated_videos/{unique_filename}"
        return jsonify({"status": "success", "video_url": video_url})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run( host="0.0.0.0", port=5000, debug=True)
