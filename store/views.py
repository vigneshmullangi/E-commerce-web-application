import json
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Category, Product, ProductPrice, Order, OrderItem, OrderStatusHistory, Customer


# ═══════════════════════════════════════════════
#  SESSION AUTH DECORATOR  (only for cart/orders)
# ═══════════════════════════════════════════════

def session_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('customer_mobile'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_customer(request):
    return {
        'mobile':  request.session.get('customer_mobile', ''),
        'name':    request.session.get('customer_name', ''),
        'address': request.session.get('customer_address', ''),
    }

def _is_logged_in(request):
    return bool(request.session.get('customer_mobile'))


# ═══════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════

def _get_cart(request):
    return request.session.get('cart', [])


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_context(request):
    cart     = _get_cart(request)
    items    = []
    subtotal = 0
    for c in cart:
        try:
            product = Product.objects.get(pk=c['product_id'])
        except Product.DoesNotExist:
            continue
        items.append({
            'product':    product,
            'unit':       c['unit'],
            'qty':        c['qty'],
            'unit_price': c['unit_price'],
            'total':      c['total'],
        })
        subtotal += c['total']

    delivery = 50 if (subtotal > 0 and subtotal < 500) else 0
    return {
        'cart_items':      items,
        'cart_subtotal':   subtotal,
        'cart_delivery':   delivery,
        'cart_total':      subtotal + delivery,
        'cart_item_count': sum(c['qty'] for c in cart),
    }


# ═══════════════════════════════════════════════
#  AUTH VIEWS
# ═══════════════════════════════════════════════

def login_view(request):
    # Already logged in → go home
    if request.session.get('customer_mobile'):
        return redirect('home')

    if request.method == 'POST':
        mobile  = request.POST.get('mobile', '').strip()
        name    = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()

        if not mobile or not name or not address:
            return render(request, 'store/login.html', {'error': 'Please fill all fields.'})

        Customer.objects.update_or_create(
            mobile=mobile,
            defaults={'name': name, 'address': address},
        )

        request.session['customer_mobile']  = mobile
        request.session['customer_name']    = name
        request.session['customer_address'] = address

        # Go back to where they came from, or home
        next_url = request.GET.get('next', 'home')
        return redirect(next_url)

    return render(request, 'store/login.html')


def logout_view(request):
    for key in ('customer_mobile', 'customer_name', 'customer_address', 'cart'):
        request.session.pop(key, None)
    return redirect('home')   # ← goes back to HOME, not login


# ═══════════════════════════════════════════════
#  MAIN PAGE VIEWS  (no login required — open to all)
# ═══════════════════════════════════════════════

def home_view(request):
    ctx = _cart_context(request)
    ctx['customer']    = _get_customer(request)
    ctx['logged_in']   = _is_logged_in(request)
    ctx['show_nav']    = True
    ctx['active_page'] = 'home'
    return render(request, 'store/home.html', ctx)


def products_view(request):
    from django.db.models import Q

    categories = Category.objects.all()
    products   = Product.objects.filter(is_active=True).select_related('category')

    cat_id = request.GET.get('cat')
    if cat_id:
        products = products.filter(category_id=cat_id)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    price_map = {}
    for product in products:
        price_map[product.id] = {}
        for pp in product.prices.filter(is_available=True).order_by('-weight_grams'):
            price_map[product.id][pp.unit_label] = float(pp.price)

    ctx = _cart_context(request)
    ctx.update({
        'categories':  categories,
        'products':    products,
        'price_map':   json.dumps(price_map),
        'active_cat':  int(cat_id) if cat_id else None,
        'query':       query,
        'count':       products.count(),
        'customer':    _get_customer(request),
        'logged_in':   _is_logged_in(request),
        'show_nav':    True,
        'active_page': 'products',
    })
    return render(request, 'store/products.html', ctx)


def about_view(request):
    ctx = _cart_context(request)
    ctx['customer']    = _get_customer(request)
    ctx['logged_in']   = _is_logged_in(request)
    ctx['show_nav']    = True
    ctx['active_page'] = 'about'
    return render(request, 'store/about.html', ctx)


# ═══════════════════════════════════════════════
#  CART  — login required
# ═══════════════════════════════════════════════

@session_required
@require_POST
def cart_add(request):
    try:
        data       = json.loads(request.body)
        product_id = int(data['product_id'])
        unit       = data['unit']
        qty        = int(data['qty'])

        product = Product.objects.get(pk=product_id, is_active=True)

        try:
            price_obj  = ProductPrice.objects.get(product=product, unit_label=unit, is_available=True)
            unit_price = float(price_obj.price)
        except ProductPrice.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Price not available.'}, status=400)

        total = round(unit_price * qty, 2)
        cart  = _get_cart(request)

        merged = False
        for item in cart:
            if item['product_id'] == product_id and item['unit'] == unit:
                item['qty']  += qty
                item['total'] = round(item['unit_price'] * item['qty'], 2)
                merged = True
                break

        if not merged:
            cart.append({
                'product_id': product_id,
                'unit':       unit,
                'qty':        qty,
                'unit_price': unit_price,
                'total':      total,
            })

        _save_cart(request, cart)
        return JsonResponse({'status': 'ok', 'message': f'{product.name} added to cart!'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@session_required
@require_POST
def cart_remove(request):
    try:
        data  = json.loads(request.body)
        index = int(data['index'])
        cart  = _get_cart(request)

        if 0 <= index < len(cart):
            cart.pop(index)
            _save_cart(request, cart)
            return JsonResponse({'status': 'ok'})

        return JsonResponse({'status': 'error', 'message': 'Invalid item.'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@session_required
def cart_get(request):
    cart     = _get_cart(request)
    items    = []
    subtotal = 0

    for c in cart:
        try:
            p = Product.objects.get(pk=c['product_id'])
            items.append({
                'product_id': c['product_id'],
                'name':       p.name,
                'emoji':      '📦',
                'unit':       c['unit'],
                'qty':        c['qty'],
                'unit_price': c['unit_price'],
                'total':      c['total'],
            })
            subtotal += c['total']
        except Product.DoesNotExist:
            continue

    delivery = 50 if (subtotal > 0 and subtotal < 500) else 0
    return JsonResponse({
        'items':      items,
        'subtotal':   subtotal,
        'delivery':   delivery,
        'total':      subtotal + delivery,
        'item_count': sum(c['qty'] for c in cart),
    })


# ═══════════════════════════════════════════════
#  ORDER — login required
# ═══════════════════════════════════════════════

@session_required
@require_POST
def order_place(request):
    cart = _get_cart(request)
    if not cart:
        return JsonResponse({'status': 'error', 'message': 'Cart is empty.'}, status=400)

    customer = _get_customer(request)
    subtotal = sum(c['total'] for c in cart)
    delivery = 50 if subtotal < 500 else 0
    total    = subtotal + delivery

    cust_obj, _ = Customer.objects.get_or_create(
        mobile=customer['mobile'],
        defaults={'name': customer['name'], 'address': customer['address']},
    )

    order = Order.objects.create(
        customer        = cust_obj,
        subtotal        = subtotal,
        delivery_charge = delivery,
        total           = total,
    )

    OrderStatusHistory.objects.create(order=order, status='pending', amount=total)

    for c in cart:
        try:
            product = Product.objects.get(pk=c['product_id'])
            OrderItem.objects.create(
                order      = order,
                product    = product,
                unit_label = c['unit'],
                unit_price = c['unit_price'],
                quantity   = c['qty'],
                line_total = c['total'],
            )
        except Product.DoesNotExist:
            continue

    _save_cart(request, [])
    return JsonResponse({'status': 'ok', 'order_id': order.pk})


@session_required
def order_confirm(request):
    customer = _get_customer(request)
    cust_obj = Customer.objects.filter(mobile=customer['mobile']).first()
    order    = Order.objects.filter(customer=cust_obj).first() if cust_obj else None

    ctx = _cart_context(request)
    ctx['order']       = order
    ctx['customer']    = customer
    ctx['logged_in']   = True
    ctx['show_nav']    = True
    ctx['active_page'] = 'products'
    return render(request, 'store/order_confirm.html', ctx)


@session_required
def order_status(request):
    customer = _get_customer(request)
    cust_obj = Customer.objects.filter(mobile=customer['mobile']).first()
    orders   = Order.objects.filter(customer=cust_obj).order_by('-created_at') if cust_obj else []

    ctx = _cart_context(request)
    ctx['orders']      = orders
    ctx['customer']    = customer
    ctx['logged_in']   = True
    ctx['show_nav']    = True
    ctx['active_page'] = 'order_status'
    return render(request, 'store/order_status.html', ctx)


@session_required
def order_detail(request, order_id):
    customer = _get_customer(request)
    cust_obj = Customer.objects.filter(mobile=customer['mobile']).first()

    if not cust_obj:
        return redirect('order_status')

    order   = get_object_or_404(Order, id=order_id, customer=cust_obj)
    history = OrderStatusHistory.objects.filter(order=order).order_by('-changed_at')

    ctx = _cart_context(request)
    ctx['order']       = order
    ctx['history']     = history
    ctx['customer']    = customer
    ctx['logged_in']   = True
    ctx['show_nav']    = True
    ctx['active_page'] = 'order_status'
    return render(request, 'store/order_detail.html', ctx)