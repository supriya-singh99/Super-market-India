from django.contrib import admin
from .models import Category, Product, CustomerProfile, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'cname')
    search_fields = ('cname',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'disprice', 'tprice', 'stock')
    list_filter = ('category',)
    search_fields = ('name', 'category__cname')
    list_editable = ('disprice', 'stock')
    list_per_page = 30

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status', 'payment_method', 'payment_status', 'total')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    inlines = (OrderItemInline,)
    list_editable = ('status', 'payment_status')
    search_fields = ('id', 'user__username', 'user__email', 'tracking_note')
    readonly_fields = ('created_at',)
    fields = ('user', 'created_at', 'status', 'tracking_note', 'payment_method', 'payment_status', 'total')

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile', 'dob')
    search_fields = ('user__username', 'user__email', 'mobile')
