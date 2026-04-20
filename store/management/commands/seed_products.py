"""
Run:  python manage.py seed_products
Seeds categories + products into the database.
Safe to run multiple times (uses get_or_create).
"""
from django.core.management.base import BaseCommand
from store.models import Category, Product


CATEGORIES = [
    {'name': 'Cooking Oils',  'icon': '🫒', 'order': 1},
    {'name': 'Dry Fruits',    'icon': '🥜', 'order': 2},
    {'name': 'Rice & Grains', 'icon': '🍚', 'order': 3},
    {'name': 'Spices',        'icon': '🧂', 'order': 4},
    {'name': 'Dairy',         'icon': '🥛', 'order': 5},
    {'name': 'Vegetables',    'icon': '🍅', 'order': 6},
]

PRODUCTS = [
    # ── Cooking Oils ──
    {'category': 'Cooking Oils',  'name': 'Sunflower Oil',   'emoji': '🌻', 'price': 120, 'base_unit': 'per L',  'units': '250ml,500ml,1L',       'bg_color': '#fef3c7', 'image_file': 'sunflower_oil.png'},
    {'category': 'Cooking Oils',  'name': 'Olive Oil',       'emoji': '🫒', 'price': 280, 'base_unit': 'per L',  'units': '250ml,500ml,1L',       'bg_color': '#d1fae5', 'image_file': 'olive_oil.png'},
    {'category': 'Cooking Oils',  'name': 'Coconut Oil',     'emoji': '🥥', 'price': 180, 'base_unit': 'per L',  'units': '250ml,500ml,1L',       'bg_color': '#fce7f3', 'image_file': 'coconut_oil.png'},
    {'category': 'Cooking Oils',  'name': 'Groundnut Oil',   'emoji': '🥜', 'price': 150, 'base_unit': 'per L',  'units': '250ml,500ml,1L',       'bg_color': '#fffbeb', 'image_file': 'groundnut_oil.png'},
    # ── Dry Fruits ──
    {'category': 'Dry Fruits',    'name': 'Almonds',         'emoji': '🥜', 'price': 600, 'base_unit': 'per kg', 'units': '50g,100g,250g,500g',   'bg_color': '#fef9c3', 'image_file': 'almonds.png'},
    {'category': 'Dry Fruits',    'name': 'Cashews',         'emoji': '🌰', 'price': 500, 'base_unit': 'per kg', 'units': '50g,100g,250g,500g',   'bg_color': '#ffedd5', 'image_file': 'cashews.png'},
    {'category': 'Dry Fruits',    'name': 'Pistachios',      'emoji': '🪰', 'price': 550, 'base_unit': 'per kg', 'units': '50g,100g,250g',        'bg_color': '#dcfce7', 'image_file': 'pistachios.png'},
    {'category': 'Dry Fruits',    'name': 'Raisins',         'emoji': '🍇', 'price': 350, 'base_unit': 'per kg', 'units': '100g,250g,500g',       'bg_color': '#ede9fe', 'image_file': 'raisins.png'},
    # ── Rice & Grains ──
    {'category': 'Rice & Grains', 'name': 'Basmati Rice',    'emoji': '🍚', 'price': 85,  'base_unit': 'per kg', 'units': '250g,500g,1kg,5kg',    'bg_color': '#fef3c7', 'image_file': 'basmati_rice.png'},
    {'category': 'Rice & Grains', 'name': 'Brown Rice',      'emoji': '🌾', 'price': 110, 'base_unit': 'per kg', 'units': '250g,500g,1kg',        'bg_color': '#fef9c3', 'image_file': 'brown_rice.png'},
    {'category': 'Rice & Grains', 'name': 'Quinoa',          'emoji': '🌿', 'price': 200, 'base_unit': 'per kg', 'units': '250g,500g,1kg',        'bg_color': '#dcfce7', 'image_file': 'quinoa.png'},
    {'category': 'Rice & Grains', 'name': 'Poha',            'emoji': '🍘', 'price': 60,  'base_unit': 'per kg', 'units': '250g,500g,1kg',        'bg_color': '#fff7ed', 'image_file': 'poha.png'},
    # ── Spices ──
    {'category': 'Spices',        'name': 'Turmeric',        'emoji': '🟡', 'price': 180, 'base_unit': 'per kg', 'units': '50g,100g,250g',        'bg_color': '#fef08a', 'image_file': 'turmeric.png'},
    {'category': 'Spices',        'name': 'Chilli Powder',   'emoji': '🌶️','price': 160, 'base_unit': 'per kg', 'units': '50g,100g,250g',        'bg_color': '#fecaca', 'image_file': 'chilli_powder.png'},
    {'category': 'Spices',        'name': 'Garam Masala',    'emoji': '🧂', 'price': 200, 'base_unit': 'per kg', 'units': '50g,100g,250g',        'bg_color': '#d1fae5', 'image_file': 'garam_masala.png'},
    {'category': 'Spices',        'name': 'Cumin Seeds',     'emoji': '🌱', 'price': 140, 'base_unit': 'per kg', 'units': '50g,100g,250g',        'bg_color': '#bbf7d0', 'image_file': 'cumin_seeds.png'},
    # ── Dairy ──
    {'category': 'Dairy',         'name': 'Fresh Milk',      'emoji': '🥛', 'price': 55,  'base_unit': 'per L',  'units': '500ml,1L,2L',          'bg_color': '#f0fdf4', 'image_file': 'fresh_milk.png'},
    {'category': 'Dairy',         'name': 'Paneer',          'emoji': '🧀', 'price': 90,  'base_unit': 'per kg', 'units': '200g,500g,1kg',        'bg_color': '#fef9c3', 'image_file': 'paneer.png'},
    {'category': 'Dairy',         'name': 'Butter',          'emoji': '🧈', 'price': 120, 'base_unit': 'per kg', 'units': '100g,200g,500g',       'bg_color': '#fffbeb', 'image_file': 'butter.png'},
    {'category': 'Dairy',         'name': 'Ghee',            'emoji': '🫙', 'price': 240, 'base_unit': 'per kg', 'units': '200g,500g,1kg',        'bg_color': '#fef3c7', 'image_file': 'ghee.png'},
    # ── Vegetables ──
    {'category': 'Vegetables',    'name': 'Tomatoes',        'emoji': '🍅', 'price': 40,  'base_unit': 'per kg', 'units': '250g,500g,1kg',        'bg_color': '#fee2e2', 'image_file': 'tomatoes.png'},
    {'category': 'Vegetables',    'name': 'Onions',          'emoji': '🧅', 'price': 35,  'base_unit': 'per kg', 'units': '250g,500g,1kg,2kg',    'bg_color': '#fce7f3', 'image_file': 'onions.png'},
    {'category': 'Vegetables',    'name': 'Potatoes',        'emoji': '🥔', 'price': 30,  'base_unit': 'per kg', 'units': '500g,1kg,2kg,5kg',     'bg_color': '#fef9c3', 'image_file': 'potatoes.png'},
    {'category': 'Vegetables',    'name': 'Green Chilli',    'emoji': '🌶️','price': 80,  'base_unit': 'per kg', 'units': '50g,100g,250g',        'bg_color': '#bbf7d0', 'image_file': 'green_chilli.png'},
]


class Command(BaseCommand):
    help = 'Seed categories and products into the database'

    def handle(self, *args, **options):
        # ── Categories ──
        cat_map = {}
        for c in CATEGORIES:
            obj, created = Category.objects.get_or_create(
                name=c['name'],
                defaults={'icon': c['icon'], 'order': c['order']}
            )
            cat_map[c['name']] = obj
            self.stdout.write(f"  Category: {obj.name} ({'created' if created else 'exists'})")

        # ── Products ──
        for p in PRODUCTS:
            obj, created = Product.objects.get_or_create(
                name=p['name'],
                category=cat_map[p['category']],
                defaults={
                    'emoji':      p['emoji'],
                    'price':      p['price'],
                    'base_unit':  p['base_unit'],
                    'units':      p['units'],
                    'bg_color':   p['bg_color'],
                    'image_file': p['image_file'],
                }
            )
            # If product already existed but has no image_file, update it
            if not created and not obj.image_file:
                obj.image_file = p['image_file']
                obj.save()
                self.stdout.write(f"  Product: {obj.name} (updated image)")
            else:
                self.stdout.write(f"  Product: {obj.name} ({'created' if created else 'exists'})")

        self.stdout.write(self.style.SUCCESS('\n✓ Seeding complete!'))
