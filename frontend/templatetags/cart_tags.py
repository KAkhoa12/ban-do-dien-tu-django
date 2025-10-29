from django import template

register = template.Library()

@register.simple_tag
def calculate_total(cart_details):
    total = 0
    for item in cart_details:
        try:
            if isinstance(item, dict):
                quantity = float(item.get('quantity', 0))
                price = item.get('product_price')
                if price is None:
                    # fallback keys if structure differs
                    price = item.get('price', 0)
                price = float(price)
            else:
                quantity = float(getattr(item, 'quantity', 0))
                # Prefer explicit field if exists, else traverse relation
                price = getattr(item, 'product_price', None)
                if price is None:
                    product = getattr(item, 'product', None)
                    price = float(getattr(product, 'price', 0)) if product is not None else 0.0
                else:
                    price = float(price)
            total += quantity * price
        except Exception:
            # Ignore malformed items
            continue
    return total

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0