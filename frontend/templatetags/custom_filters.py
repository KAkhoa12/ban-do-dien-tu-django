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
    # print(f"giá tiền: {value} và type: {type(value)}")
    try:
        if value is None or value == '' or value == 'None':
            return "0 VNĐ"
        if isinstance(value, str):
            value = float(value.replace(",", "").replace(".", ""))
        return f"{float(value):,.0f} VNĐ".replace(",", ".")
    except (ValueError, TypeError):
        return "0 VNĐ"

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='zip_lists')
def zip_lists(list1, list2):
    """Ghép hai danh sách theo cặp để lặp trong template."""
    try:
        if list1 is None or list2 is None:
            return []
        return list(zip(list1, list2))
    except Exception:
        return []