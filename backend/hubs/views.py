from django.db.models import Q
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Hub
from .serializers import (
    HubDetailSerializer,
    HubDiscoveryQuerySerializer,
    HubListSerializer,
)


class HubPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": (
                self.page.next_page_number()
                if self.page.has_next()
                else None
            ),
            "previous": (
                self.page.previous_page_number()
                if self.page.has_previous()
                else None
            ),
            "results": data,
        })


class HubDiscoveryView(generics.ListAPIView):
    serializer_class = HubListSerializer
    pagination_class = HubPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query_serializer = HubDiscoveryQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        queryset = Hub.objects.filter(is_active=True)

        if filters.get("hub_type"):
            queryset = queryset.filter(hub_type=filters["hub_type"])

        if filters.get("city"):
            queryset = queryset.filter(city__iexact=filters["city"])

        if filters.get("search"):
            search = filters["search"]
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
                | Q(slug__icontains=search)
                | Q(college_or_parent_organisation__icontains=search)
            )

        return queryset.order_by("-created_at", "-id")


class HubDetailView(generics.RetrieveAPIView):
    queryset = Hub.objects.filter(is_active=True)
    serializer_class = HubDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "hub_id"
