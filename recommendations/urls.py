# recommendations/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    
    # User recommendations
    path('recommendations/', views.my_recommendations, name='my_recommendations'),
    
    # Rating
    path('product/<int:product_id>/rate/', views.rate_product, name='rate_product'),
    
    # Cart management
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    
    # Checkout & Payment - Cart
    path('checkout/cart/', views.checkout_cart, name='checkout_cart'),
    path('payment/cart/handler/', views.payment_handler_cart, name='payment_handler_cart'),
    path('purchase/success/all/', views.purchase_success_all, name='purchase_success_all'),
    
    # Checkout & Payment - Single Product
    path('checkout/<int:product_id>/', views.checkout_page, name='checkout_page'),
    path('payment/handler/', views.payment_handler, name='payment_handler'),
    path('purchase/success/<int:product_id>/', views.purchase_success, name='purchase_success'),
    
    # API endpoints
    path('api/recommendations/<int:user_id>/', views.api_recommendations, name='api_recommendations'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),

    # urls.py
    path('wishlist/', views.wishlist_view, name='wishlist'),
path('wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)