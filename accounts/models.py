from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
        ('bodeguero', 'Bodeguero'),
        ('contador', 'Contador'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nombre_completo = models.CharField(max_length=200)
    direccion = models.CharField(max_length=300)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    # Campos específicos para Vendedor
    comision_ventas = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Porcentaje de comisión por ventas")
    ventas_mes = models.IntegerField(default=0, help_text="Número de ventas realizadas este mes")
    
    # Campos específicos para Bodeguero
    area_responsable = models.CharField(max_length=100, blank=True, null=True, help_text="Área del almacén bajo su responsabilidad")
    experiencia_anios = models.IntegerField(default=0, help_text="Años de experiencia en gestión de inventario")
    
    # Campos específicos para Contador
    especialidad = models.CharField(max_length=100, blank=True, null=True, help_text="Especialidad contable (ej: auditoría, costos, etc.)")
    certificaciones = models.TextField(blank=True, null=True, help_text="Certificaciones profesionales")

    def __str__(self):
        return f"{self.nombre_completo} ({self.get_tipo_usuario_display()})"
    
    def es_vendedor(self):
        return self.tipo_usuario == 'vendedor'
    
    def es_bodeguero(self):
        return self.tipo_usuario == 'bodeguero'
    
    def es_contador(self):
        return self.tipo_usuario == 'contador'
    
    def es_admin(self):
        return self.tipo_usuario == 'admin' or self.user.is_superuser

# Señal para crear automáticamente el Perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        # Determinar el tipo de usuario basado en si es superuser
        tipo_usuario = 'admin' if instance.is_superuser else 'cliente'
        Perfil.objects.create(user=instance, tipo_usuario=tipo_usuario)
