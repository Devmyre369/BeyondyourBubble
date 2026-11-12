
import uuid

from cloudinary import uploader
from PIL import Image, UnidentifiedImageError

from accounts.services.profile_image_service import configure_cloudinary


class MomentImageError(Exception):
    """Raised when a Moment image cannot be validated or uploaded."""


MAX_IMAGE_SIZE = 10 * 1024 * 1024

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


def validate_moment_image(uploaded_file):
    """Validate the uploaded Moment image."""

    if not uploaded_file:
        raise MomentImageError("Please select an image.")

    if uploaded_file.size > MAX_IMAGE_SIZE:
        raise MomentImageError(
            "Moment image size must not exceed 10 MB."
        )

    if uploaded_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise MomentImageError(
            "Only JPG, JPEG, PNG, and WEBP images are allowed."
        )

    try:
        uploaded_file.seek(0)

        image = Image.open(uploaded_file)
        image_format = image.format
        image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise MomentImageError(
                "Only JPG, JPEG, PNG, and WEBP images are allowed."
            )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exc:
        raise MomentImageError(
            "The uploaded file is not a valid image."
        ) from exc

    finally:
        uploaded_file.seek(0)


def upload_moment_image(user_id, uploaded_file):
    """
    Upload a Moment image to Cloudinary.

    Each Moment receives a unique Cloudinary public ID.
    """

    validate_moment_image(uploaded_file)
    configure_cloudinary()

    public_id = (
        f"byb/moments/{user_id}/{uuid.uuid4().hex}"
    )

    try:
        result = uploader.upload(
            uploaded_file,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )

        secure_url = result.get("secure_url")
        cloudinary_public_id = result.get("public_id")

        if not secure_url or not cloudinary_public_id:
            raise MomentImageError(
                "Cloudinary did not return the required image information."
            )

        return {
            "image_url": secure_url,
            "cloudinary_public_id": cloudinary_public_id,
        }

    except MomentImageError:
        raise

    except Exception as exc:
        raise MomentImageError(
            "Moment image upload failed. Please try again."
        ) from exc


def delete_moment_image(cloudinary_public_id):
    """Delete a Moment image from Cloudinary."""

    if not cloudinary_public_id:
        return {"result": "not found"}

    configure_cloudinary()

    try:
        return uploader.destroy(
            cloudinary_public_id,
            resource_type="image",
            invalidate=True,
        )

    except Exception as exc:
        raise MomentImageError(
            "Moment image deletion failed. Please try again."
        ) from exc
