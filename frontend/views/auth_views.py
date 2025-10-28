from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import redirect, render
from django.contrib.auth.hashers import make_password,check_password
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
                    'total_price': float(detail.product.price) * detail.quantity,
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
def dashboard_logout(request):
    request.session.flush()
    return redirect('dashboard_login')