# Final suggested import cleanup:
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Max
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import ItemSerializer
from .models import ItemDateBlock, Item,Reservation
from django.shortcuts import render
from django.views.decorators.http import require_POST
from datetime import datetime
from django.middleware.csrf import get_token
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
import uuid
from .serializers import ReservationSerializer
from django.db.models import Q
import json
import random
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .utils import send_push_notification
from notifications.models import Notification
from .models import Profile  # has fields: user (FK), full_name, role
from .models import Reservation  # adjust the model name if it's different




from .models import (
    Profile,
    PasswordResetCode,
    Item,
    ItemDateBlock,
    DamageReport,
    Reservation
)
from .forms import ItemForm


# ------------------- AUTHENTICATION -------------------

# Web login
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

# API login
@csrf_exempt
def login_user_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id') or data.get('username')
            password = data.get('password')
            user = authenticate(username=user_id, password=password)
            if user:
                login(request, user)
                csrf_token = get_token(request)
                return JsonResponse({'message': 'Login successful', 'csrfToken': csrf_token}, status=200)
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Register (API)
@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if User.objects.filter(username=data['user_id']).exists():
            return JsonResponse({'message': 'User already exists'}, status=400)

        # Create basic user
        user = User.objects.create_user(
            username=data['user_id'],
            email=data['email'],
            password=data['password']
        )

        # Create the profile with full name and other details
        Profile.objects.create(
            user=user,
            full_name=data['name'],  # 🟡 Store full name here
            course=data['course'],
            mobile=data['mobile'],
            role='student'  # or whatever you want
        )

        return JsonResponse({'message': 'Account created!'}, status=201)

    return JsonResponse({'message': 'Invalid method'}, status=405)

def calculate_priority(user):
    profile = Profile.objects.get(user=user)
    if profile.role == "instructor":
        return 2
    else:
        total = profile.on_time_returns + profile.late_returns
        if total == 0:
            return 1
        accuracy = profile.on_time_returns / total
        return 1 if accuracy >= 0.9 else 0


# Logout
def logout_user(request):
    logout(request)
    return redirect('/')

# ------------------- PASSWORD RESET FLOW -------------------

@csrf_exempt
def forgot_password_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'forgot_password.html', {'error': 'Email not found'})

        code = f"{random.randint(100000, 999999)}"
        expiry = timezone.now() + timezone.timedelta(minutes=10)
        PasswordResetCode.objects.create(user=user, code=code, expires_at=expiry)

        subject = 'Your TrailLend Password Reset Code'
        from_email = 'traillendsystem@gmail.com'
        to = [email]
        text_content = f'Your reset code is {code}. This code will expire in 10 minutes.'
        html_content = f'''
        <div style="font-family: Arial; padding: 10px; border: 1px solid #ccc;">
            <h2 style="color: #007BFF;">TrailLend Password Reset</h2>
            <p>Your reset code is:</p>
            <h3 style="background: #f0f0f0; padding: 10px; display: inline-block;">{code}</h3>
            <p>This code will expire in 10 minutes. Please check your spam or trash folder if you don't see it.</p>
        </div>
        '''
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        return redirect(f'/forgot-password/verify-code/?email={email}')
    return render(request, 'forgot_password.html')

@csrf_exempt
def verify_code_page(request):
    email = request.GET.get('email') or request.POST.get('email')
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            user = User.objects.get(email=email)
            reset = PasswordResetCode.objects.filter(user=user, code=code).last()
            if not reset or reset.is_expired():
                return render(request, 'verify_code.html', {'error': 'Invalid or expired code', 'email': email})
            return redirect(f'/forgot-password/set-new-password/?email={email}&code={code}')
        except User.DoesNotExist:
            return render(request, 'verify_code.html', {'error': 'Invalid email', 'email': email})
    return render(request, 'verify_code.html', {'email': email})

@csrf_exempt
def set_new_password_page(request):
    email = request.GET.get('email') or request.POST.get('email')
    code = request.GET.get('code') or request.POST.get('code')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'set_new_password.html', {'error': 'Passwords do not match', 'email': email, 'code': code})

        try:
            user = User.objects.get(email=email)
            reset = PasswordResetCode.objects.filter(user=user, code=code).last()
            if not reset or reset.is_expired():
                return render(request, 'set_new_password.html', {'error': 'Invalid or expired code', 'email': email, 'code': code})

            user.set_password(password)
            user.save()
            reset.delete()
            return redirect('/')
        except User.DoesNotExist:
            return render(request, 'set_new_password.html', {'error': 'Invalid email', 'email': email, 'code': code})

    return render(request, 'set_new_password.html', {'email': email, 'code': code})

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "❌ Current password is incorrect.")
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, "❌ New password and confirm password do not match.")
            return redirect('change_password')

        if len(new_password) < 6:
            messages.error(request, "❌ Password should be at least 6 characters.")
            return redirect('change_password')

        user.set_password(new_password)
        user.save()

        # 🔒 Keeps user logged in after password change
        update_session_auth_hash(request, user)

        messages.success(request, "✅ New password successfully updated.")
        return redirect('change_password')

    return render(request, 'change_password.html')


def send_verification_email(user_email, code):
    subject = 'Your TrailLend Verification Code'
    message = f'Your verification code is: {code}'
    from_email = 'your_gmail@gmail.com'
    recipient_list = [user_email]
    
    send_mail(subject, message, from_email, recipient_list)

@csrf_exempt
@api_view(['POST'])
def forgot_password_api(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Email not found'}, status=404)

    code = f"{random.randint(100000, 999999)}"
    expiry = timezone.now() + timezone.timedelta(minutes=10)
    PasswordResetCode.objects.create(user=user, code=code, expires_at=expiry)

    send_mail(
        subject='TrailLend Verification Code',
        message=f'Your reset code is: {code}',
        from_email='traillendsystem@gmail.com',
        recipient_list=[email],
        fail_silently=False,
    )

    return Response({'message': 'Code sent to email'}, status=200)
# ------------------- CORE PAGES -------------------
def dashboard(request):
    view = request.GET.get('view', 'overview')
    q = request.GET.get('q', '').strip()

    total_users = User.objects.count()

    instructors_qs = Profile.objects.select_related('user').filter(role='instructor')
    students_qs = Profile.objects.select_related('user').filter(role='student')

    if view == 'instructors' and q:
      instructors_qs = instructors_qs.filter(
          Q(user__username__icontains=q) |
          Q(full_name__icontains=q) |
          Q(user__email__icontains=q)
      )

    if view == 'students' and q:
      students_qs = students_qs.filter(
          Q(user__username__icontains=q) |
          Q(full_name__icontains=q) |
          Q(user__email__icontains=q)
      )

    context = {
        'total_users': total_users,
        'instructor_count': instructors_qs.count(),
        'student_count': students_qs.count(),
        'instructors': instructors_qs.order_by('-user__date_joined'),
        'students': students_qs.order_by('-user__date_joined'),
        'query': q,
    }
    return render(request, 'dashboard.html', context)
def history_logs(request):
    if request.user.is_superuser:
        reservations = Reservation.objects.all().order_by('-start_datetime')
    else:
        reservations = Reservation.objects.filter(borrower=request.user).order_by('-start_datetime')

    return render(request, 'history_logs.html', {'reservations': reservations})


def reservation_verification(request):
    query = request.GET.get('q')

    if query:
        reservations = Reservation.objects.filter(
            Q(borrower__username__icontains=query) |
            Q(borrower__profile__user_id__icontains=query)
        ).select_related('borrower__profile', 'item')
    else:
        reservations = Reservation.objects.all().select_related('borrower__profile', 'item')

    context = {
        'reservations': reservations,
        'query': query,
    }
    return render(request, 'reservation_verification.html', context)


# Borrow button action
def borrow_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Update status
    reservation.status = "BORROWED"
    reservation.save()

    # If AJAX, return JSON (for popup)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "message": "Item successfully borrowed by the user"})

    messages.success(request, "Item successfully borrowed by the user")
    return redirect("reservation_verification")


# Return button action
def return_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    # Update status
    reservation.status = "RETURNED"
    reservation.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "message": "Item successfully returned by the user"})

    messages.success(request, "Item successfully returned by the user")
    return redirect("reservation_verification")


# Show feedback page
def feedback_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, "feedback.html", {"reservation": reservation})


# Submit feedback
def submit_feedback(request, reservation_id):
    if request.method == "POST":
        reservation = get_object_or_404(Reservation, id=reservation_id)
        feedback_text = request.POST.get("feedback", "")
        status = request.POST.get("status", "Not Submitted")

        # Save feedback (you may want to create a Feedback model instead)
        reservation.feedback = feedback_text
        reservation.feedback_status = status
        reservation.save()

        messages.success(request, "Admin successfully submitted feedback")
        return redirect("reservation_verification")

    return JsonResponse({"error": "Invalid request"}, status=400)

def damage_report(request):
    return render(request, 'damage_report.html')

def calendar_modal(request):
    return render(request, 'calendar_modal.html')

def calendar_modal_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)  # get the item object
    blocked_dates_qs = ItemDateBlock.objects.filter(item_id=item_id).values_list('date', flat=True)
    blocked_dates = [d.strftime("%Y-%m-%d") for d in blocked_dates_qs]

    return render(request, 'calendar_modal.html', {
        'item': item,  # pass item to use in the template
        'blocked_dates_json': json.dumps(blocked_dates)
    })

@csrf_exempt
def save_blocked_date(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            date_str = data.get('date')
            is_blocked = data.get('is_blocked', False)

            print("🔍 Data received:", data)

            if not item_id or not date_str:
                return JsonResponse({'error': 'Missing item_id or date'}, status=400)

            # Parse date
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Expected YYYY-MM-DD'}, status=400)

            # Fetch item
            try:
                item = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                return JsonResponse({'error': f'Item with id {item_id} not found'}, status=404)

            # Save or update block (whole-day only)
            blocked_obj, created = ItemDateBlock.objects.update_or_create(
                item=item,
                date=parsed_date,
                defaults={
                    'is_blocked': is_blocked
                }
            )

            action = "blocked" if is_blocked else "unblocked"
            print(f"✅ Date {parsed_date} has been {action} for item {item.name}")

            return JsonResponse({'success': True, 'created': created})

        except Exception as e:
            print("❌ Exception occurred:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# ------------------- ITEM MANAGEMENT -------------------

def generate_item_no():
    last_item = Item.objects.order_by('-id').first()
    if last_item and last_item.item_no.startswith('I'):
        last_no = int(last_item.item_no[1:])
        new_no = last_no + 1
    else:
        new_no = 1
    return f'I{new_no:03d}'

def item_list(request):
    items = Item.objects.all().order_by('-created_at')
    return render(request, 'item_list.html', {'items': items})

def item_list_page(request):
    items = Item.objects.all()
    return render(request, 'item_list.html', {'items': items})

def create_item_page(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)

        if form.is_valid():
            item = form.save(commit=False)
            item.item_no = generate_item_no()
            availability = request.POST.get('availability', 'true')
            item.availability = availability.lower() == 'true'
            item.save()
            messages.success(request, "✅ Successfully created an item.")
            return redirect('item_list')
    else:
        form = ItemForm()
    
    # Show preview of next item_no only if not submitting form
    last_item = Item.objects.order_by('-id').first()
    if last_item and last_item.item_no.startswith('I'):
        last_no = int(last_item.item_no[1:])
        next_preview_no = f'I{last_no + 1:03d}'
    else:
        next_preview_no = 'I001'

    return render(request, 'create_item.html', {
        'form': form,
        'generated_item_no': next_preview_no,
    })

def view_item(request, pk):
    item = get_object_or_404(Item, pk=pk)

    if request.method == 'POST':
        # Only update item fields. Do NOT modify ItemDateBlock here.
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)

            # Handle availability
            availability = request.POST.get('availability', 'true')
            item.availability = availability.lower() == 'true'

            # Optional image change
            if 'image' in request.FILES:
                item.image = request.FILES['image']

            item.save()

            # ❌ DO NOT clear or rewrite blocked dates here.
            # The calendar modal (AJAX) manages ItemDateBlock records.

            messages.success(request, "✅ Changes saved successfully.")
            return redirect('item_list')  # or redirect('view_item', pk=item.pk)
        else:
            messages.error(request, "❌ Form validation failed.")
    else:
        form = ItemForm(instance=item)

    # ✅ Prepare existing blocked dates in ISO format (YYYY-MM-DD)
    blocked_dates = list(
        ItemDateBlock.objects.filter(item=item, is_blocked=True).values_list('date', flat=True)
    )
    blocked_dates_json = json.dumps([
        d.strftime('%Y-%m-%d') for d in blocked_dates
    ])

    return render(request, 'view_item.html', {
        'form': form,
        'item': item,
        'item_id': item.id,
        'blocked_dates_json': blocked_dates_json,
    })


def delete_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('item_list')
    return redirect('view_item', pk=pk)  # fallback if accessed via GET


def reservation_verification(request):
    user_id = request.GET.get('q')  # assuming the input name is 'q' in your form
    reservations = []

    if user_id:
        reservations = Reservation.objects.filter(borrower__username__icontains=user_id)

    return render(request, 'reservation_verification.html', {
        'reservations': reservations,
    })

@api_view(['GET'])
def get_user_reservations(request, user_id):
    reservations = Reservation.objects.filter(borrower__id=user_id).select_related('item')
    serialized = ReservationSerializer(reservations, many=True)
    return Response(serialized.data)
    
def damage_report_view(request):
    reports = DamageReport.objects.all().order_by('-created_at')
    reports_data = [
        {
            'id': r.id,
            'image_url': r.image.url if r.image else '',
            'location': r.location,
            'description': r.description,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
        }
        for r in reports
    ]
    return render(request, 'damage_report.html', {
        'reports': reports,
        'reports_json': json.dumps(reports_data, cls=DjangoJSONEncoder),
    })

def damage_reports(request):
    return render(request, 'damage_report.html')

@api_view(['GET'])
def get_items_api(request):
    items = Item.objects.filter(availability=True).order_by('-created_at')
    serializer = ItemSerializer(items, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reservation(request):
    print("🔵 Incoming reservation request...")
    print("🔵 User Authenticated:", request.user.is_authenticated)
    print("🔵 Method:", request.method)
    print("🔵 Headers:", request.headers)
    print("🔵 Data:", request.data)

    try:

        item = Item.objects.get(id=request.data['item_id'])
        user = request.user
        start = make_aware(parse_datetime(request.data['start_date']))
        end = make_aware(parse_datetime(request.data['end_date']))
        signature = request.data['signature']
        profile = Profile.objects.get(user=user)

        # 🔢 Priority Score
        if profile.role == "instructor":
            user_priority = 2
        else:
            total = profile.on_time_returns + profile.late_returns
            user_priority = 1 if total == 0 or (profile.on_time_returns / total) >= 0.9 else 0

        # 🔎 Conflicting reservations
        existing = Reservation.objects.filter(
            item=item,
            start_datetime__lt=end,
            end_datetime__gt=start
        )

        # 🆔 Generate transaction ID
        today_str = datetime.now().strftime("%Y%m%d")
        unique_suffix = str(uuid.uuid4())[:6]
        transaction_id = f"T{today_str}-{unique_suffix}"

        # ✅ Direct reservation if quantity available
        if existing.count() < item.quantity:
            reservation = Reservation.objects.create(
                item=item,
                borrower=user,
                start_datetime=start,
                end_datetime=end,
                signature=signature,
                status='booked',
                transaction_id=transaction_id
            )

            # ✅ Send push notification if available
            if profile.expo_push_token:
                send_push_notification(
                    expo_push_token=profile.expo_push_token,
                    title='Reservation Confirmed',
                    body=f"{item.name} successfully booked!"
                )

            return Response({
                'message': 'Reservation successful',
                'reservation': {
                    'id': reservation.id,
                    'transaction_id': reservation.transaction_id,
                    'item': item.name,
                    'fee': 'Free' if item.payment_type == 'free' else str(item.custom_price),
                    'start_datetime': start,
                    'end_datetime': end,
                    'status': reservation.status
                }
            }, status=201)

        # 🔄 Check for priority override
        if existing.exists():
            lowest = min(existing, key=lambda r: Profile.objects.get(user=r.borrower).priority_score)
            lowest_priority = Profile.objects.get(user=lowest.borrower).priority_score

            if lowest.borrower == user:
                return Response({'message': 'You already have a reservation in this slot.'}, status=200)

            if user_priority > lowest_priority:
                lowest.delete()
                reservation = Reservation.objects.create(
                    item=item,
                    borrower=user,
                    start_datetime=start,
                    end_datetime=end,
                    signature=signature,
                    status='booked',
                    transaction_id=transaction_id
                )

                if profile.expo_push_token:
                    send_push_notification(
                        expo_push_token=profile.expo_push_token,
                        title='Reservation Confirmed',
                        body=f"{item.name} successfully booked (overridden lower priority)!"
                    )

                return Response({
                    'message': 'Reservation overridden',
                    'reservation': {
                        'id': reservation.id,
                        'transaction_id': reservation.transaction_id,
                        'item': item.name,
                        'fee': 'Free' if item.payment_type == 'free' else str(item.custom_price),
                        'start_datetime': start,
                        'end_datetime': end,
                        'status': reservation.status
                    }
                }, status=200)

        return Response({'message': 'Booking failed. Slot full with higher priority.'}, status=403)

    except Exception as e:
        return Response({'error': str(e)}, status=400)


def transaction_receipt(request, transaction_id):
    reservation = get_object_or_404(Reservation, transaction_id=transaction_id)
    return render(request, 'transaction_receipt.html', {'reservation': reservation})

def save(self, *args, **kwargs):
    if not self.transaction_id:
        today_str = datetime.today().strftime('%Y%m%d')
        suffix = str(uuid.uuid4())[:6]
        self.transaction_id = f"T{today_str}-{suffix}"
    super().save(*args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_push_token(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token is required'}, status=400)

    profile = request.user.profile
    profile.expo_push_token = token
    profile.save()
    return Response({'message': 'Token saved'}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    print("🔎 User making request:", request.user)  # 👈 Add this line
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    data = [
        {
            'id': n.id,
            'verb': n.verb,
            'description': n.description,
            'timestamp': n.timestamp,
        }
        for n in notifications
    ]
    return Response(data)