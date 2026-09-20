"""
Vistas de SEO a nivel de sitio (no pertenecen a ninguna app en concreto):
robots.txt y sitemap.xml. Construyen las URLs con el dominio real de la
petición (request.build_absolute_uri), así que funcionan igual en
localhost que en producción sin tocar nada al desplegar.
"""
from django.conf import settings
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme

from blog.models import Post
from scanner.models import Ticker
from .translations import SUPPORTED_LANGS

STATIC_SITEMAP_PATHS = [
    "/",
    "/?asset=GOLD",
    "/?asset=EURUSD",
    "/?asset=BTCUSD",
    "/estrategias/",
    "/interes-compuesto/",
    "/riesgo-beneficio/",
    "/fair-value-gap/",
    "/scanner/",
    "/blog/",
    "/acerca-de/",
    "/contacto/",
    "/privacidad/",
    "/disclaimer/",
    "/terminos/",
]


def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def ads_txt(request):
    """
    Declara ante los rastreadores de AdSense que este sitio está
    autorizado a vender su propio inventario publicitario — sin este
    archivo, Google no aprueba el sitio para mostrar anuncios. El ID
    "f08c47fec0942fa0" es un identificador fijo de Google (Certification
    Authority ID), igual para todos los publishers, no es un dato propio.
    """
    if not settings.GOOGLE_ADSENSE_CLIENT_ID:
        return HttpResponse("", content_type="text/plain")

    pub_id = settings.GOOGLE_ADSENSE_CLIENT_ID.removeprefix("ca-pub-")
    line = f"google.com, pub-{pub_id}, DIRECT, f08c47fec0942fa0"
    return HttpResponse(line, content_type="text/plain")


def sitemap_xml(request):
    urls = [request.build_absolute_uri(path) for path in STATIC_SITEMAP_PATHS]

    symbols = Ticker.objects.filter(is_active=True).values_list("symbol", flat=True)
    urls += [request.build_absolute_uri(f"/scanner/accion/{symbol}/") for symbol in symbols]

    slugs = Post.objects.filter(is_published=True).values_list("slug", flat=True)
    urls += [request.build_absolute_uri(f"/blog/{slug}/") for slug in slugs]

    items = "".join(f"<url><loc>{escape(url)}</loc></url>" for url in urls)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{items}"
        "</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml")


def set_language(request, lang):
    """Guarda el idioma elegido en una cookie y regresa a la página anterior."""
    if lang not in SUPPORTED_LANGS:
        lang = SUPPORTED_LANGS[0]

    next_url = request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = "/"
    # Si la página anterior traía ?lang=xx, ese parámetro manda sobre la
    # cookie (ver config.context_processors._resolve_lang): sin quitarlo el
    # botón ES/EN guardaba la cookie pero la página seguía en el idioma de
    # la URL. Se elimina y el resto de la query se conserva.
    parts = urlsplit(next_url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "lang"]
    next_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    response = redirect(next_url)
    response.set_cookie("site_lang", lang, max_age=365 * 24 * 60 * 60)
    return response


def legacy_prediction_redirect(request):
    """/prediccion/ (la antigua "Trading con IA") ahora vive dentro de
    Trading Análisis. Redirección permanente para no romper enlaces viejos
    (posts del blog, buscadores): conserva ?asset= y ?lang= cuando aplican."""
    from tools.analysis import ASSETS

    params = {}
    asset = request.GET.get("asset")
    if asset in ASSETS:
        params["asset"] = asset
    lang = request.GET.get("lang")
    if lang in SUPPORTED_LANGS:
        params["lang"] = lang
    target = "/" + (f"?{urlencode(params)}" if params else "")
    return HttpResponsePermanentRedirect(target)
