from flask import Flask, request, jsonify, send_file, render_template
import os
import zipfile
import shutil
import face_recognition
from PIL import Image

app = Flask(__name__)

# Set up temporary directories for uploads and outputs
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/output_matches"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Configuration for the app
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limit file size to 16MB

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
    OUTPUT_FOLDER = app.config['OUTPUT_FOLDER']

    if "user_image" not in request.files or "folder_zip" not in request.files:
        return jsonify({"error": "Please upload both the user image and a zipped folder of images."}), 400

    user_image = request.files["user_image"]
    user_image_path = os.path.join(UPLOAD_FOLDER, "user_image.jpg")
    user_image.save(user_image_path)

    folder_zip = request.files["folder_zip"]
    folder_zip_path = os.path.join(UPLOAD_FOLDER, "folder.zip")
    folder_zip.save(folder_zip_path)

    extracted_folder = os.path.join(UPLOAD_FOLDER, "extracted_folder")
    os.makedirs(extracted_folder, exist_ok=True)

    with zipfile.ZipFile(folder_zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_folder)

    try:
        matching_images = find_matching_images(user_image_path, extracted_folder, OUTPUT_FOLDER)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    result_zip_path = os.path.join(OUTPUT_FOLDER, "matching_images.zip")
    with zipfile.ZipFile(result_zip_path, "w") as zipf:
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for file in files:
                if file != "matching_images.zip":
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), OUTPUT_FOLDER))

    shutil.rmtree(extracted_folder)
    os.remove(folder_zip_path)

    return send_file(result_zip_path, as_attachment=True, download_name="matching_images.zip")

def find_matching_images(user_image_path, folder_path, output_folder):
    print("Loading user image...")
    user_image = face_recognition.load_image_file(user_image_path)
    user_face_encoding = face_recognition.face_encodings(user_image)

    if not user_face_encoding:
        raise ValueError("No face found in the user's image. Please use a valid image with a visible face.")

    user_face_encoding = user_face_encoding[0]
    matching_images = []
    os.makedirs(output_folder, exist_ok=True)

    print("Scanning folder for matching images...")
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not filename.lower().endswith(("png", "jpg", "jpeg")):
            continue

        try:
            candidate_image = face_recognition.load_image_file(file_path)
            candidate_face_encodings = face_recognition.face_encodings(candidate_image)

            if not candidate_face_encodings:
                continue

            for candidate_face_encoding in candidate_face_encodings:
                match = face_recognition.compare_faces([user_face_encoding], candidate_face_encoding, tolerance=0.6)
                if match[0]:
                    matching_images.append(file_path)
                    output_path = os.path.join(output_folder, filename)
                    image = Image.open(file_path)
                    image.save(output_path)
                    break
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    return matching_images

if __name__ == "__main__":
    app.run(debug=True)