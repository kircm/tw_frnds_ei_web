from django.urls.base import reverse
from django.views.generic.base import TemplateView, RedirectView
from twython import Twython

from .config_auth import APP_KEY
from .config_auth import APP_SECRET


class IndexView(TemplateView):
    template_name = "tfei/index.html"


class MainView(TemplateView):
    template_name = "tfei/main.html"


class MainMenuView(TemplateView):
    template_name = "tfei/main-menu.html"

    tw_context = {}

    def get(self, request, *args, **kwargs):
        self.tw_context = request.session['tw_context']
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {'tw_context': self.tw_context}
        return context


class ExportView(TemplateView):
    template_name = "tfei/export.html"


class ImportView(TemplateView):
    template_name = "tfei/import.html"


class LogoutView(TemplateView):
    template_name = "tfei/logout.html"


class ErrorView(TemplateView):
    template_name = "tfei/auth-nk.html"


class TwAuthenticateRedirectView(RedirectView):

    temp_oauth_store = {}
    callback_url = None  # To be set once processing a request object

    def get(self, request, *args, **kwargs):
        # Initialize oauth store in user's session
        request.session['temp_oauth_store'] = self.temp_oauth_store
        self.callback_url = request.build_absolute_uri(reverse('tw_auth_callback'))
        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)

        # TODO try catch - TEST Twitter responding error:
        # Callback URL not approved for this client application.
        # Approved callback URLs can be adjusted in your application settings
        auth = twitter.get_authentication_tokens(callback_url=self.callback_url, force_login=True)

        oauth_token = auth['oauth_token']
        oauth_token_secret = auth['oauth_token_secret']
        self.temp_oauth_store[oauth_token] = oauth_token_secret
        auth_url = auth['auth_url']

        return auth_url


class TwAuthCallbackView(RedirectView):

    temp_oauth_store = {}
    absolute_url_builder = None
    redirect_url = None
    tw_context = {}
    msg_context = {}

    def get(self, request, *args, **kwargs):
        self.process_request(request, request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.process_request(request, request.POST)
        return super().post(request, *args, **kwargs)

    def process_request(self, request, req_method):
        # extract temp_oauth_store and tw_context from user's session
        self.temp_oauth_store = request.session['temp_oauth_store']
        # Initialize tw_context in msg_context in session
        request.session['tw_context'] = self.tw_context
        request.session['msg_context'] = self.msg_context

        oauth_token = req_method['oauth_token']
        oauth_verifier = req_method['oauth_verifier']
        oauth_denied = req_method.get('denied', False)
        self.absolute_url_builder = request.build_absolute_uri
        self.process_oauth_callback(oauth_token, oauth_verifier, oauth_denied)
        return

    def process_oauth_callback(self, oauth_token, oauth_verifier, oauth_denied):
        if oauth_denied:
            self.msg_context = {'error_message': "the OAuth request was denied by this user"}
            self.redirect_url = self.absolute_url_builder(reverse("error_view"))
            return

        if oauth_token not in self.temp_oauth_store:
            self.msg_context = {'error_message': "oauth_token not found locally"}
            self.redirect_url = self.absolute_url_builder(reverse("error_view"))
            return

        # retrieve the token secret that had been kept in oauth store before redirecting to tw auth url
        oauth_token_secret = self.temp_oauth_store[oauth_token]

        twitter = Twython(APP_KEY, APP_SECRET, oauth_token, oauth_token_secret)

        # try catch
        final_oauth_tokens = twitter.get_authorized_tokens(oauth_verifier)
        oauth_final_token = final_oauth_tokens['oauth_token']
        oauth_final_token_secret = final_oauth_tokens['oauth_token_secret']

        authenticated_twitter = Twython(APP_KEY, APP_SECRET, oauth_final_token, oauth_final_token_secret)
        creds = authenticated_twitter.verify_credentials(skip_status=True,
                                                         include_entities=False,
                                                         include_email=False)

        # we don't need the temporary OAuth tokens anymore
        del self.temp_oauth_store

        self.tw_context = {
            'oauth_final_token': oauth_final_token,
            'oauth_final_token_secret': oauth_final_token_secret,
            'user_screen_name': creds['screen_name']
        }

        self.redirect_url = self.absolute_url_builder(reverse("main_menu"))
        return

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url
