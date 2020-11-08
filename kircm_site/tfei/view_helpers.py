from django.urls import reverse
from twython import Twython
from twython import TwythonError

from .config_auth import APP_KEY
from .config_auth import APP_SECRET


def authenticate_app(request):
    callback_url = request.build_absolute_uri(reverse('tw_auth_callback'))
    twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)

    try:
        tw_auth = twitter.get_authentication_tokens(callback_url=callback_url, force_login=True)
        if 'oauth_token' not in tw_auth or 'oauth_token_secret' not in tw_auth:
            raise TwythonError(msg="Missing OAuth token and secret")

    except TwythonError as e:
        request.session['msg_context'] = {'error_message': f"Problem authenticating app: {e}"}
        redirect_url = request.build_absolute_uri(reverse('error_view'))
        return redirect_url

    oauth_token = tw_auth['oauth_token']
    oauth_token_secret = tw_auth['oauth_token_secret']
    redirect_url = tw_auth['auth_url']

    # Store the secret token keyed by oauth token for when tw redirects to this app
    request.session['temp_oauth_store'] = {oauth_token: oauth_token_secret}

    return redirect_url


def process_tw_oauth_callback_request(request, req_method):
    oauth_denied = req_method.get('denied', False)
    if oauth_denied:
        msg = "The OAuth request was denied by this user"
        return redirect_to_error_view(request, msg)

    oauth_token = req_method['oauth_token']
    oauth_verifier = req_method['oauth_verifier']

    if not oauth_token or not oauth_verifier:
        msg = "Problem interacting with Twitter's OAuth's system"
        return redirect_to_error_view(request, msg)

    return process_oauth_callback(request, oauth_token, oauth_verifier)


def process_oauth_callback(request, oauth_token, oauth_verifier):
    # retrieve the temporary OAuth store from the user's session
    temp_oauth_store = request.session['temp_oauth_store']

    if oauth_token not in temp_oauth_store:
        msg = "OAuth token not found locally"
        return redirect_to_error_view(request, msg)

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
        return redirect_to_error_view(request, msg)

    # we don't need the temporary OAuth tokens anymore
    del request.session['temp_oauth_store']

    request.session['tw_context'] = {
        'oauth_final_token': oauth_final_token,
        'oauth_final_token_secret': oauth_final_token_secret,
        'user_id': creds['id'],
        'user_screen_name': creds['screen_name'],
        'user_name': creds['name'],
        'user_friends_count': creds['friends_count']
    }

    redirect_url = request.build_absolute_uri(reverse("main_menu"))
    return redirect_url


def redirect_to_error_view(request, error_message):
    request.session['msg_context'] = {'error_message': error_message}
    redirect_url = request.build_absolute_uri(reverse("error_view"))
    return redirect_url
