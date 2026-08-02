from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsCustomer
from apps.core.responses import success_response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    @swagger_auto_schema(
        operation_description="View the current customer's cart.",
        responses={200: CartSerializer}
    )
    def get(self, request):
        cart = get_or_create_cart(request.user)
        return success_response(data=CartSerializer(cart).data)

    @swagger_auto_schema(
        operation_description="Add a food item to the cart.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["food_item", "quantity"],
            properties={
                "food_item": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the food item"),
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, description="Quantity to add"),
            }
        ),
        responses={201: CartSerializer}
    )
    def post(self, request):
        cart = get_or_create_cart(request.user)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        food_item = serializer.validated_data["food_item"]
        quantity = serializer.validated_data["quantity"]

        item, created = CartItem.objects.get_or_create(
            cart=cart, food_item=food_item, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

        return success_response(
            message="Item added to cart.",
            data=CartSerializer(cart).data,
            status=status.HTTP_201_CREATED,
        )


class CartItemDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def get_item(self, request, id):
        return get_object_or_404(CartItem, id=id, cart__user=request.user)

    @swagger_auto_schema(
        operation_description="Update the quantity of a cart item.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["quantity"],
            properties={
                "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, description="New quantity"),
            }
        )
    )
    def patch(self, request, id):
        item = self.get_item(request, id)
        quantity = request.data.get("quantity")
        if quantity is None or int(quantity) <= 0:
            return Response(
                {"success": False, "message": "Quantity must be greater than 0."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item.quantity = int(quantity)
        item.save()
        return success_response(
            message="Cart item updated.",
            data=CartSerializer(item.cart).data
        )

    @swagger_auto_schema(
        operation_description="Remove a cart item."
    )
    def delete(self, request, id):
        item = self.get_item(request, id)
        cart = item.cart
        item.delete()
        return success_response(
            message="Item removed from cart.",
            data=CartSerializer(cart).data
        )