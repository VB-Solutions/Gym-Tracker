from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Paginación por defecto de todos los listados:
    {"count", "next", "previous", "results"}. ?page=N y ?page_size=N (máximo 100).
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
