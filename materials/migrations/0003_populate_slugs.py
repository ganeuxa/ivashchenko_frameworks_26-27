from django.db import migrations, models
from django.utils.text import slugify
from unidecode import unidecode


def populate(apps, schema_editor):
    material = apps.get_model("materials", "Material")
    for obj in material.objects.using(schema_editor.connection.alias).all():
        base = slugify(unidecode(obj.name))[:190] or "material"
        obj.slug = f"{base}-{obj.pk}"
        obj.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("materials", "0002_alter_material_options_material_reorder_target_and_more"),
    ]
    operations = [
        migrations.RunPython(populate, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="material", name="slug",
            field=models.SlugField(
                "URL-идентификатор", max_length=220, unique=True,
                editable=False,
            ),
        ),
    ]
