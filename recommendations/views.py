# recommendations/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.db.models import Q, Avg, Count
from django.conf import settings
import razorpay

from .models import Product, Rating, ProductView, Purchase, Category, Cart, CartItem
from .recommendation_engine import RecommendationEngine
from django.contrib.auth.models import User


def home(request):
    """Enhanced homepage with recommendations and categories"""
    # Get all products or filter by search query
    products = Product.objects.all()
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Get categories for display
    categories = Category.objects.all()
    
    # Get cart information
    cart_count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.items.count()
        
        # Get personalized recommendations
        engine = RecommendationEngine()
        recommended_products = engine.get_hybrid_recommendations(request.user.id, n=4)
    else:
        recommended_products = []
    
    # Get popular/trending products (by rating and purchases)
    trending_products = Product.objects.annotate(
        avg_rating=Avg('rating__score'),
        purchase_count=Count('purchase')
    ).order_by('-avg_rating', '-purchase_count')[:8]
    
    context = {
        'products': products[:12],  # First 12 products
        'trending_products': trending_products,
        'recommended_products': recommended_products,
        'categories': categories,
        'cart_count': cart_count,
        'search_query': query,
    }
    return render(request, 'recommendations/home.html', context)


def product_detail(request, product_id):
    """Enhanced product detail page"""
    product = get_object_or_404(Product, id=product_id)
    
    # Track product view
    if request.user.is_authenticated:
        ProductView.objects.create(user=request.user, product=product)
    
    # Get cart info
    cart_count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.items.count()
    
    # Get recommendations
    engine = RecommendationEngine()
    if request.user.is_authenticated:
        recommendations = engine.get_hybrid_recommendations(request.user.id, n=6)
    else:
        recommendations = engine.get_content_based_recommendations(product_id, n=6)
    
    # Get similar products (same category)
    similar_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product_id)[:4]
    
    # Get user's rating if exists
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(user=request.user, product=product)
        except Rating.DoesNotExist:
            pass
    
    # Get all ratings for this product
    ratings = Rating.objects.filter(product=product).order_by('-created_at')[:5]
    
    context = {
        'product': product,
        'recommendations': recommendations,
        'similar_products': similar_products,
        'user_rating': user_rating,
        'ratings': ratings,
        'cart_count': cart_count,
    }
    return render(request, 'recommendations/product_detail.html', context)


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
                    'message': 'Rating saved successfully',
                    'average_rating': product.average_rating()
                })
        
        return redirect('product_detail', product_id=product_id)
    
    return JsonResponse({'success': False}, status=400)


@login_required
def my_recommendations(request):
    """Enhanced personalized recommendations page"""
    engine = RecommendationEngine()
    
    # Get different types of recommendations
    hybrid_recs = engine.get_hybrid_recommendations(request.user.id, n=12)
    popular_recs = engine.get_popular_products(n=6)
    
    # Get user's statistics
    total_purchases = Purchase.objects.filter(user=request.user).count()
    total_ratings = Rating.objects.filter(user=request.user).count()
    total_views = ProductView.objects.filter(user=request.user).count()
    
    # Get user's purchase history
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchased_at')[:5]
    
    # Get recently viewed products
    recently_viewed = ProductView.objects.filter(
        user=request.user
    ).order_by('-viewed_at').values_list('product', flat=True).distinct()[:6]
    recently_viewed_products = Product.objects.filter(id__in=recently_viewed)
    
    # Get cart count
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_count = cart.items.count()
    
    context = {
        'personalized_recommendations': hybrid_recs,
        'popular_products': popular_recs,
        'recent_purchases': purchases,
        'recently_viewed': recently_viewed_products,
        'total_purchases': total_purchases,
        'total_ratings': total_ratings,
        'total_views': total_views,
        'cart_count': cart_count,
    }
    return render(request, 'recommendations/my_recommendations.html', context)


def category_products(request, category_id):
    """Enhanced category page with filters"""
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    # Price filtering
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('rating__score')).order_by('-avg_rating')
    else:
        products = products.order_by('name')
    
    # Get cart count
    cart_count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.items.count()
    
    categories = Category.objects.all()
    
    context = {
        'category': category,
        'products': products,
        'categories': categories,
        'cart_count': cart_count,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'recommendations/category_products.html', context)


# ========== CART VIEWS ==========

@login_required
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.items.count(),
            'message': 'Product added to cart'
        })
    
    return redirect('cart')


@login_required
def cart_view(request):
    """Enhanced cart view with recommendations"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total = cart.total_amount() if items else 0
    
    # Get recommended products based on cart items
    engine = RecommendationEngine()
    cart_recommendations = []
    if items:
        for item in items[:2]:  # Based on first 2 items
            recs = engine.get_content_based_recommendations(item.product.id, n=3)
            cart_recommendations.extend(recs)
    
    # Remove duplicates and products already in cart
    cart_product_ids = [item.product.id for item in items]
    cart_recommendations = [p for p in cart_recommendations 
                           if p.id not in cart_product_ids][:4]
    
    context = {
        'items': items,
        'total': total,
        'cart_count': items.count(),
        'cart_recommendations': cart_recommendations,
    }
    return render(request, 'recommendations/cart.html', context)


@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'increment':
            item.quantity += 1
            item.save()
        elif action == 'decrement':
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()
        elif action == 'remove':
            item.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = item.cart if item.id else Cart.objects.get(user=request.user)
            return JsonResponse({
                'success': True,
                'total': cart.total_amount(),
                'cart_count': cart.items.count()
            })
    
    return redirect('cart')


# ========== PAYMENT VIEWS ==========

@login_required
def checkout_cart(request):
    """Checkout entire cart"""
    cart = get_object_or_404(Cart, user=request.user)
    items = cart.items.all()
    
    if not items:
        return redirect('cart_view')
    
    total_amount = int(cart.total_amount() * 100)  # Convert to paise
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    order = client.order.create({
        "amount": total_amount,
        "currency": "INR",
        "payment_capture": 1
    })
    
    context = {
        'cart': cart,
        'items': items,
        'total_amount': cart.total_amount(),
        'order': order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'cart_count': items.count(),
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
            
            # Verify signature
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
    """Success page after cart checkout"""
    engine = RecommendationEngine()
    recommendations = engine.get_hybrid_recommendations(request.user.id, n=6)
    
    recent_purchases = Purchase.objects.filter(
        user=request.user
    ).order_by('-purchased_at')[:3]
    
    context = {
        'recommendations': recommendations,
        'recent_purchases': recent_purchases,
        'cart_count': 0,
    }
    return render(request, 'recommendations/purchase_success_all.html', context)


# ========== SINGLE PRODUCT CHECKOUT ==========

@login_required
def checkout_page(request, product_id):
    """Checkout single product"""
    product = get_object_or_404(Product, id=product_id)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount = int(product.price * 100)
    
    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    
    cart_count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.items.count()
    
    context = {
        'product': product,
        'order': order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'cart_count': cart_count,
    }
    return render(request, 'recommendations/checkout.html', context)


@csrf_exempt
@login_required
def payment_handler(request):
    """Handle single product payment"""
    if request.method == "POST":
        try:
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            product_id = request.POST.get('product_id')
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            
            product = get_object_or_404(Product, id=product_id)
            Purchase.objects.create(user=request.user, product=product, quantity=1)
            
            return redirect('purchase_success', product_id=product.id)
            
        except Exception as e:
            print("PAYMENT ERROR:", e)
            return HttpResponse("Payment Failed!", status=400)
    
    return HttpResponse("Invalid request", status=400)


@login_required
def purchase_success(request, product_id):
    """Success page after single product purchase"""
    product = get_object_or_404(Product, id=product_id)
    engine = RecommendationEngine()
    recommendations = engine.get_content_based_recommendations(product_id, n=4)
    
    cart_count = 0
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_count = cart.items.count()
    
    context = {
        'product': product,
        'recommendations': recommendations,
        'cart_count': cart_count,
    }
    return render(request, 'recommendations/purchase_success.html', context)


# ========== API & UTILITY VIEWS ==========

@require_http_methods(["GET"])
def api_recommendations(request, user_id):
    """API endpoint for recommendations"""
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


def logout_view(request):
    """Custom logout"""
    logout(request)
    return redirect('home')
