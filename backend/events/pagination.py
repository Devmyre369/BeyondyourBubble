
from rest_framework.pagination import PageNumberPagination


class EventPagination(PageNumberPagination):
    """
    Shared pagination for Event Discovery,
    Hub Event Management and BYB moderation.
    """

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50
