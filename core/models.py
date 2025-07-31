# core/models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import datetime
import uuid



class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True)  # NEW
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    course = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    
    priority_score = models.IntegerField(default=1)  # NEW
    on_time_returns = models.IntegerField(default=0)  # NEW
    late_returns = models.IntegerField(default=0)     # NEW
    expo_push_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"ID: {self.user.username} | Name: {self.full_name} | Role: {self.role}"




class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.username} code: {self.code}"

class Item(models.Model):
    item_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    department = models.CharField(default="Society of College in Information Technology and Computing", max_length=150)
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)  # ✅ Added
    fee = models.CharField(max_length=20, default='Free')
    payment_type = models.CharField(max_length=20, choices=[("free", "Free"), ("custom", "Custom")], default="free")
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    availability = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class ItemDateBlock(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    date = models.DateField()
    is_blocked = models.BooleanField(default=False)

    def __str__(self):
        status = "(Blocked)" if self.is_blocked else "(Available)"
        return f"{self.item.name} - {self.date} {status}"



class DamageReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='damage_reports/', blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Report by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"

class Reservation(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    borrower = models.ForeignKey(User, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    signature = models.TextField()  # base64 string
    
    # Reservation status (pending, borrowed, returned, cancelled)
    status = models.CharField(default='pending', max_length=20)
    
    # Feedback fields (NEW)
    feedback = models.TextField(blank=True, null=True)
    feedback_status = models.CharField(
        max_length=20,
        choices=[('on_time', 'On Time'), ('late', 'Late'), ('not_submitted', 'Not Submitted')],
        blank=True,
        null=True
    )
    
    fee = models.CharField(max_length=20, default="Free")

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            today_str = datetime.now().strftime("%Y%m%d")
            unique_suffix = str(uuid.uuid4())[:6]  # random string, first 6 characters
            self.transaction_id = f"T{today_str}-{unique_suffix}"

        if self.item.payment_type == "custom" and self.item.custom_price:
            self.fee = f"₱{self.item.custom_price}"
        else:
            self.fee = "Free"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - {self.item.name} reserved by {self.borrower.username}"
