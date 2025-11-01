from django.shortcuts import render, redirect, get_object_or_404
from frontend.utils.db_helper import * 
from frontend.models import CongTrinhToanDien, GiaiPhapAmThanh, Order, MomoPayment
from django.contrib import messages 
#  View Front - End 

def home_page(request):
    categories = get_all_categories()
    products_early = get_all_products_for_early()
    products_top_selling = get_all_products_top_sell()
    brands = get_all_brands()
    # Truyền dữ liệu categories vào context
    return render(request, 'frontend/pages/homepage.html', {
        'title': 'Trang chủ',
        'categories': categories,
        '10_products_early':products_early,
        'products_top_selling':products_top_selling,
        'brands':brands
    })

def all_categories_page(request):
    categories = get_all_categories()
    return render(request, 'frontend/pages/all_categories.html', {
        'title': 'Tất cả danh mục',
        'categories': categories
    })

def all_products_by_category(request, id,page,items=12):
    categories = get_all_categories()
    products,pages = get_all_products_by_category(id,page=page,items=items)
    category = get_category_by_id(id)
    return render(request, 'frontend/pages/products_category.html', {
        'title': 'Danh sách sản phẩm',
        'categories': categories,
        'category': category,
        'products': products,
        'pages': pages,
        'current_page': int(page)
    })

def thuonghieu_page(request):
    categories = get_all_categories()
    brands = get_all_brands()
    categories = get_all_categories()
    return render(request, 'frontend/pages/thuonghieu.html', {'title': 'Thuong hieu','brands':brands,'categories':categories})
    
def products_brand_page(request, id,page = 1,items=12):  
    products,pages = get_all_products_by_brand(id,page=page,items=items)
    brand = get_brand_by_id(id)
    categories = get_all_categories()
    return render(request, 'frontend/pages/products_brand.html', {
        'title': 'Danh sách sản phẩm',
        'brand': brand,
        'categories': categories,
        'products': products,
        'pages':pages,
        'current_page': int(page)
    })
def search_page(request):
    # Lấy tham số từ GET request
    keysearch = request.GET.get('keysearch', '').strip()
    category_id = request.GET.get('category_id', '0').strip()
    categories = get_all_categories()
    
    # Nếu có tham số tìm kiếm, thực hiện tìm kiếm
    if keysearch or (category_id and category_id != '0'):
        products = get_all_product_search(keysearch, category_id)
        
        # Lấy tên category
        category_name = "Tất cả"
        if category_id and category_id != '0':
            category = get_category_by_id(category_id)
            if category:
                category_name = category.name
        
        return render(request, 'frontend/pages/search.html', {
            'title': 'Tìm kiếm', 
            'products': products,
            'categories': categories, 
            'keysearch': keysearch,
            'category_id': category_id,
            'category_name': category_name
        })
    
    # Nếu không có tham số, hiển thị trang tìm kiếm trống
    return render(request, 'frontend/pages/search.html', {
        'title': 'Tìm kiếm', 
        'categories': categories,
        'keysearch': '',
        'category_id': '0'
    })
def blank_page(request):
    return render(request, 'frontend/pages/blank.html', {'title': 'Trang trắng'})

def checkout_page(request):
    return render(request, 'frontend/pages/checkout.html', {'title': 'Thanh toán'})

def product_page(request):
    return render(request, 'frontend/pages/product.html', {'title': 'Sản phẩm'})

def cart_page(request):
    categories = get_all_categories()
    cart = get_or_create_active_cart(request.session['user_id'])
    cart_details = get_cart_detail_by_cart_id(cart.id)
    user = get_user_by_id(request.session['user_id'])
    # Chuyển đổi cart_details thành list các dictionary
    cart_details_serializable = [
        {
            'id': detail.id,
            'product_id': detail.product_id,
            'quantity': detail.quantity,
            'product_image': detail.product.image_url,
            'product_name': detail.product.name,  # Giả sử có mối quan hệ đến product
            'product_price': float(detail.product.price)  # Chuyển đổi sang float
        } for detail in cart_details
    ]    
    return render(request, 'frontend/pages/cart.html', {'title': 'Cửa hàng', 'categories': categories, 'cart_details': cart_details_serializable, 'user': user})
#  Order history page

def order_history_page(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Vui lòng đăng nhập để xem lịch sử đơn hàng')
        return redirect('login')
        
    user_id = request.session['user_id']
    orders = Order.objects.filter(user_id=user_id).order_by('-created_at')
    
    # Tạo dictionary để map order.id với MomoPayment (nếu có)
    order_payments = {}
    for order in orders:
        # Tìm MomoPayment có django_order_id trùng với order.id
        momo_payment = MomoPayment.objects.filter(order_id=order.id).first()
        if momo_payment:
            order_payments[order.id] = momo_payment
    
    return render(request, 'frontend/pages/order_history.html', {
        'title': 'Lịch sử đơn hàng',
        'orders': orders,
        'order_payments': order_payments
    })
    
def product_page(request,id):
    categories = get_all_categories()
    product = get_product_by_id(id)
    print(product)
    category = get_category_by_id(product.category_id)
    brand = get_brand_by_id(product.brand_id)
    products_related,pages = get_all_products_by_category(product.category_id,items=4)
    return render(request, 'frontend/pages/product.html', {'title': product.name, 'product': product, 'categories': categories, 'category': category,'brand': brand, 'products_related':products_related})

def cong_trinh_toan_dien_page(request, id=None):
    categories = get_all_categories()
    latest_cong_trinhs = CongTrinhToanDien.objects.filter(status='active').order_by('-created_at')[:5]
    
    if id:
        # Hiển thị chi tiết một công trình
        cong_trinh = get_object_or_404(CongTrinhToanDien, id=id, status='active')
        return render(request, 'frontend/pages/cong_trinh_toan_dien.html', {
            'title': cong_trinh.title,
            'categories': categories,
            'cong_trinh': cong_trinh,
            'latest_cong_trinhs': latest_cong_trinhs
        })
    else:
        # Hiển thị công trình mới nhất
        cong_trinh = CongTrinhToanDien.objects.filter(status='active').order_by('-created_at').first()
        return render(request, 'frontend/pages/cong_trinh_toan_dien.html', {
            'title': 'Công trình toàn diện',
            'categories': categories,
            'cong_trinh': cong_trinh,
            'latest_cong_trinhs': latest_cong_trinhs
        })

def giai_phap_am_thanh_page(request, id=None):
    categories = get_all_categories()
    latest_giai_phaps = GiaiPhapAmThanh.objects.filter(status='active').order_by('-created_at')[:5]
    
    if id:
        # Hiển thị chi tiết một giải pháp
        giai_phap = get_object_or_404(GiaiPhapAmThanh, id=id, status='active')
        return render(request, 'frontend/pages/giai_phap_am_thanh.html', {
            'title': giai_phap.title,
            'categories': categories,
            'giai_phap': giai_phap,
            'latest_giai_phaps': latest_giai_phaps
        })
    else:
        # Hiển thị danh sách giải pháp
        giai_phaps = GiaiPhapAmThanh.objects.filter(status='active').order_by('-created_at')
        giai_phap = giai_phaps.first()
        return render(request, 'frontend/pages/giai_phap_am_thanh.html', {
            'title': 'Giải pháp âm thanh',
            'categories': categories,
            'giai_phaps': giai_phaps,
            'giai_phap': giai_phap,
            'latest_giai_phaps': latest_giai_phaps
        })

def ve_chung_toi_page(request):
    categories = get_all_categories()
    return render(request, 'frontend/pages/ve_chung_toi.html', {
        'title': 'Về chúng tôi',
        'categories': categories
    })
