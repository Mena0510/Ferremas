def carrito_total(request):
    carrito = request.session.get('carrito', {})
    try:
        cantidad_total = sum(int(cantidad) for cantidad in carrito.values())
    except Exception:
        cantidad_total = 0
    return {'carrito_total': cantidad_total}
