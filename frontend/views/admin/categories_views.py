from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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
