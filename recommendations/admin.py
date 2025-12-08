from django.contrib import admin
from .models import Category, Product, Rating, ProductView, Purchase

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)
    fields = ('name', 'category', 'price', 'image', 'created_at') 


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('user__username', 'product__name')


@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'viewed_at')
    search_fields = ('user__username', 'product__name')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'purchased_at')
    search_fields = ('user__username', 'product__name')


