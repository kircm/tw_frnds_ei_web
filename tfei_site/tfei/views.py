from django.http import HttpResponse
from django.shortcuts import render
from twython import Twython
from .config_auth import APP_KEY
from .config_auth import APP_SECRET
from django.views.generic.base import RedirectView
from django.urls.base import reverse

oauth_store = {}


def index(request):
    context = {}

    return render(request, 'tfei/index.html', context)


def main_v(request):
    context = {}

    return render(request, 'tfei/main.html', context)


class TwAuthenticateRedirectView(RedirectView):

    callback_url = ""  # To be set from a request object

    def get(self, request, *args, **kwargs):
        self.callback_url = request.build_absolute_uri(reverse('tw_auth_callback'))

        print("---------")
        print("---------")
        print(f"callback_url: {self.callback_url}")
        print("---------")
        print("---------")

        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)
        auth = twitter.get_authentication_tokens(callback_url=self.callback_url, force_login=True)

        oauth_token = auth['oauth_token']
        oauth_token_secret = auth['oauth_token_secret']
        oauth_store[oauth_token] = oauth_token_secret
        auth_url = auth['auth_url']

        return auth_url


def tw_auth_callback(request):
    if request.method == 'POST':
        oauth_token = request.POST['oauth_token']
        oauth_verifier = request.POST['oauth_verifier']
        oauth_denied = request.POST.get('denied', False)
    elif request.method == 'GET':
        oauth_token = request.GET['oauth_token']
        oauth_verifier = request.GET['oauth_verifier']
        oauth_denied = request.GET.get('denied', False)
    else:
        return HttpResponse('Invalid method!')

    if oauth_denied:
        context = {'error_message': "the OAuth request was denied by this user"}
        return render(request, 'tfei/auth_nk.html', context)

    if oauth_token not in oauth_store:
        context = {'error_message': "oauth_token not found locally"}
        return render(request, 'tfei/auth_nk.html', context)

    oauth_token_secret = oauth_store[oauth_token]

    twitter = Twython(APP_KEY, APP_SECRET, oauth_token, oauth_token_secret)
    final_oauth_tokens = twitter.get_authorized_tokens(oauth_verifier)

    oauth_final_token = final_oauth_tokens['oauth_token']
    oauth_final_token_secret = final_oauth_tokens['oauth_token_secret']

    context = {'oauth_final_token': oauth_final_token,
               'oauth_final_token_secret': oauth_final_token_secret}

    return render(request, 'tfei/auth_ok.html', context)


def export_v(request):
    context = {}

    return render(request, 'tfei/export.html', context)


def import_v(request):
    context = {}

    return render(request, 'tfei/import.html', context)


def logout_v(request):
    context = {}

    return render(request, 'tfei/logout.html', context)
