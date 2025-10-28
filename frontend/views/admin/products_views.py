from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.http import urlencode
@admin_required
def admin_products(request):
    # Read GET params
    brand_query = (request.GET.get('brand') or '').strip()
    category_query = (request.GET.get('category') or '').strip()
    try:
        items = int(request.GET.get('items') or 10)
    except (TypeError, ValueError):
        items = 10
    try:
        page = int(request.GET.get('page') or 1)
    except (TypeError, ValueError):
        page = 1

    products_queryset = Product.objects.select_related('brand', 'category').all().order_by('-id')

    if brand_query:
        products_queryset = products_queryset.filter(brand_id=brand_query)
    if category_query:
        products_queryset = products_queryset.filter(category_id=category_query)

    paginator = Paginator(products_queryset, items)
    page_obj = paginator.get_page(page)

    # Build base query (no page) for links
    base_query_dict = {'items': items}
    if brand_query:
        base_query_dict['brand'] = brand_query
    if category_query:
        base_query_dict['category'] = category_query
    base_query = urlencode(base_query_dict)

    categories = Category.objects.all().order_by('name')
    brands = Brand.objects.all().order_by('name')
    return render(request, 'backend/pages/products/list.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'items': items,
        'brand_query': brand_query,
        'category_query': category_query,
        'filters_query': base_query,  # keep var name used in template
        'categories': categories,
        'brands': brands,
    })

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
