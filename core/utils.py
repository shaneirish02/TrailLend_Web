import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

def send_push_notification(expo_push_token, title, body, data=None):
    """
    Send a push notification via Expo to the specified push token.

    Args:
        expo_push_token (str): The user's Expo push token.
        title (str): Title of the notification.
        body (str): Message body.
        data (dict, optional): Extra data to send to the app (e.g., deep linking).
    """
    payload = {
        "to": expo_push_token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data or {}
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(EXPO_PUSH_URL, json=payload, headers=headers)
        response.raise_for_status()

        print("✅ Push notification sent successfully:")
        print("📤 Payload:", payload)
        print("📥 Response:", response.json())

    except httpx.HTTPStatusError as e:
        print("❌ HTTP error:", e.response.status_code, e.response.text)
    except httpx.RequestError as e:
        print("❌ Request failed:", str(e))
    except Exception as e:
        print("❌ Unknown error while sending push:", str(e))
