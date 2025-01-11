import streamlit as st
import face_recognition
import zipfile
import os
from io import BytesIO
from PIL import Image

# Helper function to process images
def process_images(target_image, image_files, tolerance=0.5):
    matched_images = []

    # Load the target image and encode its face
    try:
        target_image = face_recognition.load_image_file(target_image)
        target_encoding = face_recognition.face_encodings(target_image)
        if not target_encoding:
            st.error("No face detected in the target image. Please upload a clear photo.")
            return matched_images
        target_encoding = target_encoding[0]
    except Exception as e:
        st.error(f"Error processing target image: {e}")
        return matched_images

    # Loop through uploaded images to find matches
    for image_file in image_files:
        try:
            image = face_recognition.load_image_file(image_file)
            encodings = face_recognition.face_encodings(image)

            if encodings:  # Check if faces were found
                found = False
                for encoding in encodings:
                    match = face_recognition.compare_faces([target_encoding], encoding, tolerance=tolerance)
                    if match[0]:
                        matched_images.append(image_file)
                        found = True    
                if found:
                    st.warning(f"Correct face detected in {image_file.name}. Saving...")
                else:
                    st.warning(f"Wrong face detected in {image_file.name}. Saving...")

            else:
                st.warning(f"No face detected in {image_file.name}. Skipping...")
        except Exception as e:
            st.error(f"Error processing image {image_file.name}: {e}")

    return matched_images

# Streamlit App UI
st.title("Face Recognition Photo Selector")
st.write("Upload a photo of yourself and a folder of random photos. The app will detect and extract photos containing your face.")

# Upload target image
st.header("Step 1: Upload Your Photo")
target_image = st.file_uploader("Upload a clear photo of your face:", type=["jpg", "jpeg", "png"])

# Upload random photos
st.header("Step 2: Upload Photos to Search")
photo_files = st.file_uploader("Upload multiple photos:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Process and download results
if st.button("Find Matching Photos"):
    if target_image and photo_files:
        with st.spinner("Processing images. Please wait..."):
            # Process the images
            matched_images = process_images(target_image, photo_files, tolerance=0.6)

            if matched_images:
                st.success(f"Found {len(matched_images)} matching photos.")

                # Create a ZIP file to download
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for image_file in matched_images:
                        image_name = os.path.basename(image_file.name)
                        image_file.seek(0)
                        zip_file.writestr(image_name, image_file.read())

                zip_buffer.seek(0)

                # Provide a download link
                st.download_button(
                    label="Download Matching Photos",
                    data=zip_buffer,
                    file_name="matching_photos.zip",
                    mime="application/zip",
                )
            else:
                st.warning("No matching photos found.")
    else:
        st.error("Please upload both your photo and a set of random photos.")
