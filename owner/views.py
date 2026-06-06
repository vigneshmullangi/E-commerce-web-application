import json
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
from store.models import Order, OrderItem, OrderStatusHistory, Customer, Product, Category
from .models import DeliveryBoy

# ── Owner credentials (change these!) ──
OWNER_USERNAME = 'VIGNESH MULLANGI'
OWNER_PASSWORD = 'vignesh29'


# ═══════════════════════════════════════════════
#  AUTH DECORATORS
# ═══════════════════════════════════════════════

def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('owner_logged_in'):
            return redirect('owner:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def delivery_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('delivery_logged_in'):
            return redirect('owner:delivery_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════
#  OWNER AUTH
# ═══════════════════════════════════════════════

def owner_login(request):
    if request.session.get('owner_logged_in'):
        return redirect('owner:dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if username == OWNER_USERNAME and password == OWNER_PASSWORD:
            request.session['owner_logged_in'] = True
            request.session['owner_name']      = 'Shop Owner'
            return redirect('owner:dashboard')
        error = 'Invalid username or password.'

    return render(request, 'owner/login.html', {'error': error, 'role': 'owner'})


def owner_logout(request):
    request.session.pop('owner_logged_in', None)
    request.session.pop('owner_name', None)
    return redirect('owner:login')


# ═══════════════════════════════════════════════
#  DELIVERY BOY AUTH
# ═══════════════════════════════════════════════

def delivery_login(request):
    if request.session.get('delivery_logged_in'):
        return redirect('owner:delivery_orders')

    error = None
    if request.method == 'POST':
        mobile   = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            boy = DeliveryBoy.objects.get(mobile=mobile, is_active=True)
            if check_password(password, boy.password):
                request.session['delivery_logged_in'] = True
                request.session['delivery_id']        = boy.id
                request.session['delivery_name']      = boy.name
                return redirect('owner:delivery_orders')
            error = 'Invalid password.'
        except DeliveryBoy.DoesNotExist:
            error = 'Mobile number not found.'

    return render(request, 'owner/login.html', {'error': error, 'role': 'delivery'})


def delivery_logout(request):
    request.session.pop('delivery_logged_in', None)
    request.session.pop('delivery_id', None)
    request.session.pop('delivery_name', None)
    return redirect('owner:delivery_login')


# ═══════════════════════════════════════════════
#  OWNER DASHBOARD
# ═══════════════════════════════════════════════

@owner_required
def dashboard(request):
    today  = timezone.now().date()
    tab    = request.GET.get('tab', 'today')
    status = request.GET.get('status', '')

    # All orders queryset
    all_orders   = Order.objects.select_related('customer').prefetch_related('items')

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    today_orders = all_orders.filter(
        created_at__gte=start,
        created_at__lt=end
    )

    orders = today_orders if tab == 'today' else all_orders
    if status:
        orders = orders.filter(status=status)

    # Stats
    stats = {
        'today_count':     today_orders.count(),
        'today_sales':     today_orders.aggregate(t=Sum('total'))['t'] or 0,
        'pending':         all_orders.filter(status='pending').count(),
        'confirmed':       all_orders.filter(status='confirmed').count(),
        'shipped':         all_orders.filter(status='shipped').count(),
        'delivered':       all_orders.filter(status='delivered').count(),
        'cancelled':       all_orders.filter(status='cancelled').count(),
        'total_sales':     all_orders.filter(status='delivered').aggregate(t=Sum('total'))['t'] or 0,
        'total_customers': Customer.objects.count(),
        'total_orders':    all_orders.count(),
    }

    delivery_boys = DeliveryBoy.objects.filter(is_active=True)

    return render(request, 'owner/dashboard.html', {
        'orders':        orders,
        'stats':         stats,
        'tab':           tab,
        'active_status': status,
        'delivery_boys': delivery_boys,
        'owner_name':    request.session.get('owner_name', 'Owner'),
    })


# ═══════════════════════════════════════════════
#  ORDER DETAIL + STATUS UPDATE
# ═══════════════════════════════════════════════

@owner_required
def order_detail(request, order_id):
    order   = get_object_or_404(Order, id=order_id)
    items   = OrderItem.objects.filter(order=order).select_related('product')
    history = OrderStatusHistory.objects.filter(order=order).order_by('-changed_at')

    return render(request, 'owner/order_detail.html', {
        'order':      order,
        'items':      items,
        'history':    history,
        'statuses':   Order.STATUS_CHOICES,
        'owner_name': request.session.get('owner_name', 'Owner'),
    })


@owner_required
@require_POST
def update_status(request, order_id):
    order      = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    valid      = [s[0] for s in Order.STATUS_CHOICES]

    if new_status not in valid:
        return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)

    order.status = new_status
    order.save()

    OrderStatusHistory.objects.create(
        order=order, status=new_status, amount=order.total
    )

    return JsonResponse({'status': 'ok', 'new_status': new_status})


# ═══════════════════════════════════════════════
#  DELIVERY BOY MANAGEMENT
# ═══════════════════════════════════════════════

@owner_required
@require_POST
def add_delivery_boy(request):
    name     = request.POST.get('name', '').strip()
    mobile   = request.POST.get('mobile', '').strip()
    password = request.POST.get('password', '').strip()

    if not name or not mobile or not password:
        return JsonResponse({'status': 'error', 'message': 'All fields required.'}, status=400)

    if DeliveryBoy.objects.filter(mobile=mobile).exists():
        return JsonResponse({'status': 'error', 'message': 'Mobile already exists.'}, status=400)

    boy = DeliveryBoy.objects.create(
        name     = name,
        mobile   = mobile,
        password = make_password(password),
    )
    return JsonResponse({'status': 'ok', 'id': boy.id, 'name': boy.name, 'mobile': boy.mobile})


@owner_required
@require_POST
def remove_delivery_boy(request, boy_id):
    boy = get_object_or_404(DeliveryBoy, id=boy_id)
    boy.is_active = False
    boy.save()
    return JsonResponse({'status': 'ok'})


# ═══════════════════════════════════════════════
#  DELIVERY BOY — ORDERS VIEW
# ═══════════════════════════════════════════════

@delivery_required
def delivery_orders(request):
    status = request.GET.get('status', '')
    orders = Order.objects.select_related('customer').prefetch_related('items')

    if status:
        orders = orders.filter(status=status)

    return render(request, 'owner/delivery_orders.html', {
        'orders':        orders,
        'active_status': status,
        'delivery_name': request.session.get('delivery_name', 'Delivery Boy'),
    })


@delivery_required
def delivery_order_detail(request, order_id):
    order   = get_object_or_404(Order, id=order_id)
    items   = OrderItem.objects.filter(order=order).select_related('product')
    history = OrderStatusHistory.objects.filter(order=order).order_by('-changed_at')

    return render(request, 'owner/delivery_order_detail.html', {
        'order':         order,
        'items':         items,
        'history':       history,
        'delivery_name': request.session.get('delivery_name', 'Delivery Boy'),
    })