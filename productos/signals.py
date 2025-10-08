# productos/signals.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import ProductoTienda

def crear_grupo_gestor(sender, **kwargs):
    # Obtener o crear grupo
    grupo, created = Group.objects.get_or_create(name='GestorProductos')

    # Obtener el content type de ProductoTienda
    ct = ContentType.objects.get_for_model(ProductoTienda)

    # Coger todas las perms de ProductoTienda: add, change, delete, view
    perms = Permission.objects.filter(content_type=ct)
    grupo.permissions.set(perms)

class ProductosConfig(AppConfig):
    name = 'productos'

    def ready(self):
        post_migrate.connect(crear_grupo_gestor, sender=self)
