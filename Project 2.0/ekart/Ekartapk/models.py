from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    cname = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.cname
    class Meta: verbose_name_plural = 'Categories'

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    disprice = models.DecimalField(max_digits=10, decimal_places=2)
    tprice = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ppic = models.ImageField(upload_to='products/', null=True, blank=True)
    pdes = models.TextField(blank=True)
    color = models.CharField(max_length=40, blank=True)
    pdate = models.DateField(auto_now_add=True)
    stock = models.PositiveIntegerField(default=0)
    def __str__(self): return self.name
    class Meta: ordering = ['name']

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='customers/', null=True, blank=True)
    def __str__(self): return self.user.username

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default='Placed', choices=[('Placed','Order Placed'),('Confirmed','Confirmed'),('Packed','Packed'),('Shipped','Shipped'),('Out for Delivery','Out for Delivery'),('Delivered','Delivered'),('Cancelled','Cancelled')])
    payment_method = models.CharField(max_length=30, default='COD')
    payment_status = models.CharField(max_length=30, default='Pending')
    tracking_note = models.CharField(max_length=250, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    def __str__(self): return f'Order #{self.pk} - {self.user.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self): return f'{self.product.name} x {self.quantity}'
