import csv
import json
import re
import time
from json import JSONDecodeError
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.urls import reverse
from twython import Twython
from twython import TwythonError

from .config_app import IMP_DATA_DIR
from .config_app import MAX_FRIENDS
from .config_app import UPLOAD_MAX_SIZE
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


def task_for_user_exists(user_id):
    existing_not_finished = Task.get_existing_not_finished_for_user(user_id)
    if existing_not_finished:
        task_id = existing_not_finished.first().id
        msg = f"You have a task that's not finished yet: {task_id}. Please wait for it to finish"
        msg_context = {'error_message': msg}
        return True, msg_context
    return False, None


def resolve_twitter_error(te):
    if te.error_code == 404:
        return "User not found"
    elif te.error_code == 401:
        return "You are not authorized to access this profile. You may be blocked or the account is protected"
    else:
        return te.msg


def resolve_screen_name_for_export(tw_context, screen_name_to_export):
    oauth_token = tw_context['oauth_final_token']
    oauth_token_secret = tw_context['oauth_final_token_secret']
    twitter = Twython(app_key=APP_KEY,
                      app_secret=APP_SECRET,
                      oauth_token=oauth_token,
                      oauth_token_secret=oauth_token_secret)
    try:
        u = twitter.show_user(screen_name=screen_name_to_export)
        # test actual access to the list of friends of the user to export data for
        twitter.get_friends_list(
            screen_name=screen_name_to_export,
            skip_status=True,
            include_user_entities=False,
            count=5)

    except TwythonError as te:
        msg = resolve_twitter_error(te)
        msg = f"{screen_name_to_export}: {msg}"
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


def generate_csv_file_name(user_screen_name):
    curr_timestamp_ns = str(time.time_ns())
    return f"friends_{user_screen_name}_{curr_timestamp_ns}.csv"


def validate_uploaded_csv_file(csv_file_path_name):
    friend_contents = []
    err_msg = "The data in the file is not valid CSV"
    try:
        with open(csv_file_path_name, 'r', newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            for row in reader:
                fr_name = row[0]
                fr_id = int(row[1])
                friend_contents.append((fr_id, fr_name))
    except ValueError:
        return False, err_msg
    except IndexError:
        return False, err_msg

    if len(friend_contents) > MAX_FRIENDS:
        return False, f"We support up to {MAX_FRIENDS} friends. File contains {len(friend_contents)}"

    return True, None


def resolve_path_for_upload(user_screen_name):
    # path includes a subdirectory with the currently authenticated twitter user name, the 'owner' of the data
    path = Path(IMP_DATA_DIR).joinpath(user_screen_name).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def handle_upload_file(file_to_upload, tw_context):
    user_screen_name = tw_context['user_screen_name']
    dest_file_name = generate_csv_file_name(user_screen_name)
    dest_path = resolve_path_for_upload(user_screen_name)
    dest_file_path_name = dest_path.joinpath(dest_file_name)

    if file_to_upload.content_type != "text/csv":
        return False, None, "The file is not a CSV file"
    if file_to_upload.size > UPLOAD_MAX_SIZE:
        return False, None, f"The file is too big - we support a maximum of {MAX_FRIENDS} friends"

    total_read_size = 0
    with open(dest_file_path_name, 'wb+') as destination:
        for chunk in file_to_upload.chunks():
            total_read_size += len(chunk)
            if total_read_size > UPLOAD_MAX_SIZE:
                destination.close()
                return False, None, f"The file is too big. We stopped reading at {total_read_size} bytes"
            destination.write(chunk)

    ok, error_message = validate_uploaded_csv_file(dest_file_path_name)
    if ok:
        return True, dest_file_path_name, None
    else:
        return False, None, error_message


def add_deserialized_output_and_details(task, context_data):
    if task.finished_output:
        try:
            import_output = json.loads(task.finished_output)
            context_data.update({'task_output_deser_context': import_output})
        except JSONDecodeError:
            pass

    if task.finished_details:
        try:
            import_details = json.loads(task.finished_details)
            if not isinstance(import_details, str):
                context_data.update({'task_details_deser_context': import_details})
        except JSONDecodeError:
            pass


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


def retrieve_task_for_user(task_id, user_id):
    msg = "Task does not exist!"
    try:
        task = Task.objects.get(pk=task_id)
    except ObjectDoesNotExist:
        raise Http404(msg)

    # Important - check that the task belongs to current user
    if task.tw_user.tw_id != user_id:
        raise Http404(msg)

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
