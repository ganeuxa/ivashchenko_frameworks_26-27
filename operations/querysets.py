from django.db import models


class OperationQuerySet(models.QuerySet):
    def posted(self):
        return self.filter(status=self.model.Status.POSTED)

    def cancelled(self):
        return self.filter(status=self.model.Status.CANCELLED)

    def drafts(self):
        return self.filter(status=self.model.Status.DRAFT)

    def with_related(self):
        return self.select_related("material", "warehouse", "target_warehouse")

    def for_material(self, material_id):
        return self.filter(material_id=material_id)

    def on_date(self, day):
        return self.filter(performed_at__date=day)
