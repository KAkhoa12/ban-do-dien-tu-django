from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import create_momo_payment, verify_momo_response
from frontend.utils import random_name,upload_file
from frontend.models import Category, Product, Brand, CongTrinhToanDien, GiaiPhapAmThanh, Order, OrderDetail, CartDetail
import json
from .decorator import admin_required
import os
from django.conf import settings

from .utils.db_helper import * 

api_url = "http://127.0.0.1:8000/api/"  # Đường dẫn API
    
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

def all_products_by_category(request, id,page):
    categories = get_all_categories()
    products,pages = get_all_products_by_category(id,page=page)
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
    
def products_brand_page(request, id,page = 1):  
    products,pages = get_all_products_by_brand(id,page=page)
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
    if request.method == 'POST':
        keysearch = request.POST.get('keysearch')
        category_id = request.POST.get('category_id')
        categories = get_all_categories()
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
            'category_name': category_name
        })
    categories = get_all_categories()
    return render(request, 'frontend/pages/search.html', {'title': 'Tìm kiếm', 'categories': categories})
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
    
    return render(request, 'frontend/pages/order_history.html', {
        'title': 'Lịch sử đơn hàng',
        'orders': orders
    })

def cancel_order(request, order_id):
    if 'user_id' not in request.session:
        messages.error(request, 'Vui lòng đăng nhập để thực hiện chức năng này')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id, user_id=request.session['user_id'])
            
            # Chỉ cho phép hủy đơn hàng đang chờ xử lý
            if order.status != 'pending':
                messages.error(request, 'Không thể hủy đơn hàng này')
                return redirect('order_history')
                
            # Cập nhật trạng thái đơn hàng
            order.status = 'cancelled'
            order.save()
            
            messages.success(request, 'Đã hủy đơn hàng thành công')
        except Order.DoesNotExist:
            messages.error(request, 'Không tìm thấy đơn hàng')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            
    return redirect('order_history')

def login_page(request):
    categories = get_all_categories()
    messages = []
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.filter(username=username, role='user')
        if user.count() == 0:
            messages.append("Không tìm thấy tài khoản của bạn")
            return render(request, 'frontend/pages/login.html', {'title': 'Đăng nhập','categories': categories,'messages': messages})
        check_pass = check_password(password,user[0].password)
        if check_pass:
            user = user.get()
            cart = get_cart_by_user_id_active(user.id)
            if cart == None:
                cart = create_cart(user.id)
            cart_details = get_cart_detail_by_cart_id(cart.id)
            
            cart_details_serializable = [
                {
                    'id': detail.id,
                    'product_id': detail.product.id,
                    'quantity': detail.quantity,
                    'product_image': detail.product.image_url,
                    'product_name': detail.product.name,
                    'product_price': float(detail.product.price)
                } for detail in cart_details
            ]

            request.session['user_id'] = user.id
            request.session['role'] = 'user'  # Thêm role user
            request.session['image_url'] = user.image_url
            request.session['name'] = user.name
            request.session['email'] = user.email
            request.session['cart_id'] = cart.id
            request.session['quantity'] = len(cart_details)
            request.session['cart_details'] = cart_details_serializable
            return redirect('home')
        else:
            messages.append("Tài khoản không hợp lệ")
            return render(request, 'frontend/pages/login.html', {'title': 'Đăng nhập','messages': messages})
    return render(request, 'frontend/pages/login.html', {'title': 'Đăng nhập','categories': categories})

def register_page(request):
    messages = []
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        re_password = request.POST['re_password']
        username_exists = User.objects.filter(username=username).exists()
        email_exists = User.objects.filter(email=email).exists()
        if password != re_password:
            messages.append("Mật khẩu nhập lại không đúng")
        if username_exists:
            messages.append("Tên tài khoản đã tồn tại")
        if email_exists:
            messages.append("Email đã tồn tại")
        
        
        if len(messages) == 0:
            user = User.objects.create(
                username=username, 
                email=email, 
                password=make_password(password), 
                name =random_name.generate_random_name(),
                role='user'  # Set default role as user
            )
            user.save()
            cart = create_cart(user.id)
            cart_detail = get_cart_detail_by_cart_id(cart.id)
            request.session['user_id'] = user.id
            request.session['role'] = 'user'
            request.session['image_url'] = user.image_url
            request.session['name'] = user.name
            request.session['email'] = user.email
            request.session['cart_id'] = cart.id
            request.session['quantity'] = len(list(cart_detail))
            request.session['cart_details'] = list(cart_detail)
            return redirect('home')
        else:
            return render(request, 'frontend/pages/register.html', {'title': 'Đăng ký','messages': messages})
    categories = get_all_categories()
    return render(request, 'frontend/pages/register.html', {'title': 'Đăng ký','categories': categories})

def logout_page(request):
    request.session.flush()
    return redirect('home')
# View Back - End
def product_page(request,id):
    categories = get_all_categories()
    product = get_product_by_id(id)
    print(product)
    category = get_category_by_id(product.category_id)
    brand = get_brand_by_id(product.brand_id)
    products_related,pages = get_all_products_by_category(product.category_id,items=4)
    return render(request, 'frontend/pages/product.html', {'title': product.name, 'product': product, 'categories': categories, 'category': category,'brand': brand, 'products_related':products_related})
def add_to_cart(request, id):
    categories = get_all_categories()
    if not check_product_exists(id):
        messages.error(request, "Sản phẩm không tồn tại")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    user_id = request.session.get('user_id')
    if user_id == None:
        return render(request, 'frontend/pages/login.html', {'title': 'Đăng nhập','categories': categories})
    
    cart = get_or_create_active_cart(user_id)
    add_product_to_cart(cart.id, id)
    
    # Cập nhật session cart data
    update_cart_session(request, user_id, cart.id)
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def remove_from_cart(request, id):
    if not check_product_exists(id):
        messages.error(request, "Sản phẩm không tồn tại")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    user_id = request.session['user_id']
    cart = get_or_create_active_cart(user_id)

    if not remove_product_from_cart(cart.id, id):
        messages.error(request, "Sản phẩm không có trong giỏ hàng")
    else:
        # Cập nhật session cart data
        update_cart_session(request, user_id, cart.id)

    return redirect(request.META.get('HTTP_REFERER', 'home'))

# Thanh toán momo 

def create_payment(request):
    if request.method == 'POST':
        messages = []
        categories = get_all_categories()
        
        # Kiểm tra xem người dùng đã đăng nhập chưa
        if 'user_id' not in request.session:
            messages.append("Vui lòng đăng nhập để thực hiện thanh toán")
            return redirect('login')
        
        user_id = request.session['user_id']
        cart = get_or_create_active_cart(user_id)
        cart_details = get_cart_detail_by_cart_id(cart.id)
        user = get_user_by_id(user_id)
        
        # Kiểm tra giỏ hàng có sản phẩm không
        if not cart_details:
            messages.append("Giỏ hàng của bạn đang trống")
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'messages': messages, 
                'categories': categories, 
                'cart_details': [], 
                'user': user
            })
        
        missing_fields = []
        required_fields = ['name', 'email', 'phone', 'address']
        
        for field in required_fields:
            if not getattr(user, field):
                missing_fields.append(field)
        
        if missing_fields:
            messages.append(f"Thiếu các giá trị trong các trường: {', '.join(missing_fields)}")
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'messages': messages, 
                'categories': categories, 
                'cart_details': cart_details, 
                'user': user
            })
            
        amount = request.POST.get('amount')
        order_info = request.POST.get('order_info', 'Thanh toán đơn hàng')
        
        # Chuyển đổi amount thành số
        try:
            amount = int(float(amount))
        except (ValueError, TypeError):
            messages.append("Số tiền không hợp lệ")
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'messages': messages, 
                'categories': categories, 
                'cart_details': cart_details, 
                'user': user
            })
        
        # Lưu thông tin giỏ hàng và người dùng vào session cho quá trình thanh toán
        request.session['payment_user_id'] = user_id
        request.session['payment_cart_id'] = cart.id
        
        # Tạo thanh toán MoMo
        result = create_momo_payment(amount, order_info)
        
        if result['status'] == 'success':
            # Chuyển hướng đến trang thanh toán MoMo
            return redirect(result['payment_url'])
        else:
            # Hiển thị lỗi
            messages.append(result.get('message', 'Có lỗi xảy ra'))
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'messages': messages, 
                'categories': categories, 
                'cart_details': cart_details, 
                'user': user
            })

# Xử lý kết quả thanh toán (khi user quay lại từ MoMo)
def payment_result(request):
    try:
        # Lấy dữ liệu từ request
        if request.method == 'GET':
            data = request.GET.dict()
        else:
            try:
                data = json.loads(request.body)
            except:
                data = request.POST.dict()
        
        print("Received data from MoMo:", data)
        
        # Lấy thông tin người dùng và giỏ hàng từ session
        user_id = request.session.get('payment_user_id')
        cart_id = request.session.get('payment_cart_id')
        if not user_id or not cart_id:
            return render(request, 'frontend/pages/failed.html', {
                'error': 'Không tìm thấy thông tin thanh toán. Vui lòng thử lại.'
            })
        
        # Kiểm tra kết quả từ MoMo
        if 'resultCode' in data:
            if data['resultCode'] == '20':
                return render(request, 'frontend/pages/failed.html', {'error': 'Bad format request from MoMo'})
            elif data['resultCode'] == '0':
                try:
                    # Kiểm tra và xác minh kết quả thanh toán
                    result = verify_momo_response(data)
                    print("Verification result:", result)
                    
                    if result['status'] == 'verified':
                        payment = result['payment']
                        print("Payment status:", payment.status)
                        
                        if payment.status == 'completed':
                            # Xử lý thanh toán thành công
                            cart = get_or_create_active_cart(user_id)
                            
                            # Kiểm tra xem giỏ hàng có thuộc về người dùng đang thanh toán không
                            if cart.user_id != user_id:
                                return render(request, 'frontend/pages/failed.html', {
                                    'error': 'Giỏ hàng không thuộc về người dùng này'
                                })
                            
                            # Kiểm tra xem giỏ hàng đã được thanh toán chưa
                            if cart.status == 'completed':
                                return render(request, 'frontend/pages/failed.html', {
                                    'error': 'Giỏ hàng này đã được thanh toán'
                                })
                            
                            # Đánh dấu giỏ hàng đã thanh toán
                            cart.status = 'completed'
                            cart.save()
                            
                            # Tạo đơn hàng mới
                            order = create_order(user_id, 0)
                            cart_details = get_cart_detail_by_cart_id(cart_id)
                            
                            total_price = 0
                            for cart_detail in cart_details:
                                total_price += cart_detail.product.price * cart_detail.quantity
                                create_order_detail(order.id, cart_detail.product_id, '', cart_detail.quantity, cart_detail.product.price)
                            
                            order.total_price = total_price
                            order.status = 'pending'
                            order.save()
                            
                            # Tạo giỏ hàng mới
                            new_cart = get_or_create_active_cart(user_id)
                            
                            # Cập nhật session với giỏ hàng mới
                            update_cart_session(request, user_id, new_cart.id)
                            
                            # Xóa thông tin thanh toán từ session
                            if 'payment_user_id' in request.session:
                                del request.session['payment_user_id']
                            if 'payment_cart_id' in request.session:
                                del request.session['payment_cart_id']
                            
                            return render(request, 'frontend/pages/success.html', {'payment': payment})
                        else:
                            return render(request, 'frontend/pages/failed.html', {'payment': payment})
                    else:
                        # Thông tin debug khi xác minh thất bại
                        error_message = result.get('message', 'Có lỗi xảy ra')
                        if 'debug' in result:
                            error_message += f" - Debug info: {result['debug']}"
                        return render(request, 'frontend/pages/failed.html', {'error': error_message})
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return render(request, 'frontend/pages/failed.html', {'error': f'Lỗi xử lý: {str(e)}'})
            else:
                # Xử lý các mã lỗi khác từ MoMo
                return render(request, 'frontend/pages/failed.html', 
                             {'error': f'Error code: {data["resultCode"]}, Message: {data.get("message", "Unknown error")}'})
        
        # Xử lý khi có orderId và requestId
        if 'orderId' in data and 'requestId' in data:
            result = verify_momo_response(data)
            if result['status'] == 'verified':
                payment = result['payment']
                if payment.status == 'completed':
                    # Xử lý thanh toán thành công
                    cart = get_or_create_active_cart(user_id)
                    
                    # Kiểm tra xem giỏ hàng có thuộc về người dùng đang thanh toán không
                    if cart.user_id != user_id:
                        return render(request, 'frontend/pages/failed.html', {
                            'error': 'Giỏ hàng không thuộc về người dùng này'
                        })
                    
                    # Kiểm tra xem giỏ hàng đã được thanh toán chưa
                    if cart.status == 'completed':
                        return render(request, 'frontend/pages/failed.html', {
                            'error': 'Giỏ hàng này đã được thanh toán'
                        })
                    
                    # Đánh dấu giỏ hàng đã thanh toán
                    cart.status = 'completed'
                    cart.save()
                    
                    # Tạo đơn hàng mới
                    order = create_order(user_id, 0)
                    cart_details = get_cart_detail_by_cart_id(cart_id)
                    
                    total_price = 0
                    for cart_detail in cart_details:
                        total_price += cart_detail.product.price * cart_detail.quantity
                        create_order_detail(order.id, cart_detail.product_id, '', cart_detail.quantity, cart_detail.product.price)
                    
                    order.total_price = total_price
                    order.status = 'pending'
                    order.save()
                    
                    # Tạo giỏ hàng mới
                    new_cart = get_or_create_active_cart(user_id)
                    
                    # Cập nhật session với giỏ hàng mới
                    update_cart_session(request, user_id, new_cart.id)
                    
                    # Xóa thông tin thanh toán từ session
                    if 'payment_user_id' in request.session:
                        del request.session['payment_user_id']
                    if 'payment_cart_id' in request.session:
                        del request.session['payment_cart_id']
                    
                    return render(request, 'frontend/pages/success.html', {'payment': payment})
                else:
                    return render(request, 'frontend/pages/failed.html', {'payment': payment})
            else:
                # Thêm thông tin debug để dễ theo dõi
                error_message = result.get('message', 'Có lỗi xảy ra')
                if 'debug' in result:
                    error_message += f" - Debug info: {result['debug']}"
                return render(request, 'frontend/pages/failed.html', {'error': error_message})
        
        # Trả về lỗi nếu thiếu thông tin cần thiết
        return render(request, 'frontend/pages/failed.html', {'error': f'Thiếu thông tin từ MoMo. Dữ liệu nhận được: {data}'})
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render(request, 'frontend/pages/failed.html', {'error': f'Lỗi ngoại lệ: {str(e)}'})

# IPN (Instant Payment Notification) - MoMo sẽ gọi API này để thông báo kết quả
@csrf_exempt
@require_POST
def payment_ipn(request):
    try:
        # Đọc dữ liệu từ request body
        data = json.loads(request.body)
        
        # Verify kết quả từ MoMo
        result = verify_momo_response(data)
        print(result)
        if result['status'] == 'verified':
            # Trả về kết quả cho MoMo
            return JsonResponse({
                'partnerCode': data.get('partnerCode'),
                'orderId': data.get('orderId'),
                'requestId': data.get('requestId'),
                'resultCode': 0,
                'message': 'Success'
            })
        else:
            return JsonResponse({
                'partnerCode': data.get('partnerCode'),
                'orderId': data.get('orderId'),
                'requestId': data.get('requestId'),
                'resultCode': 1,
                'message': 'Failed to verify'
            })
    except Exception as e:
        return JsonResponse({
            'resultCode': 99,
            'message': str(e)
        })
def update_user(request, user_id):
    # Lấy thông tin người dùng
    # Đảm bảo user_id được xử lý đúng cách, nếu không có trong URL thì lấy từ session
    if not user_id: # user_id có thể là None nếu không được truyền qua URL
        user_id = request.session.get('user_id') # Sử dụng .get để tránh KeyError nếu 'user_id' không có
        if not user_id:
            messages.error(request, 'Không tìm thấy ID người dùng.')
            return redirect('home_page') # Hoặc một trang lỗi phù hợp

    user = get_user_by_id(user_id)
    if not user:
        messages.error(request, 'Người dùng không tồn tại.')
        return redirect('home_page') # Hoặc một trang lỗi phù hợp

    categories = get_all_categories()
    
    # Lấy thông tin giỏ hàng (cần cho cả GET và POST để hiển thị trên trang profile/cart)
    cart_details_serializable = []
    if 'user_id' in request.session and 'cart_id' in request.session:
        cart = get_or_create_active_cart(request.session['user_id'])
        if cart: # Đảm bảo giỏ hàng tồn tại
            cart_details = get_cart_detail_by_cart_id(cart.id)
            cart_details_serializable = [
                {
                    'id': detail.id,
                    'product_id': detail.product_id,
                    'quantity': detail.quantity,
                    'product_image': detail.product.image_url,
                    'product_name': detail.product.name,
                    'product_price': float(detail.product.price)
                } for detail in cart_details
            ]

    success = []
    errors = []

    if request.method == 'POST':
        try:
            # Validate password if attempting to make changes that require verification
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Kiểm tra xem người dùng có đang cố gắng thay đổi mật khẩu hay không
            if new_password or confirm_password:
                # Nếu không có mật khẩu hiện tại, báo lỗi
                if not current_password:
                    errors.append('Vui lòng nhập mật khẩu hiện tại để xác thực.')
                    # Trả về ngay để hiển thị lỗi
                    return render(request, 'frontend/pages/profile.html', {
                        'user': user,
                        'categories': categories,
                        'errors': errors,
                        'cart_details': cart_details_serializable, # Đảm bảo dữ liệu giỏ hàng vẫn được truyền
                    })
                
                # Kiểm tra mật khẩu hiện tại có đúng không
                hashed_current_password = hashlib.md5(current_password.encode()).hexdigest()
                if user.password != hashed_current_password:
                    errors.append('Mật khẩu hiện tại không đúng.')
                    return render(request, 'frontend/pages/profile.html', {
                        'user': user,
                        'categories': categories,
                        'errors': errors,
                        'cart_details': cart_details_serializable,
                    })
                
                # Kiểm tra mật khẩu mới và mật khẩu xác nhận có khớp nhau không
                if new_password != confirm_password:
                    errors.append('Mật khẩu mới và mật khẩu xác nhận không khớp.')
                    return render(request, 'frontend/pages/profile.html', {
                        'user': user,
                        'categories': categories,
                        'errors': errors,
                        'cart_details': cart_details_serializable,
                    })
                
                # Cập nhật mật khẩu mới
                hashed_new_password = hashlib.md5(new_password.encode()).hexdigest()
                user.password = hashed_new_password
                success.append('Cập nhật mật khẩu thành công.')
            
            # Kiểm tra xử lý ảnh đại diện
            image = request.FILES.get('image')
            if image:
                image_url = upload_file.upload_file(image, 'users')
                user.image_url = image_url
                success.append('Cập nhật ảnh đại diện thành công.')
            
            # Cập nhật thông tin cơ bản
            user.name = request.POST.get('name', user.name) # Sử dụng giá trị cũ nếu không có trong POST
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.address = request.POST.get('address', user.address)
            user.save()
            
            success.append('Cập nhật thông tin người dùng thành công.')
            
            # Nếu đang ở trang profile, trả về trang profile
            referer = request.META.get('HTTP_REFERER', '')
            if 'profile' in referer:
                return render(request, 'frontend/pages/profile.html', {
                    'user': user,
                    'categories': categories,
                    'success': success,
                    'cart_details': cart_details_serializable,
                })
            else:
                # Nếu đang ở trang cart hoặc trang khác, giữ nguyên hành vi cũ
                return render(request, 'frontend/pages/cart.html', {
                    'user': user,
                    'categories': categories,
                    'cart_details': cart_details_serializable,
                    'success': success,
                })
                
        except Exception as e:
            errors.append('Có lỗi xảy ra: ' + str(e))
            # Nếu đang ở trang profile, trả về trang profile
            referer = request.META.get('HTTP_REFERER', '')
            if 'profile' in referer:
                return render(request, 'frontend/pages/profile.html', {
                    'user': user,
                    'categories': categories,
                    'errors': errors,
                    'cart_details': cart_details_serializable,
                })
            else:
                # Nếu đang ở trang cart hoặc trang khác, giữ nguyên hành vi cũ
                return render(request, 'frontend/pages/cart.html', {
                    'user': user,
                    'categories': categories,
                    'cart_details': cart_details_serializable,
                    'errors': errors,
                })
    else:
        # Xử lý yêu cầu GET: Hiển thị trang profile với thông tin người dùng hiện tại
        return render(request, 'frontend/pages/profile.html', {
            'user': user,
            'categories': categories,
            'cart_details': cart_details_serializable, # Đảm bảo giỏ hàng được truyền cho GET request
            'success': success, # Truyền cả success và errors để template có thể xử lý
            'errors': errors,
        })


def profile_page(request):
    if not request.session['user_id']:
        return redirect('login')
    user = get_user_by_id(request.session['user_id'])
    categories = get_all_categories()
    cart_details = get_cart_detail_by_cart_id(request.session['cart_id'])
    return render(request, 'frontend/pages/profile.html', {'user': user, 'categories': categories, 'cart_details': cart_details})

def profile_page_update(request):
    if request.method == 'POST':
        user_id = request.session['user_id']
        update_user(request, user_id)
    return redirect('profile')
     

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

# Back - end 
@admin_required
def dashboard_page(request):
    # Thống kê số lượng sản phẩm, danh mục, thương hiệu
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_brands = Brand.objects.count()
    
    # Thống kê người dùng
    total_users = User.objects.count()
    total_admin_users = User.objects.filter(role='admin').count()
    total_normal_users = User.objects.filter(role='user').count()
    
    # Thống kê đơn hàng
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # Tính tổng doanh thu
    completed_orders_list = Order.objects.filter(status='completed')
    total_revenue = sum(order.total_price for order in completed_orders_list)
    
    # Lấy top 5 sản phẩm bán chạy nhất
    # Top sản phẩm được đặt nhiều nhất
    from django.db.models import Count, Sum
    top_selling_products = OrderDetail.objects.values('product_id').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Lấy thông tin chi tiết của các sản phẩm bán chạy
    top_products = []
    for item in top_selling_products:
        product = Product.objects.get(id=item['product_id'])
        top_products.append({
            'id': product.id,
            'name': product.name,
            'total_sold': item['total_sold'],
            'revenue': float(product.price) * item['total_sold']
        })
    
    # Lấy 5 đơn hàng gần nhất
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Thống kê đơn hàng theo tháng cho biểu đồ
    from django.db.models.functions import TruncMonth
    orders_by_month = Order.objects.filter(
        status='completed'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        revenue=Sum('total_price')
    ).order_by('month')
    
    # Chuẩn bị dữ liệu cho biểu đồ
    months = []
    orders_count = []
    orders_revenue = []
    
    for data in orders_by_month:
        months.append(data['month'].strftime('%m/%Y'))
        orders_count.append(data['count'])
        orders_revenue.append(float(data['revenue']))
    
    # Phân tích tỷ lệ trạng thái đơn hàng
    order_status_labels = ['Đang xử lý', 'Hoàn thành', 'Đã hủy']
    order_status_data = [pending_orders, completed_orders, cancelled_orders]
    
    return render(request, 'backend/pages/dashboard.html', {
        'title': 'Dashboard',
        'total_products': total_products,
        'total_categories': total_categories,
        'total_brands': total_brands,
        'total_users': total_users,
        'total_admin_users': total_admin_users,
        'total_normal_users': total_normal_users,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'months': months,
        'orders_count': orders_count,
        'orders_revenue': orders_revenue,
        'order_status_labels': order_status_labels,
        'order_status_data': order_status_data
    })

def dashboard_login(request):
    if request.method == 'POST':
        messages = []
        username = request.POST['username']
        password = request.POST['password']
        user = User.objects.filter(username=username, role='admin')
        if user.count() == 0:
            messages.append("Không tìm thấy tài khoản của bạn")
            return render(request, 'backend/pages/login.html', {'title': 'Đăng nhập','messages': messages})
        check_pass = check_password(password,user[0].password)
        if check_pass:
            user = user.get()
            request.session['user_id'] = user.id
            request.session['role'] = 'admin'  # Set role as admin
            request.session['name'] = user.name
            request.session['email'] = user.email
            return redirect('dashboard')
        else:
            messages.append("Tài khoản không hợp lệ")
            return render(request, 'backend/pages/login.html', {'title': 'Đăng nhập','messages': messages})
    return render(request, 'backend/pages/login.html', {'title': 'Đăng nhập'})

@admin_required
def admin_products(request):
    products = Product.objects.all()
    return render(request, 'backend/pages/products/list.html', {'products': products})

@admin_required
def admin_product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        # Handle update
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.old_price = request.POST.get('old_price')
        product.stock = request.POST.get('stock')
        product.category_id = request.POST.get('category')
        product.brand_id = request.POST.get('brand')
        if 'image' in request.FILES:
            product.image_url = upload_file.upload_file(request.FILES['image'], 'products').replace("/static/","")
        product.save()
        messages.success(request, 'Cập nhật sản phẩm thành công')
    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'backend/pages/products/detail.html', {
        'product': product,
        'categories': categories,
        'brands': brands
    })

@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        category = Category.objects.get(id=request.POST.get('category'))
        product = Product(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            price=request.POST.get('price'),
            old_price=request.POST.get('old_price'),
            stock=request.POST.get('stock'),
            category_id=category.id,
            brand_id=request.POST.get('brand')
        )
        if 'image' in request.FILES:
            product.image_url = upload_file.upload_file(request.FILES['image'], 'products').replace("/static/","")
        product.save()
        messages.success(request, 'Thêm sản phẩm thành công')
        return redirect('admin_products')
    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'backend/pages/products/add.html', {
        'categories': categories,
        'brands': brands
    })

@admin_required
def admin_product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Xóa sản phẩm thành công')
        return redirect('admin_products')
    return render(request, 'backend/pages/products/delete.html', {'product': product})

# Similar patterns for other admin views (brands, categories, users)
@admin_required
def admin_brands(request):
    brands = Brand.objects.all()
    return render(request, 'backend/pages/brands/list.html', {'brands': brands})

@admin_required
def admin_brand_detail(request, id):
    brand = get_object_or_404(Brand, id=id)
    if request.method == 'POST':
        brand.name = request.POST.get('name')
        if 'image' in request.FILES:
            brand.image_url = upload_file.upload_file(request.FILES['image'], 'brands').replace('/static/', '')
        brand.save()
        messages.success(request, 'Cập nhật nhãn hàng thành công')
    return render(request, 'backend/pages/brands/detail.html', {'brand': brand})

@admin_required
def admin_brand_add(request):
    if request.method == 'POST':
        brand = Brand(name=request.POST.get('name'))
        if 'image' in request.FILES:
            brand.image_url = upload_file.upload_file(request.FILES['image'], 'brands').replace('/static/', '')
        brand.save()
        messages.success(request, 'Thêm nhãn hàng thành công')
        return redirect('admin_brands')
    return render(request, 'backend/pages/brands/add.html')

@admin_required
def admin_brand_delete(request, id):
    brand = get_object_or_404(Brand, id=id)
    if request.method == 'POST':
        brand.delete()
        messages.success(request, 'Xóa nhãn hàng thành công')
        return redirect('admin_brands')
    return render(request, 'backend/pages/brands/delete.html', {'brand': brand})

# Categories
@admin_required
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, 'backend/pages/categories/list.html', {'categories': categories})

@admin_required
def admin_category_detail(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        if 'image' in request.FILES:
            category.image_url = upload_file.upload_file(request.FILES['image'], 'categories')
        category.save()
        messages.success(request, 'Cập nhật danh mục thành công')
    return render(request, 'backend/pages/categories/detail.html', {'category': category})

@admin_required
def admin_category_add(request):
    if request.method == 'POST':
        category = Category(
            name=request.POST.get('name'),
            description=request.POST.get('description')
            
        )
        if 'image' in request.FILES:
            category.image_url = upload_file.upload_file(request.FILES['image'], 'categories')
        category.slug = random_name.convert_to_unsign(category.name).lower().replace(' ', '-')
        category.save()
        messages.success(request, 'Thêm danh mục thành công')
        return redirect('admin_categories')
    return render(request, 'backend/pages/categories/add.html')

@admin_required
def admin_category_delete(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Xóa danh mục thành công')
        return redirect('admin_categories')
    return render(request, 'backend/pages/categories/delete.html', {'category': category})

# Users
@admin_required
def admin_users(request):
    users = User.objects.all()
    return render(request, 'backend/pages/users/list.html', {'users': users})

@admin_required
def admin_user_detail(request, id):
    user = get_object_or_404(User, id=id)

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        role = request.POST.get('role')
        image = request.FILES.get('image')

        # Kiểm tra username đã tồn tại (trừ user hiện tại)
        if User.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại')
            return redirect('admin_user_detail', user_id=user_id)

        # Kiểm tra email đã tồn tại (trừ user hiện tại)
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, 'Email đã tồn tại')
            return redirect('admin_user_detail', user_id=user_id)

        # Kiểm tra số điện thoại
        if not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
            messages.error(request, 'Số điện thoại không hợp lệ')
            return redirect('admin_user_detail', user_id=user_id)

        # Cập nhật thông tin user
        user.username = username
        user.email = email
        user.name = name
        user.phone = phone
        user.address = address
        user.role = role

        # Cập nhật mật khẩu nếu có
        if password:
            user.set_password(password)

        # Xử lý ảnh đại diện
        if image:
            image_url = upload_file.upload_file(image, 'users')
            user.image_url = image_url

        user.save()
        messages.success(request, 'Cập nhật người dùng thành công')
        return redirect('admin_users')

    return render(request, 'backend/pages/users/detail.html', {'user': user})

@admin_required
def admin_user_add(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        role = request.POST.get('role')
        image = request.FILES.get('image')

        # Kiểm tra username đã tồn tại
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại')
            return redirect('admin_user_add')

        # Kiểm tra email đã tồn tại
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email đã tồn tại')
            return redirect('admin_user_add')

        # Kiểm tra số điện thoại
        if not phone.isdigit() or len(phone) < 10 or len(phone) > 11:
            messages.error(request, 'Số điện thoại không hợp lệ')
            return redirect('admin_user_add')

        # Tạo user mới
        user = User.objects.create(
            username=username,
            email=email,
            name=name,
            phone=phone,
            address=address,
            role=role
        )
        user.set_password(password)
        user.save()

        # Xử lý ảnh đại diện
        if image:
            image_url = upload_file.upload_file(image, 'users')
            user.image_url = image_url
            user.save()

        messages.success(request, 'Thêm người dùng thành công')
        return redirect('admin_users')

    return render(request, 'backend/pages/users/add.html')

@admin_required
def admin_user_delete(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        # Không cho phép xóa chính mình
        if user.id == request.session.get('user_id'):
            messages.error(request, 'Không thể xóa tài khoản của chính mình')
            return redirect('admin_users')
            
        # Xóa ảnh đại diện nếu có
        if user.image_url:
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, user.image_url))
            except:
                pass
                
        user.delete()
        messages.success(request, 'Xóa người dùng thành công')
        
    return redirect('admin_users')

# Công trình toàn diện
@admin_required
def admin_cong_trinh(request):
    cong_trinhs = CongTrinhToanDien.objects.all()
    return render(request, 'backend/pages/cong_trinh/list.html', {'cong_trinhs': cong_trinhs})

@admin_required
def admin_cong_trinh_detail(request, id):
    cong_trinh = get_object_or_404(CongTrinhToanDien, id=id)
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            status = request.POST.get('status')
            
            # Kiểm tra dữ liệu bắt buộc
            if not title or not description or not content:
                messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc')
                return render(request, 'backend/pages/cong_trinh/detail.html', {'cong_trinh': cong_trinh})
            
            # Cập nhật thông tin
            cong_trinh.title = title
            cong_trinh.description = description
            cong_trinh.content = content
            
            # Xử lý upload ảnh mới nếu có
            if 'image' in request.FILES and request.FILES['image']:
                cong_trinh.image_url = upload_file.upload_file(request.FILES['image'], 'cong_trinh')
            cong_trinh.status = status
            # Lưu thay đổi
            cong_trinh.save()
            messages.success(request, 'Cập nhật công trình thành công')
            return redirect('admin_cong_trinh')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'backend/pages/cong_trinh/detail.html', {'cong_trinh': cong_trinh})
    
    return render(request, 'backend/pages/cong_trinh/detail.html', {'cong_trinh': cong_trinh})

@admin_required
def admin_cong_trinh_add(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            
            # Kiểm tra dữ liệu bắt buộc
            if not title or not description or not content:
                messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc')
                return render(request, 'backend/pages/cong_trinh/add.html')
            
            # Tạo công trình mới
            cong_trinh = CongTrinhToanDien(
                title=title,
                description=description,
                content=content,
                author_id=request.session['user_id'],
                status='active'
            )
            
            # Xử lý upload ảnh
            if 'image' in request.FILES:
                cong_trinh.image_url = upload_file.upload_file(request.FILES['image'], 'cong_trinh')
            else:
                messages.error(request, 'Vui lòng chọn hình ảnh cho công trình')
                return render(request, 'backend/pages/cong_trinh/add.html')
            
            # Lưu công trình
            cong_trinh.save()
            messages.success(request, 'Thêm công trình thành công')
            return redirect('admin_cong_trinh')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'backend/pages/cong_trinh/add.html')
    
    return render(request, 'backend/pages/cong_trinh/add.html')

@admin_required
def admin_cong_trinh_delete(request, id):
    try:
        cong_trinh = CongTrinhToanDien.objects.get(id=id)
        # Xóa file ảnh nếu có
        if cong_trinh.image_url:
            try:
                image_path = os.path.join(settings.MEDIA_ROOT, str(cong_trinh.image_url))
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Lỗi khi xóa file ảnh: {str(e)}")
        
        cong_trinh.delete()
        messages.success(request, 'Đã xóa công trình thành công!')
    except CongTrinhToanDien.DoesNotExist:
        messages.error(request, 'Không tìm thấy công trình cần xóa!')
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra khi xóa công trình: {str(e)}')
    
    return redirect('admin_cong_trinh')

# Giải pháp âm thanh
@admin_required
def admin_giai_phap(request):
    giai_phaps = GiaiPhapAmThanh.objects.all()
    return render(request, 'backend/pages/giai_phap/list.html', {'giai_phaps': giai_phaps})

@admin_required
def admin_giai_phap_detail(request, id):
    giai_phap = get_object_or_404(GiaiPhapAmThanh, id=id)
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            youtube_url = request.POST.get('youtube_url', '')
            
            # Kiểm tra dữ liệu bắt buộc
            if not title or not description or not content:
                messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc')
                return render(request, 'backend/pages/giai_phap/detail.html', {'giai_phap': giai_phap})
            
            # Cập nhật thông tin
            giai_phap.title = title
            giai_phap.description = description
            giai_phap.content = content
            giai_phap.youtube_url = youtube_url
            
            # Xử lý upload ảnh mới nếu có
            if 'image' in request.FILES and request.FILES['image']:
                giai_phap.image_url = upload_file.upload_file(request.FILES['image'], 'giai_phap')
            
            # Lưu thay đổi
            giai_phap.save()
            messages.success(request, 'Cập nhật giải pháp thành công')
            return redirect('admin_giai_phap')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'backend/pages/giai_phap/detail.html', {'giai_phap': giai_phap})
    
    return render(request, 'backend/pages/giai_phap/detail.html', {'giai_phap': giai_phap})

@admin_required
def admin_giai_phap_add(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            youtube_url = request.POST.get('youtube_url', '')
            
            # Kiểm tra dữ liệu bắt buộc
            if not title or not description or not content:
                messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc')
                return render(request, 'backend/pages/giai_phap/add.html')
            
            # Tạo giải pháp mới
            giai_phap = GiaiPhapAmThanh(
                title=title,
                description=description,
                content=content,
                youtube_url=youtube_url,
                author_id=request.session['user_id'],
                status='active'
            )
            
            # Xử lý upload ảnh
            if 'image' in request.FILES:
                giai_phap.image_url = upload_file.upload_file(request.FILES['image'], 'giai_phap')
            else:
                messages.error(request, 'Vui lòng chọn hình ảnh cho giải pháp')
                return render(request, 'backend/pages/giai_phap/add.html')
            
            # Lưu giải pháp
            giai_phap.save()
            messages.success(request, 'Thêm giải pháp thành công')
            return redirect('admin_giai_phap')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'backend/pages/giai_phap/add.html')
    
    return render(request, 'backend/pages/giai_phap/add.html')

@admin_required
def admin_giai_phap_delete(request, giai_phap_id):
    try:
        giai_phap = GiaiPhapAmThanh.objects.get(id=giai_phap_id)
        # Xóa file ảnh nếu có
        if giai_phap.image_url:
            try:
                image_path = os.path.join(settings.MEDIA_ROOT, str(giai_phap.image_url))
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Lỗi khi xóa file ảnh: {str(e)}")
        
        giai_phap.delete()
        messages.success(request, 'Đã xóa giải pháp thành công!')
    except GiaiPhapAmThanh.DoesNotExist:
        messages.error(request, 'Không tìm thấy giải pháp cần xóa!')
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra khi xóa giải pháp: {str(e)}')
    
    return redirect('admin_giai_phap')

@admin_required
def dashboard_logout(request):
    request.session.flush()
    return redirect('dashboard_login')

# Quản lý hóa đơn
@admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'backend/pages/orders/list.html', {'orders': orders})

@admin_required
def admin_order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    order_details = OrderDetail.objects.filter(order_id=id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
        messages.success(request, 'Cập nhật trạng thái đơn hàng thành công')
    return render(request, 'backend/pages/orders/detail.html', {
        'order': order,
        'order_details': order_details
    })

@admin_required
def admin_order_delete(request, id):
    order = get_object_or_404(Order, id=id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Xóa đơn hàng thành công')
        return redirect('admin_orders')
    return render(request, 'backend/pages/orders/delete.html', {'order': order})

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Khởi tạo RAG handler
            from frontend.aiagent.rag_handler_refactored import RAGHandler
            rag_handler = RAGHandler()
            
            # Xử lý câu hỏi
            response = rag_handler.process_query(user_message)
            
            # Phân tích response để lấy answer và sources
            import re
            answer_match = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
            answer = answer_match.group(1) if answer_match else response
            
            # Kiểm tra xem có sources không
            sources = []
            if 'product-list' in answer:
                # Trích xuất thông tin sản phẩm từ câu trả lời
                products = Product.objects.all()[:10]  # Giới hạn 10 sản phẩm
                sources = [{
                    'metadata': {
                        'product_id': product.id,
                        'name': product.name,
                        'price': str(product.price),
                        'image_url': product.image_url,
                        'description': product.description,
                        'brand': product.brand.name if product.brand else None,
                        'category': product.category.name if product.category else None
                    }
                } for product in products]
            
            return JsonResponse({
                'status': 'success',
                'response': {
                    'answer': answer.strip(),
                    'sources': sources
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Chỉ hỗ trợ phương thức POST'
    })

def handle_general_questions(question):
    """Xử lý các câu hỏi chào hỏi và câu hỏi thông thường"""
    question_lower = question.lower().strip()
    
    # Xử lý các câu chào
    greetings = ["hi", "hello", "chào", "xin chào", "hey", "hi there", "chào bạn"]
    if any(greeting == question_lower for greeting in greetings):
        return "Xin chào! Tôi là trợ lý ảo về thiết bị âm thanh, tôi có thể giúp bạn tìm kiếm thông tin về sản phẩm, giá cả, thương hiệu. Bạn cần hỏi gì về thiết bị âm thanh?"
    
    # Xử lý câu hỏi về tên
    name_questions = ["tên bạn là gì", "bạn tên gì", "tên của bạn là gì", "bạn là ai", "what is your name", "who are you"]
    if any(name_question in question_lower for name_question in name_questions):
        return "Tôi là trợ lý AI chuyên về thiết bị âm thanh của DoAn_QuanLyDoDienTu. Tôi có thể giúp bạn tìm kiếm thông tin về các sản phẩm âm thanh, giá cả, và thương hiệu. Bạn cần hỏi gì về thiết bị âm thanh?"
    
    # Xử lý cảm ơn
    thanks = ["cảm ơn", "thank", "thanks", "cám ơn"]
    if any(thank_word in question_lower for thank_word in thanks):
        return "Không có gì! Rất vui khi được giúp đỡ bạn. Bạn có câu hỏi nào khác về thiết bị âm thanh không?"
    
    # Xử lý tạm biệt
    goodbyes = ["tạm biệt", "bye", "goodbye", "gặp lại sau"]
    if any(goodbye in question_lower for goodbye in goodbyes):
        return "Tạm biệt! Rất vui được giúp đỡ bạn. Hẹn gặp lại bạn lần sau!"
    
    # Xử lý câu hỏi về khả năng của chatbot
    capabilities = ["bạn có thể làm gì", "bạn giúp được gì", "chức năng của bạn", "bạn biết gì"]
    if any(capability in question_lower for capability in capabilities):
        return "Tôi có thể giúp bạn tìm kiếm thông tin về các sản phẩm âm thanh như loa, amply, tai nghe... Tôi cũng có thể cung cấp thông tin về giá cả, thương hiệu, tính năng và so sánh các sản phẩm. Bạn có thể hỏi tôi về bất kỳ sản phẩm âm thanh nào!"
    
    # Nếu không thuộc các trường hợp trên, trả về None để xử lý như câu hỏi về sản phẩm
    return None

def handle_combined_query(question):
    """Xử lý truy vấn kết hợp giữa hãng và các tiêu chí khác"""
    question_lower = question.lower()
    
    # Kiểm tra xem có đề cập đến hãng nào không
    brands = ["JBL", "Sony", "Denon", "Yamaha", "Bose", "Sennheiser", "Audio-Technica", 
              "KEF", "Klipsch", "Polk Audio", "Cambridge Audio", "Boston Acoustics", 
              "Harman Kardon", "Marshall", "Bang & Olufsen", "Focal", "Dynaudio"]
    
    found_brand = None
    for brand in brands:
        if brand.lower() in question_lower:
            found_brand = brand
            break
    
    # Nếu không tìm thấy thương hiệu, trả về None
    if not found_brand:
        return None
    
    # Kiểm tra các tiêu chí khác
    is_top_selling = any(term in question_lower for term in ["bán chạy", "mua nhiều", "bán nhiều"])
    is_most_liked = any(term in question_lower for term in ["yêu thích", "ưa chuộng", "nhiều like", "được yêu thích"])
    is_highest_price = any(term in question_lower for term in ["đắt nhất", "cao nhất", "giá cao"])
    is_lowest_price = any(term in question_lower for term in ["rẻ nhất", "thấp nhất", "giá thấp"])
    
    # Tạo truy vấn kết hợp
    if is_top_selling:
        return f"Tên hãng: {found_brand} sản phẩm có số lượng mua nhiều nhất"
    elif is_most_liked:
        return f"Tên hãng: {found_brand} sản phẩm có số lượng like nhiều nhất"
    elif is_highest_price:
        return f"Tên hãng: {found_brand} sản phẩm có giá cao nhất"
    elif is_lowest_price:
        return f"Tên hãng: {found_brand} sản phẩm có giá thấp nhất"
    
    # Nếu chỉ có thương hiệu mà không có tiêu chí cụ thể
    return f"Tên hãng: {found_brand}"

@csrf_exempt
def get_products_by_ids(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_ids = data.get('product_ids', [])
            
            # Lấy danh sách sản phẩm từ các ID
            products = Product.objects.filter(id__in=product_ids)
            
            # Chuyển đổi queryset thành list các dictionary
            products_data = []
            for product in products:
                products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.price),
                    'image_url': product.image_url,
                    'description': product.description,
                    'brand': product.brand.name if product.brand else None,
                    'category': product.category.name if product.category else None,
                    'url': f'/product/{product.id}'
                })
            
            return JsonResponse({
                'status': 'success',
                'products': products_data
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Chỉ hỗ trợ phương thức POST'
    })

def update_cart_session(request, user_id, cart_id):
    """
    Hàm cập nhật session giỏ hàng khi có thay đổi
    """
    cart_details = get_cart_detail_by_cart_id(cart_id)
    cart_details_serializable = [
        {
            'id': detail.id,
            'product_id': detail.product_id,
            'quantity': detail.quantity,
            'product_image': detail.product.image_url,
            'product_name': detail.product.name,
            'product_price': float(detail.product.price)
        } for detail in cart_details
    ]
    request.session['cart_id'] = cart_id
    request.session['quantity'] = len(cart_details)
    request.session['cart_details'] = cart_details_serializable
    return cart_details_serializable

def increase_cart_item(request, id):
    """
    Tăng số lượng sản phẩm trong giỏ hàng
    """
    if 'user_id' not in request.session:
        return redirect('login')
    
    user_id = request.session['user_id']
    cart = get_or_create_active_cart(user_id)
    
    # Tìm cart detail
    cart_detail = CartDetail.objects.filter(cart_id=cart.id, product_id=id).first()
    
    if cart_detail:
        # Tăng số lượng và lưu lại
        cart_detail.quantity += 1
        cart_detail.save()
        
        # Cập nhật session
        update_cart_session(request, user_id, cart.id)
    else:
        messages.error(request, "Sản phẩm không có trong giỏ hàng")
    
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

def decrease_cart_item(request, id):
    """
    Giảm số lượng sản phẩm trong giỏ hàng, nếu số lượng = 0 thì xóa sản phẩm
    """
    if 'user_id' not in request.session:
        return redirect('login')
    
    user_id = request.session['user_id']
    cart = get_or_create_active_cart(user_id)
    
    # Tìm cart detail
    cart_detail = CartDetail.objects.filter(cart_id=cart.id, product_id=id).first()
    
    if cart_detail:
        # Giảm số lượng
        if cart_detail.quantity > 1:
            cart_detail.quantity -= 1
            cart_detail.save()
        else:
            # Xóa sản phẩm khỏi giỏ hàng nếu số lượng = 1
            cart_detail.delete()
        
        # Cập nhật session
        update_cart_session(request, user_id, cart.id)
    else:
        messages.error(request, "Sản phẩm không có trong giỏ hàng")
    
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

@csrf_exempt
def get_chat_history(request):
    if request.method == 'GET':
        if 'user_id' in request.session:
            # Lấy lịch sử chat từ session
            chat_history = request.session.get('chat_history', [])
            return JsonResponse({
                'status': 'success',
                'chat_history': chat_history
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Người dùng chưa đăng nhập',
                'chat_history': []
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Phương thức không được hỗ trợ'
    })

@csrf_exempt
def save_chat_history(request):
    if request.method == 'POST':
        if 'user_id' in request.session:
            try:
                data = json.loads(request.body)
                chat_history = data.get('chat_history', [])
                
                # Lưu lịch sử chat vào session
                request.session['chat_history'] = chat_history
                request.session.modified = True
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Lịch sử chat đã được lưu'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Người dùng chưa đăng nhập'
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Phương thức không được hỗ trợ'
    })

# AI Agent views
@admin_required
def admin_aiagent(request):
    """Trang quản lý AI Agent trong admin dashboard"""
    from frontend.aiagent.data_processor import DataProcessor
    
    processor = DataProcessor()
    product_count = processor.get_product_count()
    last_update = processor.get_last_update_time()
    custom_data = processor.get_custom_data()
    
    return render(request, 'backend/pages/aiagent/index.html', {
        'title': 'AI Agent Management',
        'product_count': product_count,
        'last_update': last_update,
        'custom_data': custom_data
    })

@admin_required
def admin_aiagent_update_data(request):
    """Cập nhật dữ liệu sản phẩm cho AI Agent"""
    if request.method == 'POST':
        from frontend.aiagent.data_processor import DataProcessor
        
        processor = DataProcessor()
        message, product_count = processor.generate_product_data()
        
        if product_count > 0:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('admin_aiagent')

@admin_required
def admin_aiagent_update_custom_data(request):
    """Cập nhật dữ liệu tùy chỉnh cho AI Agent"""
    if request.method == 'POST':
        from frontend.aiagent.data_processor import DataProcessor
        
        custom_data = request.POST.get('custom_data', '')
        processor = DataProcessor()
        message = processor.save_custom_data(custom_data)
        
        messages.success(request, message)
    
    return redirect('admin_aiagent')

@csrf_exempt
def function_calling(request):
    """API để thực hiện function calling với AI Agent"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            
            if not query:
                return JsonResponse({'error': 'Thiếu thông tin query'}, status=400)
            
            from frontend.aiagent.rag_handler_refactored import RAGHandler
            
            handler = RAGHandler()
            response = handler.process_query(query)
            
            return JsonResponse({'response': response})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

