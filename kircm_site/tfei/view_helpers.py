import re

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.urls import reverse
from twython import Twython
from twython import TwythonError

from .config_app import MAX_FRIENDS
from .config_auth import APP_KEY
from .config_auth import APP_SECRET
from .models import Task
from .models import TwUser
from .view_decorators import requires_tw_context


class TwContextGetter:
    def __init__(self, req):
        self.request = req

    @requires_tw_context
    def get_context(self):
        # decorator will check for existence and add it to the returned dict
        return {}

    def get_tw_context(self):
        return self.get_context()['tw_context']


def resolve_screen_name_for_export(request):
    if 'tw_user_to_export' in request.POST:
        screen_name_to_export = request.POST['tw_user_to_export']
    else:
        return False, None, "Missing value for 'tw_user_to_export'"

    twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)
    try:
        u = twitter.show_user(screen_name=screen_name_to_export)
    except TwythonError as te:
        msg = f"{screen_name_to_export}: {te.msg}"
        return False, None, msg

    resolved_screen_name = u['screen_name']
    friends_count = u['friends_count']

    if friends_count == 0:
        return False, None, f"Profile {screen_name_to_export} doesn't have any friends to export"
    elif friends_count > MAX_FRIENDS:
        err_msg_for_user = f"Profile {screen_name_to_export} has {friends_count}, we support a maximum of {MAX_FRIENDS}"
        return False, None, err_msg_for_user
    else:
        return True, resolved_screen_name, None


def resolve_file_name_for_import(request):
    # TODO: Handle file uploaded by user
    return True, "test_friends_ei_minimal.csv", None


def create_task_for_user(request, task_type, ok_view, par_exp_screen_name=None, par_imp_file_name=None):
    tw_context = TwContextGetter(request).get_tw_context()
    try:
        Task.create_from_tw_context(task_type, tw_context, par_exp_screen_name, par_imp_file_name)
    except Task.UserTaskExisting:
        msg = "There is already a non-finished task for this user"
        return redirect_to_error_view(request, msg)
    return request.build_absolute_uri(reverse(ok_view))


def retrieve_tasks_for_user(request):
    tw_context = TwContextGetter(request).get_tw_context()
    tasks_for_user = Task.retrieve_user_tasks_with_tw_context(tw_context)
    return tasks_for_user


def retrieve_task(task_id, user_id):
    try:
        task = Task.objects.get(pk=task_id)
    except ObjectDoesNotExist:
        raise Http404("Task does not exist!")

    # Important - check that the task belongs to current user
    if task.tw_user.tw_id != user_id:
        raise Http404("Task does not exist!")

    return task


def validate_user_file_path(user_screen_name, path_file):
    p = re.compile(f".*/{user_screen_name}/.*")
    return p.match(path_file)


def authenticate_app(request):
    callback_url = request.build_absolute_uri(reverse('tw_auth_callback'))
    twitter = Twython(app_key=APP_KEY, app_secret=APP_SECRET)

    try:
        tw_auth = twitter.get_authentication_tokens(callback_url=callback_url, force_login=True)
        if 'oauth_token' not in tw_auth or 'oauth_token_secret' not in tw_auth:
            raise TwythonError(msg="Missing OAuth token and secret")

    except TwythonError as e:
        return redirect_to_auth_error_view(request, f"Problem authenticating app: {e}")

    oauth_token = tw_auth['oauth_token']
    oauth_token_secret = tw_auth['oauth_token_secret']
    redirect_url = tw_auth['auth_url']

    # Store the secret token keyed by oauth token for when tw redirects to this app
    request.session['temp_oauth_store'] = {oauth_token: oauth_token_secret}

    return redirect_url


def process_tw_oauth_callback_request(request, req_method):
    oauth_denied = req_method.get('denied', False)
    if oauth_denied:
        return redirect_to_auth_error_view(request, "The OAuth request was denied by this user")

    oauth_token = req_method['oauth_token']
    oauth_verifier = req_method['oauth_verifier']

    if not oauth_token or not oauth_verifier:
        return redirect_to_auth_error_view(request, "Problem interacting with Twitter's OAuth's system")

    return process_oauth_callback(request, oauth_token, oauth_verifier)


def process_oauth_callback(request, oauth_token, oauth_verifier):
    # retrieve the temporary OAuth store from the user's session
    temp_oauth_store = request.session['temp_oauth_store']

    if oauth_token not in temp_oauth_store:
        return redirect_to_auth_error_view(request, "OAuth token not found locally")

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
        return redirect_to_auth_error_view(request, f"Problem authenticating user: {e}")

    # we don't need the temporary OAuth tokens anymore
    del request.session['temp_oauth_store']

    tw_context = {
        'oauth_final_token': oauth_final_token,
        'oauth_final_token_secret': oauth_final_token_secret,
        'user_id': creds['id'],
        'user_screen_name': creds['screen_name'],
        'user_name': creds['name'],
        'user_friends_count': creds['friends_count']
    }

    # set user info in session and save it in DB
    request.session['tw_context'] = tw_context
    TwUser.create_or_update_from_tw_context(tw_context)

    redirect_url = request.build_absolute_uri(reverse("auth_ok"))
    return redirect_url


def redirect_to_auth_error_view(request, error_message):
    request.session['msg_context'] = {'error_message': error_message}
    redirect_url = request.build_absolute_uri(reverse("auth_error"))
    return redirect_url


def redirect_to_error_view(request, error_message):
    request.session['msg_context'] = {'error_message': error_message}
    redirect_url = request.build_absolute_uri(reverse("error_view"))
    return redirect_url


def logout_user(request):
    if 'tw_context' in request.session:
        tw_id = request.session['tw_context']['user_id']
        TwUser.clear_tw_tokens(tw_id)  # clear tokens from DB
    request.session.flush()  # clear tokens from session
