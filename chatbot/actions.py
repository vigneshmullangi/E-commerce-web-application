from store.models import Product, ProductPrice, Category
from store.views import _get_cart, _save_cart, _get_customer, _is_logged_in, _cart_context
from store.models import Order, OrderItem, OrderStatusHistory, Customer


def get_total_products():
    count = Product.objects.filter(is_active=True).count()
    return {"total_products": count}


def search_products(query):
    products = Product.objects.filter(name__icontains=query, is_active=True)[:5]
    results = []
    for p in products:
        units = p.prices.filter(is_available=True).order_by('weight_grams')
        unit_info = [
            {"unit_label": u.unit_label, "price": str(u.price)}
            for u in units
        ]
        results.append({
            "id": p.id,
            "name": p.name,
            "category": p.category.name,
            "units": unit_info
        })
    return {"results": results}


def add_to_cart(request, product_name, unit_label=None, quantity=1):
    if not _is_logged_in(request):
        return {"error": "Please log in first to add items to your cart."}

    try:
        product = Product.objects.get(name__icontains=product_name, is_active=True)
    except Product.DoesNotExist:
        return {"error": f"Product '{product_name}' not found"}
    except Product.MultipleObjectsReturned:
        products = Product.objects.filter(name__icontains=product_name, is_active=True)[:5]
        names = ", ".join([p.name for p in products])
        return {"error": f"Multiple products match '{product_name}': {names}. Please specify which one."}

    if unit_label:
        price_obj = ProductPrice.objects.filter(product=product, unit_label=unit_label, is_available=True).first()
    else:
        price_obj = product.prices.filter(is_available=True).order_by('weight_grams').first()

    if not price_obj:
        return {"error": f"No available units for {product.name}"}

    unit_price = float(price_obj.price)
    total = round(unit_price * quantity, 2)
    cart = _get_cart(request)

    merged = False
    for item in cart:
        if item['product_id'] == product.id and item['unit'] == price_obj.unit_label:
            item['qty'] += quantity
            item['total'] = round(item['unit_price'] * item['qty'], 2)
            merged = True
            break

    if not merged:
        cart.append({
            'product_id': product.id,
            'unit': price_obj.unit_label,
            'qty': quantity,
            'unit_price': unit_price,
            'total': total,
        })

    _save_cart(request, cart)

    return {
        "success": True,
        "product": product.name,
        "unit_label": price_obj.unit_label,
        "quantity": quantity
    }


def view_cart(request):
    ctx = _cart_context(request)
    items = [
        {
            "name": item['product'].name,
            "unit": item['unit'],
            "qty": item['qty'],
            "unit_price": str(item['unit_price']),
            "total": str(item['total'])
        }
        for item in ctx['cart_items']
    ]
    return {
        "items": items,
        "subtotal": str(ctx['cart_subtotal']),
        "delivery": str(ctx['cart_delivery']),
        "total": str(ctx['cart_total'])
    }


def place_order(request):
    if not _is_logged_in(request):
        return {"error": "Please log in first to place an order."}

    cart = _get_cart(request)
    if not cart:
        return {"error": "Your cart is empty."}

    customer = _get_customer(request)
    subtotal = sum(c['total'] for c in cart)
    delivery = 50 if subtotal < 500 else 0
    total = subtotal + delivery

    cust_obj, _ = Customer.objects.get_or_create(
        mobile=customer['mobile'],
        defaults={'name': customer['name'], 'address': customer['address']},
    )

    order = Order.objects.create(
        customer=cust_obj,
        subtotal=subtotal,
        delivery_charge=delivery,
        total=total,
    )

    OrderStatusHistory.objects.create(order=order, status='pending', amount=total)

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

    return {"success": True, "order_id": order.pk, "total": str(total)}