from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Hub
from .permissions import CanEditHub
from .serializers import (
    HubCreateSerializer,
    HubDetailSerializer,
    HubDiscoveryQuerySerializer,
    HubListSerializer,
    HubUpdateSerializer,
)


class HubPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param, "1")

        try:
            page_number = int(page_number)
            if page_number < 1:
                raise ValueError
        except (TypeError, ValueError):
            raise NotFound("Invalid page number.")

        self.page_number = page_number
        self.count = queryset.count()
        start = (page_number - 1) * self.page_size
        self.end = start + self.page_size

        return list(queryset[start:self.end])

    def get_paginated_response(self, data):
        return Response({
            "count": self.count,
            "next": self.page_number + 1 if self.end < self.count else None,
            "previous": self.page_number - 1 if self.page_number > 1 else None,
            "results": data,
        })


class HubDiscoveryView(generics.ListCreateAPIView):
    serializer_class = HubListSerializer
    pagination_class = HubPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return HubCreateSerializer
        return HubListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hub = serializer.save()
        response_data = HubDetailSerializer(
            hub,
            context=self.get_serializer_context(),
        ).data
        headers = self.get_success_headers(response_data)
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

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


class HubDetailView(generics.RetrieveUpdateAPIView):
    queryset = Hub.objects.filter(is_active=True)
    serializer_class = HubDetailSerializer
    permission_classes = [IsAuthenticated, CanEditHub]
    http_method_names = ["get", "patch", "head", "options"]
    lookup_field = "id"
    lookup_url_kwarg = "hub_id"

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return HubUpdateSerializer
        return HubDetailSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        hub = self.get_object()
        response.data = HubDetailSerializer(
            hub,
            context=self.get_serializer_context(),
        ).data
        return response
