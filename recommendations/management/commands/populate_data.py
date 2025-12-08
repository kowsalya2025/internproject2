# management/commands/populate_data.py
# Create this file structure: recommendations/management/commands/populate_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from recommendations.models import Category, Product, Rating, Purchase, ProductView
import random

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            ('Electronics', 'Electronic devices and gadgets'),
            ('Books', 'Books and e-books'),
            ('Clothing', 'Fashion and apparel'),
            ('Home & Kitchen', 'Home appliances and kitchenware'),
            ('Sports', 'Sports equipment and gear'),
        ]
        
        categories = []
        for name, desc in categories_data:
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc}
            )
            categories.append(cat)
            if created:
                self.stdout.write(f'Created category: {name}')
        
        # Create products
        products_data = [
            ('Laptop Pro 15', 'High-performance laptop', 0, 1299.99),
            ('Wireless Mouse', 'Ergonomic wireless mouse', 0, 29.99),
            ('USB-C Hub', '7-in-1 USB-C adapter', 0, 49.99),
            ('Mechanical Keyboard', 'RGB mechanical keyboard', 0, 129.99),
            ('Python Programming', 'Learn Python from scratch', 1, 39.99),
            ('Data Science Handbook', 'Complete guide to data science', 1, 49.99),
            ('Fiction Novel', 'Bestselling fiction', 1, 19.99),
            ('Cotton T-Shirt', 'Premium cotton t-shirt', 2, 24.99),
            ('Denim Jeans', 'Classic fit jeans', 2, 59.99),
            ('Running Shoes', 'Lightweight running shoes', 2, 89.99),
            ('Blender Pro', 'High-speed blender', 3, 79.99),
            ('Coffee Maker', 'Programmable coffee maker', 3, 69.99),
            ('Cookware Set', '10-piece cookware set', 3, 149.99),
            ('Yoga Mat', 'Non-slip yoga mat', 4, 29.99),
            ('Dumbbells Set', 'Adjustable dumbbells', 4, 199.99),
            ('Tennis Racket', 'Professional tennis racket', 4, 129.99),
        ]
        
        products = []
        for name, desc, cat_idx, price in products_data:
            prod, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'category': categories[cat_idx],
                    'price': price
                }
            )
            products.append(prod)
            if created:
                self.stdout.write(f'Created product: {name}')
        
        # Create users
        users = []
        for i in range(1, 11):
            username = f'user{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'User{i}',
                    'last_name': 'Test'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            users.append(user)
        
        # Create ratings
        for user in users:
            # Each user rates 3-7 random products
            num_ratings = random.randint(3, 7)
            rated_products = random.sample(products, num_ratings)
            
            for product in rated_products:
                score = random.randint(3, 5)
                Rating.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={'score': score}
                )
        
        self.stdout.write('Creating ratings...')
        
        # Create purchases
        for user in users:
            num_purchases = random.randint(1, 4)
            purchased_products = random.sample(products, num_purchases)
            
            for product in purchased_products:
                Purchase.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={'quantity': random.randint(1, 3)}
                )
        
        self.stdout.write('Creating purchases...')
        
        # Create product views
        for user in users:
            num_views = random.randint(5, 15)
            viewed_products = random.choices(products, k=num_views)
            
            for product in viewed_products:
                ProductView.objects.create(user=user, product=product)
        
        self.stdout.write('Creating product views...')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))