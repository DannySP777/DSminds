"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from blog.urls import pages_urlpatterns
from config.views import ads_txt, robots_txt, set_language, sitemap_xml

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots-txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap-xml'),
    path('ads.txt', ads_txt, name='ads-txt'),
    path('idioma/<str:lang>/', set_language, name='set-language'),
    path('', include('scanner.urls')),
    path('noticias/', include('news.urls')),
    path('blog/', include('blog.urls')),
    path('prediccion/', include('dsprofeta.urls')),
    path('', include(pages_urlpatterns)),
]
