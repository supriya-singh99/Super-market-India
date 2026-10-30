from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from Ekartapk import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('products/', views.products, name='products'),
    path('user/products/', views.products, name='user-products'),
    path('contactus/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('sevices/', views.services, name='services-old'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('user/signin/', views.signin, name='user-signin'),
    path('logout/', views.signout, name='logout'),
    path('user/logout/', views.signout, name='user-logout'),
    path('user/viewdetails/', views.viewdetails, name='viewdetails'),
    path('user/process/', views.process, name='process'),
    path('user/cart/', views.cart, name='user-cart'),
    path('cart/', views.cart, name='cart'),
    path('myprofile/', views.myprofile, name='myprofile'),
    path('myorder/', views.myorder, name='myorder'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/demo/', views.demo_payment, name='demo_payment'),
    path('orders/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
