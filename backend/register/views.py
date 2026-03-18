import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from django.contrib.auth import views as auth_views
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


from .forms import RegisterForm

User = get_user_model()


def _parse_json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


def _json_form_errors(form):
    errors = {}
    for field, field_errors in form.errors.items():
        errors[field] = [str(e) for e in field_errors]
    return errors


def _user_payload(user):
    return {
        "is_authenticated": True,
        "username": user.get_username(),
        "is_superuser": bool(getattr(user, "is_superuser", False)),
        "is_approved": bool(getattr(user, "is_approved", False)),
        "is_active": bool(getattr(user, "is_active", False)),
    }


@require_GET
@ensure_csrf_cookie
def api_csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})


@require_GET
def api_me(request):
    if request.user.is_authenticated:
        return JsonResponse(_user_payload(request.user))
    return JsonResponse({"is_authenticated": False, "username": None})


@require_POST
@csrf_protect
def api_register(request):
    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    form = RegisterForm(payload)
    if not form.is_valid():
        return JsonResponse(_json_form_errors(form), status=400)

    user = form.save(commit=False)
    user.is_active = False
    user.save()

    message = form.cleaned_data.get("message")
    admin_email = settings.ADMIN_EMAIL #if not settings.DEBUG else "linksiddharthp@gmail.com"
    site_url = settings.SITE_URL

    subject = "New User Registration Pending Approval"
    email_message = f"""
        A new user has registered and is awaiting your approval:
        Username: {user.username}
        Email: {user.email}
        Institution: {getattr(user, "institution", "")}
        Message: {message}

        Please review the registration at your admin dashboard.
        {site_url}/admin/register/customuser/
    """

    send_mail(
        subject,
        email_message,
        "Admin Team <admin@gensurv.de>",
        [admin_email],
        fail_silently=False,
    )

    return JsonResponse({"status": "pending"}, status=201)


@require_POST
@csrf_protect
def api_login(request):
    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({"ok": False, "detail": "Invalid JSON."}, status=400)

    form = AuthenticationForm(request, data=payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": _json_form_errors(form)}, status=400)

    username = form.cleaned_data.get("username")
    password = form.cleaned_data.get("password")
    print("Username: ", username)
    print("Password: ", password)
    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse(
            {"ok": False, "code": "invalid_credentials", "detail": "Invalid username or password."},
            status=400,
        )

    if not user.is_active:
        return JsonResponse(
            {"ok": False, "code": "inactive", "detail": "Your account is inactive."},
            status=403,
        )

    if getattr(user, "is_superuser", False):
        login(request, user)
        return JsonResponse({"ok": True, "user": _user_payload(user)})

    if not getattr(user, "is_approved", False):
        return JsonResponse(
            {"ok": False, "code": "not_approved", "detail": "Your account has not been approved yet."},
            status=403,
        )

    login(request, user)
    return JsonResponse({"ok": True, "user": _user_payload(user)})


@require_POST
@csrf_protect
def api_logout(request):
    logout(request)
    return JsonResponse({"ok": True})

class CustomPasswordResetView(auth_views.PasswordResetView):
    def get_email_context(self, **kwargs):
        user = kwargs.get("user")
        token_generator = kwargs.get("token_generator", default_token_generator)
        context = super().get_email_context(**kwargs)

        context["domain"] = "gensurv.de"
        context["site_name"] = "GenSurv"
        context["protocol"] = "https"
        context["uid"] = urlsafe_base64_encode(force_bytes(user.pk))
        context["token"] = token_generator.make_token(user)

        return context