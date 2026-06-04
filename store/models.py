from django.db import models


# ─────────────────────────────────────────
# Customer  (replaces Django User for ordering)
# ─────────────────────────────────────────
class Customer(models.Model):
    name    = models.CharField(max_length=100)
    mobile  = models.CharField(max_length=10, unique=True)
    address = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.mobile})"


# ─────────────────────────────────────────
# Product Category
# ─────────────────────────────────────────
class Category(models.Model):
    name  = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def product_count(self):
        return self.products.count()
    product_count.short_description = 'Products'


# ─────────────────────────────────────────
# Product
# ─────────────────────────────────────────
class Product(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image_file  = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.name} ({self.category})'

    def get_available_units(self):
        return self.prices.filter(is_available=True).order_by('weight_grams')


# ─────────────────────────────────────────
# Product Price
# ─────────────────────────────────────────
class ProductPrice(models.Model):
    product      = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    unit_label   = models.CharField(max_length=20)
    weight_grams = models.PositiveIntegerField()
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['-weight_grams']
        unique_together = ('product', 'unit_label')

    def __str__(self):
        return f'{self.product.name} - {self.unit_label} @ ₹{self.price}'


# ─────────────────────────────────────────
# Order
# ─────────────────────────────────────────
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped',   'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    # null=True allows migration without breaking existing rows
    customer        = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=6,  decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.customer.name if self.customer else 'Unknown'
        return f'Order #{self.pk} — {name} — ₹{self.total}'


# ─────────────────────────────────────────
# Order Item
# ─────────────────────────────────────────
class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_label = models.CharField(max_length=20)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity   = models.PositiveSmallIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity}x {self.product.name} ({self.unit_label})'


# ─────────────────────────────────────────
# Order Status History
# ─────────────────────────────────────────
class OrderStatusHistory(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status     = models.CharField(max_length=20)
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.order.id} → {self.status}'