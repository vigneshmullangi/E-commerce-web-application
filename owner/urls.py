from django.urls import path
from . import views

app_name = 'owner'

urlpatterns = [
    # ── Owner auth ──
    path('login/',  views.owner_login,  name='login'),
    path('logout/', views.owner_logout, name='logout'),

    # ── Owner dashboard ──
    path('',                              views.dashboard,    name='dashboard'),
    path('order/<int:order_id>/',         views.order_detail, name='order_detail'),
    path('order/<int:order_id>/status/',  views.update_status,name='update_status'),

    # ── Price management ──
    path('prices/',                views.prices_view,   name='prices'),
    path('prices/update/',         views.update_price,  name='update_price'),
    path('prices/toggle-product/', views.toggle_product,name='toggle_product'),

    # ── Delivery boy management ──
    path('delivery/add/',                    views.add_delivery_boy,    name='add_delivery_boy'),
    path('delivery/remove/<int:boy_id>/',    views.remove_delivery_boy, name='remove_delivery_boy'),

    # ── Delivery boy portal ──
    path('delivery/login/',                        views.delivery_login,          name='delivery_login'),
    path('delivery/logout/',                       views.delivery_logout,         name='delivery_logout'),
    path('delivery/orders/',                       views.delivery_orders,         name='delivery_orders'),
    path('delivery/orders/<int:order_id>/',        views.delivery_order_detail,   name='delivery_order_detail'),
]