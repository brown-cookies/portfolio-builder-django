from django.db import models


class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('free', 'Free Plan'),
        ('basic', 'Basic Plan'),
    ]
    """PayPal Subscription Plans (e.g., Basic, Premium, etc.)"""
    paypal_plan_id = models.CharField(max_length=255, unique=True)
    paypal_plan_metadata = models.JSONField(default=dict) 
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPES, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    interval = models.CharField(max_length=50, choices=[("monthly", "Monthly"), ("yearly", "Yearly")])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Subscription(models.Model):
    """Tracks user subscriptions linked to PayPal"""
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    subscription_id = models.CharField(max_length=255, unique=True)
    subscription_metadata = models.JSONField(default=dict)
    status = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Transaction(models.Model):
    """Records PayPal payments for subscriptions"""
    subscription = models.ForeignKey(Subscription   , on_delete=models.CASCADE, related_name="transactions")
    transaction_id = models.CharField(max_length=255, unique=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=50)
    payment_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class WebhookEvent(models.Model):
    """Stores PayPal webhook events for tracking"""
    user = models.ForeignKey('account.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="webhook_events")  # Link to user if available
    event_id = models.CharField(max_length=255, unique=True)  # PayPal Webhook Event ID
    event_type = models.CharField(max_length=255)  # e.g., PAYMENT.SALE.COMPLETED
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="webhook_events")  # Related subscription if applicable
    event_data = models.JSONField()  # Store full webhook data
    received_at = models.DateTimeField(auto_now_add=True)