from cloudinary import config as cloudinary_config
from cloudinary import uploader
from django.conf import settings
from PIL import Image, UnidentifiedImageError


class HubImageError(Exception):
    """Raised when a Hub image cannot be validated or uploaded."""


IMAGE_CONFIG = {
    "logo": {
        "max_size": 5 * 1024 * 1024,
        "public_id": "logo",
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


def validate_hub_image(uploaded_file, image_type):
    """Validate the uploaded Hub image's size, MIME type, and format."""

    if image_type not in IMAGE_CONFIG:
        raise HubImageError("Invalid image type.")

    if not uploaded_file:
        raise HubImageError("Please select an image.")

    config = IMAGE_CONFIG[image_type]

    if uploaded_file.size > config["max_size"]:
        max_size_mb = config["max_size"] // (1024 * 1024)
        raise HubImageError(
            f"Image size must not exceed {max_size_mb} MB."
        )

    if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HubImageError(
            "Only JPG, JPEG, PNG, and WEBP images are allowed."
        )

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image_format = image.format
        image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise HubImageError(
                "Only JPG, JPEG, PNG, and WEBP images are allowed."
            )

    except (UnidentifiedImageError, OSError, ValueError):
        raise HubImageError("The uploaded file is not a valid image.")

    finally:
        uploaded_file.seek(0)


def get_hub_image_public_id(hub_id, image_type):
    """Generate a stable Cloudinary public ID for a Hub image."""

    if image_type not in IMAGE_CONFIG:
        raise HubImageError("Invalid image type.")

    image_name = IMAGE_CONFIG[image_type]["public_id"]

    return f"byb/hubs/{hub_id}/{image_name}"


def upload_hub_image(hub_id, image_type, uploaded_file):
    """Validate and upload a Hub logo or cover image to Cloudinary."""

    validate_hub_image(uploaded_file, image_type)
    configure_cloudinary()

    public_id = get_hub_image_public_id(hub_id, image_type)

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
            raise HubImageError(
                "Cloudinary did not return an image URL."
            )

        return secure_url

    except HubImageError:
        raise
    except Exception as exc:
        raise HubImageError(
            "Image upload failed. Please try again."
        ) from exc
