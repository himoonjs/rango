from django import template
from rango.models import Category, Page

register = template.Library()

@register.inclusion_tag('rango/cats.html')
def get_category_list(cat=None):
    return {'cats': Category.objects.all(), 'act_cat': cat}

@register.inclusion_tag('rango/page_list.html')
def get_page_list(cat=None):
    return {'pages': Page.objects.all(), 'act_cat': cat}