# productos/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Reclamo

from .models import ProductoTienda   # o el modelo que uses para productos

class ProductoForm(forms.ModelForm):
    class Meta:
        model = ProductoTienda
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'imagen']

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class DatosContactoForm(forms.Form):
    nombre = forms.CharField(max_length=150)
    correo = forms.EmailField()

class ReclamoForm(forms.ModelForm):
    class Meta:
        model = Reclamo
        fields = ['nombre', 'correo', 'asunto', 'mensaje']