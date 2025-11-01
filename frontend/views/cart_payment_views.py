from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from frontend.utils.db_helper import * 
from frontend.services import create_momo_payment, verify_momo_response
from django.shortcuts import redirect, render
from frontend.models import Cart, CartDetail, Order
from django.contrib import messages
import json
from django.http import JsonResponse
def add_to_cart(request, id):
    if request.method == 'GET':
        if request.session.get('user_id') == None:
            return redirect('login')
        user_id = request.session.get('user_id')
        cart = get_or_create_active_cart(user_id)
        add_product_to_cart(cart.id, id)
        update_cart_session(request, user_id, cart.id)
    else:
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


def create_payment(request):
    if request.method == 'POST':
        categories = get_all_categories()
        
        # Kiểm tra xem người dùng đã đăng nhập chưa
        if 'user_id' not in request.session:
            messages.error(request, "Vui lòng đăng nhập để thực hiện thanh toán")
            return redirect('login')
        
        user_id = request.session['user_id']
        cart = get_or_create_active_cart(user_id)
        cart_details = get_cart_detail_by_cart_id(cart.id)
        user = get_user_by_id(user_id)
        
        # Kiểm tra giỏ hàng có sản phẩm không
        if not cart_details:
            messages.error(request, "Giỏ hàng của bạn đang trống")
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'categories': categories, 
                'cart_details': [], 
                'user': user
            })
        
        # Kiểm tra stock có đủ với quantity trong giỏ hàng không
        insufficient_stock_items = []
        for cart_detail in cart_details:
            product = cart_detail.product
            if product.stock < cart_detail.quantity:
                insufficient_stock_items.append({
                    'product_name': product.name,
                    'requested': cart_detail.quantity,
                    'available': product.stock
                })
        
        if insufficient_stock_items:
            error_messages = []
            for item in insufficient_stock_items:
                error_messages.append(
                    f"Sản phẩm '{item['product_name']}': chỉ còn {item['available']} sản phẩm trong kho, "
                    f"nhưng bạn đã chọn {item['requested']} sản phẩm."
                )
            messages.error(request, "Không đủ số lượng sản phẩm trong kho:\n" + "\n".join(error_messages))
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'categories': categories, 
                'cart_details': cart_details, 
                'user': user
            })
        
        missing_fields = []
        required_fields = ['name', 'email', 'phone', 'address']
        
        for field in required_fields:
            if not getattr(user, field):
                missing_fields.append(field)
        
        if missing_fields:
            messages.error(request, f"Must fill in the following fields: {', '.join(missing_fields)}")
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
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
            messages.error(request, "Số tiền không hợp lệ")
            return render(request, 'frontend/pages/cart.html', {
                'title': 'Giỏ hàng - Thanh toán', 
                'categories': categories, 
                'cart_details': cart_details, 
                'user': user
            })
        
        payment_method = request.POST.get('payment_method', 'cod')
        
        if payment_method == 'momo':
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
                messages.error(request, result.get('message', 'Có lỗi xảy ra'))
                return render(request, 'frontend/pages/cart.html', {
                    'title': 'Giỏ hàng - Thanh toán', 
                    'categories': categories, 
                    'cart_details': cart_details, 
                    'user': user
                })
        else:
            # Xử lý thanh toán COD (Cash On Delivery)
            # Đánh dấu giỏ hàng đã thanh toán
            cart.status = 'completed'
            cart.save()
            
            # Tạo đơn hàng mới với type='cod'
            order = create_order(user_id, 0, order_type='cod')
            
            cart_details_list = get_cart_detail_by_cart_id(cart.id)
            
            total_price = 0
            for cart_detail in cart_details_list:
                
                product = cart_detail.product
                item_price = product.price * cart_detail.quantity
                total_price += item_price
                
                # Tạo chi tiết đơn hàng
                create_order_detail(
                    order.id, 
                    cart_detail.product_id, 
                    cart_detail.product_options, 
                    cart_detail.quantity, 
                    cart_detail.product.price
                )
            
            # Cập nhật tổng tiền và trạng thái đơn hàng
            # Lưu ý: Logic trừ số lượng sản phẩm đã được chuyển vào Order.save() khi status = 'completed'
            order.total_price = total_price
            order.status = 'pending'
            order.save()
            
            # Tạo giỏ hàng mới cho người dùng
            new_cart = get_or_create_active_cart(user_id)
            
            # Cập nhật session với giỏ hàng mới
            update_cart_session(request, user_id, new_cart.id)
            
            # Hiển thị thông báo thành công
            messages.success(request, 'Đặt hàng thành công! Vui lòng thanh toán khi nhận hàng.')
            
            return redirect('order_history')

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
        # http://localhost:8000/payment/momo/result/?partnerCode=MOMOBKUN20180529&orderId=ad82a6b2-7a81-4fe5-9346-7fb06c25d647&requestId=354f75a6-7103-4c5c-ad18-2cbec11969e5&amount=1520000&orderInfo=Thanh+to%C3%A1n+%C4%91%C6%A1n+h%C3%A0ng&orderType=momo_wallet&transId=4603150621&resultCode=0&message=Successful.&payType=qr&responseTime=1761741495103&extraData=&signature=1fbfea876d7cbc80d66e7cb5c8fb8058bbc8a687c4e4c717470ffc9cebfc2a1e
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
                            
                            # Tạo đơn hàng mới với type='momo'
                            order = create_order(user_id, 0, order_type='momo')
                            cart_details = get_cart_detail_by_cart_id(cart_id)
                            
                            total_price = 0
                            for cart_detail in cart_details:
                                total_price += cart_detail.product.price * cart_detail.quantity
                                create_order_detail(order.id, cart_detail.product_id, '', cart_detail.quantity, cart_detail.product.price)
                            
                            # Cập nhật tổng tiền và trạng thái đơn hàng
                            # Lưu ý: Logic trừ số lượng sản phẩm đã được chuyển vào Order.save() khi status = 'completed'
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
                    
                    # Tạo đơn hàng mới với type='momo'
                    order = create_order(user_id, 0, order_type='momo')
                    cart_details = get_cart_detail_by_cart_id(cart_id)
                    
                    total_price = 0
                    for cart_detail in cart_details:
                        total_price += cart_detail.product.price * cart_detail.quantity
                        create_order_detail(order.id, cart_detail.product_id, '', cart_detail.quantity, cart_detail.product.price)
                    
                    # Cập nhật tổng tiền và trạng thái đơn hàng
                    # Lưu ý: Logic trừ số lượng sản phẩm đã được chuyển vào Order.save() khi status = 'completed'
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
            'total_price': float(detail.product.price) * detail.quantity,
            'product_image': detail.product.image_url,
            'product_name': detail.product.name,
            'product_price': float(detail.product.price)
        } for detail in cart_details
    ]
    request.session['cart_id'] = cart_id
    request.session['quantity'] = len(cart_details)
    request.session['cart_details'] = cart_details_serializable
    request.session['cart_total'] = sum(detail['total_price'] for detail in cart_details_serializable)
    return cart_details_serializable

