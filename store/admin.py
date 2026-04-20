from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from .models import UserProfile, Category, Product, ProductPrice, Order, OrderItem, OrderStatusHistory


# ─── Product Resource (Import/Export) ────────
class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='name')
    )

    # 👉 ADD THESE FIELDS
    unit_label = fields.Field(column_name='unit_label')
    weight_grams = fields.Field(column_name='weight_grams')
    price = fields.Field(column_name='price')
    is_available = fields.Field(column_name='is_available')

    class Meta:
        model = Product
        fields = (
            'id',
            'category',
            'name',
            'description',
            'image_file',
            'is_active',
            'created_at',

            # 👉 INCLUDE THESE
            'unit_label',
            'weight_grams',
            'price',
            'is_available',
        )
        export_order = fields
        import_id_fields = ['name']

    def after_import_row(self, row, row_result, **kwargs):
        if row_result.import_type in ('new', 'update') and row.get('unit_label'):
            product = Product.objects.get(pk=row_result.object_id)

            ProductPrice.objects.update_or_create(
                product=product,
                unit_label=row['unit_label'],
                defaults={
                    'weight_grams': row.get('weight_grams') or 0,
                    'price': row.get('price') or 0,
                    'is_available': str(row.get('is_available')).lower() == 'true',
                }
            )

# ─── Category ────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'product_count')
    ordering     = ('order', 'name')


# ─── Product Price (inline for Product) ──────
class ProductPriceInline(admin.TabularInline):
    model  = ProductPrice
    extra  = 1
    fields = ('unit_label', 'weight_grams', 'price', 'is_available')


# ─── Product ─────────────────────────────────
@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]

    list_display  = ('name', 'category', 'is_active', 'created_at')
    list_filter   = ('category', 'is_active')
    search_fields = ('name',)
    ordering      = ('category', 'name')
    inlines       = [ProductPriceInline]


# ─── Order ───────────────────────────────────
class OrderItemInline(admin.TabularInline):
    model           = OrderItem
    extra           = 0
    readonly_fields = ('product', 'unit_label', 'unit_price', 'quantity', 'line_total')
    can_delete      = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display       = ('pk', 'user', 'subtotal', 'delivery_charge', 'total', 'status', 'created_at')
    list_display_links = ('user',)
    list_filter        = ('status', 'created_at')
    search_fields      = ('user__email', 'user__first_name', 'user',)
    inlines            = [OrderItemInline]
    readonly_fields    = ('subtotal', 'delivery_charge', 'total', 'created_at', 'updated_at')
    fields             = ('user', 'status', 'subtotal', 'delivery_charge', 'total', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            super().save_model(request, obj, form, change)
            OrderStatusHistory.objects.create(
                order=obj,
                status=obj.status,
                amount=obj.total
            )
        else:
            super().save_model(request, obj, form, change)


# ─── Order Status History ─────────────────────
@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display    = ('order', 'status', 'amount', 'changed_at')
    list_filter     = ('status', 'changed_at')
    readonly_fields = ('order', 'status', 'amount', 'changed_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ─── UserProfile ──────────────────────────────
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'phone')

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'