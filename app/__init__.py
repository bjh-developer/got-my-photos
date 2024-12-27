from flask import Flask
import os

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
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

    # Import and register the routes
    from .routes import register_routes
    register_routes(app)

    return app
