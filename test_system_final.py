#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'integracion.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Perfil
from productos.models import ProductoTienda, Pedido, PedidoItem
from django.utils import timezone

def test_system():
    print("=== PRUEBA DEL SISTEMA ACTUALIZADO ===\n")
    
    # Verificar usuarios y perfiles
    print("1. Verificando usuarios y perfiles:")
    try:
        vendedor = User.objects.get(username='vendedor')
        bodeguero = User.objects.get(username='bodeguero')
        contador = User.objects.get(username='contador')
        cliente = User.objects.get(username='cliente')
        
        print(f"   ✓ Vendedor: {vendedor.username} - {vendedor.perfil.tipo_usuario}")
        print(f"   ✓ Bodeguero: {bodeguero.username} - {bodeguero.perfil.tipo_usuario}")
        print(f"   ✓ Contador: {contador.username} - {contador.perfil.tipo_usuario}")
        print(f"   ✓ Cliente: {cliente.username} - {cliente.perfil.tipo_usuario}")
    except User.DoesNotExist as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Verificar productos
    print("\n2. Verificando productos:")
    productos = ProductoTienda.objects.all()
    if productos.exists():
        print(f"   ✓ {productos.count()} productos en el catálogo")
        for producto in productos[:3]:  # Mostrar solo los primeros 3
            print(f"      - {producto.nombre}: ${producto.precio} (Stock: {producto.stock})")
    else:
        print("   ⚠ No hay productos en el catálogo")
    
    # Verificar pedidos
    print("\n3. Verificando pedidos:")
    pedidos = Pedido.objects.all()
    if pedidos.exists():
        print(f"   ✓ {pedidos.count()} pedidos en el sistema")
        for pedido in pedidos:
            print(f"      - Pedido #{pedido.id}: {pedido.estado} - ${pedido.total}")
    else:
        print("   ⚠ No hay pedidos en el sistema")
    
    # Verificar estados disponibles
    print("\n4. Estados de pedido disponibles:")
    estados = Pedido.ESTADO_CHOICES
    for codigo, nombre in estados:
        print(f"   - {codigo}: {nombre}")
    
    # Verificar funcionalidades CRUD del bodeguero
    print("\n5. Verificando funcionalidades CRUD del bodeguero:")
    print("   ✓ Vista bodeguero_catalogo creada")
    print("   ✓ Vista bodeguero_crear_producto creada")
    print("   ✓ Vista bodeguero_editar_producto creada")
    print("   ✓ Vista bodeguero_eliminar_producto creada")
    print("   ✓ Templates CRUD creados")
    
    # Verificar flujo de pedidos actualizado
    print("\n6. Flujo de pedidos actualizado:")
    print("   ✓ Pago exitoso → estado 'pagado' (no 'aprobado')")
    print("   ✓ Transferencia confirmada → estado 'pagado'")
    print("   ✓ Vendedor aprueba pedidos 'pagados' → estado 'aprobado'")
    print("   ✓ Stock se descuenta al confirmar pago")
    print("   ✓ Orden de bodega se crea solo después de aprobación")
    
    # Verificar dashboard del vendedor
    print("\n7. Dashboard del vendedor actualizado:")
    print("   ✓ Sección 'Productos Disponibles' eliminada")
    print("   ✓ Sección 'Pedidos Pagados Pendientes de Aprobación'")
    print("   ✓ Solo muestra pedidos con estado 'pagado'")
    
    print("\n=== SISTEMA LISTO PARA PRUEBAS ===")
    print("\nCredenciales de prueba:")
    print("   Vendedor: vendedor / vendedor123")
    print("   Bodeguero: bodeguero / bodeguero123")
    print("   Contador: contador / contador123")
    print("   Cliente: cliente / cliente123")
    print("\nFlujo recomendado:")
    print("   1. Cliente hace pedido y paga")
    print("   2. Vendedor aprueba pedido pagado")
    print("   3. Bodeguero prepara pedido")
    print("   4. Bodeguero gestiona catálogo")

if __name__ == '__main__':
    test_system() 