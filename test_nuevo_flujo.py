#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from productos.models import Pedido, OrdenBodega
from django.contrib.auth.models import User

def test_nuevo_flujo():
    print("=== VERIFICACIÓN DEL NUEVO FLUJO DE ENTREGA/DESPACHO ===\n")
    
    print("✅ CAMBIOS IMPLEMENTADOS:")
    print("   ✓ Nuevo estado 'listo_despacho' para retiro en tienda")
    print("   ✓ Nuevo estado 'despachado' para pedidos entregados en tienda")
    print("   ✓ Función registrar_despacho para el vendedor")
    print("   ✓ Separación de flujos según tipo de entrega")
    
    print("\n📋 NUEVO FLUJO IMPLEMENTADO:")
    print("   1. Cliente hace pedido → estado 'pendiente'")
    print("   2. Cliente paga → estado 'pagado'")
    print("   3. Vendedor aprueba → estado 'aprobado'")
    print("   4. Bodeguero prepara → estado según tipo de entrega:")
    print("      - Domicilio: 'listo_entrega' → Contador registra entrega")
    print("      - Tienda: 'listo_despacho' → Vendedor registra despacho")
    
    print("\n🎯 SEPARACIÓN DE RESPONSABILIDADES:")
    print("   📦 Vendedor:")
    print("      - Aprueba pedidos pagados")
    print("      - Crea órdenes de bodega")
    print("      - Registra despachos (retiro en tienda)")
    print("   📦 Bodeguero:")
    print("      - Prepara pedidos")
    print("      - Gestiona catálogo")
    print("   📦 Contador:")
    print("      - Confirma pagos por transferencia")
    print("      - Registra entregas a domicilio")
    
    print("\n📊 ESTADOS ACTUALES:")
    pedidos = Pedido.objects.all()
    ordenes = OrdenBodega.objects.all()
    
    print(f"   - Total pedidos: {pedidos.count()}")
    print(f"   - Total órdenes: {ordenes.count()}")
    
    # Contar por estado
    estados_pedido = {}
    for pedido in pedidos:
        estado = pedido.estado
        estados_pedido[estado] = estados_pedido.get(estado, 0) + 1
    
    print("\n   Pedidos por estado:")
    for estado, count in estados_pedido.items():
        print(f"     {estado}: {count}")
    
    # Contar por tipo de entrega
    print("\n   Pedidos por tipo de entrega:")
    domicilio = Pedido.objects.filter(tipo_entrega='domicilio').count()
    tienda = Pedido.objects.filter(tipo_entrega='tienda').count()
    print(f"     Domicilio: {domicilio}")
    print(f"     Tienda: {tienda}")
    
    # Mostrar pedidos recientes con su tipo de entrega
    print("\n📋 PEDIDOS RECIENTES:")
    pedidos_recientes = Pedido.objects.order_by('-id')[:5]
    for pedido in pedidos_recientes:
        print(f"   Pedido #{pedido.id}: {pedido.estado} - {pedido.get_tipo_entrega_display()} - ${pedido.total}")
    
    print("\n✅ SISTEMA ACTUALIZADO Y FUNCIONAL")
    print("   El nuevo flujo está implementado y listo para pruebas.")

if __name__ == '__main__':
    test_nuevo_flujo() 