from django.utils import timezone

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .notification_serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_query_param = "page"
    max_page_size = 50


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = (
            Notification.objects.filter(recipient=request.user)
            .select_related("actor", "actor__profile", "handshake")
            .order_by("-created_at")
        )
        paginator = NotificationPagination()
        page = paginator.paginate_queryset(notifications, request, view=self)
        return Response({
            "count": paginator.page.paginator.count,
            "next": (
                paginator.page.next_page_number()
                if paginator.page.has_next()
                else None
            ),
            "previous": (
                paginator.page.previous_page_number()
                if paginator.page.has_previous()
                else None
            ),
            "unread_count": notifications.filter(read_at__isnull=True).count(),
            "results": NotificationSerializer(page, many=True).data,
        })


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_count = Notification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
        ).count()
        return Response({"unread_count": unread_count})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = Notification.objects.filter(
            recipient=request.user,
            id=notification_id,
        ).first()
        if notification is None:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response({"read": True})


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated_count = Notification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
        ).update(read_at=timezone.now())
        return Response({"read_count": updated_count})
