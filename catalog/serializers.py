from rest_framework import serializers

from accounts.models import User

from .models import Category, Product, SellerProduct


class CategorySerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'createdAt', 'updatedAt']


class ProductSerializer(serializers.ModelSerializer):
    imageUrl = serializers.SerializerMethodField()
    categoryId = serializers.CharField(source='category.id', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    condition = serializers.CharField(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'price',
            'stock',
            'brand',
            'condition',
            'category',
            'categoryId',
            'imageUrl',
            'createdAt',
            'updatedAt',
        ]

    def get_imageUrl(self, obj):
        if not obj.image_url:
            return ''

        url = obj.image_url.url
        request = self.context.get('request')
        if request is None:
            return url
        return request.build_absolute_uri(url)


class ProductWriteSerializer(serializers.ModelSerializer):
    categoryId = serializers.CharField(write_only=True)
    imageFile = serializers.ImageField(source='image_url', required=False, allow_null=True, write_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'price',
            'stock',
            'brand',
            'categoryId',
            'imageFile',
            'condition',
        ]

    def _resolve_category(self, category_id: str):
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist as exc:
            raise serializers.ValidationError({'categoryId': 'Selected category does not exist.'}) from exc

    def create(self, validated_data):
        category_id = validated_data.pop('categoryId')
        validated_data['category'] = self._resolve_category(category_id)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        category_id = validated_data.pop('categoryId', None)
        if category_id is not None:
            validated_data['category'] = self._resolve_category(category_id)
        return super().update(instance, validated_data)


class SellerProductSerializer(serializers.ModelSerializer):
    sellerId = serializers.UUIDField(source='seller.id', read_only=True)
    imageUrl = serializers.SerializerMethodField()
    categoryId = serializers.CharField(source='category.id', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = SellerProduct
        fields = [
            'id',
            'sellerId',
            'name',
            'price',
            'stock',
            'brand',
            'condition',
            'category',
            'categoryId',
            'imageUrl',
            'createdAt',
            'updatedAt',
        ]

    def get_imageUrl(self, obj):
        if not obj.image_url:
            return ''

        url = obj.image_url.url
        request = self.context.get('request')
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def create(self, validated_data):
        seller = self.context['seller']
        validated_data['seller'] = seller
        return super().create(validated_data)


class SellerProductWriteSerializer(serializers.ModelSerializer):
    sellerId = serializers.UUIDField(required=False)
    categoryId = serializers.CharField(write_only=True)
    imageFile = serializers.ImageField(source='image_url', required=False, allow_null=True, write_only=True)

    class Meta:
        model = SellerProduct
        fields = [
            'id',
            'sellerId',
            'name',
            'price',
            'stock',
            'brand',
            'categoryId',
            'imageFile',
            'condition',
        ]

    def _resolve_category(self, category_id: str):
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist as exc:
            raise serializers.ValidationError({'categoryId': 'Selected category does not exist.'}) from exc

    def create(self, validated_data):
        seller = validated_data.pop('seller', None)
        seller_id = validated_data.pop('sellerId', None)
        category_id = validated_data.pop('categoryId')

        if seller is None and seller_id is not None:
            seller = User.objects.get(id=seller_id)

        if seller is None:
            request_user = self.context['request'].user
            if request_user.role != 'seller':
                raise serializers.ValidationError({'sellerId': 'sellerId is required for admin or staff users.'})
            seller = request_user

        validated_data['category'] = self._resolve_category(category_id)
        validated_data['seller'] = seller
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('sellerId', None)
        category_id = validated_data.pop('categoryId', None)
        if category_id is not None:
            validated_data['category'] = self._resolve_category(category_id)
        return super().update(instance, validated_data)