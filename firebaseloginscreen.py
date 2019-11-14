from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, StringProperty
from kivy.event import EventDispatcher
from kivy.network.urlrequest import UrlRequest
from kivy.app import App
from kivy.lang import Builder
from kivy.factory import Factory
import sys
sys.path.append("/".join(x for x in __file__.split("/")[:-1]))
from json import dumps
import os.path
import progressspinner
folder = os.path.dirname(os.path.realpath(__file__))
Builder.load_file(folder + "/kv/themedwidgets.kv")
Builder.load_file(folder + "/kv/signinscreen.kv")
Builder.load_file(folder + "/kv/createaccountscreen.kv")
Builder.load_file(folder + "/kv/welcomescreen.kv")
Builder.load_file(folder + "/kv/loadingpopup.kv")
from welcomescreen import WelcomeScreen
from signinscreen import SignInScreen
from createaccountscreen import CreateAccountScreen


class FirebaseLoginScreen(Screen, EventDispatcher):
    web_api_key = StringProperty()
    refresh_token = ""
    localId = ""
    idToken = ""
    login_success = BooleanProperty(False)
    sign_up_msg = StringProperty()
    sign_in_msg = StringProperty()
    email_exists = BooleanProperty(False)
    email_not_found = BooleanProperty(False)
    debug = False
    popup = Factory.LoadingPopup()
    popup.background = folder + "/transparent_image.png"

    def on_login_success(self, *args):
        print("Logged in successfully", args)

    def on_web_api_key(self, *args):
        self.refresh_token_file = App.get_running_app().user_data_dir + "/refresh_token.txt"
        if self.debug:
            print("Looking for a refresh token in:", self.refresh_token_file)
        if os.path.exists(self.refresh_token_file):
            self.load_saved_account()

    def sign_up(self, email, password):
        if self.debug:
            print("Attempting to create a new account: ", email, password)
        signup_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser?key=" + self.web_api_key
        signup_payload = dumps(
            {"email": email, "password": password, "returnSecureToken": "true"})

        UrlRequest(signup_url, req_body=signup_payload,
                   on_success=self.successful_login,
                   on_failure=self.sign_up_failure,
                   on_error=self.sign_up_error)

    def successful_login(self, urlrequest, log_in_data):
        self.hide_loading_screen()
        self.refresh_token = log_in_data['refreshToken']
        self.localId = log_in_data['localId']
        self.idToken = log_in_data['idToken']
        self.save_refresh_token(self.refresh_token)
        self.login_success = True
        if self.debug:
            print("Successfully logged in a user: ", log_in_data)

    def sign_up_failure(self, urlrequest, failure_data):
        self.hide_loading_screen()
        self.email_exists = False
        print(failure_data)
        msg = failure_data['error']['message'].replace("_", " ").capitalize()

        if msg == self.sign_up_msg:
            msg = " " + msg + " "
        self.sign_up_msg = msg
        if msg == "Email exists":
            self.email_exists = True
        if self.debug:
            print("Couldn't sign the user up: ", failure_data)

    def sign_up_error(self, *args):
        self.hide_loading_screen()
        if self.debug:
            print("Sign up Error: ", args)

    def sign_in(self, email, password):
        if self.debug:
            print("Attempting to sign user in: ", email, password)
        sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + self.web_api_key
        sign_in_payload = dumps(
            {"email": email, "password": password, "returnSecureToken": True})

        UrlRequest(sign_in_url, req_body=sign_in_payload,
                   on_success=self.successful_login,
                   on_failure=self.sign_in_failure,
                   on_error=self.sign_in_error)

    def sign_in_failure(self, urlrequest, failure_data):
        self.hide_loading_screen()
        self.email_not_found = False
        print(failure_data)
        msg = failure_data['error']['message'].replace("_", " ").capitalize()

        if msg == self.sign_in_msg:
            msg = " " + msg + " "
        self.sign_in_msg = msg
        if msg == "Email not found":
            self.email_not_found = True
        if self.debug:
            print("Couldn't sign the user in: ", failure_data)

    def sign_in_error(self, *args):
        self.hide_loading_screen()
        if self.debug:
            print("Sign in error", args)

    def reset_password(self, email):
        if self.debug:
            print("Attempting to send a password reset email to: ", email)
        reset_pw_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode?key=" + self.web_api_key
        reset_pw_data = dumps({"email": email, "requestType": "PASSWORD_RESET"})

        UrlRequest(reset_pw_url, req_body=reset_pw_data,
                   on_success=self.successful_reset,
                   on_failure=self.sign_in_failure,
                   on_error=self.sign_in_error)

    def successful_reset(self, urlrequest, reset_data):
        self.hide_loading_screen()
        if self.debug:
            print("Successfully sent a password reset email", reset_data)
        self.sign_in_msg = "Reset password instructions sent to your email."

    def save_refresh_token(self, refresh_token):
        if self.debug:
            print("Saving the refresh token to file: ", self.refresh_token_file)
        with open(self.refresh_token_file, "w") as f:
            f.write(refresh_token)

    def load_refresh_token(self):
        if self.debug:
            print("Loading refresh token from file: ", self.refresh_token_file)
        with open(self.refresh_token_file, "r") as f:
            self.refresh_token = f.read()

    def load_saved_account(self):
        if self.debug:
            print("Attempting to log in a user automatically using a refresh token.")
        self.load_refresh_token()
        refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + self.web_api_key
        refresh_payload = dumps({"grant_type": "refresh_token", "refresh_token": self.refresh_token})
        UrlRequest(refresh_url, req_body=refresh_payload,
                   on_success=self.successful_account_load,
                   on_failure=self.failed_account_load,
                   on_error=self.failed_account_load)

    def successful_account_load(self, urlrequest, loaded_data):
        self.hide_loading_screen()
        if self.debug:
            print("Successfully logged a user in automatically using the refresh token")
        self.idToken = loaded_data['id_token']
        self.localId = loaded_data['user_id']
        self.login_success = True

    def failed_account_load(self, *args):
        self.hide_loading_screen()
        if self.debug:
            print("Failed to load an account.", args)

    def display_loading_screen(self, *args):
        self.popup.color = self.tertiary_color
        self.popup.open()

    def hide_loading_screen(self, *args):
        self.popup.dismiss()


