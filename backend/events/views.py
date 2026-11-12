from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Event
from .serializers import EventChoiceSerializer


class EventChoiceListView(generics.ListAPIView):

    serializer_class = EventChoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(
            organiser=self.request.user,
            status__in=[
                Event.Status.PUBLISHED,
                Event.Status.COMPLETED,
            ],
        ).order_by("-starts_at", "-created_at")