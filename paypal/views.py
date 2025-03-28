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
    
    print(f'the user is {user.username}')
    
    if user.subscription and user.subscription.status == "ACTIVE":
        return Response({ "message": "User is already subscribed!" })
    
    if user.subscription and user.subscription.status == "APPROVAL_PENDING":
        link = user.subscription.subscription_metadata['links'][0]['href']
        return Response({ "message": "Subscription already created, waiting for approval!", "link": link  })
    
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    app_url = os.getenv('APP_URL')
    
    if not client_id or not client_secret:
        print("❌ Missing PayPal credentials")
        return Response({"error": "PayPal credentials are not set"}, status=500)

    if not app_url:
        print("❌ Missing APP__FRONTEND_URL")
        return Response({"error": "APP_URL is not set"}, status=500)
    
    print(f'paypal id is {client_id}')
    print(f'paypal secret is {client_secret}')
    
    try:
        credentials = f"{client_id}:{client_secret}".encode("utf-8")
        encoded_credentials = base64.b64encode(credentials).decode("utf-8")

        authorization_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f"Basic {encoded_credentials}"
        }
        authorization_data = 'grant_type=client_credentials'

        auth_response = requests.post(
            'https://api-m.sandbox.paypal.com/v1/oauth2/token',
            headers=authorization_headers,
            data=authorization_data
        )

        if auth_response.status_code != 200:
            print("❌ PayPal Authorization Failed:", auth_response.text)
            return Response({"error": "Failed to get PayPal token", "details": auth_response.text}, status=500)

        authorization_token = auth_response.json().get('access_token')
        print(f'✅ PayPal Token: {authorization_token[:10]}...')

    except Exception as e:
        print("❌ Error in PayPal Authorization:", str(e))
        return Response({"error": "PayPal authorization failed", "details": str(e)}, status=500)
    
    authorization_data = 'grant_type=client_credentials&ignoreCache=true&return_authn_schemes=true&return_client_metadata=true&return_unconsented_scopes=true'
    authorization_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f"Basic {encoded_credentials}"
    }
    
    basic_plan = SubscriptionPlan.objects.filter(plan_type="basic").first()
    
    billing_plan_id = basic_plan.paypal_plan_id
    
    try:
        subscription_data = {
            "plan_id": billing_plan_id,
            "start_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
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
                "return_url": f"https://portfolio-builder-dj-2457a65d65d7.herokuapp.com/paypal/subscribe/basic/success",
                "cancel_url": f"https://portfolio-builder-dj-2457a65d65d7.herokuapp.com/paypal/subscribe/basic/cancel"
            }
        }

        print(f'✅ Sending subscription request to PayPal: {json.dumps(subscription_data, indent=4)}')

        subscription_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {authorization_token}'
        }

        subscription_response = requests.post(
            'https://api-m.sandbox.paypal.com/v1/billing/subscriptions',
            headers=subscription_headers,
            json=subscription_data
        )

        if subscription_response.status_code != 201:
            print("❌ Subscription Creation Failed:", subscription_response.text)
            return Response({"error": "Failed to create subscription", "details": subscription_response.text}, status=500)

        subscription_response_data = subscription_response.json()

        subscription_id = subscription_response_data.get('id')
        subscription_status = subscription_response_data.get('status')
        subscription_approve_link = next(
            (link['href'] for link in subscription_response_data.get('links', []) if link['rel'] == 'approve'), None
        )

        print(f'✅ Subscription Created: ID={subscription_id}, Status={subscription_status}')

        if not subscription_approve_link:
            print("❌ No approval link found in response!")
            return Response({"error": "No approval link found"}, status=500)

    except Exception as e:
        print("❌ Error Creating PayPal Subscription:", str(e))
        return Response({"error": "PayPal subscription creation failed", "details": str(e)}, status=500)
        
    try:
        subscription = Subscription.objects.create(
            user=user,
            plan=basic_plan,
            subscription_id=subscription_id,
            status=subscription_status,
            subscription_metadata=subscription_response_data,
            start_date=datetime.now(timezone.utc)
        )

        subscription.save()
        user.subscription = subscription
        user.save()

    except Exception as e:
        print("❌ Database Save Error:", str(e))
        return Response({"error": "Database save failed", "details": str(e)}, status=500)
    
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