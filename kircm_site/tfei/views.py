from django.urls.base import reverse
from django.views.generic.base import TemplateView, RedirectView
from twython import Twython, TwythonError

from .config_auth import APP_KEY
from .config_auth import APP_SECRET


class IndexView(TemplateView):
    template_name = "tfei/index.html"


class MainView(TemplateView):
    template_name = "tfei/main.html"


class MainMenuView(TemplateView):
    template_name = "tfei/main-menu.html"

    def get_context_data(self, **kwargs):
        context = {'tw_context': self.request.session['tw_context']}
        return context


class ExportView(TemplateView):
    template_name = "tfei/export.html"


class ImportView(TemplateView):
    template_name = "tfei/import.html"


class LogoutView(TemplateView):
    template_name = "tfei/logout.html"


class ErrorView(TemplateView):
    template_name = "tfei/auth-nk.html"

    def get_context_data(self, **kwargs):
        context = {'msg_context': self.request.session['msg_context']}
        return context


class TwAuthenticateRedirectView(RedirectView):
    redirect_url = None

    def get(self, request, *args, **kwargs):
        callback_url = request.build_absolute_uri(reverse('tw_auth_callback'))
        twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)

        try:
            tw_auth = twitter.get_authentication_tokens(callback_url=callback_url, force_login=True)
            if 'oauth_token' not in tw_auth or 'oauth_token_secret' not in tw_auth:
                raise TwythonError(msg="Missing OAuth token and secret")

        except TwythonError as e:
            self.request.session['msg_context'] = {'error_message': f"Problem authenticating app: {e}"}
            self.redirect_url = request.build_absolute_uri(reverse('error_view'))
            return super().get(self, request, *args, **kwargs)

        oauth_token = tw_auth['oauth_token']
        oauth_token_secret = tw_auth['oauth_token_secret']

        # Store the secret token keyed by oauth token for when tw redirects to this app
        self.request.session['temp_oauth_store'] = {oauth_token: oauth_token_secret}

        # set redirect url to tw's returned url for user authentication
        self.redirect_url = tw_auth['auth_url']
        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url


class TwAuthCallbackView(RedirectView):
    absolute_url_builder = None
    redirect_url = None

    def get(self, request, *args, **kwargs):
        self.process_request(request, request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.process_request(request, request.POST)
        return super().post(request, *args, **kwargs)

    def process_request(self, request, req_method):
        self.absolute_url_builder = request.build_absolute_uri
        
        oauth_denied = req_method.get('denied', False)
        if oauth_denied:
            msg = "The OAuth request was denied by this user"
            return self.redirect_to_error_view(msg)

        oauth_token = req_method['oauth_token']
        oauth_verifier = req_method['oauth_verifier']

        if not oauth_token or not oauth_verifier:
            msg = "Problem interacting with Twitter's OAuth's system"
            return self.redirect_to_error_view(msg)

        return self.process_oauth_callback(oauth_token, oauth_verifier)

    def process_oauth_callback(self, oauth_token, oauth_verifier):
        # retrieve the temporary OAuth store from the user's session
        temp_oauth_store = self.request.session['temp_oauth_store']

        if oauth_token not in temp_oauth_store:
            msg = "OAuth token not found locally"
            return self.redirect_to_error_view(msg)

        # We found the token secret in the temp store
        oauth_token_secret = temp_oauth_store[oauth_token]

        try:
            twitter = Twython(APP_KEY, APP_SECRET, oauth_token, oauth_token_secret)
            final_oauth_tokens = twitter.get_authorized_tokens(oauth_verifier)
            oauth_final_token = final_oauth_tokens['oauth_token']
            oauth_final_token_secret = final_oauth_tokens['oauth_token_secret']

            authenticated_twitter = Twython(APP_KEY, APP_SECRET, oauth_final_token, oauth_final_token_secret)
            creds = authenticated_twitter.verify_credentials(skip_status=True,
                                                             include_entities=False,
                                                             include_email=False)
        except TwythonError as e:
            msg = f"Problem authenticating user: {e}"
            return self.redirect_to_error_view(msg)

        # we don't need the temporary OAuth tokens anymore
        del self.request.session['temp_oauth_store']

        self.request.session['tw_context'] = {
            'oauth_final_token': oauth_final_token,
            'oauth_final_token_secret': oauth_final_token_secret,
            'user_screen_name': creds['screen_name']
        }

        self.redirect_url = self.absolute_url_builder(reverse("main_menu"))
        return

    def redirect_to_error_view(self, error_message):
        self.request.session['msg_context'] = {'error_message': error_message}
        self.redirect_url = self.absolute_url_builder(reverse("error_view"))
        return

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url
