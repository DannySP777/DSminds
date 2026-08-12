from django.db import models
from django.urls import reverse


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField(
        help_text="Se renderiza como HTML sin sanitizar (safe) — solo para contenido de confianza."
    )
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog-detail", kwargs={"slug": self.slug})


class Page(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Feedback(models.Model):
    """
    Sugerencias/comentarios enviados desde /contacto/. Intencionalmente
    no se muestran en ninguna página pública — solo visibles desde el
    panel de administración (/admin/), para el equipo del sitio.
    """
    name = models.CharField("nombre", max_length=120, blank=True)
    email = models.EmailField("correo", blank=True)
    message = models.TextField("mensaje")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField("leído", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "sugerencia/comentario"
        verbose_name_plural = "sugerencias/comentarios"

    def __str__(self):
        return f"{self.name or 'Anónimo'} — {self.created_at:%d/%m/%Y %H:%M}"
