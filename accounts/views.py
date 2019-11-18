from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
# Create your views here.
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import FormView

from accounts.forms import CustomUserCreationForm
from .tokens import account_activate_token


class RegisterUser(SuccessMessageMixin, FormView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('index')
    success_message = 'Successfully registered! But activate your account before login!'

    def form_valid(self, form):
        user = form.save(commit=True)

        mail_subject = 'Activate your account. Before login.'
        current_site = get_current_site(self.request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activate_token.make_token(user)
        link_dict = {'url': reverse('activate', kwargs={'uidb64': uid, 'token': token})}
        link = f"http://{get_current_site(self.request).domain}{link_dict.get('url')}"

        message = render_to_string('accounts/activate_account.html', {
            'user': user, 'domain': current_site.domain,
            'uid': uid, 'token': token
        })
        email = send_mail(mail_subject, message, settings.EMAIL_HOST_USER, (user.email,),
                          fail_silently=True)
        print('success\n', link) if email else print('something wrong!')
        return super().form_valid(form)


class LoginUserView(SuccessMessageMixin, LoginView):
    template_name = 'accounts/login.html'
    form_class = AuthenticationForm
    success_message = 'You are successfully logged on system! '


class ActivateView(View):

    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, TypeError, ValueError, OverflowError):
            user = None
        if user is not None and account_activate_token.check_token(user=user, token=token):
            user.is_active = True
            user.save()
            login(request=request, user=user)
            messages.add_message(request, messages.INFO, 'You are successfully activated your account')
            return redirect('index')
        else:
            return HttpResponse('The link is invalid sorry!')
