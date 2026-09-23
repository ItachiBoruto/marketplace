from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_id = serializers.IntegerField(source='store.id', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    category_emoji = serializers.CharField(source='category.emoji', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'additional_info', 'image',
            'stock', 'keywords', 'is_available',
            'store_name', 'store_id',
            'category_id', 'category_name', 'category_slug', 'category_emoji',
        ]