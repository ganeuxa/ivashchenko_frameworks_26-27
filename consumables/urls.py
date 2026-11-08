from django.contrib import admin
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("materials/", include("materials.urls")),
    path("warehouses/", include("warehouses.urls")),
    path("operations/", include("operations.urls")),
]

handler404 = "homepage.views.page_not_found"

admin.site.site_header = "Учёт расходных материалов"
admin.site.site_title = "Складской учёт"
admin.site.index_title = "Управление материалами и складами"

if settings.ENABLE_DEBUG_TOOLBAR:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
