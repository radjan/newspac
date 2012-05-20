from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, pattern):
    words = pattern.split('|')
    for word in words:
        text = text.replace(word, "<span class='highlight'>%s</span>" % word)
    return mark_safe(text)
#highlight.is_safe = True
#highlight.need_autoescape = True
