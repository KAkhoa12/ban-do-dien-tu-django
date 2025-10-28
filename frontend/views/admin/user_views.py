from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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
