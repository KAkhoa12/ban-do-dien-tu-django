from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render
# Quản lý hóa đơn
@admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'backend/pages/orders/list.html', {'orders': orders})

@admin_required
def admin_order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    order_details = OrderDetail.objects.filter(order_id=id)
    if request.method == 'POST':
        order.status = request.POST.get('status')
        order.save()
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
