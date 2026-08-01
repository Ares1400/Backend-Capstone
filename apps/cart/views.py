from django.shortcuts import get_object_or_404
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

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CartView(APIView):
    """GET /api/cart/ — view current cart. POST /api/cart/ — add an item."""

    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    @swagger_auto_schema(
        request_body=CartItemSerializer,
        operation_description="Add a food item to the cart. If the item already exists, quantity is increased."
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

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='New quantity')
            }
        ),
        operation_description="Update the quantity of a cart item."
    )

    def get_item(self, request, id):
        return get_object_or_404(CartItem, id=id, cart__user=request.user)

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
        return success_response(message="Cart item updated.", data=CartSerializer(item.cart).data)

    def delete(self, request, id):
        item = self.get_item(request, id)
        cart = item.cart
        item.delete()
        return success_response(message="Item removed from cart.", data=CartSerializer(cart).data)
