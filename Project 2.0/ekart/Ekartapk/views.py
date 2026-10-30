from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Category, Product, CustomerProfile, Order, OrderItem


def home(request):
    return render(request, 'user/index.html', {
        'data': Category.objects.all(),
        'products': Product.objects.select_related('category').all()[:8],
    })

def about(request): return render(request, 'user/about.html')
def contact(request): return render(request, 'user/contect.html')
def services(request): return render(request, 'user/sevices.html')

def products(request):
    items = Product.objects.select_related('category').all()
    category_id = request.GET.get('abc')
    if category_id:
        items = items.filter(category_id=category_id)
    q = request.GET.get('q', '').strip()
    if q: items = items.filter(Q(name__icontains=q) | Q(category__cname__icontains=q))
    return render(request, 'user/products.html', {'products': items, 'cat': Category.objects.all(), 'search_query': q})

def viewdetails(request):
    item = get_object_or_404(Product, pk=request.GET.get('msg'))
    return render(request, 'user/viewdetails.html', {'d': [item]})

def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('passwd', '')
        if not name or not email or not password:
            messages.error(request, 'Please fill all required fields.')
        elif User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered. Please sign in.')
        else:
            user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
            CustomerProfile.objects.create(user=user, dob=request.POST.get('dob') or None,
                mobile=request.POST.get('mobile', ''), address=request.POST.get('address', ''),
                photo=request.FILES.get('myfile'))
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('home')
    return render(request, 'user/signup.html')

def signin(request):
    if request.method == 'POST':
        email = request.POST.get('uname', '').strip().lower()
        password = request.POST.get('passwd', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid email or password.')
    return render(request, 'user/signin.html')

def signout(request):
    logout(request)
    return redirect('home')


def _cart_items(request):
    """Session cart: {product_id: quantity}."""
    raw = request.session.get('cart_items', {})
    # Migrate old cart_ids sessions without losing products.
    if not raw and request.session.get('cart_ids'):
        raw = {str(pid): 1 for pid in request.session.get('cart_ids', [])}
        request.session['cart_items'] = raw
    return {str(k): max(1, int(v)) for k, v in raw.items()}

def cart(request):
    # Handle quantity updates before the add-to-cart branch.
    if request.method == 'POST' and request.POST.get('update_cart'):
        items = _cart_items(request)
        for pid in list(items):
            try:
                qty = int(request.POST.get(f'qty_{pid}', items[pid]))
                if qty <= 0:
                    items.pop(pid, None)
                else:
                    items[pid] = min(qty, 99)
            except (TypeError, ValueError):
                pass
        request.session['cart_items'] = items
        request.session.modified = True
        messages.success(request, 'Cart updated successfully.')
        return redirect('cart')

    if request.method == 'POST':
        pid = request.POST.get('product_id')
        product = Product.objects.filter(pk=pid).first() if pid else None
        if product:
            items = _cart_items(request)
            items[str(product.id)] = min(items.get(str(product.id), 0) + 1, 99)
            request.session['cart_items'] = items
            request.session.modified = True
            messages.success(request, f'{product.name} added to cart.')
        return redirect('cart')

    remove_id = request.GET.get('remove')
    if remove_id:
        items = _cart_items(request)
        items.pop(str(remove_id), None)
        request.session['cart_items'] = items
        request.session.modified = True
        messages.success(request, 'Product removed from cart.')
        return redirect('cart')

    quantities = _cart_items(request)
    products_by_id = {str(p.id): p for p in Product.objects.filter(
        id__in=quantities).select_related('category')}
    rows, total = [], Decimal('0.00')
    for pid, qty in quantities.items():
        product = products_by_id.get(pid)
        if not product:
            continue
        line_total = product.disprice * qty
        total += line_total
        rows.append({'product': product, 'quantity': qty, 'line_total': line_total})
    return render(request, 'user/cart.html', {
        'cart_items': rows, 'cart_total': total,
        'cart_count': sum(row['quantity'] for row in rows),
    })

def process(request):
    pid = request.GET.get('pid')
    product = get_object_or_404(Product, pk=pid)
    action = request.GET.get('bn', 'cart')
    if action == 'cart':
        items = _cart_items(request)
        items[str(product.id)] = items.get(str(product.id), 0) + 1
        request.session['cart_items'] = items
        messages.success(request, f'{product.name} added to cart.')
        return redirect('cart')
    if action == 'order':
        request.session['checkout_product'] = product.id
        return redirect('checkout')
    if action == 'orderfromcart':
        return redirect('checkout')
    return redirect('products')

def _checkout_lines(request):
    quantities = _cart_items(request)
    single_id = request.session.get('checkout_product')
    if single_id:
        quantities = {str(single_id): 1}
    products_by_id = {str(item.id): item for item in Product.objects.filter(id__in=quantities)}
    lines, total = [], Decimal('0.00')
    for pid, qty in quantities.items():
        product = products_by_id.get(pid)
        if product:
            line_total = product.disprice * qty
            total += line_total
            lines.append((product, qty, line_total))
    return lines, total

@login_required(login_url='signin')
def checkout(request):
    lines, total = _checkout_lines(request)
    if not lines:
        messages.info(request, 'Your cart is empty. Add products before checkout.')
        return redirect('products')
    if request.method == 'POST':
        method = request.POST.get('payment_method', 'COD')
        if method not in ('COD', 'DEMO_UPI', 'DEMO_CARD'):
            method = 'COD'
        request.session['pending_payment_method'] = method
        return redirect('demo_payment')
    return render(request, 'user/checkout.html', {'lines': lines, 'total': total})

@login_required(login_url='signin')
def demo_payment(request):
    lines, total = _checkout_lines(request)
    if not lines:
        messages.info(request, 'Your checkout session expired. Please select products again.')
        return redirect('cart')
    method = request.session.get('pending_payment_method', 'DEMO_CARD')
    if request.method == 'POST':
        action = request.POST.get('payment_action', 'success')
        if action not in ('success', 'failure'):
            action = 'failure'
        if action == 'failure':
            messages.error(request, 'Demo payment was not completed. No money was charged.')
            return redirect('demo_payment')
        # Check inventory again immediately before creating the order.
        for product, qty, _ in lines:
            product.refresh_from_db()
            if product.stock > 0 and product.stock < qty:
                messages.error(request, f'Only {product.stock} unit(s) of {product.name} are available.')
                return redirect('cart')
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user, total=total, status='Confirmed',
                payment_method=method,
                payment_status='Pending' if method == 'COD' else 'Demo Successful - Not Charged',
                tracking_note='Order confirmed. This is a college project demonstration.'
            )
            for product, qty, _ in lines:
                OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.disprice)
                if product.stock > 0:
                    product.stock -= qty
                    product.save(update_fields=['stock'])
        if request.session.get('checkout_product'):
            request.session.pop('checkout_product', None)
        else:
            request.session['cart_items'] = {}
        request.session.pop('pending_payment_method', None)
        return redirect('order_confirmation', order_id=order.id)
    return render(request, 'user/payment.html', {
        'lines': lines, 'total': total, 'payment_method': method,
    })

@login_required(login_url='signin')
def order_confirmation(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=order_id, user=request.user
    )
    return render(request, 'user/order_confirmation.html', {'order': order})

@login_required(login_url='signin')
def myprofile(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('name', request.user.first_name)
        request.user.save()
        profile.mobile = request.POST.get('mobile', profile.mobile)
        profile.address = request.POST.get('address', profile.address)
        if request.FILES.get('myfile'): profile.photo = request.FILES['myfile']
        profile.save(); messages.success(request, 'Profile updated.')
        return redirect('myprofile')
    return render(request, 'user/myprofile.html', {'profile': profile})

@login_required(login_url='signin')
def myorder(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    stages = ['Placed', 'Confirmed', 'Packed', 'Shipped', 'Out for Delivery', 'Delivered']
    progress_map = {'Placed': 0, 'Confirmed': 1, 'Packed': 2, 'Shipped': 3,
                    'Out for Delivery': 4, 'Delivered': 5, 'Cancelled': -1}
    # Attach a template-friendly progress index to each order.
    for order in orders:
        order_progress = progress_map.get(order.status, 0)
        order.order_progress = order_progress
    return render(request, 'user/myorder.html', {'orders': orders, 'stages': stages})


def wishlist(request):
    saved = request.session.get('wishlist_items', [])
    if request.method == 'POST':
        pid = str(request.POST.get('product_id', ''))
        if Product.objects.filter(pk=pid).exists():
            if pid in saved:
                saved.remove(pid)
                messages.info(request, 'Product removed from wishlist.')
            else:
                saved.append(pid)
                messages.success(request, 'Product saved to wishlist.')
            request.session['wishlist_items'] = saved
            request.session.modified = True
        return redirect(request.POST.get('next') or 'wishlist')
    products_saved = Product.objects.filter(id__in=saved).select_related('category')
    return render(request, 'user/wishlist.html', {'wishlist_products': products_saved})
