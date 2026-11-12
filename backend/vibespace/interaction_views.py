
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile

from .models import Vibe, Moment, Comment, Revibe, SavedContent
from .serializers import (
    CommentSerializer,
    RevibeSerializer,
    SavedContentSerializer,
)


def get_visible_vibe(user, vibe_id):
    queryset = Vibe.objects.select_related(
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

    return get_object_or_404(queryset, id=vibe_id)


def get_visible_moment(user, moment_id):
    queryset = Moment.objects.select_related(
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

    return get_object_or_404(queryset, id=moment_id)


class ContentCommentListCreateView(APIView):
    """
    List comments on a visible Vibe or Moment and allow authenticated
    users to publish comments.
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_content(self):
        content_type = self.kwargs["content_type"]
        content_id = self.kwargs["content_id"]

        if content_type == "vibe":
            return "vibe", get_visible_vibe(self.request.user, content_id)

        if content_type == "moment":
            return "moment", get_visible_moment(self.request.user, content_id)

        raise NotFound("Invalid content type.")

    def get(self, request, *args, **kwargs):
        content_type, content = self.get_content()

        if content_type == "vibe":
            comments = Comment.objects.filter(vibe=content)
        else:
            comments = Comment.objects.filter(moment=content)

        comments = comments.select_related("author").order_by("created_at")

        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, *args, **kwargs):
        content_type, content = self.get_content()

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if content_type == "vibe":
            comment = serializer.save(
                author=request.user,
                vibe=content,
                moment=None,
            )
        else:
            comment = serializer.save(
                author=request.user,
                moment=content,
                vibe=None,
            )

        return Response(
            {
                "success": True,
                "message": "Comment published successfully.",
                "comment": CommentSerializer(comment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer

    queryset = Comment.objects.select_related(
        "author",
        "vibe__author",
        "vibe__author__profile",
        "moment__author",
        "moment__author__profile",
    )

    lookup_field = "id"
    lookup_url_kwarg = "comment_id"

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_object(self):
        comment = get_object_or_404(
            self.get_queryset(),
            id=self.kwargs["comment_id"],
        )

        if comment.vibe_id:
            get_visible_vibe(self.request.user, comment.vibe_id)
        else:
            get_visible_moment(self.request.user, comment.moment_id)

        if self.request.method in ("PUT", "PATCH", "DELETE"):
            if comment.author_id != self.request.user.id:
                raise PermissionDenied(
                    "Only the comment author can edit or delete this comment."
                )

        return comment


class ContentRevibeView(APIView):
    """
    Retrieve, create, update, or remove the current user's Revibe
    of a Vibe or Moment.
    """

    permission_classes = [IsAuthenticated]

    def get_content(self):
        content_type = self.kwargs["content_type"]
        content_id = self.kwargs["content_id"]

        if content_type == "vibe":
            return "vibe", get_visible_vibe(self.request.user, content_id)

        if content_type == "moment":
            return "moment", get_visible_moment(self.request.user, content_id)

        raise NotFound("Invalid content type.")

    def get(self, request, *args, **kwargs):
        content_type, content = self.get_content()

        filters = {"author": request.user}

        if content_type == "vibe":
            filters["vibe"] = content
        else:
            filters["moment"] = content

        revibe = Revibe.objects.filter(**filters).first()

        if not revibe:
            return Response(None, status=status.HTTP_200_OK)

        return Response(RevibeSerializer(revibe).data)

    def post(self, request, *args, **kwargs):
        content_type, content = self.get_content()

        if content_type == "vibe":
            existing = Revibe.objects.filter(
                author=request.user,
                vibe=content,
            ).first()
        else:
            existing = Revibe.objects.filter(
                author=request.user,
                moment=content,
            ).first()

        serializer = RevibeSerializer(
            existing,
            data=request.data,
            partial=existing is not None,
        )

        serializer.is_valid(raise_exception=True)

        if existing:
            revibe = serializer.save()
            message = "Revibe updated successfully."
            response_status = status.HTTP_200_OK
        else:
            if content_type == "vibe":
                revibe = serializer.save(
                    author=request.user,
                    vibe=content,
                    moment=None,
                )
            else:
                revibe = serializer.save(
                    author=request.user,
                    vibe=None,
                    moment=content,
                )

            message = "Revibe published successfully."
            response_status = status.HTTP_201_CREATED

        return Response(
            {
                "success": True,
                "message": message,
                "revibe": RevibeSerializer(revibe).data,
            },
            status=response_status,
        )

    def delete(self, request, *args, **kwargs):
        content_type, content = self.get_content()

        if content_type == "vibe":
            revibe = Revibe.objects.filter(
                author=request.user,
                vibe=content,
            ).first()
        else:
            revibe = Revibe.objects.filter(
                author=request.user,
                moment=content,
            ).first()

        if not revibe:
            return Response(
                {
                    "success": False,
                    "message": "You have not Revibed this content.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        revibe.delete()

        return Response(
            {
                "success": True,
                "message": "Revibe removed successfully.",
            },
            status=status.HTTP_200_OK,
        )


class SavedContentListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return (
            SavedContent.objects.filter(user=user)
            .filter(
                Q(
                    vibe__isnull=False,
                    vibe__author__profile__visibility=Profile.Visibility.PUBLIC,
                )
                | Q(vibe__author=user)
                | Q(
                    moment__isnull=False,
                    moment__author__profile__visibility=Profile.Visibility.PUBLIC,
                )
                | Q(moment__author=user)
            )
            .select_related(
                "vibe",
                "vibe__author",
                "moment",
                "moment__author",
            )
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vibe = serializer.validated_data.get("vibe")
        moment = serializer.validated_data.get("moment")

        if vibe is not None:
            get_visible_vibe(request.user, vibe.id)
        elif moment is not None:
            get_visible_moment(request.user, moment.id)
        else:
            return Response(
                {
                    "success": False,
                    "message": "Select a Vibe or Moment to save.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved_content, created = SavedContent.objects.get_or_create(
            user=request.user,
            vibe=vibe,
            moment=moment,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Content saved successfully."
                    if created
                    else "This content is already saved."
                ),
                "saved_content": SavedContentSerializer(saved_content).data,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class SavedContentDetailView(generics.DestroyAPIView):
    serializer_class = SavedContentSerializer
    permission_classes = [IsAuthenticated]

    lookup_field = "id"
    lookup_url_kwarg = "saved_id"

    def get_queryset(self):
        return SavedContent.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        return Response(
            {
                "success": True,
                "message": "Saved content removed successfully.",
            },
            status=status.HTTP_200_OK,
        )
