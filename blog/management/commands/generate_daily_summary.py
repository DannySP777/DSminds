from django.core.management.base import BaseCommand

from blog.models import Post
from blog.services import build_daily_summary


class Command(BaseCommand):
    help = (
        "Genera (o actualiza) el post de resumen diario de mercado a partir del "
        "scanner, el calendario económico y los fundamentales ya guardados."
    )

    def handle(self, *args, **options):
        data = build_daily_summary()
        if not data:
            self.stdout.write(self.style.WARNING(
                "No hay resultados del scanner todavía; corre run_scan primero."
            ))
            return

        post, created = Post.objects.update_or_create(
            slug=data["slug"],
            defaults={
                "title": data["title"],
                "excerpt": data["excerpt"],
                "body": data["body"],
                "published_at": data["published_at"],
                "is_published": True,
            },
        )
        action = "Creado" if created else "Actualizado"
        self.stdout.write(self.style.SUCCESS(f"{action} post: {post.title} ({post.get_absolute_url()})"))
