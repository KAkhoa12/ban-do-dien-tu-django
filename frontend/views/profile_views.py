from django.contrib import messages
from django.shortcuts import redirect, render 
from django.contrib.auth.hashers import make_password,check_password
# Thanh toán momo 
from frontend.utils.db_helper import * 
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
                check_pass = check_password(current_password,user.password)
                if not check_pass:
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
                hashed_new_password = make_password(new_password)
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
     
