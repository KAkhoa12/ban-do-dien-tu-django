from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from frontend.utils.types import status_order_choices
from datetime import datetime
# Quản lý hóa đơn
@admin_required
def admin_orders(request):
    # Filters
    search_query = request.GET.get('q', '').strip()
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()
    status = request.GET.get('status', '').strip()
    try:
        items_per_page = int(request.GET.get('items', '10'))
    except ValueError:
        items_per_page = 10

    queryset = Order.objects.select_related('user').order_by('-created_at')

    if search_query:
        search_filter = Q(user__name__icontains=search_query) | Q(user__email__icontains=search_query)
        if search_query.isdigit():
            search_filter = search_filter | Q(id=int(search_query))
        queryset = queryset.filter(search_filter)

    # Date range filtering
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to)
        except ValueError:
            pass

    # Status filtering
    if status and status in status_order_choices.keys():
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'backend/pages/orders/list.html', {
        'orders': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'q': search_query,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'status': status,
        'items': items_per_page,
        'status_choices': status_order_choices,
    })

@admin_required
def admin_order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    order_details = OrderDetail.objects.filter(order_id=id)
    if request.method == 'POST':
        old_status = order.status
        new_status = request.POST.get('status')
        
        # Lưu status cũ để kiểm tra
        order.status = new_status
        order.save()
        
        # Thông báo nếu đã trừ stock (khi chuyển sang completed)
        if old_status != 'completed' and new_status == 'completed':
            messages.success(request, f'Cập nhật trạng thái đơn hàng thành công. Đã trừ số lượng sản phẩm trong kho.')
        elif old_status == 'completed' and new_status != 'completed':
            messages.warning(request, 'Không thể thay đổi trạng thái đơn hàng đã hoàn thành.')
        else:
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
