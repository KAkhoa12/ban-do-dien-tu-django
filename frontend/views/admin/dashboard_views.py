from frontend.decorator import admin_required
from frontend.utils.db_helper import * 
from django.shortcuts import render
from frontend.utils.types import status_order_choices
# Back - end 
@admin_required
def dashboard_page(request):
    # Thống kê số lượng sản phẩm, danh mục, thương hiệu
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_brands = Brand.objects.count()
    
    # Thống kê người dùng
    total_users = User.objects.count()
    total_admin_users = User.objects.filter(role='admin').count()
    total_normal_users = User.objects.filter(role='user').count()
    
    # Thống kê đơn hàng
    total_orders = Order.objects.count()
    # Đếm theo tất cả trạng thái dựa trên types.py
    status_counts = {}
    for status_key in status_order_choices.keys():
        status_counts[status_key] = Order.objects.filter(status=status_key).count()
    # Giữ lại các biến cũ (nếu template/logic khác còn dùng)
    pending_orders = status_counts.get('pending', 0)
    completed_orders = status_counts.get('completed', 0)
    cancelled_orders = status_counts.get('cancelled', 0)
    
    # Tính tổng doanh thu
    completed_orders_list = Order.objects.filter(status='completed')
    total_revenue = sum(order.total_price for order in completed_orders_list)
    
    # Lấy top 5 sản phẩm bán chạy nhất
    # Top sản phẩm được đặt nhiều nhất (chỉ tính từ đơn hàng đã hoàn thành - completed)
    from django.db.models import Count, Sum
    top_selling_products = OrderDetail.objects.filter(
        order__status='completed'
    ).values('product_id').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]
    
    # Lấy thông tin chi tiết của các sản phẩm bán chạy
    top_products = []
    for item in top_selling_products:
        product = Product.objects.get(id=item['product_id'])
        top_products.append({
            'id': product.id,
            'name': product.name,
            'total_sold': item['total_sold'],
            'revenue': float(product.price) * item['total_sold']
        })
    
    # Lấy 5 đơn hàng gần nhất
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Thống kê đơn hàng theo tháng cho biểu đồ
    from django.db.models.functions import TruncMonth
    orders_by_month = Order.objects.filter(
        status='completed'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        revenue=Sum('total_price')
    ).order_by('month')
    
    # Chuẩn bị dữ liệu cho biểu đồ
    months = []
    orders_count = []
    orders_revenue = []
    
    for data in orders_by_month:
        months.append(data['month'].strftime('%m/%Y'))
        orders_count.append(data['count'])
        orders_revenue.append(float(data['revenue']))
    
    # Phân tích số lượng theo trạng thái dựa trên types.py (duy trì thứ tự keys)
    order_status_labels = [status_order_choices[k] for k in status_order_choices.keys()]
    order_status_data = [status_counts.get(k, 0) for k in status_order_choices.keys()]
    
    return render(request, 'backend/pages/dashboard.html', {
        'title': 'Dashboard',
        'total_products': total_products,
        'total_categories': total_categories,
        'total_brands': total_brands,
        'total_users': total_users,
        'total_admin_users': total_admin_users,
        'total_normal_users': total_normal_users,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'months': months,
        'orders_count': orders_count,
        'orders_revenue': orders_revenue,
        'order_status_labels': order_status_labels,
        'order_status_data': order_status_data
    })
