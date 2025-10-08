from django.apps import AppConfig


class ProductosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'productos'
    def ready(self):
        # importa para que django ejecute post_migrate
        import productos.signals
