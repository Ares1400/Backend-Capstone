"""
Helper for creating notifications from anywhere in the codebase, e.g.:

    from apps.notifications.services import notify
    notify(user=order.customer, type=NotificationType.ORDER_UPDATE,
           title="Order accepted", message="Your order #12 was accepted.")
"""

from .models import Notification


def notify(user, type, title, message):
    return Notification.objects.create(user=user, type=type, title=title, message=message)
