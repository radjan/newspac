from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, word):
    return mark_safe(text.replace(word, "<span class='highlight'>%s</span>" % word))
#highlight.is_safe = True
highlight.need_autoescape = True
