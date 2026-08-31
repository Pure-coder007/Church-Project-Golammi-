import os
import secrets
from io import BytesIO
from PIL import Image
from flask import current_app, has_request_context, url_for
import re
from datetime import datetime
from werkzeug.utils import secure_filename

try:
    import cloudinary
    import cloudinary.uploader
except ImportError:  # pragma: no cover
    cloudinary = None


def cloudinary_enabled():
    return bool(
        cloudinary
        and current_app.config.get("CLOUDINARY_CLOUD_NAME")
        and current_app.config.get("CLOUDINARY_API_KEY")
        and current_app.config.get("CLOUDINARY_API_SECRET")
    )


def configure_cloudinary():
    if not cloudinary_enabled():
        return False

    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    return True


def is_remote_media(path):
    return isinstance(path, str) and path.startswith(("http://", "https://"))


def media_url(path):
    if not path:
        return ""
    if is_remote_media(path):
        return path
    if has_request_context():
        return url_for("static", filename=f"uploads/{path}")
    return path


def _strip_extension(value):
    root, ext = os.path.splitext(value)
    return root if ext else value


def _extract_cloudinary_identity(path):
    if not is_remote_media(path) or "res.cloudinary.com" not in path:
        return None, None

    match = re.search(r"/(image|video|raw)/upload/(?:.*?/)?v\d+/(.+)$", path)
    if not match:
        match = re.search(r"/(image|video|raw)/upload/(.+)$", path)
    if not match:
        return None, None

    resource_type = match.group(1)
    public_id = match.group(2).split("?")[0]
    if resource_type in {"image", "video"}:
        public_id = _strip_extension(public_id)

    return public_id, resource_type


def delete_media_asset(path):
    if not path:
        return

    if is_remote_media(path):
        if not configure_cloudinary():
            return
        public_id, resource_type = _extract_cloudinary_identity(path)
        if public_id and resource_type:
            cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=True)
        return

    local_path = os.path.join(current_app.config["UPLOAD_FOLDER"], path)
    if os.path.exists(local_path):
        os.remove(local_path)


def save_picture(file, folder="gallery", size=(800, 800)):
    """Save uploaded image with proper resizing and naming"""
    if not file:
        return None

    if not allowed_file(file.filename):
        raise ValueError("Unsupported image format.")

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(secure_filename(file.filename))
    picture_fn = random_hex + f_ext
    normalized_ext = (f_ext or ".jpg").lower()

    output_size = size
    i = Image.open(file)
    i.verify()
    file.stream.seek(0)
    i = Image.open(file)
    i.thumbnail(output_size)

    if configure_cloudinary():
        image_format = "JPEG" if normalized_ext in {".jpg", ".jpeg"} else normalized_ext.lstrip(".").upper()
        if image_format == "JPG":
            image_format = "JPEG"

        if image_format == "JPEG" and i.mode != "RGB":
            i = i.convert("RGB")
        elif i.mode not in ("RGB", "RGBA"):
            i = i.convert("RGB")

        buffer = BytesIO()
        save_kwargs = {"format": image_format}
        if image_format in {"JPEG", "WEBP"}:
            save_kwargs.update({"optimize": True, "quality": 85})
        i.save(buffer, **save_kwargs)
        buffer.seek(0)

        result = cloudinary.uploader.upload(
            buffer,
            folder=folder.strip("/"),
            public_id=_strip_extension(picture_fn),
            resource_type="image",
            overwrite=True,
        )
        return result.get("secure_url")

    picture_path = os.path.join(current_app.config["UPLOAD_FOLDER"], folder, picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    i.save(picture_path, optimize=True, quality=85)

    return os.path.join(folder, picture_fn)


def save_file(file, folder="files"):
    """Save uploaded file with proper naming"""
    if not file:
        return None

    if not allowed_file(file.filename):
        raise ValueError("Unsupported file format.")

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(secure_filename(file.filename))
    file_fn = random_hex + f_ext

    if configure_cloudinary():
        file.stream.seek(0)
        result = cloudinary.uploader.upload(
            file.stream,
            folder=folder.strip("/"),
            public_id=file_fn,
            resource_type="raw",
            overwrite=True,
            use_filename=False,
        )
        return result.get("secure_url")

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
