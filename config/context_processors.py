from django.conf import settings

from .translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations


def language(request):
    lang = request.COOKIES.get("site_lang", DEFAULT_LANG)
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    return {"LANG": lang, "T": get_translations(lang)}


def analytics(request):
    return {"GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID}
