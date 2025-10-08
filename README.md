pip install --upgrade pip
pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py runserver


para probar mercadopago: 
en una nueva terminal ejecutar "ngrok http 8000"
y obtendras un link como este: Forwarding https://7c52-186-79-92-22.ngrok-free.app -> http://localhost:8000  
Ocupalo en: views.py y en settings.py 

settings.py 

CSRF_TRUSTED_ORIGINS = [
    "https://7c52-186-79-92-22.ngrok-free.app",  # Reemplaza por tu URL actual de ngrok
]

views.py

BASE_URL = "https://7c52-186-79-92-22.ngrok-free.app"

Datos para comprar con credito y APROBACION:

nombre: APRO
Número: 5416 7526 0258 2580
Código de seguridad:
123	
Fecha de caducidad:
11/30
identidad: (OTRO) 123456789

Datos para comprar con debito y RECHAZADO:
nombre: APRO
Número:
4023 6535 2391 4373	
Código de seguridad:
123	
Fecha de caducidad:
11/30
identidad: (OTHE) 123456789



   Email: vendedor@admin.cl
   Nombre: Juan Vendedor
   Tipo: vendedor


   Email: bodeguero@admin.cl
   Nombre: María Bodeguera
   Tipo: bodeguero


   Email: contador@admin.cl
   Nombre: Pedro Contador
   Tipo: contador


cliente@test.cl