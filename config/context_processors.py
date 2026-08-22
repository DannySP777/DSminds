from django.conf import settings

from .translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations


def _resolve_lang(request):
    # ?lang= manda sobre la cookie — así una URL como /prediccion/?lang=en
    # sirve inglés de forma determinística sin importar qué haya elegido
    # el visitante antes. Necesario para que hreflang apunte a URLs que
    # de verdad sirven ese idioma cuando Google (u otro usuario) las abre
    # directamente, sin la cookie puesta. Ver hreflang() más abajo y los
    # _get_lang() equivalentes en scanner/dsprofeta/blog views.py —
    # deben resolver el idioma exactamente igual, o T/LANG del layout
    # quedaría desincronizado del contenido que arma cada vista.
    lang = request.GET.get("lang") or request.COOKIES.get("site_lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def language(request):
    lang = _resolve_lang(request)
    return {"LANG": lang, "T": get_translations(lang)}


def hreflang(request):
    query = request.GET.copy()
    urls = {}
    for lang in SUPPORTED_LANGS:
        query["lang"] = lang
        urls[lang] = f"https://www.dsminds.com{request.path}?{query.urlencode()}"
    # x_default (guion bajo: las plantillas de Django no resuelven guiones
    # en {{ foo.bar-baz }}) — la versión que se muestra cuando ningún
    # hreflang calza con el idioma del visitante, el idioma por defecto.
    urls["x_default"] = urls[DEFAULT_LANG]
    return {"HREFLANG_URLS": urls}


def analytics(request):
    return {
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
        "GOOGLE_ADSENSE_CLIENT_ID": settings.GOOGLE_ADSENSE_CLIENT_ID,
    }
