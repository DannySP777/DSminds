# DSMarketLearning

Scanner diario de acciones con potencial de inversión, noticias de mercado y gráficas — contenido informativo, no asesoría financiera.

## Estructura del proyecto

```
DSMarketScan/
├── config/          # settings del proyecto Django (por crear con django-admin)
├── scanner/         # app: lógica del scanner diario (yfinance, indicadores)
├── news/            # app: noticias diarias de mercado
├── blog/            # app: posts, páginas del sitio
├── templates/        # plantillas HTML compartidas
├── static/            # CSS, JS, imágenes
│   ├── css/
│   ├── js/
│   └── images/
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup inicial (Windows, PowerShell, en VS Code)

Abre esta carpeta en VS Code y corre en la terminal integrada:

```powershell
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar variables de entorno
copy .env.example .env

# 5. Iniciar el proyecto Django (genera manage.py y config/settings.py reales)
django-admin startproject config .

# 6. Convertir scanner/news/blog en apps Django reales
python manage.py startapp scanner
python manage.py startapp news
python manage.py startapp blog

# 7. Migrar base de datos inicial
python manage.py migrate

# 8. Crear superusuario para el panel admin
python manage.py createsuperuser

# 9. Correr servidor local
python manage.py runserver
```

> Nota: los pasos 6 recrearán models.py/admin.py etc. en scanner/news/blog —
> mantén el contenido que ya tengas en esos archivos o combínalo con lo generado.

## Próximos pasos

1. Definir los indicadores del scanner (RSI, volumen relativo, rupturas) en `scanner/services.py`
2. Configurar `APScheduler` en `scanner/tasks.py` para correr el scan diario
3. Conectar la API de noticias en `news/services.py`
4. Generar gráficas con Plotly por ticker
