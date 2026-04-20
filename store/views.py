import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import UserProfile, Category, Product, ProductPrice, Order, OrderItem, OrderStatusHistory


# ═══════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════

def _get_cart(request):
    """Read cart from session. Each item: {product_id, unit, qty, unit_price, total}"""
    return request.session.get('cart', [])


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_context(request):
    """Build context dict for the cart badge + drawer."""
    cart    = _get_cart(request)
    items   = []
    subtotal = 0
    for c in cart:
        try:
            product = Product.objects.get(pk=c['product_id'])
        except Product.DoesNotExist:
            continue
        items.append({
            'product':   product,
            'unit':      c['unit'],
            'qty':       c['qty'],
            'unit_price': c['unit_price'],
            'total':     c['total'],
        })
        subtotal += c['total']

    delivery = 50 if (subtotal > 0 and subtotal < 500) else 0
    return {
        'cart_items':       items,
        'cart_subtotal':    subtotal,
        'cart_delivery':    delivery,
        'cart_total':       subtotal + delivery,
        'cart_item_count':  sum(c['qty'] for c in cart),
    }


# ═══════════════════════════════════════════════
#  AUTH VIEWS
# ═══════════════════════════════════════════════

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        email    = request.POST.get('email', '').strip()
        phone    = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        error = None
        if not all([name, email, phone, password]):
            error = 'Please fill all fields.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.objects.filter(email=email).exists():
            error = 'Email is already registered.'

        if error:
            return render(request, 'store/signup.html', {'error': error})

        # Create user
        username = email.split('@')[0]
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name,
        )
        UserProfile.objects.create(user=user, phone=phone)
        return render(request, 'store/signup.html', {'success': 'Account created! Please login.'})

    return render(request, 'store/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            return render(request, 'store/login.html', {'error': 'Please fill all fields.'})

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'store/login.html', {'error': 'Invalid email or password.'})

        user = authenticate(request, username=user_obj.username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'store/login.html', {'error': 'Invalid email or password.'})

    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ═══════════════════════════════════════════════
#  MAIN PAGE VIEWS
# ═══════════════════════════════════════════════

@login_required
def home_view(request):
    ctx = _cart_context(request)
    ctx['show_nav']    = True
    ctx['active_page'] = 'home'
    return render(request, 'store/home.html', ctx)


@login_required
def products_view(request):
    categories = Category.objects.all()
    products   = Product.objects.filter(is_active=True).select_related('category')

    # Optional filter by category
    cat_id = request.GET.get('cat')
    if cat_id:
        products = products.filter(category_id=cat_id)

    # Build price map: {product_id: {unit_label: price}}
    price_map = {}
    for product in products:
        price_map[product.id] = {}
        for pp in product.prices.filter(is_available=True).order_by('-weight_grams'):
            price_map[product.id][pp.unit_label] = float(pp.price)

    ctx = _cart_context(request)
    ctx.update({
        'categories': categories,
        'products':   products,
        'price_map':  json.dumps(price_map),  # Pass to JS
        'active_cat': int(cat_id) if cat_id else None,
        'show_nav':    True,
        'active_page': 'products',
    })
    return render(request, 'store/products.html', ctx)


@login_required
def about_view(request):
    ctx = _cart_context(request)
    ctx['total_customers'] = User.objects.count()
    ctx['show_nav']        = True
    ctx['active_page']     = 'about'
    return render(request, 'store/about.html', ctx)


# ═══════════════════════════════════════════════
#  CART  (AJAX endpoints)
# ═══════════════════════════════════════════════

@login_required
@require_POST
def cart_add(request):
    print("\n" + "="*60)
    print("CART ADD REQUEST RECEIVED")
    print("="*60)
    print(f"User: {request.user.username}")
    print(f"Request body: {request.body}")
    
    try:
        data = json.loads(request.body)
        print(f"Parsed data: {data}")
        
        product_id = int(data['product_id'])
        unit = data['unit']
        qty = int(data['qty'])
        
        print(f"Product ID: {product_id}, Unit: {unit}, Qty: {qty}")

        product = Product.objects.get(pk=product_id, is_active=True)
        print(f"Product found: {product.name}")
        
        # Fetch price from ProductPrice table
        try:
            price_obj = ProductPrice.objects.get(product=product, unit_label=unit, is_available=True)
            unit_price = float(price_obj.price)
            print(f"Price found: ₹{unit_price}")
        except ProductPrice.DoesNotExist:
            print("ERROR: Price not found!")
            return JsonResponse({'status': 'error', 'message': 'Price not available for this unit.'}, status=400)
        
        total = round(unit_price * qty, 2)
        print(f"Total calculated: ₹{total}")

        cart = _get_cart(request)
        print(f"Current cart before add: {cart}")

        # Check if same product + unit exists → merge
        merged = False
        for item in cart:
            if item['product_id'] == product_id and item['unit'] == unit:
                item['qty'] += qty
                item['total'] = round(item['unit_price'] * item['qty'], 2)
                merged = True
                print(f"Merged with existing item. New qty: {item['qty']}")
                break

        if not merged:
            new_item = {
                'product_id': product_id,
                'unit': unit,
                'qty': qty,
                'unit_price': unit_price,
                'total': total,
            }
            cart.append(new_item)
            print(f"Added new item: {new_item}")

        _save_cart(request, cart)
        print(f"Final cart: {cart}")
        print("="*60 + "\n")
        
        return JsonResponse({'status': 'ok', 'message': f'{product.name} added to cart!'})

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def cart_remove(request):
    print("\n" + "="*60)
    print("CART REMOVE REQUEST")
    print("="*60)
    
    try:
        data = json.loads(request.body)
        index = int(data['index'])
        print(f"Removing index: {index}")
        
        cart = _get_cart(request)
        print(f"Cart before remove: {cart}")
        
        if 0 <= index < len(cart):
            removed = cart.pop(index)
            print(f"Removed item: {removed}")
            _save_cart(request, cart)
            print(f"Cart after remove: {cart}")
            print("="*60 + "\n")
            return JsonResponse({'status': 'ok'})
        
        print("ERROR: Invalid index")
        print("="*60 + "\n")
        return JsonResponse({'status': 'error', 'message': 'Invalid item.'}, status=400)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("="*60 + "\n")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def cart_get(request):
    """Return full cart JSON for the drawer."""
    print("\n" + "="*60)
    print("CART GET REQUEST")
    print("="*60)
    
    cart = _get_cart(request)
    print(f"Retrieved cart: {cart}")
    
    items = []
    subtotal = 0
    
    for c in cart:
        try:
            p = Product.objects.get(pk=c['product_id'])
            items.append({
                'product_id': c['product_id'],
                'name': p.name,
                'emoji': '📦',
                'unit': c['unit'],
                'qty': c['qty'],
                'unit_price': c['unit_price'],
                'total': c['total'],
            })
            subtotal += c['total']
        except Product.DoesNotExist:
            print(f"WARNING: Product {c['product_id']} not found")
            continue

    delivery = 50 if (subtotal > 0 and subtotal < 500) else 0
    
    response_data = {
        'items': items,
        'subtotal': subtotal,
        'delivery': delivery,
        'total': subtotal + delivery,
        'item_count': sum(c['qty'] for c in cart),
    }
    
    print(f"Returning response: {response_data}")
    print("="*60 + "\n")
    
    return JsonResponse(response_data)


# ═══════════════════════════════════════════════
#  ORDER
# ═══════════════════════════════════════════════

@login_required
@require_POST
def order_place(request):
    """Create Order + OrderItems, clear cart, return order id."""
    cart = _get_cart(request)
    if not cart:
        return JsonResponse({'status': 'error', 'message': 'Cart is empty.'}, status=400)

    subtotal = sum(c['total'] for c in cart)
    delivery = 50 if subtotal < 500 else 0
    total    = subtotal + delivery

    order = Order.objects.create(
        user=request.user,
        subtotal=subtotal,
        delivery_charge=delivery,
        total=total,
    )

    # Save initial status to history
    OrderStatusHistory.objects.create(
        order=order,
        status='pending',
        amount=total
    )

    for c in cart:
        try:
            product = Product.objects.get(pk=c['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                unit_label=c['unit'],
                unit_price=c['unit_price'],
                quantity=c['qty'],
                line_total=c['total'],
            )
        except Product.DoesNotExist:
            continue

    _save_cart(request, [])
    return JsonResponse({'status': 'ok', 'order_id': order.pk})


@login_required
def order_confirm(request):
    """Confirmation page."""
    order = Order.objects.filter(user=request.user).first()
    ctx   = _cart_context(request)
    ctx['order']       = order
    ctx['show_nav']    = True
    ctx['active_page'] = 'products'
    return render(request, 'store/order_confirm.html', ctx)


@login_required
def order_status(request):
    """List all orders for current user."""
    orders = Order.objects.filter(user=request.user)
    ctx = _cart_context(request)
    ctx['orders']      = orders
    ctx['show_nav']    = True
    ctx['active_page'] = 'products'
    return render(request, 'store/order_status.html', ctx)


@login_required
def order_detail(request, order_id):
    """Detail page for one order."""
    order   = get_object_or_404(Order, id=order_id, user=request.user)
    history = OrderStatusHistory.objects.filter(order=order).order_by('-changed_at')
    
    ctx = _cart_context(request)
    ctx['order']       = order
    ctx['history']     = history
    ctx['show_nav']    = True
    ctx['active_page'] = 'products'
    return render(request, 'store/order_detail.html', ctx)


