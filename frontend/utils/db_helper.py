from frontend.models import Category, Brand, Product, User, Cart,CartDetail,Order,OrderDetail


# Category
def get_all_categories():
    return list(Category.objects.all())

def get_category_by_id(category_id):
    try:
        return Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return None

# Brand
def get_all_brands():
    return list(Brand.objects.all())

def get_brand_by_id(brand_id):
    try:
        return Brand.objects.get(id=brand_id)
    except Brand.DoesNotExist:
        return None

# Product
def get_all_products_by_category(category_id, items=10, page=1):
    offset = (page - 1) * items
    products = list(Product.objects.filter(category=category_id).order_by('-created_at')[offset:offset + items])
    pages = (Product.objects.filter(category=category_id).count() + items - 1) // items
    return products, pages

def get_all_products_by_brand(brand_id, items=10, page=1):
    offset = (page - 1) * items
    products = list(Product.objects.filter(brand=brand_id).order_by('-created_at')[offset:offset + items])
    pages = (Product.objects.filter(brand=brand_id).count() + items - 1) // items
    return products, pages

def get_all_products_for_early(items=10):
    return list(Product.objects.all().order_by('-created_at')[:items])

def get_all_products_top_sell(items=10):
    return list(Product.objects.all().order_by('-number_of_sell')[:items])

def get_all_product_search(keyword, category_id):
    if not int(category_id) == 0:
        return list(Product.objects.filter(name__icontains=keyword, category=category_id))
    return list(Product.objects.filter(name__icontains=keyword))

def get_product_by_id(product_id):
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return None

# Cart
def create_cart(user_id):
    cart = Cart(user_id=user_id, status="active")
    cart.save()
    return cart

def get_cart_by_user_id_active(user_id):
    try:
        return Cart.objects.get(user_id=user_id, status="active")
    except Cart.DoesNotExist:
        return None

def get_cart_detail_by_cart_id(cart_id):
    try:
        return list(CartDetail.objects.filter(cart_id=cart_id))
    except CartDetail.DoesNotExist:
        return None

def create_cart_detail(cart_id, product_id, quantity):
    try:
        CartDetail.objects.create(cart_id=cart_id, product_id=product_id, quantity=quantity)
        return True
    except:
        return False

def update_cart_detail(cart_id, product_id, quantity):
    try:
        cart_detail = CartDetail.objects.get(cart_id=cart_id, product_id=product_id)
        cart_detail.quantity = quantity
        cart_detail.save()
        return True
    except:
        return False
    
def get_or_create_active_cart(user_id):
    """
    Lấy hoặc tạo giỏ hàng active cho user
    
    Args:
        user_id (int): ID của user

    Returns:
        Cart: Giỏ hàng active
    """
    cart, created = Cart.objects.get_or_create(
        user_id=user_id, 
        status="active", 
        defaults={'user_id': user_id, 'status': 'active'}
    )
    return cart

def get_cart_detail(cart_id, product_id):
    """
    Lấy chi tiết giỏ hàng của sản phẩm
    
    Args:
        cart_id (int): ID của giỏ hàng
        product_id (int): ID của sản phẩm

    Returns:
        CartDetail hoặc None
    """
    try:
        return CartDetail.objects.get(cart_id=cart_id, product_id=product_id)
    except CartDetail.DoesNotExist:
        return None

def add_product_to_cart(cart_id, product_id, quantity=1):
    """
    Thêm sản phẩm vào giỏ hàng
    
    Args:
        cart_id (int): ID của giỏ hàng
        product_id (int): ID của sản phẩm
        quantity (int, optional): Số lượng. Defaults to 1.

    Returns:
        CartDetail: Chi tiết giỏ hàng được thêm hoặc cập nhật
    """
    cart_detail = get_cart_detail(cart_id, product_id)
    
    if cart_detail:
        # Nếu sản phẩm đã có trong giỏ hàng, tăng số lượng
        cart_detail.quantity += quantity
        cart_detail.save()
    else:
        # Nếu chưa có, tạo mới
        cart_detail = CartDetail.objects.create(
            cart_id=cart_id, 
            product_id=product_id, 
            quantity=quantity
        )
    
    return cart_detail

def remove_product_from_cart(cart_id, product_id, quantity=1):
    """
    Xóa sản phẩm khỏi giỏ hàng
    
    Args:
        cart_id (int): ID của giỏ hàng
        product_id (int): ID của sản phẩm
        quantity (int, optional): Số lượng. Defaults to 1.

    Returns:
        bool: Thành công hay không
    """
    cart_detail = get_cart_detail(cart_id, product_id)
    
    if not cart_detail:
        return False
    
    if cart_detail.quantity > quantity:
        # Nếu số lượng còn lớn hơn số lượng muốn xóa
        cart_detail.quantity -= quantity
        cart_detail.save()
    else:
        # Nếu số lượng bằng hoặc nhỏ hơn thì xóa cart detail
        cart_detail.delete()
    
    return True

def check_product_exists(product_id):
    """
    Kiểm tra sản phẩm có tồn tại không
    
    Args:
        product_id (int): ID của sản phẩm

    Returns:
        bool: Sản phẩm có tồn tại hay không
    """
    return Product.objects.filter(id=product_id).exists()
# User

def get_user_by_id(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
    
    
#  order

def get_order_by_id(order_id):
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None
    
def get_all_order_user(user_id):
    try:
        return list(Order.objects.filter(user_id=user_id))
    except Order.DoesNotExist:
        return None
    
def create_order(user_id, total_price):
    order = Order(user_id=user_id, total_price=total_price)
    order.save()
    return order

def create_order_detail(order_id, product_id, product_options, quantity, price):
    order_detail = OrderDetail(order_id=order_id, product_id=product_id, product_options=product_options, quantity=quantity, price=price)
    order_detail.save()
    return order_detail