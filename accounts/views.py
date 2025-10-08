from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from .models import Perfil

# Vista de registro de usuarios con nombre completo, email y dirección
def register_view(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        email = request.POST['email']
        direccion = request.POST['direccion']
        password = request.POST['password']
        password2 = request.POST['password2']
        tipo_usuario = request.POST.get('tipo_usuario', 'cliente')

        # Validación de contraseñas
        if password != password2:
            return render(request, 'accounts/register.html', {'error': 'Las contraseñas no coinciden'})

        # Verificar si el usuario ya existe
        if User.objects.filter(username=email).exists():
            return render(request, 'accounts/register.html', {'error': 'Ya existe un usuario con este correo'})

        # Crear el usuario y perfil
        user = User.objects.create_user(username=email, email=email, password=password)
        perfil = user.perfil
        perfil.nombre_completo = nombre
        perfil.direccion = direccion
        perfil.tipo_usuario = tipo_usuario
        perfil.save()

        messages.success(request, 'Cuenta creada exitosamente. Ahora puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'accounts/register.html')

# Vista de login que acepta username o email
def login_view(request):
    if request.method == 'POST':
        credential = request.POST['email']
        password = request.POST['password']

        # Intentar autenticación usando credential como username
        user = authenticate(request, username=credential, password=password)
        if not user:
            # Si falla, buscar por email
            try:
                u = User.objects.get(email=credential)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            login(request, user)
            # Redirigir según el tipo de usuario
            if user.is_superuser:
                return redirect('panel_admin')
            elif hasattr(user, 'perfil'):
                if user.perfil.es_vendedor():
                    return redirect('vendedor_dashboard')
                elif user.perfil.es_bodeguero():
                    return redirect('bodeguero_dashboard')
                elif user.perfil.es_contador():
                    return redirect('contador_dashboard')
                else:
                    return redirect('client_dashboard')
            else:
                return redirect('client_dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Credenciales incorrectas'})

    return render(request, 'accounts/login.html')

# Vista de logout
def logout_view(request):
    logout(request)
    return redirect('home')
