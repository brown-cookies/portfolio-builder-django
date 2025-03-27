import base64
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import json
import os
import requests

from paypal.models import SubscriptionPlan, Subscription, Transaction

from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response

load_dotenv()

# Create your views here.
@api_view(["POST"])
def subscribe_to_basic_plan(request):
    user = request.user
    
    if user.subscription and user.subscription.status == "ACTIVE":
        return Response({ "message": "User is already subscribed!" })
    
    if user.subscription and user.subscription.status == "APPROVAL_PENDING":
        link = user.subscription.subscription_metadata['links'][0]['href']
        return Response({ "message": "Subscription already created, waiting for approval!", "link": link  })
    
    credentials = f"{os.getenv('PAYPAL_CLIENT_ID')}:{os.getenv('PAYPAL_CLIENT_SECRET')}".encode("utf-8")
    encoded_credentials = base64.b64encode(credentials).decode("utf-8")
    
    authorization_data = 'grant_type=client_credentials&ignoreCache=true&return_authn_schemes=true&return_client_metadata=true&return_unconsented_scopes=true'
    authorization_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f"Basic {encoded_credentials}"
    }
    
    authorization_response = requests.request("POST", 'https://api-m.sandbox.paypal.com/v1/oauth2/token', headers=authorization_headers, data=authorization_data)
    
    authorization_token = authorization_response.json()['access_token']
    
    basic_plan = SubscriptionPlan.objects.filter(plan_type="basic").first()
    
    billing_plan_id = basic_plan.paypal_plan_id
        
    subscription_data = {
        "plan_id": billing_plan_id,
        "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "shipping_amount": {
            "currency_code": "USD",
            "value": int(basic_plan.price)
        },
        "subscriber": {
            "name": {
                "given_name": user.first_name,
                "surname": user.last_name
            },
            "email_address": user.email,
        },
        "application_context": {
            "brand_name": "Portfolio Builder",
            "locale": "en-US",
            "user_action": "SUBSCRIBE_NOW",
            "payment_method": {
                "payer_selected": "PAYPAL",
                "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
            },
        "return_url": f"{os.getenv('APP_URL')}/paypal/subscribe/basic/success",
        "cancel_url": "https://example.com/cancel"
        }
    }
    subscription_headers = {
        'Content-Type': 'application/json',
        'PayPal-Request-Id': '14ff1f7e-b119-407b-b491-9a4e5fd4d91c',
        'Prefer': 'return=representation',
        'Authorization': f'Bearer {authorization_token}'
    }
    
    subscription_response = requests.request("POST", 'https://api-m.sandbox.paypal.com/v1/billing/subscriptions', headers=subscription_headers, data=json.dumps(subscription_data))
    subscription_response_data = subscription_response.json()
    
    subscription_id = subscription_response_data['id']
    subscription_status = subscription_response_data['status']
    subscription_start_time = subscription_response_data['start_time']
    subscription_approve_link = subscription_response_data['links'][0]['href']
    
    subscription = Subscription.objects.create(
        plan=basic_plan,
        subscription_id = subscription_id,
        status=subscription_status,
        subscription_metadata=subscription_response_data,
        start_date=subscription_start_time
    )
    
    subscription.save()
    
    user.subscription = subscription
    
    user.save()
    
    return Response({ "message": "Waiting for approval!", "link": subscription_approve_link })


@api_view(["GET"])
def subscribe_to_basic_plan_on_success(request):
    subscription_id = request.GET.get('subscription_id')
    ba_token = request.GET.get('ba_token')
    token = request.GET.get('token')
    
    credentials = f"{os.getenv('PAYPAL_CLIENT_ID')}:{os.getenv('PAYPAL_CLIENT_SECRET')}".encode("utf-8")
    encoded_credentials = base64.b64encode(credentials).decode("utf-8")
    
    authorization_data = 'grant_type=client_credentials&ignoreCache=true&return_authn_schemes=true&return_client_metadata=true&return_unconsented_scopes=true'
    authorization_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f"Basic {encoded_credentials}"
    }
    
    authorization_response = requests.request("POST", 'https://api-m.sandbox.paypal.com/v1/oauth2/token', headers=authorization_headers, data=authorization_data)
    
    authorization_token = authorization_response.json()['access_token']
    
    payload = {}
    headers = {
    'PayPal-Request-Id': '640379e1-29d2-499c-93b8-1b823380984b',
    'Authorization': f'Bearer {authorization_token}'
    }
    
    response = requests.request("GET", f'https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}', headers=headers, data=payload)
    response_data = response.json()
    
    subscription = Subscription.objects.filter(subscription_id=subscription_id).first()
    subscription.subscription_metadata = response_data
    subscription.status = response_data['status']
    
    subscription.save()
    
    return redirect(f"{os.getenv('APP_FRONTEND_URL')}/dashboard")

@api_view(["GET"])
def subscribe_to_basic_plan_on_error(request):
    pass