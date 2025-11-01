from django.db import models
import uuid

class Category(models.Model):
    name = models.CharField(max_length=255)
    image_url = models.TextField()
    slug = models.TextField(default="default-slug")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    image_url = models.TextField()
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    role = models.CharField(max_length=10, choices=[('customer', 'Customer'), ('manager', 'Manager')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255)
    image_url = models.TextField()
    slug = models.TextField(default="default-slug")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField()
    old_price = models.FloatField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    number_of_sell = models.IntegerField(default=0)
    image_url = models.TextField()
    number_of_like = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    status = models.CharField(max_length=10, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name

class CartDetail(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_options = models.TextField()
    quantity = models.IntegerField()

    def __str__(self):
        return self.product.name
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    total_price = models.FloatField()
    status = models.CharField(max_length=10, default="pending")
    type = models.CharField(max_length=10, default="cod")  # cod hoặc momo
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name
    
    def save(self, *args, **kwargs):
        # Ngăn không cho cập nhật order nếu đã completed và đang cố thay đổi status
        if self.pk:  # Chỉ áp dụng khi update (không phải create mới)
            try:
                old_order = Order.objects.get(pk=self.pk)
                if old_order.status == 'completed' and self.status != 'completed':
                    # Nếu order cũ đã completed và đang cố thay đổi status, giữ nguyên completed
                    self.status = 'completed'
                elif old_order.status != 'completed' and self.status == 'completed':
                    # Khi chuyển sang completed, trừ số lượng sản phẩm
                    # Lưu ý: Logic này sẽ tự động được gọi khi admin cập nhật status từ admin_order_detail
                    self._deduct_product_stock()
            except Order.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def _deduct_product_stock(self):
        """Trừ số lượng sản phẩm trong kho khi order được completed"""
        order_details = self.orderdetail_set.all()
        for order_detail in order_details:
            product = order_detail.product
            product.stock -= order_detail.quantity
            if product.stock < 0:
                product.stock = 0  # Đảm bảo stock không âm
            product.save()

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_options = models.TextField()
    quantity = models.IntegerField()
    price = models.FloatField()

    def __str__(self):
        return self.product.name
    

class MomoPayment(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    order_info = models.CharField(max_length=255)
    request_id = models.CharField(max_length=50, unique=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    response_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_id} - {self.amount}"

    @staticmethod
    def generate_order_id():
        return str(uuid.uuid4())

    @staticmethod
    def generate_request_id():
        return str(uuid.uuid4())

class CongTrinhToanDien(models.Model):
    title = models.CharField(max_length=255, default="")
    description = models.TextField(default="")
    content = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.TextField(default="")
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return self.title

class GiaiPhapAmThanh(models.Model):
    title = models.CharField(max_length=255, default="")
    description = models.TextField(default="")
    content = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.TextField(default="")
    youtube_url = models.URLField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, default='active')

    def __str__(self):
        return self.title