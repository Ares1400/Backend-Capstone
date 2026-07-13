"""
Notification views — list the user's own notifications and mark them read.
Not explicitly given a method/endpoint table in the spec (section 4.11
only lists features), so routes follow the same REST conventions as the
rest of the API.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.views import APIView

from apps.core.responses import success_response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/ — the authenticated user's notifications, newest first."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    """PATCH /api/notifications/{id}/read/ — mark a single notification as read."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        notification = get_object_or_404(Notification, id=id, user=request.user)
        notification.is_read = True
        notification.save()
        return success_response(message="Notification marked as read.", data=NotificationSerializer(notification).data)


class MarkAllNotificationsReadView(APIView):
    """PATCH /api/notifications/read-all/ — mark all of the user's notifications as read."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read.")
