# recommendations/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/rate/', views.rate_product, name='rate_product'),
    path('product/<int:product_id>/purchase/', views.purchase_product, name='purchase_product'),
    path('purchase-success/<int:product_id>/', views.purchase_success, name='purchase_success'),
    path('my-recommendations/', views.my_recommendations, name='my_recommendations'),
    path('api/recommendations/<int:user_id>/', views.api_recommendations, name='api_recommendations'),
    path('logout/', views.logout_view, name='logout'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    # path("buy/<int:product_id>/", views.buy_product, name="buy_product"),
    
        path('product/<int:product_id>/checkout/', views.checkout_page, name='checkout_page'),

    # Razorpay payment verification handler
    path('payment-handler/', views.payment_handler, name='payment_handler'),

    # Payment success page
    path('purchase-success/<int:product_id>/', views.purchase_success, name='purchase_success'),

    path('cart/', views.cart_view, name='cart'), 
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('cart/payment_handler/', views.payment_handler_cart, name='payment_handler_cart'),
    path('cart/success/', views.purchase_success_all, name='purchase_success_all'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
]