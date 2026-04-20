from django.contrib import admin
from django.urls import path
from store import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Auth ──
    path('signup/',  views.signup_view,  name='signup'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),

    # ── Main pages ──
    path('',          views.home_view,     name='home'),
    path('products/', views.products_view, name='products'),
    path('about/',    views.about_view,    name='about'),

    # ── Cart ──
    path('cart/add/',    views.cart_add,    name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/get/',    views.cart_get,    name='cart_get'),

    # ── Order ──
    path('order/place/',   views.order_place,   name='order_place'),
    path('order/confirm/', views.order_confirm, name='order_confirm'),

    # ✅ Order Status & History
    path('orders/', views.order_status, name='order_status'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)