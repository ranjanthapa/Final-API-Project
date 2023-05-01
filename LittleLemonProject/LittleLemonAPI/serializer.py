from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User, Group
from rest_framework.validators import UniqueValidator
from rest_framework.fields import CurrentUserDefault


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=225, validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'groups']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'groups': {
                'read_only': True
            }
        }

    def create(self, validated_data):
        user = User.objects.create(username=validated_data['username'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['title']


class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']


class CartSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ["user", "menuitem", "quantity"]
        read_only_fields = ["user"]


class OrderSerializer(serializers.ModelSerializer):
    order = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['order', 'delivery_crew', 'status', 'total', 'date']


class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer()
    user = UserSerializer(read_only=True)
    total_price = serializers.SerializerMethodField(method_name='total')

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'unit_price', 'quantity', 'total_price']

    def total(self, product: OrderItem):
        return product.unit_price * product.quantity
