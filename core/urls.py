from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .api import save_expo_token, get_notifications
from .views import save_push_token
from .views import user_notifications
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    # ----------------- Web Pages -----------------
    path('', views.login_page, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Item Management
    path('items/', views.item_list, name='item_list'),
    path('item-list/', views.item_list_page),  # optional duplicate, can be removed
    path('items/create/', views.create_item_page, name='create_item'),
    path('items/view/<int:pk>/', views.view_item, name='view_item'),
    path('items/<int:pk>/edit/', views.view_item, name='edit_item'),  # mapped to same view
    path('items/<int:pk>/delete/', views.delete_item, name='delete_item'),
    path('items/save-blocked-date/', views.save_blocked_date, name='save_blocked_date'),

    # Calendar Modal
    path('calendar-modal/', views.calendar_modal, name='calendar_modal'),

    # Reservations
    path('reservation_verification/', views.reservation_verification, name='reservation_verification'),
    path('history-logs/', views.history_logs, name='history_logs'),

    # Damage Reports
    path('user-feedback/', views.damage_report, name='damage_report'),
    path('damage-reports/', views.damage_reports, name='damage_reports'),

    # ----------------- Authentication -----------------
    path('logout/', views.logout_user, name='logout'),
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('forgot-password/verify-code/', views.verify_code_page, name='verify_code'),
    path('forgot-password/set-new-password/', views.set_new_password_page, name='set_new_password'),
    path('change_password/', views.change_password, name='change_password'),

    # Optional: Django's built-in password change (not needed if using your custom one)
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='change_password.html',
        success_url='/dashboard/'
    ), name='change_password_django'),

    # ----------------- APIs -----------------
    path('api/users/register/', views.register_user, name='register_user'),
    path('api/users/login/', views.login_user_api, name='login_user_api'),
    path('api/forgot-password/', views.forgot_password_api, name='forgot_password_api'),
    path('api/items/', views.get_items_api, name='get_items_api'),
    path('api/users/request-reset/', views.forgot_password_api),

    # ✅ Reservation API (needed by ReservationSummaryScreen)
    path('api/reserve/', views.create_reservation, name='create_reservation'),
    path('receipt/<str:transaction_id>/', views.transaction_receipt, name='transaction_receipt'),
    path('api/reservations/<int:user_id>/', views.get_user_reservations),

    path('api/save-token/', save_expo_token),
    path('api/notifications/', get_notifications),
    path('save_push_token/', save_push_token),
    path('api/notifications/', user_notifications),
    path('api/notifications/', views.user_notifications),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
