from django.core.paginator import Paginator
from django.template.response import TemplateResponse

from wagtail.models import Locale, Page


def search(request):
    search_query = request.GET.get("query", "").strip()
    page = request.GET.get("page", 1)

    # Search
    if search_query:
        search_results = Page.objects.live().public().filter(locale=Locale.get_active()).specific().search(search_query)
    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)
    search_results = paginator.get_page(page)

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
        },
    )
