from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views
from productos.views import (
    home,
    crear_producto,
    editar_producto,
    eliminar_producto,
    lista_productos,
    catalogo_productos,
    detalle_producto,
    ver_carrito,
    agregar_al_carrito,
    actualizar_carrito,
    eliminar_del_carrito,
    checkout,
    pagar_mercadopago,
    pago_exitoso,
    pago_fallido,
    webhook_mercadopago,
    panel_admin,
    vendedor_dashboard,
    bodeguero_dashboard,
    contador_dashboard,
    client_dashboard,
    subir_comprobante,
    aprobar_rechazar_pedido,
    crear_orden_bodega,
    aceptar_orden_bodega,
    preparar_pedido,
    entregar_a_vendedor,
    confirmar_pago_transferencia,
    registrar_entrega,
    registrar_despacho,
    bodeguero_crear_producto,
    bodeguero_editar_producto,
    bodeguero_eliminar_producto,
    bodeguero_catalogo,
    crear_reclamo,
)

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Autenticación de usuarios
    path('accounts/', include('accounts.urls')),
    path('admin-panel/', panel_admin, name='panel_admin'),

    # Dashboards específicos por perfil
    path('vendedor/', vendedor_dashboard, name='vendedor_dashboard'),
    path('bodeguero/', bodeguero_dashboard, name='bodeguero_dashboard'),
    path('contador/', contador_dashboard, name='contador_dashboard'),
    path('cliente/', client_dashboard, name='client_dashboard'),

    # Funcionalidades del Vendedor
    path('vendedor/aprobar-pedido/<int:pedido_id>/', aprobar_rechazar_pedido, name='aprobar_rechazar_pedido'),
    path('vendedor/crear-orden-bodega/<int:pedido_id>/', crear_orden_bodega, name='crear_orden_bodega'),
    path('vendedor/registrar-despacho/<int:pedido_id>/', registrar_despacho, name='registrar_despacho'),

    # Funcionalidades del Bodeguero
    path('bodeguero/aceptar-orden/<int:orden_id>/', aceptar_orden_bodega, name='aceptar_orden_bodega'),
    path('bodeguero/preparar-pedido/<int:orden_id>/', preparar_pedido, name='preparar_pedido'),
    path('bodeguero/entregar-vendedor/<int:orden_id>/', entregar_a_vendedor, name='entregar_a_vendedor'),

    # Funcionalidades del Contador
    path('contador/confirmar-pago/<int:pedido_id>/', confirmar_pago_transferencia, name='confirmar_pago_transferencia'),
    path('contador/registrar-entrega/<int:pedido_id>/', registrar_entrega, name='registrar_entrega'),

    # Funcionalidades del Cliente
    path('cliente/subir-comprobante/<int:pedido_id>/', subir_comprobante, name='subir_comprobante'),

    # Página de inicio
    path('', home, name='home'),

    # Panel interno de productos (solo staff)
    path('productos/admin/crear/', crear_producto, name='crear_producto'),
    path('productos/admin/editar/<int:producto_id>/', editar_producto, name='editar_producto'),
    path('productos/admin/eliminar/<int:producto_id>/', eliminar_producto, name='eliminar_producto'),

    # Listados y detalles públicos de productos
    path('productos/', lista_productos, name='lista_productos'),
    path('catalogo/', catalogo_productos, name='catalogo_productos'),
    path('producto/<int:producto_id>/', detalle_producto, name='detalle_producto'),

    # Carrito de compras y checkout
    path('carrito/', ver_carrito, name='ver_carrito'),
    path('agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('actualizar/<int:producto_id>/', actualizar_carrito, name='actualizar_carrito'),
    path('eliminar/<int:producto_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('checkout/', checkout, name='checkout'),

    # Pagos con MercadoPago
    path('pagar/', pagar_mercadopago, name='pagar_mercadopago'),
    path('pago-exitoso/', pago_exitoso, name='pago_exitoso'),
    path('pago-fallido/', pago_fallido, name='pago_fallido'),
    path('webhook/', webhook_mercadopago, name='webhook_mercadopago'),

    # URLs para Bodeguero CRUD
    path('bodeguero/catalogo/', bodeguero_catalogo, name='bodeguero_catalogo'),
    path('bodeguero/producto/crear/', bodeguero_crear_producto, name='bodeguero_crear_producto'),
    path('bodeguero/producto/<int:producto_id>/editar/', bodeguero_editar_producto, name='bodeguero_editar_producto'),
    path('bodeguero/producto/<int:producto_id>/eliminar/', bodeguero_eliminar_producto, name='bodeguero_eliminar_producto'),

    #Reclamo
    path('reclamo/', crear_reclamo, name='crear_reclamo'),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
