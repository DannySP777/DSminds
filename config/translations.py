"""
Traducciones estáticas del "chrome" del sitio (nav, scanner, página Acerca de).

No usamos el framework de i18n de Django (gettext) a propósito: requiere
las herramientas GNU gettext instaladas en el sistema para compilar los
.po a .mo, y no queremos depender de eso en un entorno Windows sin
gettext. En su lugar, el idioma activo se guarda en la cookie
"site_lang" (ver config/context_processors.py) y las plantillas leen
las cadenas de aquí a través de la variable de contexto `T`.

El contenido del blog (artículos educativos y diario del inversionista)
NO está cubierto por esta traducción — vive en la base de datos y
solo existe en español por ahora.
"""

T = {
    "es": {
        # Page title / meta
        "home_title": "DSMarketLearning — Scanner diario de acciones",
        "home_meta_description": "Scanner diario que identifica acciones con RSI en zona de impulso, volumen relativo alto y rupturas de rango. Contenido informativo, no asesoría financiera.",

        # Nav / chrome
        "nav_scanner": "Scanner",
        "nav_news": "Noticias",
        "nav_blog": "Blog",
        "nav_about": "Acerca de",
        "nav_suggestions": "Sugerencias",
        "footer_about": "Acerca de",
        "footer_contact": "Contacto",
        "footer_privacy": "Política de privacidad",
        "footer_disclaimer": "Aviso legal",
        "footer_terms": "Términos de uso",
        "footer_copyright_text": "DSMarketLearning. Contenido informativo con fines educativos — no constituye asesoría financiera. Ver",
        "footer_disclaimer_link": "aviso legal",
        "cookie_text": "Usamos cookies propias y de terceros (incluida publicidad de Google) para analizar el uso del sitio y mostrar anuncios personalizados. Puedes leer más en nuestra",
        "cookie_privacy_link": "política de privacidad",
        "cookie_decline": "Rechazar no esenciales",
        "cookie_accept": "Aceptar",
        "lang_switch_label": "Idioma",

        # Scanner header
        "header_subtitle_text": "Scanner diario de acciones",
        "header_subtitle_title": "Cada día revisamos un grupo de acciones y calculamos señales técnicas de corto plazo (RSI, volumen relativo, rupturas de rango) y de fondo (tendencia vs. su media de 200 días, fuerza relativa vs. el S&P 500). Selecciona una acción en la tabla para ver su gráfica e indicadores.",

        # Disclaimer banner
        "tool_disclaimer_prefix": "⚠ Herramienta con fines educativos e informativos — no es asesoría de inversión ni una recomendación de compra o venta. Invertir implica riesgo de pérdida de capital. Lee el",
        "disclaimer_link_text": "aviso legal completo",

        # Filters
        "filters_toggle": "Filtros avanzados",
        "filters_active_badge": "activos",
        "filter_legend_price_market": "Precio y mercado",
        "filter_price_lt": "Precio menor a",
        "filter_any": "Cualquiera",
        "filter_exchange": "Bolsa",
        "filter_rel_vol_min": "Volumen relativo mín.",
        "filter_legend_key_indicators": "Indicadores clave",
        "filter_score_min": "Score mín.",
        "filter_pe_min": "P/E mín.",
        "filter_pe_max": "P/E máx.",
        "filter_peg_min": "PEG mín.",
        "filter_peg_max": "PEG máx.",
        "filter_cap_min": "Market cap mín. (millones USD)",
        "filter_cap_max": "Market cap máx. (millones USD)",
        "filter_target_min": "Precio objetivo mín. (USD)",
        "filter_target_max": "Precio objetivo máx. (USD)",
        "filter_apply": "Aplicar filtros",
        "filter_clear": "Limpiar filtros",

        # Panels
        "panel_screening": "Screening",
        "panel_chart": "Gráfica",
        "panel_indicators": "Indicadores",
        "panel_indices": "Índices & alertas",

        # Scan date / note
        "scan_stocks_word": "acciones",
        "scan_from": "scan del",
        "scan_top": "Top",
        "scan_best_score_of": "con mejor score de",
        "scan_analyzed": "acciones analizadas",
        "scan_matching_filters": "que cumplen los filtros",
        "scan_note_prefix": "Por defecto mostramos solo las",
        "scan_note_mid": "acciones con mejor puntaje, para no abrumarte con una tabla larga. Usa los",
        "scan_note_link": "filtros avanzados",
        "scan_note_suffix": "para explorar el resto del universo analizado.",
        "scan_note_mid_short": "con mejor puntaje.",
        "scan_note_show_all_link": "ver todas",
        "scan_note_show_less_link": "Mostrar solo el top 10",

        # Table headers + tooltips
        "th_ver": "Ver",
        "tip_ver": "Selecciona una acción para ver su gráfica e indicadores.",
        "th_ticker": "Ticker",
        "tip_ticker": "Símbolo de la acción en bolsa.",
        "th_score": "Score",
        "tip_score": "Puntaje 0-100 que resume varias señales técnicas del día en un solo número, para no tener que interpretar cada indicador por separado.",
        "th_price": "Precio",
        "tip_price": "Último precio de cierre.",
        "th_pe": "P/E",
        "tip_pe": "Precio sobre utilidad (PER). Cuánto paga el mercado por cada dólar de utilidad.",
        "th_peg": "PEG",
        "tip_peg": "P/E ajustado por crecimiento esperado. Por debajo de 1 puede indicar que está barata para su crecimiento.",
        "th_market_cap": "Market cap",
        "tip_market_cap": "Valor total de la empresa en bolsa (precio × acciones en circulación).",
        "th_volume": "Volumen",
        "tip_volume": "Volumen de hoy vs. el promedio de los últimos 20 días. Más de 1x indica más interés del mercado.",
        "th_market": "Mercado",
        "tip_market": "Bolsa donde cotiza la acción (NASDAQ, NYSE, etc.).",
        "th_target": "Precio objetivo",
        "tip_target": "Promedio de los precios objetivo publicados por los analistas que cubren la acción.",
        "th_chart": "Gráfica",
        "tip_chart": "Ver la gráfica de velas con RSI, volumen e indicadores.",
        "th_news": "Noticias",
        "tip_news": "Ver noticias relacionadas con este ticker.",
        "link_ver": "ver",

        # Empty states
        "empty_no_filter_match": "Ningún resultado coincide con los filtros aplicados. Prueba ajustarlos o",
        "empty_clear_link": "límpialos",
        "empty_no_scan": "No hay resultados guardados todavía. Corre",
        "select_stock_for_chart": "Selecciona una acción en la tabla para ver su gráfica.",
        "select_stock_for_indicators": "Selecciona una acción en la tabla para ver sus indicadores.",

        # Methodology
        "methodology_title": "Cómo funciona el score",
        "methodology_p1": (
            "DSMarketLearning diseñó una categorización de acciones definida por un "
            "score que agrupa una decena de indicadores técnicos, lo que permite "
            "tener una idea rápida de qué acciones están en una posición "
            "potencialmente favorable. El score resume todas esas señales en un "
            "solo número de 0 a 100, calculado a partir de señales de corto plazo "
            "(RSI, volumen relativo, ruptura de rango) y de fondo (tendencia "
            "respecto a su media de 200 días, fuerza relativa frente al S&P 500). "
            "Si quieres ver el detalle completo de cada una de esas señales para "
            'una acción en particular, entra a su página individual desde la '
            'columna "Gráfica".'
        ),
        "methodology_pe_peg_label": "P/E y PEG:",
        "methodology_pe_peg_text": "qué tan caro o barato luce el precio frente a las utilidades de la empresa y su crecimiento esperado. Lee más en nuestro artículo sobre",
        "methodology_pe_peg_link": "P/E, PEG y por qué el precio no dice nada por sí solo",
        "methodology_market_cap_label": "Market cap:",
        "methodology_market_cap_text": "el tamaño de la empresa en bolsa — influye en su volatilidad y liquidez.",
        "methodology_volume_label": "Volumen:",
        "methodology_volume_text": "compara el volumen del día contra el promedio de los últimos 20 días; más volumen sugiere mayor interés del mercado.",
        "methodology_market_label": "Mercado:",
        "methodology_market_text": "la bolsa donde cotiza la acción (NASDAQ, NYSE, etc.).",
        "methodology_target_label": "Precio objetivo:",
        "methodology_target_text": "promedio de los precios objetivo que publican los analistas que cubren la acción — entra en más detalle, junto con la recomendación de consenso, en la página de cada acción.",
        "methodology_disclaimer": "Esta información es únicamente educativa. DSMarketLearning no ofrece asesoría de inversión personalizada; lee nuestro",

        # About page
        "about_title": "Acerca de DSMarketLearning",
        "about_intro": "Soy un ingeniero informático amante de las finanzas, con más de 5 años de experiencia siguiendo mercados financieros e invirtiendo por cuenta propia. DSMarketLearning nace de juntar esas dos cosas: uso mis conocimientos de programación para construir herramientas de análisis técnico que yo mismo uso para investigar acciones, y decidí compartirlas abiertamente con fines educativos.",
        "about_h2_what": "Qué es DSMarketLearning",
        "about_what_text": "Es un scanner diario de acciones que calcula señales técnicas (RSI, volumen relativo, ruptura de rango, tendencia respecto a la media móvil de 200 días, fuerza relativa frente al S&P 500) y datos fundamentales (P/E, PEG, deuda/patrimonio, recomendaciones de analistas) para un grupo amplio de acciones de NYSE y NASDAQ. Todo se actualiza automáticamente cada día hábil. El sitio también incluye noticias de mercado, un calendario económico semanal y artículos educativos que explican cómo interpretar cada indicador.",
        "about_h2_methodology": "Metodología, de forma transparente",
        "about_methodology_text": "No hay caja negra: cada indicador que usa el scanner está documentado en la propia página de resultados y en el detalle de cada acción, incluyendo cómo se calcula el puntaje (score) y qué significa cada semáforo. Los datos de mercado provienen de Yahoo Finance a través de la librería pública yfinance; pueden tener errores, retrasos o estar incompletos, y lo dejo explícito donde corresponde.",
        "about_h2_not_advice": "No es asesoría financiera",
        "about_not_advice_prefix": "No soy un asesor de inversión registrado, y nada en este sitio — el scanner, las noticias, los artículos del blog — constituye una recomendación de compra o venta. Es contenido informativo y educativo, pensado para que investigues por tu cuenta, no para reemplazar el criterio propio ni el consejo de un profesional autorizado. Antes de invertir, lee el",
        "about_not_advice_link": "aviso legal completo",
        "about_h2_contact": "Contacto",
        "about_contact_prefix": "¿Preguntas, sugerencias o encontraste un error? Escríbeme desde la página de",
        "about_contact_link": "contacto",

        # Chart panel / ticker detail
        "chart_rel_vol": "Vol. relativo",
        "chart_breakout": "Ruptura",
        "yes": "Sí",
        "no": "No",
        "chart_ref_current_label": "Precio actual:",
        "chart_ref_current_text": "línea blanca sólida — el último precio de cierre disponible.",
        "chart_ref_target_label": "Precio objetivo:",
        "chart_ref_target_text": "línea verde punteada — precio objetivo promedio a 12 meses según los analistas que cubren la acción.",
        "chart_ref_low_label": "Mínimo del trimestre:",
        "chart_ref_low_text": "línea naranja punteada — el precio más bajo de los últimos ~3 meses, como referencia de soporte reciente.",
        "chart_zoom_hint": "Puedes hacer zoom arrastrando un rectángulo sobre la gráfica, o con la rueda del mouse. Doble clic para restablecer la vista.",
        "ticker_title_suffix": "— gráfica y señales técnicas",
        "ticker_meta_description_prefix": "Gráfica de velas de",
        "ticker_meta_description_suffix": "con RSI, volumen y ruptura de rango, con periodos desde 1 minuto hasta mensual.",
        "ticker_last_scan": "Último scan",
        "ticker_price_word": "precio",
        "ticker_rel_vol_word": "volumen relativo",
        "ticker_score_word": "score",
        "ticker_no_results": "Este ticker todavía no tiene resultados guardados del scanner diario.",
        "ticker_see_news": "Ver noticias de",
        "ticker_back_to_scanner": "volver al scanner",
        "ticker_search_placeholder": "Buscar otra acción por símbolo o nombre (ej: MSFT, Tesla)…",
        "ticker_search_btn": "Buscar",
        "ticker_price_chart_h2": "Gráfica de precio",
        "ticker_analysts_h2": "Qué dicen los analistas",
        "ticker_methodology_h2": "Qué muestra esta gráfica",
        "ticker_candles_label": "Velas japonesas:",
        "ticker_candles_text": "verde cuando el cierre del periodo es mayor al de apertura, roja cuando es menor.",
        "ticker_volume_text": "barras coloreadas igual que la vela del mismo periodo.",
        "ticker_rsi_text": "línea inferior con referencias en 70 (sobrecompra) y 30 (sobreventa) — el mismo indicador que usa el scanner diario.",
        "ticker_dotted_line_label": "Línea punteada superior:",
        "ticker_dotted_line_text": "máximo de los últimos 20 periodos, la misma referencia que usa el scanner para detectar rupturas.",
        "ticker_data_disclaimer": "Datos de mercado vía Yahoo Finance, con fines informativos. No es asesoría de inversión — lee el",

        # Indicators panel (fundamentals)
        "fund_score": "puntaje",
        "fund_score_scale": "1 = compra fuerte, 5 = venta",
        "fund_analysts": "analistas",
        "fund_buy": "Compra",
        "fund_hold": "Mantener",
        "fund_sell": "Venta",
        "fund_no_breakdown": "No hay desglose de analistas disponible para",
        "fund_avg_target": "Precio objetivo promedio:",
        "fund_vs_current_price": "vs. precio actual",
        "fund_range": "rango",
        "fund_healthy": "Saludable",
        "fund_moderate": "Moderado",
        "fund_attention": "Atención",
        "fund_no_data": "Sin dato",
        "fund_market_cap": "Market cap",
        "fund_market_cap_desc": "Valor total de la empresa en bolsa (precio × acciones en circulación).",
        "fund_pe_trailing": "P/E (trailing)",
        "fund_pe_forward": "P/E (forward)",
        "fund_pe_forward_desc": "Igual que el P/E, con utilidades estimadas a futuro.",
        "fund_debt_equity": "Deuda/Patrimonio",
        "fund_net_margin": "Margen neto",
        "fund_dividend": "Dividendo",
        "fund_beta": "Beta (riesgo)",
        "fund_disclaimer": "Rangos generales de referencia, no varían por sector. Datos vía Yahoo Finance; pueden estar incompletos. No es asesoría de inversión.",
        "fund_no_data_available": "No hay datos fundamentales disponibles para",
        "fund_na": "N/D",

        # Índices
        "nasdaq": "Nasdaq",
        "sp500": "S&P 500",
        "dow": "Dow Jones",
        "gold": "Oro",
        "oil": "Petróleo",

        # Intervalos de la gráfica
        "1m": "1 min",
        "5m": "5 min",
        "30m": "30 min",
        "1h": "1 hora",
        "4h": "4 horas",
        "1d": "Diario",
        "1wk": "Semanal",
        "1mo": "Mensual",

        # Noticias / calendario
        "news_title": "Noticias de mercado",
        "news_meta_description": "Resumen diario de noticias de Yahoo Finance para las acciones que seguimos en el scanner.",
        "news_intro_prefix": "Noticias de Yahoo Finance para los mismos tickers que cubre el",
        "news_intro_link": "scanner diario",
        "news_intro_suffix": ", así puedes ver qué se dice de una acción justo cuando aparece en los resultados.",
        "news_showing_for": "Mostrando noticias de",
        "news_see_all": "ver todas",
        "calendar_title": "Calendario económico de EE. UU. — esta semana",
        "calendar_disclaimer": "Solo eventos de impacto medio (★★) y alto (★★★): los que más suelen mover el mercado. No se incluyen los de impacto bajo.",
        "calendar_date": "Fecha",
        "calendar_time": "Hora",
        "calendar_event": "Evento",
        "calendar_impact": "Impacto",
        "calendar_forecast": "Pronóstico",
        "calendar_previous": "Anterior",
        "calendar_actual": "Actual",
        "calendar_empty": "Todavía no hay calendario cargado. Corre",
        "news_empty_for_ticker": "No hay noticias guardadas para",
        "news_empty": "Todavía no hay noticias cargadas. Corre",
        "news_empty_suffix": "para traer las últimas de Yahoo Finance.",

        # Blog
        "blog_meta_description": "Guías y análisis sobre indicadores técnicos, lectura de mercado y cómo usar el scanner de DSMarketLearning.",
        "blog_intro": "Guías y análisis sobre indicadores técnicos y cómo interpretar los resultados del scanner.",
        "blog_empty": "Todavía no hay artículos publicados.",

        # Ad slot
        "ad_label": "Publicidad",

        # Legal: comunes
        "last_updated": "Última actualización",

        # Privacidad
        "privacy_title": "Política de privacidad",
        "privacy_meta_description": "Cómo DSMarketLearning recopila y usa datos, incluyendo cookies de publicidad de Google y terceros.",
        "privacy_h2_data": "Qué datos recopilamos",
        "privacy_data_p1": "DSMarketLearning no requiere registro para navegar el sitio. Como cualquier sitio web, nuestro servidor y las herramientas de analítica que usemos pueden registrar automáticamente datos técnicos básicos: dirección IP, tipo de navegador, páginas visitadas y fecha/hora de la visita.",
        "privacy_data_p2_prefix": "Si usas el formulario de",
        "privacy_data_p2_link": "sugerencias y comentarios",
        "privacy_data_p2_suffix": ", guardamos el nombre y correo que ingreses (ambos opcionales) junto con tu mensaje, únicamente para que el equipo lo revise y pueda responderte si lo pediste. Estos mensajes son privados: no se publican ni se muestran a otros visitantes del sitio, y no se comparten con terceros.",
        "privacy_h2_cookies": "Cookies y publicidad",
        "privacy_cookies_p1": "Este sitio puede mostrar anuncios a través de Google AdSense. Google, como proveedor externo, usa cookies (incluida la cookie DoubleClick) para mostrar anuncios basados en tus visitas anteriores a este y otros sitios en internet.",
        "privacy_cookies_li1_prefix": "Puedes inhabilitar la publicidad personalizada visitando la",
        "privacy_cookies_li1_link": "Configuración de anuncios de Google",
        "privacy_cookies_li2_prefix": "También puedes inhabilitar el uso de cookies de terceros con fines publicitarios visitando",
        "privacy_cookies_li3": "Terceros, incluido Google, pueden usar cookies para publicar anuncios según tus visitas anteriores a este sitio o a otros sitios web.",
        "privacy_h2_functional": "Cookies funcionales y traducción automática",
        "privacy_functional_text": "Usamos una cookie propia (no de terceros ni publicitaria) para recordar tu preferencia de idioma (español/inglés) entre visitas. Además, cuando ves el sitio en español, la descripción de cada empresa se traduce automáticamente del inglés usando el servicio de traducción de Google — el texto enviado es información pública de la empresa (no datos personales tuyos).",
        "privacy_h2_analytics": "Analítica",
        "privacy_analytics_text": "Podemos usar herramientas de analítica web (como Google Analytics) para entender cómo se usa el sitio de forma agregada y anónima. Estas herramientas también pueden usar cookies propias o de terceros.",
        "privacy_h2_sharing": "Con quién compartimos datos",
        "privacy_sharing_text": "No vendemos datos personales. Compartimos datos únicamente con proveedores necesarios para operar el sitio (por ejemplo, Google AdSense/Analytics), sujetos a sus propias políticas de privacidad.",
        "privacy_h2_choices": "Tus opciones",
        "privacy_choices_text": "Puedes configurar tu navegador para rechazar cookies; ten en cuenta que algunas funciones del sitio podrían no funcionar correctamente sin ellas.",
        "privacy_contact_prefix": "Si tienes preguntas sobre esta política, escríbenos desde la página de",

        # Disclaimer
        "disclaimer_meta_description": "DSMarketLearning no ofrece asesoría financiera; el contenido es informativo y educativo.",
        "disclaimer_h1": "Aviso legal / Disclaimer",
        "disclaimer_h2_not_advice": "No es asesoría de inversión",
        "disclaimer_not_advice_text": "El contenido publicado en DSMarketLearning — incluyendo los resultados del scanner, indicadores técnicos, noticias y artículos del blog — tiene fines exclusivamente informativos y educativos. Nada de lo publicado aquí constituye una recomendación de compra o venta, ni asesoría financiera, legal o fiscal personalizada.",
        "disclaimer_h2_risk": "Riesgo de pérdida",
        "disclaimer_risk_text": "Invertir en acciones y otros instrumentos financieros implica riesgo, incluida la posible pérdida total del capital invertido. El rendimiento pasado de un instrumento, indicador o estrategia no garantiza resultados futuros.",
        "disclaimer_h2_data": "Sobre los datos e indicadores",
        "disclaimer_data_text_prefix": "Los precios, volúmenes e indicadores (RSI, volumen relativo, rupturas de rango) provienen de fuentes de terceros (como Yahoo Finance vía la librería",
        "disclaimer_data_text_suffix": ") y pueden tener retrasos, errores o interrupciones. No garantizamos su exactitud, integridad o disponibilidad en todo momento.",
        "disclaimer_h2_consult": "Consulta a un profesional",
        "disclaimer_consult_text": "Antes de tomar cualquier decisión financiera, consulta a un asesor de inversión registrado y autorizado en tu jurisdicción, que pueda evaluar tu situación particular.",
        "disclaimer_h2_liability": "Limitación de responsabilidad",
        "disclaimer_liability_text": "DSMarketLearning y sus autores no se hacen responsables de pérdidas o daños derivados del uso de la información publicada en este sitio.",

        # Términos
        "terms_meta_description": "Condiciones de uso del sitio DSMarketLearning.",
        "terms_h2_acceptance": "Aceptación de los términos",
        "terms_acceptance_prefix": "Al usar DSMarketLearning aceptas estos términos de uso y nuestra",
        "terms_acceptance_suffix": ". Si no estás de acuerdo, por favor no uses el sitio.",
        "terms_h2_use": "Uso permitido",
        "terms_use_text": "Puedes navegar y consultar el contenido del sitio para uso personal y no comercial. No está permitido copiar, redistribuir o reutilizar el contenido con fines comerciales sin autorización previa.",
        "terms_h2_ip": "Propiedad intelectual",
        "terms_ip_text": "El diseño, textos y código de DSMarketLearning son propiedad de sus autores, salvo el contenido de terceros (datos de mercado, noticias) que pertenece a sus respectivos titulares.",
        "terms_h2_no_warranty": "Sin garantías",
        "terms_no_warranty_prefix": 'El sitio se ofrece "tal cual", sin garantías de disponibilidad continua, exactitud o ausencia de errores. Ver también nuestro',
        "terms_no_warranty_suffix": "sobre el contenido financiero.",
        "terms_h2_changes": "Cambios a estos términos",
        "terms_changes_text": 'Podemos actualizar estos términos en cualquier momento; la fecha de "última actualización" reflejará el cambio más reciente.',

        # Contacto
        "contact_meta_description": "Envía tus sugerencias, comentarios o reporta errores del sitio DSMarketLearning.",
        "contact_intro": "¿Tienes dudas sobre el scanner, encontraste un error o quieres sugerir un ticker? Escríbenos por correo o deja tu comentario aquí abajo — lo revisamos nosotros, no se publica en el sitio.",
        "contact_email_note": "Nota: esta dirección es un ejemplo — reemplázala por tu correo real antes de publicar el sitio.",
        "contact_h2_suggestions": "Sugerencias y comentarios",
        "contact_submit": "Enviar",
        "contact_privacy_note": "Tu mensaje se guarda de forma privada para que el equipo lo revise — no se publica ni se muestra a otros visitantes del sitio.",

        # Add ticker widget
        "add_ticker_title": "Agregar una acción al scanner",
        "add_ticker_label": "Símbolo o nombre de la empresa",
        "add_ticker_placeholder": "Ej: NOK, Nokia…",
        "add_ticker_button": "Agregar",
        "add_ticker_searching": "Buscando…",
        "add_ticker_no_results": "No se encontraron coincidencias.",
        "add_ticker_missing": "Escribe un símbolo o nombre de empresa.",
        "add_ticker_not_found": 'No se encontró ninguna acción para "{symbol}".',
        "add_ticker_success": "Se agregó {symbol} al scanner.",

        # Company blurb (indicators panel)
        "company_no_summary": "No hay una descripción disponible para esta empresa.",
        "target_upside_label": "vs. precio actual",

        # Added-ticker badge (tabla)
        "row_added_badge": "Agregada",
        "row_added_badge_title": "La agregaste tú al scanner — se muestra siempre arriba, sin importar los filtros.",
        "remove_ticker_button": "Quitar",
        "remove_ticker_title": "Quitar del scanner",
        "remove_ticker_success": "Se quitó {symbol} del scanner.",
    },
    "en": {
        # Page title / meta
        "home_title": "DSMarketLearning — Daily stock scanner",
        "home_meta_description": "Daily scanner that identifies stocks with RSI in momentum zone, high relative volume, and range breakouts. Informational content, not financial advice.",

        # Nav / chrome
        "nav_scanner": "Scanner",
        "nav_news": "News",
        "nav_blog": "Blog",
        "nav_about": "About",
        "nav_suggestions": "Feedback",
        "footer_about": "About",
        "footer_contact": "Contact",
        "footer_privacy": "Privacy policy",
        "footer_disclaimer": "Disclaimer",
        "footer_terms": "Terms of use",
        "footer_copyright_text": "DSMarketLearning. Informational content for educational purposes — not financial advice. See",
        "footer_disclaimer_link": "disclaimer",
        "cookie_text": "We use our own and third-party cookies (including Google advertising) to analyze site usage and show personalized ads. Read more in our",
        "cookie_privacy_link": "privacy policy",
        "cookie_decline": "Reject non-essential",
        "cookie_accept": "Accept",
        "lang_switch_label": "Language",

        # Scanner header
        "header_subtitle_text": "Daily stock scanner",
        "header_subtitle_title": "Every day we scan a group of stocks and calculate short-term technical signals (RSI, relative volume, range breakouts) and longer-term ones (trend vs. 200-day moving average, relative strength vs. the S&P 500). Select a stock in the table to see its chart and indicators.",

        # Disclaimer banner
        "tool_disclaimer_prefix": "⚠ Tool for educational and informational purposes only — not investment advice or a recommendation to buy or sell. Investing carries risk of capital loss. Read the",
        "disclaimer_link_text": "full disclaimer",

        # Filters
        "filters_toggle": "Advanced filters",
        "filters_active_badge": "active",
        "filter_legend_price_market": "Price and market",
        "filter_price_lt": "Price under",
        "filter_any": "Any",
        "filter_exchange": "Exchange",
        "filter_rel_vol_min": "Min. relative volume",
        "filter_legend_key_indicators": "Key indicators",
        "filter_score_min": "Min. score",
        "filter_pe_min": "Min. P/E",
        "filter_pe_max": "Max. P/E",
        "filter_peg_min": "Min. PEG",
        "filter_peg_max": "Max. PEG",
        "filter_cap_min": "Min. market cap (USD millions)",
        "filter_cap_max": "Max. market cap (USD millions)",
        "filter_target_min": "Min. target price (USD)",
        "filter_target_max": "Max. target price (USD)",
        "filter_apply": "Apply filters",
        "filter_clear": "Clear filters",

        # Panels
        "panel_screening": "Screening",
        "panel_chart": "Chart",
        "panel_indicators": "Indicators",
        "panel_indices": "Indices & alerts",

        # Scan date / note
        "scan_stocks_word": "stocks",
        "scan_from": "scan from",
        "scan_top": "Top",
        "scan_best_score_of": "by best score out of",
        "scan_analyzed": "stocks analyzed",
        "scan_matching_filters": "matching the filters",
        "scan_note_prefix": "By default we only show the top",
        "scan_note_mid": "stocks by score, so you're not overwhelmed by a long table. Use the",
        "scan_note_link": "advanced filters",
        "scan_note_suffix": "to explore the rest of the analyzed universe.",
        "scan_note_mid_short": "by score.",
        "scan_note_show_all_link": "show all",
        "scan_note_show_less_link": "Show only the top 10",

        # Table headers + tooltips
        "th_ver": "View",
        "tip_ver": "Select a stock to see its chart and indicators.",
        "th_ticker": "Ticker",
        "tip_ticker": "Stock's ticker symbol.",
        "th_score": "Score",
        "tip_score": "0-100 score that summarizes several of the day's technical signals in a single number, so you don't have to read each indicator separately.",
        "th_price": "Price",
        "tip_price": "Last closing price.",
        "th_pe": "P/E",
        "tip_pe": "Price-to-earnings ratio. How much the market pays for each dollar of earnings.",
        "th_peg": "PEG",
        "tip_peg": "P/E adjusted for expected growth. Below 1 may indicate the stock is cheap relative to its growth.",
        "th_market_cap": "Market cap",
        "tip_market_cap": "Total market value of the company (price × shares outstanding).",
        "th_volume": "Volume",
        "tip_volume": "Today's volume vs. the average of the last 20 days. Above 1x indicates more market interest.",
        "th_market": "Market",
        "tip_market": "Exchange where the stock trades (NASDAQ, NYSE, etc.).",
        "th_target": "Target price",
        "tip_target": "Average target price published by analysts covering the stock.",
        "th_chart": "Chart",
        "tip_chart": "View the candlestick chart with RSI, volume and indicators.",
        "th_news": "News",
        "tip_news": "View news related to this ticker.",
        "link_ver": "view",

        # Empty states
        "empty_no_filter_match": "No results match the applied filters. Try adjusting them or",
        "empty_clear_link": "clear them",
        "empty_no_scan": "No saved results yet. Run",
        "select_stock_for_chart": "Select a stock in the table to see its chart.",
        "select_stock_for_indicators": "Select a stock in the table to see its indicators.",

        # Methodology
        "methodology_title": "How the score works",
        "methodology_p1": (
            "DSMarketLearning designed a stock categorization defined by a score "
            "that groups together about a dozen technical indicators, giving "
            "you a quick read on which stocks are in a potentially favorable "
            "position. The score summarizes all of those signals into a single "
            "number from 0 to 100, calculated from short-term signals (RSI, "
            "relative volume, range breakout) and longer-term ones (trend vs. "
            "its 200-day moving average, relative strength vs. the S&P 500). "
            "If you want the full detail behind each of those signals for a "
            'particular stock, open its individual page from the "Chart" '
            "column."
        ),
        "methodology_pe_peg_label": "P/E and PEG:",
        "methodology_pe_peg_text": "how expensive or cheap the price looks relative to the company's earnings and expected growth. Read more in our article on",
        "methodology_pe_peg_link": "P/E, PEG, and why price alone tells you nothing",
        "methodology_market_cap_label": "Market cap:",
        "methodology_market_cap_text": "the size of the company on the market — affects its volatility and liquidity.",
        "methodology_volume_label": "Volume:",
        "methodology_volume_text": "compares today's volume against the average of the last 20 days; higher volume suggests more market interest.",
        "methodology_market_label": "Market:",
        "methodology_market_text": "the exchange where the stock trades (NASDAQ, NYSE, etc.).",
        "methodology_target_label": "Target price:",
        "methodology_target_text": "average target price published by analysts covering the stock — see more detail, along with the consensus recommendation, on each stock's page.",
        "methodology_disclaimer": "This information is for educational purposes only. DSMarketLearning does not offer personalized investment advice; read our",

        # About page
        "about_title": "About DSMarketLearning",
        "about_intro": "I'm a software engineer who loves finance, with more than 5 years of experience following financial markets and investing on my own. DSMarketLearning comes from combining those two things: I use my programming background to build technical analysis tools that I use myself to research stocks, and I decided to share them openly for educational purposes.",
        "about_h2_what": "What DSMarketLearning is",
        "about_what_text": "It's a daily stock scanner that calculates technical signals (RSI, relative volume, range breakout, trend vs. the 200-day moving average, relative strength vs. the S&P 500) and fundamental data (P/E, PEG, debt/equity, analyst recommendations) for a broad group of NYSE and NASDAQ stocks. Everything updates automatically every business day. The site also includes market news, a weekly economic calendar, and educational articles explaining how to read each indicator.",
        "about_h2_methodology": "Methodology, made transparent",
        "about_methodology_text": "There's no black box: every indicator the scanner uses is documented right on the results page and on each stock's detail page, including how the score is calculated and what each traffic-light color means. Market data comes from Yahoo Finance via the public yfinance library; it can have errors, delays, or be incomplete, and I say so explicitly where relevant.",
        "about_h2_not_advice": "This is not financial advice",
        "about_not_advice_prefix": "I'm not a registered investment advisor, and nothing on this site — the scanner, the news, the blog articles — is a recommendation to buy or sell. It's informational and educational content, meant for you to research on your own, not to replace your own judgment or the advice of a licensed professional. Before investing, read the",
        "about_not_advice_link": "full disclaimer",
        "about_h2_contact": "Contact",
        "about_contact_prefix": "Questions, suggestions, or found an error? Write to me from the",
        "about_contact_link": "contact page",

        # Chart panel / ticker detail
        "chart_rel_vol": "Rel. volume",
        "chart_breakout": "Breakout",
        "yes": "Yes",
        "no": "No",
        "chart_ref_current_label": "Current price:",
        "chart_ref_current_text": "solid white line — the latest available closing price.",
        "chart_ref_target_label": "Target price:",
        "chart_ref_target_text": "dashed green line — average 12-month target price from analysts covering the stock.",
        "chart_ref_low_label": "Quarter low:",
        "chart_ref_low_text": "dotted orange line — the lowest price over the last ~3 months, as a recent support reference.",
        "chart_zoom_hint": "You can zoom by dragging a rectangle over the chart, or with your mouse wheel. Double-click to reset the view.",
        "ticker_title_suffix": "— chart and technical signals",
        "ticker_meta_description_prefix": "Candlestick chart for",
        "ticker_meta_description_suffix": "with RSI, volume, and range breakout, with periods from 1 minute to monthly.",
        "ticker_last_scan": "Last scan",
        "ticker_price_word": "price",
        "ticker_rel_vol_word": "relative volume",
        "ticker_score_word": "score",
        "ticker_no_results": "This ticker doesn't have any saved daily scanner results yet.",
        "ticker_see_news": "See news for",
        "ticker_back_to_scanner": "back to scanner",
        "ticker_search_placeholder": "Search another stock by symbol or name (e.g. MSFT, Tesla)…",
        "ticker_search_btn": "Search",
        "ticker_price_chart_h2": "Price chart",
        "ticker_analysts_h2": "What analysts say",
        "ticker_methodology_h2": "What this chart shows",
        "ticker_candles_label": "Japanese candlesticks:",
        "ticker_candles_text": "green when the period's close is higher than its open, red when it's lower.",
        "ticker_volume_text": "bars colored the same as the candle for that period.",
        "ticker_rsi_text": "bottom line with reference levels at 70 (overbought) and 30 (oversold) — the same indicator the daily scanner uses.",
        "ticker_dotted_line_label": "Dotted line on top:",
        "ticker_dotted_line_text": "the high of the last 20 periods, the same reference the scanner uses to detect breakouts.",
        "ticker_data_disclaimer": "Market data via Yahoo Finance, for informational purposes. Not investment advice — read the",

        # Indicators panel (fundamentals)
        "fund_score": "score",
        "fund_score_scale": "1 = strong buy, 5 = sell",
        "fund_analysts": "analysts",
        "fund_buy": "Buy",
        "fund_hold": "Hold",
        "fund_sell": "Sell",
        "fund_no_breakdown": "No analyst breakdown available for",
        "fund_avg_target": "Average target price:",
        "fund_vs_current_price": "vs. current price",
        "fund_range": "range",
        "fund_healthy": "Healthy",
        "fund_moderate": "Moderate",
        "fund_attention": "Attention",
        "fund_no_data": "No data",
        "fund_market_cap": "Market cap",
        "fund_market_cap_desc": "Total market value of the company (price × shares outstanding).",
        "fund_pe_trailing": "P/E (trailing)",
        "fund_pe_forward": "P/E (forward)",
        "fund_pe_forward_desc": "Same as P/E, using estimated future earnings.",
        "fund_debt_equity": "Debt/Equity",
        "fund_net_margin": "Net margin",
        "fund_dividend": "Dividend",
        "fund_beta": "Beta (risk)",
        "fund_disclaimer": "General reference ranges, do not vary by sector. Data via Yahoo Finance; may be incomplete. Not investment advice.",
        "fund_no_data_available": "No fundamental data available for",
        "fund_na": "N/A",

        # Indices
        "nasdaq": "Nasdaq",
        "sp500": "S&P 500",
        "dow": "Dow Jones",
        "gold": "Gold",
        "oil": "Oil",

        # Chart intervals
        "1m": "1 min",
        "5m": "5 min",
        "30m": "30 min",
        "1h": "1 hr",
        "4h": "4 hr",
        "1d": "Daily",
        "1wk": "Weekly",
        "1mo": "Monthly",

        # News / calendar
        "news_title": "Market news",
        "news_meta_description": "Daily news roundup from Yahoo Finance for the stocks we track in the scanner.",
        "news_intro_prefix": "Yahoo Finance news for the same tickers covered by the",
        "news_intro_link": "daily scanner",
        "news_intro_suffix": ", so you can see what's being said about a stock right when it shows up in the results.",
        "news_showing_for": "Showing news for",
        "news_see_all": "see all",
        "calendar_title": "U.S. economic calendar — this week",
        "calendar_disclaimer": "Only medium (★★) and high (★★★) impact events: the ones most likely to move the market. Low-impact events are not included.",
        "calendar_date": "Date",
        "calendar_time": "Time",
        "calendar_event": "Event",
        "calendar_impact": "Impact",
        "calendar_forecast": "Forecast",
        "calendar_previous": "Previous",
        "calendar_actual": "Actual",
        "calendar_empty": "No calendar loaded yet. Run",
        "news_empty_for_ticker": "No news saved for",
        "news_empty": "No news loaded yet. Run",
        "news_empty_suffix": "to fetch the latest from Yahoo Finance.",

        # Blog
        "blog_meta_description": "Guides and analysis on technical indicators, reading the market, and how to use the DSMarketLearning scanner.",
        "blog_intro": "Guides and analysis on technical indicators and how to interpret the scanner's results.",
        "blog_empty": "No articles published yet.",

        # Ad slot
        "ad_label": "Advertisement",

        # Legal: shared
        "last_updated": "Last updated",

        # Privacy
        "privacy_title": "Privacy policy",
        "privacy_meta_description": "How DSMarketLearning collects and uses data, including Google and third-party advertising cookies.",
        "privacy_h2_data": "What data we collect",
        "privacy_data_p1": "DSMarketLearning doesn't require registration to browse the site. Like any website, our server and any analytics tools we use may automatically log basic technical data: IP address, browser type, pages visited, and date/time of the visit.",
        "privacy_data_p2_prefix": "If you use the",
        "privacy_data_p2_link": "suggestions and feedback form",
        "privacy_data_p2_suffix": ", we store the name and email you enter (both optional) along with your message, solely so the team can review it and reply if you asked us to. These messages are private: they are not published or shown to other site visitors, and are not shared with third parties.",
        "privacy_h2_cookies": "Cookies and advertising",
        "privacy_cookies_p1": "This site may show ads through Google AdSense. Google, as a third-party vendor, uses cookies (including the DoubleClick cookie) to serve ads based on your prior visits to this and other sites on the internet.",
        "privacy_cookies_li1_prefix": "You can opt out of personalized advertising by visiting",
        "privacy_cookies_li1_link": "Google Ads Settings",
        "privacy_cookies_li2_prefix": "You can also opt out of third-party cookies for advertising purposes by visiting",
        "privacy_cookies_li3": "Third parties, including Google, may use cookies to serve ads based on your prior visits to this site or other websites.",
        "privacy_h2_functional": "Functional cookies and automatic translation",
        "privacy_functional_text": "We use a first-party cookie (not third-party or advertising) to remember your language preference (Spanish/English) between visits. Additionally, when you view the site in Spanish, each company's description is automatically translated from English using Google's translation service — the text sent is public company information (not your personal data).",
        "privacy_h2_analytics": "Analytics",
        "privacy_analytics_text": "We may use web analytics tools (such as Google Analytics) to understand how the site is used in aggregate and anonymously. These tools may also use their own or third-party cookies.",
        "privacy_h2_sharing": "Who we share data with",
        "privacy_sharing_text": "We do not sell personal data. We only share data with providers necessary to run the site (for example, Google AdSense/Analytics), subject to their own privacy policies.",
        "privacy_h2_choices": "Your choices",
        "privacy_choices_text": "You can configure your browser to reject cookies; keep in mind some site features may not work properly without them.",
        "privacy_contact_prefix": "If you have questions about this policy, write to us from the",

        # Disclaimer
        "disclaimer_meta_description": "DSMarketLearning does not offer financial advice; the content is informational and educational.",
        "disclaimer_h1": "Legal notice / Disclaimer",
        "disclaimer_h2_not_advice": "Not investment advice",
        "disclaimer_not_advice_text": "The content published on DSMarketLearning — including scanner results, technical indicators, news, and blog articles — is for informational and educational purposes only. Nothing published here constitutes a recommendation to buy or sell, nor personalized financial, legal, or tax advice.",
        "disclaimer_h2_risk": "Risk of loss",
        "disclaimer_risk_text": "Investing in stocks and other financial instruments carries risk, including possible total loss of the invested capital. Past performance of an instrument, indicator, or strategy does not guarantee future results.",
        "disclaimer_h2_data": "About the data and indicators",
        "disclaimer_data_text_prefix": "Prices, volumes, and indicators (RSI, relative volume, range breakouts) come from third-party sources (such as Yahoo Finance via the",
        "disclaimer_data_text_suffix": " library) and may be delayed, contain errors, or be interrupted. We do not guarantee their accuracy, completeness, or availability at all times.",
        "disclaimer_h2_consult": "Consult a professional",
        "disclaimer_consult_text": "Before making any financial decision, consult a registered investment advisor authorized in your jurisdiction, who can evaluate your particular situation.",
        "disclaimer_h2_liability": "Limitation of liability",
        "disclaimer_liability_text": "DSMarketLearning and its authors are not liable for losses or damages arising from the use of the information published on this site.",

        # Terms
        "terms_meta_description": "Terms of use for the DSMarketLearning website.",
        "terms_h2_acceptance": "Acceptance of terms",
        "terms_acceptance_prefix": "By using DSMarketLearning you accept these terms of use and our",
        "terms_acceptance_suffix": ". If you do not agree, please do not use the site.",
        "terms_h2_use": "Permitted use",
        "terms_use_text": "You may browse and view the site's content for personal, non-commercial use. Copying, redistributing, or reusing the content for commercial purposes without prior authorization is not permitted.",
        "terms_h2_ip": "Intellectual property",
        "terms_ip_text": "DSMarketLearning's design, text, and code are the property of its authors, except for third-party content (market data, news) which belongs to its respective owners.",
        "terms_h2_no_warranty": "No warranties",
        "terms_no_warranty_prefix": 'The site is provided "as is", with no guarantee of continuous availability, accuracy, or absence of errors. See also our',
        "terms_no_warranty_suffix": "regarding financial content.",
        "terms_h2_changes": "Changes to these terms",
        "terms_changes_text": 'We may update these terms at any time; the "last updated" date will reflect the most recent change.',

        # Contact
        "contact_meta_description": "Send your suggestions, feedback, or report issues with the DSMarketLearning site.",
        "contact_intro": "Have questions about the scanner, found a bug, or want to suggest a ticker? Email us or leave your comment below — our team reviews it, it's not published on the site.",
        "contact_email_note": "Note: this address is a placeholder — replace it with your real email before publishing the site.",
        "contact_h2_suggestions": "Suggestions and feedback",
        "contact_submit": "Submit",
        "contact_privacy_note": "Your message is stored privately for the team to review — it is not published or shown to other site visitors.",

        # Add ticker widget
        "add_ticker_title": "Add a stock to the scanner",
        "add_ticker_label": "Stock symbol or company name",
        "add_ticker_placeholder": "E.g. NOK, Nokia…",
        "add_ticker_button": "Add",
        "add_ticker_searching": "Searching…",
        "add_ticker_no_results": "No matches found.",
        "add_ticker_missing": "Enter a stock symbol or company name.",
        "add_ticker_not_found": 'No stock found for "{symbol}".',
        "add_ticker_success": "Added {symbol} to the scanner.",

        # Company blurb (indicators panel)
        "company_no_summary": "No description available for this company.",
        "target_upside_label": "vs. current price",

        # Added-ticker badge (table)
        "row_added_badge": "Added",
        "row_added_badge_title": "You added this to the scanner — always shown at the top, regardless of filters.",
        "remove_ticker_button": "Remove",
        "remove_ticker_title": "Remove from scanner",
        "remove_ticker_success": "Removed {symbol} from the scanner.",
    },
}

DEFAULT_LANG = "es"
SUPPORTED_LANGS = ("es", "en")


def get_translations(lang):
    return T.get(lang, T[DEFAULT_LANG])
