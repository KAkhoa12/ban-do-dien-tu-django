from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from frontend.models import GiaiPhapAmThanh
from frontend.utils.upload_file import upload_file
import os
from django.conf import settings
import requests
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
            if 'image' in request.FILES:
                giai_phap.image_url = upload_file(request.FILES['image'], 'giai_phap')
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
                giai_phap.image_url = upload_file(request.FILES['image'], 'giai_phap')
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

