# productos/views.py
from django.core.paginator import Paginator
import requests
from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
import mercadopago
from django.contrib.auth.decorators import permission_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .forms import ReclamoForm
from django.contrib import messages

from .models import (
    ProductoTienda, Pedido, PedidoItem, OrdenBodega
)
from .forms import ProductoForm

def es_staff(user):
    return user.is_staff


@csrf_exempt
def webhook_mercadopago(request):
    # El webhook permanece, pero no se usará para el flujo de stock
    if request.method == 'POST':
        import json
        data = json.loads(request.body.decode('utf-8'))
        if data.get('type') == 'payment':
            payment_id = data['data']['id']
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            payment = sdk.payment().get(payment_id)['response']
            metadata = payment.get('metadata', {})
            pedido_id = metadata.get('pedido_id')
            if pedido_id:
                try:
                    pedido = Pedido.objects.get(id=pedido_id)
                    status = payment.get('status')
                    pedido.estado = 'aprobado' if status == 'approved' else 'rechazado'
                    pedido.mercadopago_id = str(payment_id)
                    pedido.save()
                except Pedido.DoesNotExist:
                    pass
        return JsonResponse({'status': 'ok'})

def crear_reclamo(request):
    if request.method == 'POST':
        form = ReclamoForm(request.POST)
        if form.is_valid():
            reclamo = form.save(commit=False)
            if request.user.is_authenticated:
                reclamo.usuario = request.user
            reclamo.save()
            messages.success(request, 'Tu reclamo fue enviado correctamente.')
            return redirect('crear_reclamo')
    else:
        form = ReclamoForm()
    return render(request, 'productos/reclamo_form.html', {'form': form})

@login_required
def pagar_mercadopago(request):
    carrito = request.session.get('carrito', {})
    productos = ProductoTienda.objects.filter(id__in=carrito.keys())

    preference_items = []
    for producto in productos:
        cantidad = carrito.get(str(producto.id), 0)
        if cantidad > 0:
            preference_items.append({
                "title": producto.nombre,
                "quantity": int(cantidad),
                "unit_price": float(producto.precio)
            })

    if not preference_items:
        messages.error(request, "No hay productos válidos en el carrito.")
        return redirect('ver_carrito')

    total = sum(item["unit_price"] * item["quantity"] for item in preference_items)
    
    # Crear pedido con información del cliente
    pedido = Pedido.objects.create(
        cliente=request.user,
        total=total,
        metodo_pago='debito',  # Por defecto para MercadoPago
        tipo_entrega=request.session.get('tipo_entrega', 'tienda'),
        direccion_entrega=request.session.get('direccion_entrega', ''),
        telefono_contacto=request.session.get('telefono_contacto', '')
    )

    for producto in productos:
        cantidad = carrito.get(str(producto.id), 0)
        if cantidad > 0:
            PedidoItem.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )

    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        
        # Configurar URLs de retorno
        success_url = f"{settings.BASE_URL.rstrip('/')}{reverse('pago_exitoso')}"
        failure_url = f"{settings.BASE_URL.rstrip('/')}{reverse('pago_fallido')}"
        pending_url = f"{settings.BASE_URL.rstrip('/')}{reverse('pago_fallido')}"

        # Configurar preferencia de pago
        preference_data = {
            "items": preference_items,
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
            "auto_return": "approved",
            "external_reference": str(pedido.id),
            "notification_url": f"{settings.BASE_URL.rstrip('/')}{reverse('webhook_mercadopago')}",
            "expires": True,
            "expiration_date_to": "2025-12-31T23:59:59.000-03:00"
        }

        preference_response = sdk.preference().create(preference_data)
        
        if preference_response.get("status") == 201:
            init_point = preference_response.get("response", {}).get("init_point")
            if init_point:
                return redirect(init_point)
            else:
                messages.error(request, "Error: No se pudo obtener el enlace de pago.")
                return redirect('checkout')
        else:
            error_message = preference_response.get("response", {}).get("message", "Error desconocido")
            messages.error(request, f"Error al crear preferencia de pago: {error_message}")
            return redirect('checkout')
            
    except Exception as e:
        messages.error(request, f"Error de conexión con MercadoPago: {str(e)}")
        return redirect('checkout')


def catalogo_productos(request):
    productos = ProductoTienda.objects.all()
    nombre = request.GET.get('nombre')
    categoria = request.GET.get('categoria')
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if categoria and categoria != 'Todas':
        productos = productos.filter(categoria__iexact=categoria)
    categorias = ProductoTienda.objects.values_list('categoria', flat=True).distinct()
    paginator = Paginator(productos, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'productos/catalogo.html', {
        'page_obj': page_obj,
        'categorias': categorias,
        'nombre_actual': nombre or '',
        'categoria_actual': categoria or 'Todas'
    })


def home(request):
    productos_destacados = ProductoTienda.objects.order_by('-stock')[:6]
    return render(request, 'productos/home.html', {
        'productos_destacados': productos_destacados
    })


def detalle_producto(request, producto_id):
    producto = get_object_or_404(ProductoTienda, id=producto_id)
    return render(request, 'productos/detalle_producto.html', {'producto': producto})


def lista_productos(request):
    api_url = "https://raw.githubusercontent.com/alebasti/int-plataformas/main/db.json"
    data = requests.get(api_url).json()
    productos = data.get('productos', [])
    return render(request, 'productos/lista.html', {'productos': productos})


def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(ProductoTienda, id=producto_id)
    carrito = request.session.get('carrito', {})
    cantidad = 1
    if producto.stock >= carrito.get(str(producto.id), 0) + cantidad:
        carrito[str(producto.id)] = carrito.get(str(producto.id), 0) + cantidad
        request.session['carrito'] = carrito
        messages.success(request, f'{producto.nombre} agregado al carrito.')
    else:
        messages.warning(request, f'Solo hay {producto.stock} unidades disponibles.')
    return redirect('catalogo_productos')


def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    productos = ProductoTienda.objects.filter(id__in=carrito.keys())
    items, total = [], 0
    for producto in productos:
        cantidad = carrito[str(producto.id)]
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
    return render(request, 'productos/carrito.html', {'items': items, 'total': total})


def actualizar_carrito(request, producto_id):
    if request.method == 'POST':
        nueva_cantidad = int(request.POST.get('cantidad', 1))
        producto = get_object_or_404(ProductoTienda, id=producto_id)
        carrito = request.session.get('carrito', {})
        if nueva_cantidad > producto.stock:
            nueva_cantidad = producto.stock
            messages.warning(request, f'Solo hay {producto.stock} unidades disponibles.')
        if nueva_cantidad < 1:
            carrito.pop(str(producto_id), None)
        else:
            carrito[str(producto_id)] = nueva_cantidad
        request.session['carrito'] = carrito
        messages.success(request, f'Cantidad de {producto.nombre} actualizada.')
    return redirect('ver_carrito')


def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    if str(producto_id) in carrito:
        del carrito[str(producto_id)]
        request.session['carrito'] = carrito
        messages.success(request, 'Producto eliminado del carrito.')
    return redirect('ver_carrito')


@login_required
def checkout(request):
    carrito = request.session.get('carrito', {})
    productos = ProductoTienda.objects.filter(id__in=carrito.keys())
    items, total = [], 0
    for producto in productos:
        cantidad = carrito[str(producto.id)]
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
    
    perfil = getattr(request.user, 'perfil', None)
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        tipo_entrega = request.POST.get('tipo_entrega')
        direccion_entrega = request.POST.get('direccion_entrega', '')
        telefono_contacto = request.POST.get('telefono_contacto', '')
        
        # Guardar información en sesión
        request.session['tipo_entrega'] = tipo_entrega
        request.session['direccion_entrega'] = direccion_entrega
        request.session['telefono_contacto'] = telefono_contacto
        
        if metodo_pago in ['debito', 'credito']:
            # Redirigir a MercadoPago
            return pagar_mercadopago(request)
        elif metodo_pago == 'transferencia':
            # Crear pedido para transferencia
            pedido = Pedido.objects.create(
                cliente=request.user,
                total=total,
                metodo_pago='transferencia',
                tipo_entrega=tipo_entrega,
                direccion_entrega=direccion_entrega,
                telefono_contacto=telefono_contacto
            )
            
            for producto in productos:
                cantidad = carrito[str(producto.id)]
                if cantidad > 0:
                    PedidoItem.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio
                    )
            
            # Vaciar carrito
            request.session['carrito'] = {}
            messages.success(request, f'¡Pedido creado exitosamente! Sube el comprobante de transferencia.')
            return redirect('subir_comprobante', pedido_id=pedido.id)
    
    return render(request, 'productos/checkout.html', {
        'items': items,
        'total': total,
        'nombre': perfil.nombre_completo if perfil else '',
        'email': request.user.email,
        'direccion': perfil.direccion if perfil else ''
    })


def pago_exitoso(request):
    try:
        # Leer parámetros de MercadoPago
        status = request.GET.get('collection_status')
        pedido_id = request.GET.get('external_reference')
        payment_id = request.GET.get('payment_id')
        preference_id = request.GET.get('preference_id')

        print(f"DEBUG - Status: {status}, Pedido ID: {pedido_id}, Payment ID: {payment_id}")

        if not pedido_id:
            messages.error(request, "Error: No se pudo identificar el pedido.")
            return redirect('pago_fallido')

        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            messages.error(request, "Error: Pedido no encontrado.")
            return redirect('pago_fallido')

        # Verificar el estado del pago
        if status == 'approved':
            # Descontar stock sólo una vez
            if not pedido.stock_actualizado:
                for item in pedido.items.all():
                    producto = item.producto
                    if producto.stock >= item.cantidad:
                        producto.stock = max(producto.stock - item.cantidad, 0)
                        producto.save()
                    else:
                        messages.warning(request, f"Stock insuficiente para {producto.nombre}")
                
                pedido.estado = 'pagado'
                pedido.stock_actualizado = True
                if payment_id:
                    pedido.mercadopago_id = payment_id
                pedido.save()

            # Vaciar carrito
            request.session['carrito'] = {}
            messages.success(request, "¡Pago exitoso! Tu pedido ha sido procesado y está pendiente de aprobación.")
            return render(request, 'productos/pago_exitoso.html', {'pedido': pedido})
        
        elif status == 'pending':
            messages.warning(request, "El pago está pendiente de confirmación.")
            return redirect('pago_fallido')
        
        elif status == 'rejected':
            messages.error(request, "El pago fue rechazado.")
            return redirect('pago_fallido')
        
        else:
            messages.error(request, f"Estado de pago desconocido: {status}")
            return redirect('pago_fallido')

    except Exception as e:
        print(f"ERROR en pago_exitoso: {str(e)}")
        messages.error(request, "Error al procesar el pago exitoso.")
        return redirect('pago_fallido')


def pago_fallido(request):
    messages.error(request, "El pago fue rechazado o cancelado.")
    return render(request, 'productos/pago_fallido.html')


@permission_required('productos.add_productotienda', raise_exception=True)
@login_required
@user_passes_test(es_staff)
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('catalogo_productos')
    else:
        form = ProductoForm()
    return render(request, 'productos/crear_producto.html', {'form': form})


@permission_required('productos.add_productotienda', raise_exception=True)
@login_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(ProductoTienda, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('catalogo_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/editar_producto.html', {'form': form, 'producto': producto})


@login_required
@user_passes_test(es_staff)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(ProductoTienda, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        return redirect('catalogo_productos')
    return render(request, 'productos/confirmar_eliminar.html', {'producto': producto})


@staff_member_required
def panel_admin(request):
    # Estadísticas para el panel de administración
    total_productos = ProductoTienda.objects.count()
    total_pedidos = Pedido.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    ventas_mes = Pedido.objects.filter(
        fecha__month=timezone.now().month,
        estado='aprobado'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Productos más vendidos
    productos_vendidos = PedidoItem.objects.values('producto__nombre').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:5]
    
    context = {
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'ventas_mes': ventas_mes,
        'productos_vendidos': productos_vendidos,
    }
    return render(request, 'productos/panel_admin.html', context)

# Vistas específicas para cada perfil

@login_required
def vendedor_dashboard(request):
    # Verificar que el usuario sea vendedor
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_vendedor():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    # Pedidos pagados pendientes de aprobación
    pedidos_pendientes = Pedido.objects.filter(estado='pagado').order_by('fecha')
    
    # Pedidos aprobados que NO tienen órdenes de bodega
    pedidos_sin_orden = Pedido.objects.filter(
        estado='aprobado'
    ).exclude(
        orden_bodega__isnull=False
    ).order_by('fecha')
    
    # Pedidos aprobados que SÍ tienen órdenes de bodega
    pedidos_con_orden = Pedido.objects.filter(
        estado='aprobado'
    ).filter(
        orden_bodega__isnull=False
    ).order_by('fecha')
    
    # Pedidos listos para despacho (retiro en tienda)
    pedidos_listos_despacho = Pedido.objects.filter(estado='listo_despacho').order_by('fecha')
    
    # Pedidos despachados recientemente
    pedidos_despachados = Pedido.objects.filter(estado='despachado').order_by('-fecha_entrega')[:10]
    
    context = {
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_sin_orden': pedidos_sin_orden,
        'pedidos_con_orden': pedidos_con_orden,
        'pedidos_listos_despacho': pedidos_listos_despacho,
        'pedidos_despachados': pedidos_despachados,
        'perfil': request.user.perfil,
    }
    return render(request, 'productos/vendedor_dashboard.html', context)

@login_required
def aprobar_rechazar_pedido(request, pedido_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_vendedor():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('vendedor_dashboard')
    
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='pagado')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        observaciones = request.POST.get('observaciones', '')
        
        if accion == 'aprobar':
            pedido.estado = 'aprobado'
            pedido.vendedor = request.user
            pedido.fecha_aprobacion = timezone.now()
            pedido.observaciones = observaciones
            pedido.save()
            
            # Crear orden de bodega
            OrdenBodega.objects.create(
                pedido=pedido,
                estado='pendiente'
            )
            
            messages.success(request, f'Pedido #{pedido.id} aprobado exitosamente.')
        elif accion == 'rechazar':
            pedido.estado = 'rechazado'
            pedido.vendedor = request.user
            pedido.observaciones = observaciones
            pedido.save()
            messages.success(request, f'Pedido #{pedido.id} rechazado.')
    
    return redirect('vendedor_dashboard')

@login_required
def crear_orden_bodega(request, pedido_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_vendedor():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('vendedor_dashboard')
    
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='aprobado')
    
    if request.method == 'POST':
        bodeguero_id = request.POST.get('bodeguero')
        observaciones = request.POST.get('observaciones', '')
        
        try:
            bodeguero = User.objects.get(id=bodeguero_id, perfil__tipo_usuario='bodeguero')
            
            # Actualizar orden de bodega
            orden_bodega = pedido.orden_bodega
            orden_bodega.bodeguero = bodeguero
            orden_bodega.observaciones = observaciones
            orden_bodega.save()
            
            # Actualizar pedido
            pedido.bodeguero = bodeguero
            pedido.save()
            
            messages.success(request, f'Orden de bodega creada para el pedido #{pedido.id}')
        except User.DoesNotExist:
            messages.error(request, 'Bodeguero no encontrado.')
    
    return redirect('vendedor_dashboard')

@login_required
def bodeguero_dashboard(request):
    # Verificar que el usuario sea bodeguero
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    # Órdenes de bodega asignadas al bodeguero (activas)
    ordenes_asignadas = OrdenBodega.objects.filter(
        bodeguero=request.user,
        estado__in=['aceptada', 'preparando', 'completada']
    ).select_related('pedido').order_by('-fecha_creacion')
    
    # Órdenes completadas recientemente (para historial)
    ordenes_completadas = OrdenBodega.objects.filter(
        bodeguero=request.user,
        estado='entregada'
    ).select_related('pedido').order_by('-fecha_entrega_vendedor')[:5]
    
    # Órdenes pendientes (sin bodeguero asignado)
    ordenes_pendientes = OrdenBodega.objects.filter(
        bodeguero__isnull=True
    ).select_related('pedido').order_by('-fecha_creacion')
    
    context = {
        'ordenes_asignadas': ordenes_asignadas,
        'ordenes_completadas': ordenes_completadas,
        'ordenes_pendientes': ordenes_pendientes,
        'perfil': request.user.perfil,
    }
    return render(request, 'productos/bodeguero_dashboard.html', context)

@login_required
def aceptar_orden_bodega(request, orden_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('bodeguero_dashboard')
    
    orden = get_object_or_404(OrdenBodega, id=orden_id, bodeguero__isnull=True)
    
    if request.method == 'POST':
        orden.bodeguero = request.user
        orden.estado = 'aceptada'
        orden.fecha_aceptacion = timezone.now()
        orden.save()
        
        # Actualizar pedido
        pedido = orden.pedido
        pedido.bodeguero = request.user
        pedido.estado = 'preparando'
        pedido.fecha_preparacion = timezone.now()
        pedido.save()
        
        messages.success(request, f'Orden de bodega #{orden.id} aceptada.')
    
    return redirect('bodeguero_dashboard')

@login_required
def preparar_pedido(request, orden_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('bodeguero_dashboard')
    
    orden = get_object_or_404(OrdenBodega, id=orden_id, bodeguero=request.user)
    
    if request.method == 'POST':
        orden.estado = 'completada'
        orden.fecha_completado = timezone.now()
        orden.save()
        
        # Actualizar pedido según tipo de entrega
        pedido = orden.pedido
        if pedido.tipo_entrega == 'domicilio':
            # Para entrega a domicilio: va al contador para registrar entrega
            pedido.estado = 'listo_entrega'
        else:
            # Para retiro en tienda: va al vendedor para registrar despacho
            pedido.estado = 'listo_despacho'
        pedido.save()
        
        tipo_entrega_texto = "entrega a domicilio" if pedido.tipo_entrega == 'domicilio' else "retiro en tienda"
        messages.success(request, f'Pedido #{pedido.id} preparado y listo para {tipo_entrega_texto}.')
    
    return redirect('bodeguero_dashboard')

@login_required
def entregar_a_vendedor(request, orden_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('bodeguero_dashboard')
    
    orden = get_object_or_404(OrdenBodega, id=orden_id, bodeguero=request.user, estado='completada')
    
    if request.method == 'POST':
        vendedor_id = request.POST.get('vendedor')
        
        try:
            vendedor = User.objects.get(id=vendedor_id, perfil__tipo_usuario='vendedor')
            
            orden.estado = 'entregada'
            orden.fecha_entrega_vendedor = timezone.now()
            orden.save()
            
            # Actualizar pedido
            pedido = orden.pedido
            pedido.vendedor = vendedor
            pedido.save()
            
            messages.success(request, f'Pedido #{pedido.id} entregado al vendedor.')
        except User.DoesNotExist:
            messages.error(request, 'Vendedor no encontrado.')
    
    return redirect('bodeguero_dashboard')

@login_required
def contador_dashboard(request):
    # Verificar que el usuario sea contador
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_contador():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    # Pedidos con transferencia pendiente de confirmación
    pedidos_transferencia = Pedido.objects.filter(
        metodo_pago='transferencia',
        pago_confirmado=False
    ).order_by('fecha')
    
    # Pedidos listos para entrega a domicilio
    pedidos_listos_entrega = Pedido.objects.filter(
        estado='listo_entrega',
        tipo_entrega='domicilio'
    ).order_by('fecha')
    
    # Pedidos entregados a domicilio
    pedidos_entregados = Pedido.objects.filter(
        estado='entregado',
        tipo_entrega='domicilio'
    ).order_by('-fecha')[:10]
    
    context = {
        'pedidos_transferencia': pedidos_transferencia,
        'pedidos_listos_entrega': pedidos_listos_entrega,
        'pedidos_entregados': pedidos_entregados,
        'perfil': request.user.perfil,
    }
    return render(request, 'productos/contador_dashboard.html', context)

@login_required
def confirmar_pago_transferencia(request, pedido_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_contador():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('contador_dashboard')
    
    pedido = get_object_or_404(Pedido, id=pedido_id, metodo_pago='transferencia', pago_confirmado=False)
    
    if request.method == 'POST':
        # Descontar stock si no se ha hecho
        if not pedido.stock_actualizado:
            for item in pedido.items.all():
                producto = item.producto
                if producto.stock >= item.cantidad:
                    producto.stock = max(producto.stock - item.cantidad, 0)
                    producto.save()
                else:
                    messages.warning(request, f"Stock insuficiente para {producto.nombre}")
        
        pedido.pago_confirmado = True
        pedido.contador = request.user
        pedido.fecha_confirmacion_pago = timezone.now()
        pedido.estado = 'pagado'  # Cambiar a "pagado" en lugar de "aprobado"
        pedido.stock_actualizado = True
        pedido.save()
        
        messages.success(request, f'Pago del pedido #{pedido.id} confirmado. El pedido está pendiente de aprobación.')
    
    return redirect('contador_dashboard')

@login_required
def registrar_entrega(request, pedido_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_contador():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('contador_dashboard')
    
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='listo_entrega')
    
    if request.method == 'POST':
        pedido.estado = 'entregado'
        pedido.fecha_entrega = timezone.now()
        pedido.save()
        
        # Descontar stock si no se ha hecho
        if not pedido.stock_actualizado:
            for item in pedido.items.all():
                producto = item.producto
                producto.stock = max(producto.stock - item.cantidad, 0)
                producto.save()
            pedido.stock_actualizado = True
            pedido.save()
        
        messages.success(request, f'Entrega del pedido #{pedido.id} registrada.')
    
    return redirect('contador_dashboard')

@login_required
def client_dashboard(request):
    # Verificar que el usuario sea cliente
    if hasattr(request.user, 'perfil') and not request.user.perfil.tipo_usuario == 'cliente':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    # Historial de compras del cliente
    historial_compras = Pedido.objects.filter(cliente=request.user).order_by('-fecha')
    
    # Productos recomendados basados en categorías populares
    categorias_populares = PedidoItem.objects.values('producto__categoria').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:3]
    
    productos_recomendados = ProductoTienda.objects.filter(
        categoria__in=[cat['producto__categoria'] for cat in categorias_populares]
    )[:6]
    
    context = {
        'perfil': request.user.perfil,
        'historial_compras': historial_compras,
        'productos_recomendados': productos_recomendados,
    }
    return render(request, 'productos/client_dashboard.html', context)

@login_required
def subir_comprobante(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    
    if request.method == 'POST':
        comprobante = request.FILES.get('comprobante')
        if comprobante:
            pedido.comprobante_transferencia = comprobante
            pedido.save()
            messages.success(request, 'Comprobante subido exitosamente. Espera la confirmación del contador.')
            return redirect('client_dashboard')
        else:
            messages.error(request, 'Debes subir un comprobante de transferencia.')
    
    return render(request, 'productos/subir_comprobante.html', {'pedido': pedido})

# Vistas CRUD para Bodeguero
@login_required
def bodeguero_crear_producto(request):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('bodeguero_dashboard')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('bodeguero_catalogo')
    else:
        form = ProductoForm()
    
    return render(request, 'productos/bodeguero_crear_producto.html', {'form': form})

@login_required
def bodeguero_editar_producto(request, producto_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('bodeguero_dashboard')
    
    producto = get_object_or_404(ProductoTienda, id=producto_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('bodeguero_catalogo')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'productos/bodeguero_editar_producto.html', {'form': form, 'producto': producto})

@login_required
def bodeguero_eliminar_producto(request, producto_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('bodeguero_dashboard')
    
    producto = get_object_or_404(ProductoTienda, id=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect('bodeguero_catalogo')
    
    return render(request, 'productos/bodeguero_confirmar_eliminar.html', {'producto': producto})

@login_required
def bodeguero_catalogo(request):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_bodeguero():
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    productos = ProductoTienda.objects.all().order_by('categoria', 'nombre')
    nombre = request.GET.get('nombre')
    categoria = request.GET.get('categoria')
    
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if categoria and categoria != 'Todas':
        productos = productos.filter(categoria__iexact=categoria)
    
    categorias = ProductoTienda.objects.values_list('categoria', flat=True).distinct()
    paginator = Paginator(productos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'productos/bodeguero_catalogo.html', {
        'page_obj': page_obj,
        'categorias': categorias,
        'nombre_actual': nombre or '',
        'categoria_actual': categoria or 'Todas'
    })

@login_required
def registrar_despacho(request, pedido_id):
    if not hasattr(request.user, 'perfil') or not request.user.perfil.es_vendedor():
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('vendedor_dashboard')
    
    pedido = get_object_or_404(Pedido, id=pedido_id, estado='listo_despacho')
    
    if request.method == 'POST':
        pedido.estado = 'despachado'
        pedido.fecha_entrega = timezone.now()
        pedido.save()
        
        messages.success(request, f'Despacho del pedido #{pedido.id} registrado exitosamente.')
    
    return redirect('vendedor_dashboard')
