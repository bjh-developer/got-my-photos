"""Got My Photos? Version 1.0.0"""

import streamlit as st
import face_recognition
import zipfile
import os
from io import BytesIO
from PIL import Image, ExifTags


# Web page configuration
st.set_page_config(
    page_title="Got My Photos?",
    page_icon="📸",
    layout="centered"
)


def rotate_image(image):
    """
    Rotate the image based on EXIF orientation metadata if needed.
    This function checks the EXIF metadata of the given image to determine its orientation.
    If the image is not in 'RGB' mode, it converts it to 'RGB'. It then reads the EXIF
    orientation tag and rotates the image accordingly:
    - 180 degrees if the orientation is 3
    - 270 degrees if the orientation is 6
    - 90 degrees if the orientation is 8
    The rotated image is saved as a JPEG file in memory and returned as a BytesIO object.
    Args:
        image (PIL.Image.Image): The image to be rotated.
    Returns:
        BytesIO: The rotated image saved as a JPEG file in memory.
    Raises:
        AttributeError: If the image does not have EXIF metadata.
        KeyError: If the EXIF metadata does not contain the orientation tag.
        IndexError: If the orientation tag is not found in the EXIF metadata.
    """

    try:
        if image.mode!='RGB':
            image = image.convert('RGB')

        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break

        exif = image._getexif()

        if exif and orientation in exif:
            if exif[orientation]==3:
                image = image.rotate(180, expand=True)
            elif exif[orientation]==6:
                image = image.rotate(270, expand=True)
            elif exif[orientation]==8:
                image = image.rotate(90, expand=True)

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        return img_byte_arr
    
    except (AttributeError, KeyError, IndexError):
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return img_byte_arr


def process_images(target_image, image_files, tolerance, updates_expand, progress_bar, curr_progress, max_progress):
    """
    Processes a target image and a list of image files to find matches based on facial recognition.
    Args:
        target_image (UploadedFile): The uploaded target image file.
        image_files (list): A list of uploaded image files to be processed.
        tolerance (float): The tolerance level for face matching. Lower values mean stricter matching.
    Returns:
        dict: A dictionary of matched image files with their names as keys.
    Raises:
        Exception: If there is an error processing the target image or any of the uploaded images.
    Notes:
        - The function uses the `face_recognition` library to encode and compare faces.
        - The `rotate_image` function is used to correct the orientation of images before processing.
        - The function displays error and warning messages using the `streamlit` library (`st`).
        - If no face is detected in the target image, an error message is displayed and an empty dictionary is returned.
        - For each uploaded image, if a matching face is found, the image is added to the `matched_images` dictionary.
        - If no face is detected or if the face does not match, appropriate warning messages are displayed.
    """

    matched_images = {}

    # Load the target image and encode its face
    target_image = rotate_image(Image.open(target_image))
    try:
        target_image = face_recognition.load_image_file(target_image)
        target_encoding = face_recognition.face_encodings(target_image, num_jitters=100)

        if not target_encoding:
            st.error("No face detected in your selfie (photo from step 1). Please upload a clear photo.")
            return matched_images
        
        target_encoding = target_encoding[0]
    
    except Exception as e:
        st.error(f"Error processing target image: {e}")
        return matched_images

    # Loop through uploaded images to find matches
    for image_file in image_files:
        name = image_file.name
        image_file = rotate_image(Image.open(image_file))

        try:
            image = face_recognition.load_image_file(image_file)
            encodings = face_recognition.face_encodings(image)

            if encodings:  # Check if faces were found
                found = False
                for encoding in encodings:
                    match = face_recognition.compare_faces([target_encoding], encoding, tolerance=tolerance)
                    if match[0]:
                        matched_images[name] = image_file
                        found = True    
                if found:
                    updates_expand.warning(f"✅ Correct face detected in {name}. Saving...")
                else:
                    updates_expand.warning(f"❌ Wrong face detected in {name}. Skipping...")

            else:
                updates_expand.warning(f"🤷‍♂️ No face detected in {name}. Skipping...")
            
            # Update progress bar
            curr_progress += 1
            progress_bar.progress(curr_progress/max_progress)

        except Exception as e:
            st.error(f"Error processing image {name}: {e}")

    return matched_images


# Streamlit App UI
st.toast("This webapp does not store any images or data. All processing is done locally on your device.", icon="🔒")
intro_container = st.container()
with intro_container:
    st.title("📸 Got My Photos?")
    st.write("Received many photos but was unable to find which ones you're in. Upload a photo of yourself and the many photos. The web app will detect and extract photos containing your face.")
    story_expand = st.expander("Story behind this webapp...", icon=":material/info:")
    story_expand.write("By Joon Hao: The inspiration behind this webapp comes from my time in Hwa Chong Institution (College).")
    story_expand.write("During my time at Hwa Chong Institution (College)\
                       , I always looked forward to receiving the photographs\
                        taken by Studio Ardent (a Service and Enrichment CCA that\
                        contributes in a great way to major school events\
                        through its photography, videography and PA/AVA services)\
                        after any key events."
                    )
    story_expand.write("However, I found it tedious to look through the hundreds\
                        of wonderful photographs by Studio Ardent in search of\
                        images with me inside to download.")
    story_expand.write("That's when I decided to create the web app\
                        'Got My Photos?' to alleviate this problem.")
    story_expand.write("'Got My Photos?' aims to help HCI (College) students automate\
                        the task of sieving out images of themselves taken by Studio Ardent.")
    story_expand.write("Just in 3 simple steps, they can download Studio Ardent\
                        images that have their face in them!")
    tutorial_expand = st.expander("How to use this webapp?", expanded=False)
    with tutorial_expand:
        st.write("1. Upload a clear photo of your face. Ensure no other faces are in the photo.")
        st.write("2. Upload a set of random photos. You can drag and drop folders of photos.")
        st.write("3. Click the 'Find Matching Photos' button and wait for the results.")
        st.write("4. Download the ZIP file containing the matching photos.")


st.divider()

steps_container = st.container()
with steps_container:
    # Upload target image
    st.header("Step 1: Upload Your Photo")
    target_image = st.file_uploader("Upload a clear photo of your face (tip: take a selfie with a clean background):", type=["jpg", "jpeg", "png"])

    # Upload random photos
    st.header("Step 2: Upload Photos to Search")
    photo_files = st.file_uploader("Upload multiple photos:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    # Process and download results
    st.header("Step 3: Click, Wait and Download!")
    st.info("It may take a while to process the images.\
             You may leave this running in the background.\
             Accuracy varies, please submit a feedback form if it is highly inaccurate.")
    if st.button("Find Matching Photos"):
        if target_image and photo_files:
            with st.spinner("Processing images. Please wait..."):
                curr_progress = 0
                max_progress = len(photo_files)
                progress_bar = st.progress(curr_progress, text="Progress bar:")
                updates_expand = st.expander("Updates", icon="⏳")

                # Process the images
                matched_images = process_images(target_image, photo_files, 0.43, updates_expand, progress_bar, curr_progress, max_progress)

                if matched_images:
                    st.balloons()
                    st.success(f"Found {len(matched_images)} matching photo." if len(matched_images)==1 else f"Found {len(matched_images)} matching photos.")

                    # Create a ZIP file to download
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                        for name in matched_images:
                            matched_images[name].seek(0)
                            zip_file.writestr(name, matched_images[name].read())

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


st.divider()

feedback_container = st.container()
with feedback_container:
    # Feedback
    st.header("Have Feedback?")
    st.write("If you have any feedback, suggestions, or bug reports, feel free to share them here.")
    st.link_button("Share Feedback", "https://forms.gle/G4QKeWFLEi8JqpoH7")


st.divider()

info_container = st.container()
with info_container:
    # More information
    about_tab, privacy_tab, version_tab = st.tabs(["About", "Privacy", "Version History"])
    with about_tab:
        st.write("Created by [Bek Joon Hao](https://www.linkedin.com/in/bek-joon-hao/), this webapp uses facial recognition to find photos\
                containing your face from a set of random photos. It is built with Streamlit\
                and the face_recognition library.")
        st.write("For the full story behind this webapp, check out the 'Story behind this webapp' toggle above!")
        st.write("Even though the target audience is HCI (College) students, anyone can feel free\
                to use this webapp to find photos with their face in them.")
        st.write("The source code is available on [GitHub](https://github.com/bjh-developer/got-my-photos)")
        st.warning("Disclaimer: This webapp is not affiliated with Studio Ardent or Hwa Chong Institution (College).\
                    This is a personal project created to bring convenience to people.\
                    No money is earned from this webapp.")
    with privacy_tab:
        st.write("This webapp does not store any images or data. All processing is done locally on your device.")
        st.write("For more information, please refer to the [Streamlit Privacy Policy](https://streamlit.io/privacy-policy).")
    with version_tab:
        st.write("Currently: Version 1.0.0")
        version_history_expand = st.expander("Version History", expanded=False)
        with version_history_expand:
            st.write("**Version 1.0.0** (12 Jan 2025): Initial release of the webapp.")


st.divider()

footer_container = st.container()
with footer_container:
    # Footer
    st.write("Made with ❤️ by [Bek Joon Hao](https://www.linkedin.com/in/bek-joon-hao/)")
    st.write("© 2025 Got My Photos?. All rights reserved.")

