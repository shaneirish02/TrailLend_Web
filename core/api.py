from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import Notification

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_expo_token(request):
    token = request.data.get('token')
    if not token:
        return Response({"error": "Token missing"}, status=400)

    profile = request.user.profile
    profile.expo_push_token = token
    profile.save()
    return Response({"message": "Token saved successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    user = request.user
    notifications = Notification.objects.filter(recipient=user).order_by('-timestamp')
    return Response([
        {
            "id": n.id,
            "verb": n.verb,
            "description": n.description,
            "timestamp": n.timestamp,
            "read": not n.unread
        }
        for n in notifications
    ])
