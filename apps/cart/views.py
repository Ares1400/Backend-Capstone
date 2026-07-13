"""
Cart views.

Covers spec section 4.5:
    POST   /api/cart/        -> add item to cart
    GET    /api/cart/        -> view current cart
    DELETE /api/cart/{id}/   -> remove a cart item

Also supports updating quantity via PATCH on the item id, which the spec's
"Update quantity" feature implies but doesn't enumerate as a separate route.
"""

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


class CartView(APIView):
    """GET /api/cart/ — view current cart. POST /api/cart/ — add an item (or bump quantity)."""

    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        return success_response(data=CartSerializer(cart).data)

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
    """PATCH /api/cart/{id}/ — update quantity. DELETE /api/cart/{id}/ — remove item."""

    permission_classes = [permissions.IsAuthenticated, IsCustomer]

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
