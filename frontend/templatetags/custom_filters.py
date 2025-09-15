from django import template

register = template.Library()

@register.filter
def split_and_upper(value, delimiter=","):
    """
    Tách chuỗi bằng delimiter và chuyển từng phần tử thành chữ hoa.
    """
    if not value:
        return []
    return [item.strip().upper() for item in value.split(delimiter)]


@register.filter
def currency_format(value):
    value = float(value)  # Chuyển giá trị thành số nguyên
    return f"{value:,.0f} VNĐ".replace(",", ".")  

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0