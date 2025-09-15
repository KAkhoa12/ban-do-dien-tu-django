from django.urls import path
from . import views

urlpatterns = [
    # Front end url 
    path('', views.home_page, name='home'),
    path('blank/', views.blank_page, name='blank'),
    path('checkout/', views.checkout_page, name='checkout'),
    path('product/', views.product_page, name='product'), 
    path('cart/', views.cart_page, name='cart'),
    path('categories/', views.all_categories_page, name='categories'),
    path('categories/<int:id>/<int:page>', views.all_products_by_category, name='view_products_by_category'),
    path('brands/', views.thuonghieu_page, name='brands'),
    path('brand/<int:id>/<int:page>', views.products_brand_page, name='brand_products'),
    path('search/', views.search_page, name='search'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('product/<int:id>', views.product_page, name='product_detail'),
    path('logout/', views.logout_page, name='logout'),
    path('add-to-cart/<int:id>', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:id>', views.remove_from_cart, name='remove_from_cart'),
    path('increase-cart-item/<int:id>', views.increase_cart_item, name='increase_cart_item'),
    path('decrease-cart-item/<int:id>', views.decrease_cart_item, name='decrease_cart_item'),
    path('payment/create/', views.create_payment, name='create_payment'),
    path('payment/momo/result/', views.payment_result, name='payment_result'),
    path('payment/ipn/', views.payment_ipn, name='payment_ipn'),
    path('profile/<int:user_id>', views.update_user, name='profile'),
    path('profile/', views.profile_page, name='profile_page'),
    path('profile/update/', views.profile_page_update, name='profile_update'),
    path('cong-trinh-toan-dien/', views.cong_trinh_toan_dien_page, name='cong_trinh_toan_dien'),
    path('cong-trinh-toan-dien/<int:id>/', views.cong_trinh_toan_dien_page, name='cong_trinh_detail'),
    path('giai-phap-am-thanh/', views.giai_phap_am_thanh_page, name='giai_phap_am_thanh'),
    path('giai-phap-am-thanh/<int:id>/', views.giai_phap_am_thanh_page, name='giai_phap_detail'),
    path('ve-chung-toi/', views.ve_chung_toi_page, name='ve_chung_toi'),
    
    # Back end url
    path('dashboard/login/', views.dashboard_login, name='dashboard_login'),
    path('dashboard/logout/', views.dashboard_logout, name='dashboard_logout'),
    path('dashboard/', views.dashboard_page, name='dashboard'),
    
    # Admin Products
    path('dashboard/products/', views.admin_products, name='admin_products'),
    path('dashboard/products/<int:id>/', views.admin_product_detail, name='admin_product_detail'),
    path('dashboard/products/add/', views.admin_product_add, name='admin_product_add'),
    path('dashboard/products/delete/<int:id>/', views.admin_product_delete, name='admin_product_delete'),
    
    # Admin Brands
    path('dashboard/brands/', views.admin_brands, name='admin_brands'),
    path('dashboard/brands/<int:id>/', views.admin_brand_detail, name='admin_brand_detail'),
    path('dashboard/brands/add/', views.admin_brand_add, name='admin_brand_add'),
    path('dashboard/brands/delete/<int:id>/', views.admin_brand_delete, name='admin_brand_delete'),
    
    # Admin Categories
    path('dashboard/categories/', views.admin_categories, name='admin_categories'),
    path('dashboard/categories/<int:id>/', views.admin_category_detail, name='admin_category_detail'),
    path('dashboard/categories/add/', views.admin_category_add, name='admin_category_add'),
    path('dashboard/categories/delete/<int:id>/', views.admin_category_delete, name='admin_category_delete'),
    
    # Admin Users
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/users/<int:id>/', views.admin_user_detail, name='admin_user_detail'),
    path('dashboard/users/add/', views.admin_user_add, name='admin_user_add'),
    path('dashboard/users/delete/<int:id>/', views.admin_user_delete, name='admin_user_delete'),
    
    # Admin Công trình toàn diện
    path('dashboard/cong-trinh/', views.admin_cong_trinh, name='admin_cong_trinh'),
    path('dashboard/cong-trinh/<int:id>/', views.admin_cong_trinh_detail, name='admin_cong_trinh_detail'),
    path('dashboard/cong-trinh/add/', views.admin_cong_trinh_add, name='admin_cong_trinh_add'),
    path('dashboard/cong-trinh/delete/<int:id>/', views.admin_cong_trinh_delete, name='admin_cong_trinh_delete'),
    
    # Admin Giải pháp âm thanh
    path('dashboard/giai-phap/', views.admin_giai_phap, name='admin_giai_phap'),
    path('dashboard/giai-phap/<int:id>/', views.admin_giai_phap_detail, name='admin_giai_phap_detail'),
    path('dashboard/giai-phap/add/', views.admin_giai_phap_add, name='admin_giai_phap_add'),
    path('dashboard/giai-phap/delete/<int:id>/', views.admin_giai_phap_delete, name='admin_giai_phap_delete'),
    
    # Admin Orders
    path('dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('dashboard/orders/<int:id>/', views.admin_order_detail, name='admin_order_detail'),
    path('dashboard/orders/delete/<int:id>/', views.admin_order_delete, name='admin_order_delete'),
    
    # Chatbot API
    # path('api/chatbot/', views.chatbot_query, name='chatbot_query'),
    path('api/products-by-ids/', views.get_products_by_ids, name='get_products_by_ids'),
    path('api/get-chat-history/', views.get_chat_history, name='get_chat_history'),
    path('api/save-chat-history/', views.save_chat_history, name='save_chat_history'),

    # Order history URLs
    path('order-history/', views.order_history_page, name='order_history'),
    path('order-history/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # AI Agent URLs
    path('dashboard/aiagent/', views.admin_aiagent, name='admin_aiagent'),
    path('dashboard/aiagent/update-data/', views.admin_aiagent_update_data, name='admin_aiagent_update_data'),
    path('dashboard/aiagent/update-custom-data/', views.admin_aiagent_update_custom_data, name='admin_aiagent_update_custom_data'),
    path('api/function-calling/', views.function_calling, name='function_calling'),
]