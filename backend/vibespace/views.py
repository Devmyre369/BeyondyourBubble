
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts.models import Profile

from .models import Vibe, Moment
from .serializers import VibeSerializer, MomentSerializer
from .permissions import IsAuthorOrReadOnly
from .service.moment_image_service import (
    MomentImageError,
    upload_moment_image,
    delete_moment_image,
)


# ==================================================
# SHARED VISIBILITY QUERYSET
# ==================================================

class VibeSpaceVisibilityMixin:

    def get_visible_queryset(self, queryset):
        user = self.request.user

        queryset = queryset.select_related(
            "author",
            "author__profile",
            "event",
        )

        if user.is_authenticated:
            queryset = queryset.filter(
                Q(author__profile__visibility=Profile.Visibility.PUBLIC)
                | Q(author=user)
            )
        else:
            queryset = queryset.filter(
                author__profile__visibility=Profile.Visibility.PUBLIC
            )

        username = self.request.query_params.get("username")

        if username:
            queryset = queryset.filter(
                author__username__iexact=username
            )

        return queryset


# ==================================================
# VIBE LIST / CREATE
# ==================================================

class VibeListCreateView(
    VibeSpaceVisibilityMixin,
    generics.ListCreateAPIView,
):

    serializer_class = VibeSerializer
    queryset = Vibe.objects.all()
    parser_classes = [JSONParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]

        return [AllowAny()]

    def get_queryset(self):
        return self.get_visible_queryset(
            Vibe.objects.all()
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ==================================================
# VIBE DETAIL / UPDATE / DELETE
# ==================================================

class VibeDetailView(
    VibeSpaceVisibilityMixin,
    generics.RetrieveUpdateDestroyAPIView,
):

    serializer_class = VibeSerializer
    queryset = Vibe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = "id"

    def get_queryset(self):
        return self.get_visible_queryset(
            Vibe.objects.all()
        )


# ==================================================
# MOMENT LIST / CREATE
# ==================================================

class MomentListCreateView(
    VibeSpaceVisibilityMixin,
    generics.ListCreateAPIView,
):

    serializer_class = MomentSerializer
    queryset = Moment.objects.all()

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]

        return [AllowAny()]

    def get_queryset(self):
        return self.get_visible_queryset(
            Moment.objects.all()
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = request.FILES.get("image")

        if not uploaded_file:
            return Response(
                {
                    "success": False,
                    "message": "Please select an image for your Moment.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            image_data = upload_moment_image(
                user_id=request.user.id,
                uploaded_file=uploaded_file,
            )

        except MomentImageError as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            moment = serializer.save(
                author=request.user,
                image_url=image_data["image_url"],
                cloudinary_public_id=image_data["cloudinary_public_id"],
            )

        except Exception:
            try:
                delete_moment_image(
                    image_data["cloudinary_public_id"]
                )
            except MomentImageError:
                pass

            raise

        return Response(
            {
                "success": True,
                "message": "Moment published successfully.",
                "moment": self.get_serializer(moment).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ==================================================
# MOMENT DETAIL / UPDATE / DELETE
# ==================================================

class MomentDetailView(
    VibeSpaceVisibilityMixin,
    generics.RetrieveUpdateDestroyAPIView,
):

    serializer_class = MomentSerializer
    queryset = Moment.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = "id"

    def get_queryset(self):
        return self.get_visible_queryset(
            Moment.objects.all()
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            delete_moment_image(
                instance.cloudinary_public_id
            )

        except MomentImageError as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        instance.delete()

        return Response(
            {
                "success": True,
                "message": "Moment deleted successfully.",
            },
            status=status.HTTP_200_OK,
        )
