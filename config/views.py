"""
Vistas de SEO a nivel de sitio (no pertenecen a ninguna app en concreto):
robots.txt y sitemap.xml. Construyen las URLs con el dominio real de la
petición (request.build_absolute_uri), así que funcionan igual en
localhost que en producción sin tocar nada al desplegar.
"""
from django.conf import settings
from django.db.models import Max
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme

from blog.models import Post
from scanner.models import ScanResult, Ticker
from .translations import SUPPORTED_LANGS

# Fecha del último rediseño sitewide (paleta clara + cabecera/pie oscuros
# con acento neón + portada Trading Análisis): al cambiar el HTML/CSS de
# TODO el sitio, el contenido servido de cada URL estática cambió de
# verdad en esta fecha — es el <lastmod> más honesto que se puede dar sin
# trackear ediciones página por página. Actualizar a mano el día de otro
# cambio grande de plantillas/diseño que afecte a todo el sitio.
SITE_REDESIGN_DATE = "2026-09-19"

# path -> (changefreq, priority). No son promesas exactas para Google,
# son una señal de qué tan seguido cambia el contenido real de cada
# sección, para que reparta mejor su presupuesto de rastreo: la home y el
# scanner traen datos de mercado nuevos todos los días, las calculadoras
# y "Acerca de" casi no cambian, y lo legal cambia menos todavía.
STATIC_SITEMAP_META = {
    "/": ("daily", "1.0"),
    "/?asset=GOLD": ("daily", "0.9"),
    "/?asset=EURUSD": ("daily", "0.9"),
    "/?asset=BTCUSD": ("daily", "0.9"),
    "/estrategias/": ("monthly", "0.6"),
    "/interes-compuesto/": ("monthly", "0.6"),
    "/riesgo-beneficio/": ("monthly", "0.6"),
    "/fair-value-gap/": ("monthly", "0.6"),
    "/scanner/": ("daily", "0.9"),
    "/blog/": ("daily", "0.7"),
    "/acerca-de/": ("yearly", "0.3"),
    "/contacto/": ("yearly", "0.3"),
    "/privacidad/": ("yearly", "0.2"),
    "/disclaimer/": ("yearly", "0.2"),
    "/terminos/": ("yearly", "0.2"),
}

STATIC_SITEMAP_PATHS = list(STATIC_SITEMAP_META.keys())


def _sitemap_entry(loc, lastmod=None, changefreq=None, priority=None):
    parts = [f"<loc>{escape(loc)}</loc>"]
    if lastmod:
        parts.append(f"<lastmod>{lastmod}</lastmod>")
    if changefreq:
        parts.append(f"<changefreq>{changefreq}</changefreq>")
    if priority:
        parts.append(f"<priority>{priority}</priority>")
    return "<url>" + "".join(parts) + "</url>"


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
    entries = []

    for path in STATIC_SITEMAP_PATHS:
        changefreq, priority = STATIC_SITEMAP_META[path]
        entries.append(_sitemap_entry(
            request.build_absolute_uri(path),
            lastmod=SITE_REDESIGN_DATE,
            changefreq=changefreq,
            priority=priority,
        ))

    # Fecha real del último dato de cada ticker (última fila de
    # ScanResult), no una fecha inventada: cada vez que el scan diario
    # corre, esa página sí cambió de verdad.
    symbols = Ticker.objects.filter(is_active=True).values_list("symbol", flat=True)
    latest_scan_by_symbol = dict(
        ScanResult.objects.filter(ticker__symbol__in=symbols)
        .values("ticker__symbol")
        .annotate(latest=Max("date"))
        .values_list("ticker__symbol", "latest")
    )
    for symbol in symbols:
        lastmod = latest_scan_by_symbol.get(symbol)
        entries.append(_sitemap_entry(
            request.build_absolute_uri(f"/scanner/accion/{symbol}/"),
            lastmod=lastmod.isoformat() if lastmod else None,
            changefreq="daily",
            priority="0.6",
        ))

    # published_at es lo único que guarda el modelo Post (no hay
    # updated_at) — se usa como lastmod porque es la fecha real más
    # cercana a "esta página cambió" que tenemos.
    posts = Post.objects.filter(is_published=True).values_list("slug", "published_at")
    for slug, published_at in posts:
        entries.append(_sitemap_entry(
            request.build_absolute_uri(f"/blog/{slug}/"),
            lastmod=published_at.date().isoformat() if published_at else None,
            changefreq="monthly",
            priority="0.5",
        ))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{''.join(entries)}"
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
