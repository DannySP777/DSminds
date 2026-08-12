from django.urls import path

from . import views

urlpatterns = [
    path("", views.post_list, name="blog-list"),
    path("<slug:slug>/", views.post_detail, name="blog-detail"),
]

pages_urlpatterns = [
    path("acerca-de/", views.about, name="page-about"),
    path("contacto/", views.contact, name="page-contact"),
    path("privacidad/", views.privacy, name="page-privacy"),
    path("disclaimer/", views.disclaimer, name="page-disclaimer"),
    path("terminos/", views.terms, name="page-terms"),
]
