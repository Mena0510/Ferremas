# productos/migrations/0002_create_gestor_group.py
from django.db import migrations

def create_gestor_group(apps, schema_editor):
    # Obtener modelos a través de apps (no import directo)
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    # Ajusta 'productos' y 'productotienda' según tu app_label y model lowercase
    ct = ContentType.objects.get(app_label='productos', model='productotienda')
    perms = Permission.objects.filter(content_type=ct)

    # Crear o actualizar el grupo
    grupo, created = Group.objects.get_or_create(name='GestorProductos')
    grupo.permissions.set(perms)
    grupo.save()

class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_gestor_group),
    ]
