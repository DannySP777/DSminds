from django import template

register = template.Library()


@register.filter
def dict_get(mapping, key):
    """Uso: {{ T|dict_get:idx.key }} — busca `key` en el dict `mapping`."""
    if not mapping:
        return key
    return mapping.get(key, key)


@register.filter
def get_title(post, lang):
    return post.get_title(lang)


@register.filter
def get_excerpt(post, lang):
    return post.get_excerpt(lang)


@register.filter
def get_body(post, lang):
    return post.get_body(lang)
