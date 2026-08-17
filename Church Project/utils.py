import os
import secrets
from PIL import Image
from flask import current_app
import re
from datetime import datetime


def save_picture(file, folder="gallery", size=(800, 800)):
    """Save uploaded image with proper resizing and naming"""
    if not file:
        return None

    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(file.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder, picture_fn)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    # Resize and save image
    output_size = size
    i = Image.open(file)
    i.thumbnail(output_size)
    i.save(picture_path, optimize=True, quality=85)

    return os.path.join(folder, picture_fn)


def save_file(file, folder="files"):
    """Save uploaded file with proper naming"""
    if not file:
        return None

    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(file.filename)
    file_fn = random_hex + f_ext
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder, file_fn)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    return os.path.join(folder, file_fn)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def generate_slug(title):
    """Generate a URL-friendly slug from a title"""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def get_current_time():
    """Get current UTC datetime"""
    return datetime.utcnow()


def truncate_text(text, length=150):
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length] + "..."


def format_date(date_obj, format_str="%B %d, %Y"):
    """Format datetime object"""
    if not date_obj:
        return ""
    return date_obj.strftime(format_str)


def format_time(time_str):
    """Format time string (e.g., '14:30' to '2:30 PM')"""
    if not time_str:
        return ""
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except:
        return time_str
