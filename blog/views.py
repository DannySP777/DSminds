from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from config.translations import DEFAULT_LANG, SUPPORTED_LANGS

from .forms import FeedbackForm
from .models import Post

SUCCESS_MESSAGE = {
    "es": "¡Gracias! Recibimos tu mensaje.",
    "en": "Thanks! We received your message.",
}

MONTH_NAMES = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}


def _get_lang(request):
    # ?lang= manda sobre la cookie — debe resolver igual que
    # config.context_processors._resolve_lang, o T/LANG del layout queda
    # desincronizado del idioma que arma esta vista.
    lang = request.GET.get("lang") or request.COOKIES.get("site_lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def _format_long_date(lang):
    today = date.today()
    month = MONTH_NAMES.get(lang, MONTH_NAMES["es"])[today.month - 1]
    if lang == "en":
        return f"{month} {today.day}, {today.year}"
    return f"{today.day} de {month} de {today.year}"


def post_list(request):
    posts = Post.objects.filter(is_published=True)
    return render(request, "blog/list.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    lang = _get_lang(request)
    return render(request, "blog/detail.html", {
        "post": post,
        "og_title": post.get_title(lang),
        "og_description": post.get_excerpt(lang),
    })


def about(request):
    return render(request, "pages/about.html")


def privacy(request):
    return render(request, "pages/privacy.html", {"today": _format_long_date(_get_lang(request))})


def disclaimer(request):
    return render(request, "pages/disclaimer.html")


def terms(request):
    return render(request, "pages/terms.html", {"today": _format_long_date(_get_lang(request))})


def contact(request):
    lang = _get_lang(request)
    if request.method == "POST":
        form = FeedbackForm(request.POST, lang=lang)
        if form.is_valid():
            form.save()
            messages.success(request, SUCCESS_MESSAGE.get(lang, SUCCESS_MESSAGE["es"]))
            return redirect("page-contact")
    else:
        form = FeedbackForm(lang=lang)

    return render(request, "pages/contact.html", {"form": form})
