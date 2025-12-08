# recommendations/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Product, Rating, ProductView, Purchase, Category
from .recommendation_engine import RecommendationEngine
from django.contrib.auth.models import User

# recommendations/views.py
from django.shortcuts import render
from .models import Product, Cart, CartItem

def home(request):
    products = Product.objects.all()

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_count = cart_items.count()
    else:
        cart_items = []
        cart_count = 0

    context = {
        'products': products,
        'cart_items': cart_items,
        'cart_count': cart_count
    }
    return render(request, 'recommendations/home.html', context)



# def home(request):
#     """Homepage with product listing"""
#     products = Product.objects.all()[:12]
#     categories = Category.objects.all()
    
#     context = {
#         'products': products,
#         'categories': categories
#     }
#     return render(request, 'recommendations/home.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Track product view
    if request.user.is_authenticated:
        ProductView.objects.create(user=request.user, product=product)

    # Get user's cart info
    cart_items = []
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            cart_count = cart_items.count()
        except Cart.DoesNotExist:
            cart_items = []
            cart_count = 0

    # Get recommendations
    engine = RecommendationEngine()
    if request.user.is_authenticated:
        recommendations = engine.get_hybrid_recommendations(request.user.id, n=6)
    else:
        recommendations = engine.get_content_based_recommendations(product_id, n=6)

    # Get user's rating if exists
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(user=request.user, product=product)
        except Rating.DoesNotExist:
            pass

    context = {
        'product': product,
        'recommendations': recommendations,
        'user_rating': user_rating,
        'cart_count': cart_count,
    }
    return render(request, 'recommendations/product_detail.html', context)


# def product_detail(request, product_id):
#     """Product detail page with recommendations"""
#     product = get_object_or_404(Product, id=product_id)
    
#     # Track product view
#     if request.user.is_authenticated:
#         ProductView.objects.create(user=request.user, product=product)
    
#     # Get recommendations
#     engine = RecommendationEngine()
    
#     if request.user.is_authenticated:
#         recommendations = engine.get_hybrid_recommendations(request.user.id, n=6)
#     else:
#         recommendations = engine.get_content_based_recommendations(product_id, n=6)
    
#     # Get user's rating if exists
#     user_rating = None
#     if request.user.is_authenticated:
#         try:
#             user_rating = Rating.objects.get(user=request.user, product=product)
#         except Rating.DoesNotExist:
#             pass
    
#     context = {
#         'product': product,
#         'recommendations': recommendations,
#         'user_rating': user_rating
#     }
#     return render(request, 'recommendations/product_detail.html', context)



@login_required
def rate_product(request, product_id):
    """Rate a product"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        score = int(request.POST.get('score', 0))
        
        if 1 <= score <= 5:
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={'score': score}
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Rating saved successfully'
                })
        
        return redirect('product_detail', product_id=product_id)
    
    return JsonResponse({'success': False}, status=400)

@login_required
def purchase_product(request, product_id):
    """Process product purchase and redirect to success page"""
    
    product = get_object_or_404(Product, id=product_id)

    # Allow only POST method to create a purchase
    if request.method == 'POST':
        quantity = request.POST.get('quantity', 1)

        try:
            quantity = int(quantity)
            if quantity < 1:
                quantity = 1
        except ValueError:
            quantity = 1

        # Save the purchase
        Purchase.objects.create(
            user=request.user,
            product=product,
            quantity=quantity
        )

        # Redirect to the success page with product_id
        return redirect('purchase_success', product_id=product.id)

    # If method != POST, send user back to product page
    return redirect('product_detail', product_id=product.id)

@login_required
def purchase_success(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    engine = RecommendationEngine()
    recommendations = engine.get_content_based_recommendations(product_id, n=4)

    return render(request, 'recommendations/purchase_success.html', {
        "product": product,
        "recommendations": recommendations
    })



@login_required
def my_recommendations(request):
    """User's personalized recommendations page"""
    engine = RecommendationEngine()
    
    # Get different types of recommendations
    hybrid_recs = engine.get_hybrid_recommendations(request.user.id, n=8)
    popular_recs = engine.get_popular_products(n=6)
    
    # Get user's purchase history
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchased_at')[:5]
    
    context = {
        'personalized_recommendations': hybrid_recs,
        'popular_products': popular_recs,
        'recent_purchases': purchases
    }
    return render(request, 'recommendations/my_recommendations.html', context)

@require_http_methods(["GET"])
def api_recommendations(request, user_id):
    """API endpoint for getting recommendations"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    engine = RecommendationEngine()
    recommendations = engine.get_hybrid_recommendations(user_id, n=10)
    
    data = {
        'user_id': user_id,
        'recommendations': [
            {
                'id': p.id,
                'name': p.name,
                'price': str(p.price),
                'category': p.category.name,
                'average_rating': p.average_rating()
            }
            for p in recommendations
        ]
    }
    
    return JsonResponse(data)


# Add to recommendations/views.py

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    """Custom logout view"""
    logout(request)
    return redirect('home')


from .models import Category, Product

def category_products(request, category_id):
    category = Category.objects.get(id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, "recommendations/category_products.html", {
        "category": category,
        "products": products
    })


import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Purchase
from django.contrib.auth.decorators import login_required


@login_required
def purchase_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        amount = int(product.price * quantity * 100)  # Razorpay uses paise

        client = razorpay.Client(auth=("YOUR_KEY", "YOUR_SECRET"))

        # 1️⃣ Create RAZORPAY ORDER
        order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })

        # 2️⃣ Send this to the checkout form
        context = {
            "product": product,
            "quantity": quantity,
            "order_id": order["id"],
            "amount": amount,
            "user": request.user
        }
        return render(request, "recommendations/checkout.html", context)

    return redirect('product_detail', product_id=product_id)


from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    FileResponse,
)

@login_required
@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = request.POST
        client = razorpay.Client(auth=("YOUR_KEY", "YOUR_SECRET"))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })

            # Payment success → now create purchase
            product = Product.objects.get(id=data['product_id'])

            Purchase.objects.create(
                user=request.user,
                product=product,
                quantity=data['quantity']
            )

            return redirect("purchase_success", product_id=product.id)

        except:
            return HttpResponse("Payment Failed")

    return HttpResponse("Invalid Request")


import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Product, Purchase
from .recommendation_engine import RecommendationEngine

@login_required
def checkout_page(request, product_id):
    """Create Razorpay order and show checkout page"""
    product = get_object_or_404(Product, id=product_id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount = int(product.price * 100)  # in paise

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return render(request, "recommendations/checkout.html", {
        "product": product,
        "order": order,
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })


@csrf_exempt
@login_required
def payment_handler(request):
    """Verify Razorpay payment and save purchase"""
    if request.method == "POST":
        try:
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            product_id = request.POST.get('product_id')

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Verify signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Signature verified → save purchase
            product = get_object_or_404(Product, id=product_id)
            Purchase.objects.create(user=request.user, product=product, quantity=1)

            return redirect('purchase_success', product_id=product.id)

        except Exception as e:
            print("PAYMENT ERROR:", e)
            return HttpResponse("Payment Failed!", status=400)

    return HttpResponse("Invalid request", status=400)


@login_required
def cart_view(request):
    """Show all items in user's cart"""
    # Assuming you have a Cart model linked to User
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount
    }
    return render(request, 'recommendations/cart.html', context)


# recommendations/views.py
from .models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import razorpay
from django.conf import settings

from django.shortcuts import redirect
from .models import Cart, CartItem, Product

def add_to_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    return redirect('cart_view')  # Make sure 'cart' URL exists



@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()  # Fetch all items for this cart
    total = cart.total_amount() if items else 0

    context = {
        'items': items,
        'total': total,
    }
    return render(request, 'recommendations/cart.html', context)



@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'increment':
            item.quantity += 1
            item.save()
        elif action == 'decrement':
            item.quantity -= 1
            if item.quantity < 1:
                item.delete()
            else:
                item.save()
        elif action == 'remove':
            item.delete()

    return redirect('cart_view')


@login_required
def checkout_cart(request):
    """Create Razorpay order for all cart items"""
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.all()
    if not items:
        return redirect('cart_view')

    total_amount = int(cart.total_amount() * 100)  # in paise
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    order = client.order.create({
        "amount": total_amount,
        "currency": "INR",
        "payment_capture": 1
    })

    context = {
        'cart': cart,
        'items': items,
        'total_amount': total_amount,
        'order': order,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    }
    return render(request, 'recommendations/checkout_cart.html', context)


@login_required
@csrf_exempt
def payment_handler_cart(request):
    """Handle Razorpay payment for cart"""
    if request.method == "POST":
        try:
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Save purchases and clear cart
            cart = get_object_or_404(Cart, user=request.user)
            for item in cart.items.all():
                Purchase.objects.create(
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity
                )
            cart.items.all().delete()

            return redirect('purchase_success_all')

        except Exception as e:
            print("PAYMENT ERROR:", e)
            return HttpResponse("Payment Failed!", status=400)

    return HttpResponse("Invalid request", status=400)


@login_required
def purchase_success_all(request):
    """Show success page after cart checkout"""
    return render(request, 'recommendations/purchase_success_all.html')
