
import uuid

from cloudinary import uploader
from PIL import Image, UnidentifiedImageError

from accounts.services.profile_image_service import configure_cloudinary


class EventImageError(Exception):
    """Raised when an event cover image cannot be validated or uploaded."""


MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000

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


def validate_event_cover_image(uploaded_file):
    """Validate the uploaded event cover image."""

    if not uploaded_file:
        raise EventImageError("Please select an image.")

    if uploaded_file.size > MAX_IMAGE_SIZE:
        raise EventImageError(
            "Cover image size must not exceed 10 MB."
        )

    if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise EventImageError(
            "Only JPG, JPEG, PNG, and WEBP images are allowed."
        )

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image_format = image.format
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise EventImageError("Image dimensions are too large.")
        image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise EventImageError(
                "Only JPG, JPEG, PNG, and WEBP images are allowed."
            )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exc:
        raise EventImageError(
            "The uploaded file is not a valid image."
        ) from exc

    finally:
        uploaded_file.seek(0)


def upload_event_cover_image(event_id, uploaded_file):
    """
    Upload an event cover image to Cloudinary.

    Uses the event's UUID as a stable folder path with a unique filename.
    """

    validate_event_cover_image(uploaded_file)
    configure_cloudinary()

    public_id = f"byb/events/{event_id}/cover_{uuid.uuid4().hex}"

    try:
        result = uploader.upload(
            uploaded_file,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
            invalidate=True,
        )

        secure_url = result.get("secure_url")

        if not secure_url:
            raise EventImageError(
                "Cloudinary did not return the required image information."
            )

        return secure_url

    except EventImageError:
        raise

    except Exception as exc:
        raise EventImageError(
            "Event cover image upload failed. Please try again."
        ) from exc
