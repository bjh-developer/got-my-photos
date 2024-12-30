from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import os
import zipfile
import shutil
import face_recognition
from PIL import Image
from pathlib import Path

app = FastAPI()

# Set up temporary directories for uploads and outputs
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/output_matches"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    template_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(template_path, "r") as file:
        return file.read()

@app.post("/upload")
def upload_files(user_image: UploadFile = File(...), folder_zip: UploadFile = File(...)):
    global UPLOAD_FOLDER, OUTPUT_FOLDER
    UPLOAD_FOLDER = Path(UPLOAD_FOLDER)
    OUTPUT_FOLDER = Path(OUTPUT_FOLDER)

    # Save the uploaded user image
    user_image_path = UPLOAD_FOLDER / "user_image.jpg"
    with user_image.file as f:
        user_image_path.write_bytes(f.read())

    # Save the uploaded zip file
    folder_zip_path = UPLOAD_FOLDER / "folder.zip"
    with folder_zip.file as f:
        folder_zip_path.write_bytes(f.read())

    # Extract the contents of the zip file
    extracted_folder = UPLOAD_FOLDER / "extracted_folder"
    extracted_folder.mkdir(exist_ok=True)

    with zipfile.ZipFile(folder_zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_folder)

    try:
        matching_images = find_matching_images(user_image_path, extracted_folder, OUTPUT_FOLDER)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Create a zip file of the matching images
    result_zip_path = OUTPUT_FOLDER / "matching_images.zip"
    with zipfile.ZipFile(result_zip_path, "w") as zipf:
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for file in files:
                if file != "matching_images.zip":
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(OUTPUT_FOLDER))

    # Clean up temporary files
    shutil.rmtree(extracted_folder)
    folder_zip_path.unlink()

    return FileResponse(result_zip_path, media_type="application/zip", filename="matching_images.zip")

def find_matching_images(user_image_path, folder_path, output_folder):
    print("Loading user image...")
    user_image = face_recognition.load_image_file(user_image_path)
    user_face_encoding = face_recognition.face_encodings(user_image)

    if not user_face_encoding:
        raise ValueError("No face found in the user's image. Please use a valid image with a visible face.")

    user_face_encoding = user_face_encoding[0]
    matching_images = []
    output_folder.mkdir(exist_ok=True)

    print("Scanning folder for matching images...")
    for filename in os.listdir(folder_path):
        file_path = folder_path / filename
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
                    output_path = output_folder / filename
                    image = Image.open(file_path)
                    image.save(output_path)
                    break
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    return matching_images

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
