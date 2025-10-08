#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from productos.models import Pedido, OrdenBodega
from django.contrib.auth.models import User

def test_estados():
    print("=== VERIFICACIÓN DE ESTADOS ===\n")
    
    # Verificar pedidos recientes
    print("1. Pedidos recientes:")
    pedidos_recientes = Pedido.objects.order_by('-id')[:5]
    for pedido in pedidos_recientes:
        print(f"   Pedido #{pedido.id}: {pedido.estado} - ${pedido.total}")
        if hasattr(pedido, 'orden_bodega'):
            print(f"      Orden Bodega: {pedido.orden_bodega.estado}")
        else:
            print(f"      Sin orden de bodega")
    
    # Verificar órdenes de bodega
    print("\n2. Órdenes de bodega:")
    ordenes = OrdenBodega.objects.order_by('-id')[:5]
    for orden in ordenes:
        print(f"   Orden #{orden.id} - Pedido #{orden.pedido.id}: {orden.estado}")
        if orden.bodeguero:
            print(f"      Bodeguero: {orden.bodeguero.username}")
        else:
            print(f"      Sin bodeguero asignado")
    
    # Verificar bodegueros disponibles
    print("\n3. Bodegueros disponibles:")
    bodegueros = User.objects.filter(perfil__tipo_usuario='bodeguero')
    for bodeguero in bodegueros:
        print(f"   ID: {bodeguero.id} - {bodeguero.username}")
    
    # Verificar órdenes por estado
    print("\n4. Órdenes por estado:")
    estados = ['pendiente', 'aceptada', 'preparando', 'completada', 'entregada']
    for estado in estados:
        count = OrdenBodega.objects.filter(estado=estado).count()
        print(f"   {estado}: {count} órdenes")
    
    # Verificar pedidos por estado
    print("\n5. Pedidos por estado:")
    estados_pedido = ['pendiente', 'pagado', 'aprobado', 'rechazado', 'preparando', 'listo_entrega', 'entregado', 'cancelado']
    for estado in estados_pedido:
        count = Pedido.objects.filter(estado=estado).count()
        print(f"   {estado}: {count} pedidos")

if __name__ == '__main__':
    test_estados() 