from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.signals import notify
from .models import Reservation
from .utils import send_push_notification

@receiver(post_save, sender=Reservation)
def send_reservation_notification(sender, instance, created, **kwargs):
    if not created:
        return

    user = instance.borrower
    item = instance.item.name
    date = instance.start_datetime.strftime("%Y-%m-%d")

    message = f"Your reservation for {item} on {date} is confirmed."

    # Store in in-app notification
    try:
        notify.send(
            sender=instance,
            recipient=user,
            verb="Reservation Confirmed",
            description=message
        )
    except Exception as e:
        print("❌ Notification failed:", e)


    # Send Expo Push Notification
    if hasattr(user, 'profile') and user.profile.expo_push_token:
        send_push_notification(user.profile.expo_push_token, "Reservation Confirmed", message)
