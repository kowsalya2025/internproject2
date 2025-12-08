# recommendations/recommendation_engine.py
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from django.contrib.auth.models import User
from .models import Product, Rating, Purchase, ProductView

class RecommendationEngine:
    
    def __init__(self):
        self.user_item_matrix = None
        self.similarity_matrix = None
        
    def build_user_item_matrix(self):
        """Build user-item interaction matrix from ratings"""
        ratings = Rating.objects.all().values('user_id', 'product_id', 'score')
        
        if not ratings:
            return pd.DataFrame()
        
        df = pd.DataFrame(ratings)
        
        # Create pivot table: users as rows, products as columns
        self.user_item_matrix = df.pivot_table(
            index='user_id',
            columns='product_id',
            values='score',
            fill_value=0
        )
        
        return self.user_item_matrix
    
    def calculate_similarity(self):
        """Calculate user-user similarity using cosine similarity"""
        if self.user_item_matrix is None or self.user_item_matrix.empty:
            self.build_user_item_matrix()
        
        if self.user_item_matrix.empty:
            return np.array([])
        
        # Calculate cosine similarity between users
        self.similarity_matrix = cosine_similarity(self.user_item_matrix)
        
        return self.similarity_matrix
    
    def get_collaborative_recommendations(self, user_id, n=5):
        """Get recommendations using collaborative filtering"""
        
        self.build_user_item_matrix()
        
        if self.user_item_matrix.empty:
            return self.get_popular_products(n)
        
        # If user has no ratings, return popular items
        if user_id not in self.user_item_matrix.index:
            return self.get_popular_products(n)
        
        self.calculate_similarity()
        
        # Get user's index in matrix
        user_idx = list(self.user_item_matrix.index).index(user_id)
        
        # Get similar users
        user_similarities = self.similarity_matrix[user_idx]
        
        # Get weighted scores for all products
        weighted_scores = np.dot(user_similarities, self.user_item_matrix.values)
        
        # Get user's rated products
        user_ratings = self.user_item_matrix.loc[user_id]
        rated_products = user_ratings[user_ratings > 0].index.tolist()
        
        # Create recommendations excluding already rated products
        product_ids = self.user_item_matrix.columns.tolist()
        recommendations = []
        
        for i, product_id in enumerate(product_ids):
            if product_id not in rated_products:
                recommendations.append({
                    'product_id': product_id,
                    'score': weighted_scores[i]
                })
        
        # Sort by score and return top N
        recommendations = sorted(
            recommendations,
            key=lambda x: x['score'],
            reverse=True
        )[:n]
        
        product_ids = [r['product_id'] for r in recommendations]
        return Product.objects.filter(id__in=product_ids)
    
    def get_content_based_recommendations(self, product_id, n=5):
        """Get similar products based on category and attributes"""
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Product.objects.none()
        
        # Find products in same category
        similar_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product_id)
        
        # Order by rating and return top N
        recommendations = []
        for p in similar_products:
            recommendations.append({
                'product': p,
                'score': p.average_rating()
            })
        
        recommendations = sorted(
            recommendations,
            key=lambda x: x['score'],
            reverse=True
        )[:n]
        
        return [r['product'] for r in recommendations]
    
    def get_popular_products(self, n=5):
        """Get most popular products based on ratings and purchases"""
        products = Product.objects.all()
        
        product_scores = []
        for product in products:
            rating_score = product.average_rating() or 0
            purchase_count = Purchase.objects.filter(product=product).count()
            view_count = ProductView.objects.filter(product=product).count()
            
            # Weighted score
            total_score = (rating_score * 2) + (purchase_count * 1.5) + (view_count * 0.5)
            
            product_scores.append({
                'product': product,
                'score': total_score
            })
        
        product_scores = sorted(
            product_scores,
            key=lambda x: x['score'],
            reverse=True
        )[:n]
        
        return [ps['product'] for ps in product_scores]
    
    def get_hybrid_recommendations(self, user_id, n=5):
        """Combine collaborative and content-based recommendations"""
        
        # Get collaborative recommendations
        collab_recs = list(self.get_collaborative_recommendations(user_id, n))
        
        # If user has purchases, get content-based recommendations
        recent_purchases = Purchase.objects.filter(user_id=user_id).order_by('-purchased_at')[:3]
        
        content_recs = []
        for purchase in recent_purchases:
            content_recs.extend(
                self.get_content_based_recommendations(purchase.product_id, 2)
            )
        
        # Combine and deduplicate
        all_recs = collab_recs + content_recs
        seen = set()
        unique_recs = []
        
        for product in all_recs:
            if product.id not in seen:
                seen.add(product.id)
                unique_recs.append(product)
        
        return unique_recs[:n]
