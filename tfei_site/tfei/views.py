from django.urls.base import reverse
from django.views.generic.base import TemplateView, RedirectView
from twython import Twython

from .config_auth import APP_KEY
from .config_auth import APP_SECRET

# OAUTH_store should be in session
oauth_store = {}


class IndexView(TemplateView):
    template_name = "tfei/index.html"


class MainView(TemplateView):
    template_name = "tfei/main.html"


class MainMenuView(TemplateView):
    template_name = "tfei/main-menu.html"


class ExportView(TemplateView):
    template_name = "tfei/export.html"


class ImportView(TemplateView):
    template_name = "tfei/import.html"


class LogoutView(TemplateView):
    template_name = "tfei/logout.html"


class ErrorView(TemplateView):
    template_name = "tfei/auth-nk.html"


class TwAuthenticateRedirectView(RedirectView):

    callback_url = ""  # To be set once processing a request object

    def get(self, request, *args, **kwargs):
        self.callback_url = request.build_absolute_uri(reverse('tw_auth_callback'))
        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)
        auth = twitter.get_authentication_tokens(callback_url=self.callback_url, force_login=True)

        oauth_token = auth['oauth_token']
        oauth_token_secret = auth['oauth_token_secret']
        oauth_store[oauth_token] = oauth_token_secret
        auth_url = auth['auth_url']

        return auth_url


class TwAuthCallbackView(RedirectView):

    absolute_url_builder = None
    context = {}
    redirect_url = None

    def get(self, request, *args, **kwargs):
        oauth_token = request.GET['oauth_token']
        oauth_verifier = request.GET['oauth_verifier']
        oauth_denied = request.GET.get('denied', False)
        self.absolute_url_builder = request.build_absolute_uri
        self.process_oauth_callback(oauth_token, oauth_verifier, oauth_denied)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        oauth_token = request.POST['oauth_token']
        oauth_verifier = request.POST['oauth_verifier']
        oauth_denied = request.POST.get('denied', False)
        self.absolute_url_builder = request.build_absolute_uri
        self.process_oauth_callback(oauth_token, oauth_verifier, oauth_denied)
        return super().post(request, *args, **kwargs)

    def process_oauth_callback(self, oauth_token, oauth_verifier, oauth_denied):
        if oauth_denied:
            self.context = {'error_message': "the OAuth request was denied by this user"}
            self.redirect_url = self.absolute_url_builder(reverse("error_view"))
            return

        if oauth_token not in oauth_store:
            self.context = {'error_message': "oauth_token not found locally"}
            self.redirect_url = self.absolute_url_builder(reverse("error_view"))
            return

        oauth_token_secret = oauth_store[oauth_token]

        twitter = Twython(APP_KEY, APP_SECRET, oauth_token, oauth_token_secret)
        final_oauth_tokens = twitter.get_authorized_tokens(oauth_verifier)
        oauth_final_token = final_oauth_tokens['oauth_token']
        oauth_final_token_secret = final_oauth_tokens['oauth_token_secret']

        authenticated_twitter = Twython(APP_KEY, APP_SECRET, oauth_final_token, oauth_final_token_secret)
        creds = authenticated_twitter.verify_credentials(skip_status=True,
                                                         include_entities=False,
                                                         include_email=False)

        self.context = {
            'oauth_final_token': oauth_final_token,
            'oauth_final_token_secret': oauth_final_token_secret,
            'user_screen_name': creds['screen_name']
        }

        self.redirect_url = self.absolute_url_builder(reverse("main_menu"))
        return

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url
