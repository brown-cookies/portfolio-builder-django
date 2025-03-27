from .models import Subscription, SubscriptionPlan, Transaction, WebhookEvent 
from django.contrib import admin

# Register your models here.
admin.site.register(SubscriptionPlan)
admin.site.register(Subscription)
admin.site.register(Transaction)
admin.site.register(WebhookEvent)