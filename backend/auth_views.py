try:
    from rest_framework.decorators import api_view, permission_classes  # type: ignore
    from rest_framework.permissions import IsAuthenticated  # type: ignore
    from rest_framework.response import Response  # type: ignore
    from rest_framework_simplejwt.views import TokenObtainPairView  # type: ignore
except Exception:
    # Minimal fallbacks for environments without DRF / simplejwt (linters, CI, or lightweight runtimes)
    def api_view(methods):
        def decorator(func):
            return func
        return decorator

    def permission_classes(classes):
        def decorator(func):
            return func
        return decorator

    class IsAuthenticated:
        pass

    class TokenObtainPairView:
        serializer_class = None

    # Use Django's JsonResponse as a simple Response fallback
    from django.http import JsonResponse as Response

from .auth_serializers import EmailOrUsernameTokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


class EmailOrUsernameTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
    })


@csrf_exempt
def lookup_user_by_email(request):
    # POST with JSON {"email": "user@example.com"}
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
        email = payload.get('email')
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    if not email:
        return JsonResponse({'error': 'missing email'}, status=400)

    User = get_user_model()
    try:
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return JsonResponse({'error': 'not found'}, status=404)
        # return username (staff ID) — used for recovery
        return JsonResponse({'username': user.username, 'is_active': user.is_active})
    except Exception:
        return JsonResponse({'error': 'server error'}, status=500)


@csrf_exempt
def set_initial_password(request):
    # POST { "username": "STAFFID", "email": "user@example.com", "password": "newpass" }
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    username = payload.get('username')
    email = (payload.get('email') or '').strip()
    password = payload.get('password')

    if not username or not email or not password:
        return JsonResponse({'error': 'missing fields'}, status=400)

    User = get_user_model()
    try:
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return JsonResponse({'error': 'user not found'}, status=404)
        # require email to match for extra verification (compare trimmed, case-insensitive)
        stored_email = (user.email or '').strip()
        if stored_email:
            if stored_email.lower() != email.lower():
                return JsonResponse({'error': 'email mismatch'}, status=403)
        else:
            # no email on file — accept and store the supplied email
            user.email = email
        # only allow setting password if account has no usable password
        if user.has_usable_password():
            return JsonResponse({'error': 'password already set'}, status=400)
        user.set_password(password)
        user.save()
        return JsonResponse({'ok': True}, status=201)
    except Exception:
        return JsonResponse({'error': 'server error'}, status=500)
