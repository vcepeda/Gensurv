from django.shortcuts import render,redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate,get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site

User = get_user_model()

def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Make the user inactive until admin approval
            user.save()

            # Send email to admin for approval
            message = form.cleaned_data.get('message')
            admin_email = settings.ADMIN_EMAIL #in settings.py
            site_url = settings.SITE_URL #in settings.py

            # Get the current site to include in the email

            subject = "New User Registration Pending Approval"
            email_message = f"""
            A new user has registered and is awaiting your approval:
            Username: {user.username}
            Email: {user.email}
            Institution: {user.institution}
            Message: {message}

            Please review the registration at your admin dashboard.
            {site_url}/admin/register/customuser/

            """

            send_mail(
                subject,
                email_message,
                'Admin Team <admin@gensurv.de>',  # Custom name and email in 'From'
                [admin_email],
                fail_silently=False,
            )# real from email: #settings.DEFAULT_FROM_EMAIL,


            return render(response, 'register/registration_pending.html')
    else:
        form = RegisterForm()
    return render(response, "register/register.html", {"form": form})


##my additional part
def login_viewold(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})

from django.contrib.auth.models import AnonymousUser

def login_viewprev(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_active:
                # Check if the user is an instance of CustomUser
                if hasattr(user, 'is_approved'):
                    if user.is_approved:
                        login(request, user)
                        return redirect('home')  # Redirect to the homepage or any other page
                    else:
                        form.add_error(None, "Your account has not been approved yet.")
                else:
                    # If it's not a CustomUser, proceed without checking for is_approved
                    login(request, user)
                    return redirect('home')  # Redirect for regular users like admin
            else:
                form.add_error(None, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_active:
                # Check if the user is a superuser (admin)
                if user.is_superuser:
                    # Bypass is_approved check for superusers
                    login(request, user)
                    return redirect('home')  # Redirect to the homepage or any other page
                
                # For non-superusers, check if the user is approved
                if getattr(user, 'is_approved', False):
                    login(request, user)
                    return redirect('home')  # Redirect to the homepage or any other page
                else:
                    form.add_error(None, "Your account has not been approved yet.")
            else:
                form.add_error(None, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})




def logout_view(request):
    logout(request)  # Logs out the user    
    return render(request, 'registration/logout.html')  # Render a custom logout confirmation page
    #return redirect('login')  # Redirect to login page after logout

from django.contrib.auth import views as auth_views
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model

class CustomPasswordResetView(auth_views.PasswordResetView):
    def get_email_context(self, **kwargs):
        # Retrieve user details to create the email context
        user = kwargs.get('user')
        token_generator = kwargs.get('token_generator', default_token_generator)
        context = super().get_email_context(**kwargs)
        
        # Override domain and protocol in email context
        context['domain'] = 'gensurv.de'
        context['site_name'] = 'GenSurv'
        context['protocol'] = 'https'  # Assuming your site is running over HTTPS

        # You can also make sure to add the token and UID in the email context
        context['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
        context['token'] = token_generator.make_token(user)

        return context
