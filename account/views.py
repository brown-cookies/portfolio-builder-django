from account.models import User

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def create_user(request):
    
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('firstName', '')
    last_name = request.data.get('lastName', '')
    
    if not username or not email or not password:
        return Response(
            {"error": "Username, email, and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already taken."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already registered."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    
    return Response({
        "message": "User registered successfully",
        "access": access_token,
        "refresh": str(refresh),
        },
        status=status.HTTP_201_CREATED
    ) 

@api_view(['GET'])
def user_info(request):
    user = request.user
    
    user_plan = request.user.plan
    
    print(user_plan)
    
    return Response({
        "id": user.id, 
        "username": user.username, 
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name 
    })
    
@api_view(["POST"])
def validate_token(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

    token = auth_header.split(" ")[1] 

    try:
        access_token = AccessToken(token)
        user_id = access_token["user_id"]
        user = User.objects.filter(id=user_id).first()

        subscription = {}
        
        if user.subscription:
            plan = user.subscription.plan
            subscription['plan'] = {
                'name': plan.name,
                'description': plan.description,
                'plan_type': plan.plan_type,
                'price': float(plan.price),
                'currency': plan.currency,
                'interval': plan.interval,
                'created_at': plan.created_at.isoformat(),
                'updated_at': plan.updated_at.isoformat(),
            }
            subscription['id'] = user.subscription.subscription_id
            subscription['status'] = user.subscription.status

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "valid": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name 
                },
                "subscription": subscription
            },
            status=status.HTTP_200_OK,
        )
    except TokenError:
        return Response({"valid": False}, status=status.HTTP_401_UNAUTHORIZED)