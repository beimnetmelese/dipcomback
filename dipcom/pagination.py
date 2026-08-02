from rest_framework.pagination import PageNumberPagination


class SellerListPagination(PageNumberPagination):
    """A predictable page size for the seller management lists."""

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
