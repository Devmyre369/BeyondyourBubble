
from cloudinary import config as cloudinary_config
from cloudinary import uploader
from django.conf import settings
from PIL import Image, UnidentifiedImageError


class ProfileImageError(Exception):
    """Raised when a profile image cannot be validated or uploaded."""


IMAGE_CONFIG = {
    "profile_picture": {
        "max_size": 5 * 1024 * 1024,
        "public_id": "profile_picture",
    },
    "cover_image": {
        "max_size": 10 * 1024 * 1024,
        "public_id": "cover_image",
    },
}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


def configure_cloudinary():
    """Configure the Cloudinary SDK using backend environment settings."""

    cloudinary_config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def validate_image_file(uploaded_file, image_type):
    """Validate the uploaded image's size, MIME type, and actual format."""

    if image_type not in IMAGE_CONFIG:
        raise ProfileImageError("Invalid image type.")

    if not uploaded_file:
        raise ProfileImageError("Please select an image.")

    config = IMAGE_CONFIG[image_type]

    if uploaded_file.size > config["max_size"]:
        max_size_mb = config["max_size"] // (1024 * 1024)
        raise ProfileImageError(
            f"Image size must not exceed {max_size_mb} MB."
        )

    if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ProfileImageError(
            "Only JPG, JPEG, PNG, and WEBP images are allowed."
        )

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image_format = image.format
        image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise ProfileImageError(
                "Only JPG, JPEG, PNG, and WEBP images are allowed."
            )

    except (UnidentifiedImageError, OSError, ValueError):
        raise ProfileImageError("The uploaded file is not a valid image.")

    finally:
        uploaded_file.seek(0)


def get_image_public_id(user_id, image_type):
    """Generate a stable Cloudinary public ID for a user's image."""

    if image_type not in IMAGE_CONFIG:
        raise ProfileImageError("Invalid image type.")

    image_name = IMAGE_CONFIG[image_type]["public_id"]

    return f"byb/profiles/{user_id}/{image_name}"


def upload_profile_image(user_id, image_type, uploaded_file):
    """Validate and upload a profile or cover image to Cloudinary."""

    validate_image_file(uploaded_file, image_type)
    configure_cloudinary()

    public_id = get_image_public_id(user_id, image_type)

    try:
        result = uploader.upload(
            uploaded_file,
            public_id=public_id,
            overwrite=True,
            invalidate=True,
            resource_type="image",
        )

        secure_url = result.get("secure_url")

        if not secure_url:
            raise ProfileImageError(
                "Cloudinary did not return an image URL."
            )

        return secure_url

    except ProfileImageError:
        raise
    except Exception as exc:
        raise ProfileImageError(
            "Image upload failed. Please try again."
        ) from exc


def delete_profile_image(user_id, image_type):
    """Delete a user's profile or cover image from Cloudinary."""

    configure_cloudinary()

    public_id = get_image_public_id(user_id, image_type)

    try:
        return uploader.destroy(
            public_id,
            invalidate=True,
            resource_type="image",
        )

    except Exception as exc:
        raise ProfileImageError(
            "Image deletion failed. Please try again."
        ) from exc
