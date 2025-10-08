# productos/models.py
from django.db import models
from django.contrib.auth.models import User


class Producto(models.Model):
    codigo_producto = models.CharField(max_length=50)
    marca = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_producto})"


class Precio(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='precios'
    )
    fecha = models.DateTimeField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} - {self.valor}"


class ProductoTienda(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    categoria = models.CharField(max_length=100, default="General")  # Categoría por defecto

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('preparando', 'Preparando'),
        ('listo_entrega', 'Listo para Entrega'),
        ('listo_despacho', 'Listo para Despacho'),
        ('entregado', 'Entregado'),
        ('despachado', 'Despachado'),
        ('cancelado', 'Cancelado'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
        ('transferencia', 'Transferencia'),
    ]
    
    TIPO_ENTREGA_CHOICES = [
        ('tienda', 'Retiro en Tienda'),
        ('domicilio', 'Despacho a Domicilio'),
    ]
    
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos_cliente')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos_vendedor', null=True, blank=True)
    bodeguero = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos_bodeguero', null=True, blank=True)
    contador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos_contador', null=True, blank=True)
    
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_preparacion = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='debito'
    )
    
    tipo_entrega = models.CharField(
        max_length=20,
        choices=TIPO_ENTREGA_CHOICES,
        default='tienda'
    )
    
    direccion_entrega = models.TextField(blank=True, null=True)
    telefono_contacto = models.CharField(max_length=20, blank=True, null=True)
    
    total = models.DecimalField(max_digits=10, decimal_places=2)
    mercadopago_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    # Para pagos por transferencia
    comprobante_transferencia = models.ImageField(upload_to='comprobantes/', null=True, blank=True)
    pago_confirmado = models.BooleanField(default=False)
    fecha_confirmacion_pago = models.DateTimeField(null=True, blank=True)
    
    stock_actualizado = models.BooleanField(
        default=False,
        help_text="Indica si ya se descontó el stock al confirmar el pago"
    )
    
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Pedido #{self.id} - {self.cliente.username} - {self.estado}'
    
    def puede_aprobar_vendedor(self):
        return self.estado == 'pendiente'
    
    def puede_preparar_bodeguero(self):
        return self.estado == 'aprobado'
    
    def puede_confirmar_pago_contador(self):
        return self.estado == 'pendiente' and self.metodo_pago == 'transferencia' and not self.pago_confirmado


class PedidoItem(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(
        ProductoTienda,
        on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.producto.nombre} x{self.cantidad}'

class Reclamo(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_proceso", "En proceso"),
        ("resuelto", "Resuelto"),
        ("rechazado", "Rechazado"),
    ]

    cliente = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reclamos"
    )
    pedido = models.ForeignKey(
        Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name="reclamos"
    )
    nombre = models.CharField(max_length=150, null=True, blank=True)
    correo = models.EmailField(null=True, blank=True)
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default="pendiente"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Reclamo #{self.id} - {self.cliente.username} - {self.estado}"

class OrdenBodega(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('preparando', 'Preparando'),
        ('completada', 'Completada'),
        ('entregada', 'Entregada al Vendedor'),
    ]
    
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='orden_bodega')
    bodeguero = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordenes_bodega', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    fecha_entrega_vendedor = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f'Orden Bodega #{self.id} - Pedido #{self.pedido.id} - {self.estado}'