from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("materials/", include("materials.urls")),
    path("warehouses/", include("warehouses.urls")),
    path("operations/", include("operations.urls")),
]

handler404 = "homepage.views.page_not_found"
