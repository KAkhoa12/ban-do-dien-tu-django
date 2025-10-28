from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect, get_object_or_404
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
