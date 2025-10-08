from django.contrib import admin
from .models import ProductoTienda

@admin.register(ProductoTienda)
class ProductoTiendaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'mostrar_imagen')
    search_fields = ('nombre', 'categoria')
    list_filter = ('categoria',)

    def mostrar_imagen(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" width="50" height="50" style="object-fit: cover;" />'
        return 'Sin imagen'
    mostrar_imagen.allow_tags = True
    mostrar_imagen.short_description = 'Imagen'
