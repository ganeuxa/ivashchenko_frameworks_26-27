from materials.models import Material


def site_info(request):
    return {
        "site_name": "Учёт расходных материалов",
        "site_material_count": Material.objects.count(),
    }
