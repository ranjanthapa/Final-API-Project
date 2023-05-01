import json
from datetime import datetime
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from .models import MenuItem, Category
from .serializer import *
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveDestroyAPIView, RetrieveAPIView
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.models import User, Group
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .permissions import IsManager, IsAuthorizedGetMethod, IsCustomer, IsDeliveryCrew


class RegisterUser(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"message": 'something went wrong'}, status.HTTP_403_FORBIDDEN)
        serializer.save()
        user = User.objects.get(username=serializer.data['username'])
        token_obj, created = Token.objects.get_or_create(user=user)
        return Response({'result': serializer.data, 'token': str(token_obj)})


class GroupView(ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_permissions(self):
        return [IsManager()]


class MenuItemView(ListAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering = ['price', 'title']
    search_fields = ['title', 'category__title']
    permission_classes = [IsManager | IsAuthorizedGetMethod]


class SingleMenuItemView(RetrieveDestroyAPIView):
    permission_classes = [IsManager | IsAuthorizedGetMethod]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def patch(self, request, pk):
        try:
            menu_item = MenuItem.objects.get(pk=pk)
        except menu_item.DoesNotExist:
            return Response({"error": "menu item not found"}, status.HTTP_404_NOT_FOUND)
        serializers = MenuItemSerializer(menu_item, data=request.data, partial=True)
        if serializers.is_valid():
            serializers.save()
            return Response({'menu-item': serializers.data}, status.HTTP_200_OK)
        return Response({'message': "invalid entry"}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET', 'DELETE'])
@permission_classes([IsManager])
def manager(request):
    username = request.data.get('username')
    if request.method == 'POST':
        if username:
            user = User.objects.filter(username=username).first()
            if user is None:
                return Response({"error": f"No username {user} exists"})
            managers = Group.objects.get(name='Manager')
            if user.groups.filter(name="Manager").exists():
                return Response({"Message": "User exists in the group already"})
            managers.user_set.add(user)
            return Response({"message": f"{user} added to Manager group."})
        else:
            return Response({"error": "Please provide a username."})

    elif request.method == 'GET':
        managers = Group.objects.get(name='Manager')
        users = managers.user_set.all().values_list('username', flat=True)
        return Response({"managers": {'username': list(users)}}, status.HTTP_200_OK)

    elif request.method == "DELETE":
        if not username:
            return Response({"error": "please provide the username"})
        user = User.objects.filter(username=username).first()
        if user is None:
            return Response({"error": f"User named {user} doesn't exists"})
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return Response({"message": "User sucessfully removed from the group"})
    else:
        raise MethodNotAllowed(request.method)


class DeliveryCrewView(APIView):
    username = None
    permission_classes = [IsManager]

    def post(self, request):
        self.username = request.data.get('username')
        if self.username:
            user = User.objects.filter(username=self.username).first()
            if user is None:
                return Response({"Message": "The user doesn't exists"})
            delivery = Group.objects.get(name='Delivery')
            delivery.user_set.add(user)
            return Response({"message": "User added to delivery Group"}, status.HTTP_201_CREATED)

    def get(self, request):
        delivery = Group.objects.get(name='Delivery')
        users = delivery.user_set.all().values_list('username', flat=True)
        return Response({'message': {'username': list(users)}}, status.HTTP_200_OK)

    def delete(self, request):
        self.username = request.data.get("username")
        if self.username:
            user = User.objects.filter(username=self.username).first()
            if user is not None:
                delivery = Group.objects.get(name='Delivery')
                delivery.user_set.remove(user)
                delivery.refresh_from_db()
                return Response({"message": f"{user} successfully removed from the group"})
            return Response({"error": "User not found"})
        return Response({"error": "Enter the User"})


class CartView(ListCreateAPIView, RetrieveDestroyAPIView):
    permission_classes = [IsCustomer]

    def get(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        if cart.exists():
            serializer = CartSerializer(cart, many=True)
            return Response(serializer.data)
        return Response({"message": "No iteam has been added to cart"})

    def post(self, request, *args, **kwargs):
        id = request.data.get("menuitem")
        quantity = request.data.get("quantity")
        menuitem = MenuItem.objects.get(pk=id)
        cart, created = Cart.objects.get_or_create(user=request.user, menuitem=menuitem, quantity=quantity)
        if not created:
            cart.quantity += int(quantity)
            cart.save()
        else:
            cart.quantity = int(quantity)
            cart.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        cart_id = kwargs.get('pk')
        try:
            cart = Cart.objects.get(user=request.user, menuitem=cart_id)
            cart.delete()
            return Response({"message": "Item removed from the cart"})
        except Cart.DoesNotExist:
            return Response({"error": "Cart item does not exist"})


class OrderView(ListCreateAPIView):
    permission_classes = [IsCustomer, IsAuthorizedGetMethod]
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(user=request.user)
        order_serializer = OrderSerializer(order, many=True)
        return Response(order_serializer.data)

    def post(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user)
        cart_serializer = CartSerializer(cart, many=True)

        if not cart_serializer.data:
            return Response({"message:" "the Cart is empty"})

        order = Order()
        order.user = request.user
        order.status = 0
        order.total = sum(Decimal(item['menuitem']['price']) * int(item['quantity']) for item in cart_serializer.data)
        order.date = datetime.now().date()
        order.save()

        for cItem in cart_serializer.data:
            order_item = OrderItem()
            order_item.order = order
            order_item.menuitem_id = cItem['menuitem']['id']
            order_item.quantity = cItem['quantity']
            order_item.unit_price = Decimal(cItem['menuitem']['price'])
            order_item.price = Decimal(cItem['menuitem']['price']) * Decimal(cItem['quantity'])
            order_item.save()

        cart.delete()

        return Response({"Message": "Cart items place in order"})


class AssignOrder(RetrieveAPIView):
    permission_classes = [IsManager]

    def patch(self, request):
        order_id = request.data['order_id']
        user_id = request.data['user_id']
        delivery_grp = Group.objects.filter(name="Delivery").first()
        user = delivery_grp.user_set.filter(id=user_id).first()
        if not user:
            return Response({"message": "User doesn't exist in the group"})
        order = Order.objects.get(pk=order_id)
        if not order.delivery_crew:
            order.delivery_crew = user
            order.save()
            order_serializer = OrderSerializer(order, partial=True)
            return Response(order_serializer.data)
        return Response({"message": "Order already assigned to a delivery crew"})


class UpdateDeliveryStatus(APIView):
    permission_classes = [IsDeliveryCrew]

    def patch(self, request):
        order_id = request.data["order_id"]
        status = request.data["status"]
        order = Order.objects.filter(pk=order_id, delivery_crew=request.user).first()
        if not order:
            return Response({"message:""Something went wrong"})
        order.status = status
        order.save()
        order_serializer = OrderSerializer(order, partial=True)
        return Response(order_serializer.data)
