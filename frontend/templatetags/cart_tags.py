from django import template

register = template.Library()

@register.simple_tag
def calculate_total(cart_details):
    return sum(item['quantity'] * item['product_price'] for item in cart_details)

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0