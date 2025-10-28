from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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
