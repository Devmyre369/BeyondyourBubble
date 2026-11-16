from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from hubs.models import Hub, HubMembership


def _slug_for_suffix(base_slug, suffix):
    suffix_text = "" if suffix == 1 else f"-{suffix}"
    stem = base_slug[:200 - len(suffix_text)].rstrip("-")
    return f"{stem}{suffix_text}"


@transaction.atomic
def create_hub(creator, data):
    base_slug = slugify(data["name"])[:200].rstrip("-") or "hub"
    suffix = 1

    while True:
        slug = _slug_for_suffix(base_slug, suffix)

        if Hub.objects.filter(slug=slug).exists():
            suffix += 1
            continue

        try:
            with transaction.atomic():
                hub_data = dict(data)
                hub_data.update(
                    slug=slug,
                    visibility=Hub.Visibility.PUBLIC,
                    created_by=creator,
                    owner=creator,
                    is_verified=False,
                    is_active=True,
                )
                hub = Hub.objects.create(**hub_data)
            break
        except IntegrityError:
            if not Hub.objects.filter(slug=slug).exists():
                raise
            suffix += 1

    HubMembership.objects.create(
        hub=hub,
        user=creator,
        role=HubMembership.Role.OWNER,
        status=HubMembership.Status.APPROVED,
        joined_at=timezone.now(),
    )

    return hub
