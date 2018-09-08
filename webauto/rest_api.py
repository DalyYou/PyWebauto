"""
# @Author   : DaoQ You

# @File     : rest_api.py

# @Project  : webauto

# @Software : PyCharm Community Edition
"""

# !/usr/bin/python
# -*- coding:utf-8 -*-
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from request_data import RequestData
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class RestAPI(object):
    """
    Basic API Functions
    """
    def __init__(self, tenant_id, host):
        self.tenant_id = tenant_id
        self.host = host
        self.challenges = {}
        self.session_id = []
        if tenant_id:
            self.url = "https://{}.{}".format(tenant_id, host)
        else:
            self.url = "https://{}".format(host)
        self.headers = RequestData.get_header_data()
        self.cookies = {}
        self.auth_details = {}

    def security_startauthentication(self, user, application_id=None, mfa_requestor=None, version="1.0"):
        """
        /Security/StartAuthentication

        :param user: user name

        :param application_id: applicaiton id, the default value is None

        :param mfa_requestor: the mfa requestor, if no, the default value is None

        :param version: The version number

        :return: requests.post
        """

        body = RequestData.get_start_auth_data(self.tenant_id, user, application_id, mfa_requestor, version)
        post_request = requests.post(url=self.url + "/Security/StartAuthentication", data=json.dumps(body), headers=self.headers, verify=False)

        if post_request.ok and 'SessionId' in post_request.json()['Result']:
            self.session_id = post_request.json()['Result']['SessionId']
        if post_request.ok and 'Challenges' in post_request.json()['Result']:
            self.challenges = post_request.json()['Result']['Challenges']
        return post_request

    def security_advanceauthentication(self, answer, challenge_index=None, mechanism_index=None, mechanism_id=None):
        """
        /Security/AdvanceAuthentication

        :param answer:

        :param challenge_index:

        :param mechanism_index:

        :param mechanism_id:

        :return:
        """
        if mechanism_id is None and challenge_index is None and mechanism_index is None:
            raise NotEnoughInformationToAdvanceAuthException("A mechanism_id or a challenge_index and mechanism_index is required")
        elif mechanism_id is None and challenge_index is not None and mechanism_index is not None:
            mechanism_id = self.challenges[challenge_index]['Mechanisms'][mechanism_index]['MechanismId']
        elif mechanism_id is None:
            raise NotEnoughInformationToAdvanceAuthException("Both a challenge_index and mechanism_index are required if either are to be used")
        body = RequestData.get_advance_auth_data(self.tenant_id, self.session_id, mechanism_id, answer, persistentlogin="True", action="Answer")
        post_request = requests.post(url=self.url + "/Security/AdvanceAuthentication", data=json.dumps(body), headers=self.headers, verify=False)

        if post_request.ok:
            self.cookies = post_request.cookies
            result_summary = post_request.json()['Result']['Summary']
            if result_summary == 'LoginSuccess':
                self.auth_details = post_request.json()['Result']
        return post_request

    def security_logout(self, authorization=None):
        '''
        /Security/Logout

        :param authorization:

        :return:
        '''
        if authorization is None and self.auth_details:
            authorization = self.auth_details['Auth']

        body = {
            "Authorization": authorization
        }

        post_request = requests.post(url=self.url + "/Security/Logout", data=json.dumps(body), headers=self.headers, cookies=self.cookies, verify=False)
        print(post_request)
        return post_request

    def api_login(self, username, challenge_dict, centrify_session=None):
        '''
        API login

        :param username:

        :param challenge_dict:

        :param centrify_session:

        :return:
        '''
        '''
        challenge_dict = {
            'Password': password,
            'Security Question': {
                "What is the name of the road you grew up on?": 'Johnson Ave'
            }
        }
        '''
        # Start the login process
        if centrify_session is None:
            centrify_session = self.__init__(self.tenant_id, self.host)
        response = centrify_session.security_startauthentication(username)

        logged_in = False
        # To log in, we need to answer challenges until we get "LoginSuccess"
        for challenge in response.json()['Result']['Challenges']:
            for mechanism in challenge['Mechanisms']:
                mech_id = mechanism['MechanismId']
                current_step = mechanism['PromptSelectMech']
                print("Current step is: {}".format(current_step))
                answer = ''
                # search through our challenge dictionary to see if we can answer the current challenge
                if current_step in challenge_dict:
                    if current_step == "Security Question":
                        if "MultipartMechanism" in mechanism:
                            print("Mechanism for current step: {mechanism}")
                            for multi_mech in mechanism["MultipartMechanism"]["MechanismParts"]:
                                if multi_mech['QuestionText'] in challenge_dict[current_step]:
                                    answer = challenge_dict[current_step][multi_mech['QuestionText']]
                    else:
                        answer = challenge_dict[current_step]
                    if answer is None:
                        print("Mechanism was in challenge dictionary, but the value was either empty or not found")
                else:
                    print("Unable to handle {} mechanism".format(current_step))
                # Answer the challenge
                response = centrify_session.security_advanceauthentication(answer, mechanism_id=mech_id)
                result_summary = response.json()['Result']['Summary']
                print("Authentication step attempt resulted in: {}".format(result_summary))
                if result_summary == 'LoginSuccess':
                    logged_in = True
                    break
            if logged_in is True:
                break

        if logged_in is False:
            print('Login failed')
        else:
            print('Login success')

        return centrify_session

    def query(self, script):
        '''
        Redrock Query

        :param script:

        :return:
        '''
        body = RequestData.get_redrock_query_data(script)
        post_request = requests.post(url=self.url + "/RedRock/query", data=json.dumps(body), headers=self.headers, cookies=self.cookies, verify=False)
        return post_request.json()

    def uprest_get_up_data(self, username):
        '''
        /UPRest/GetUPData

        :param username:

        :return:
        '''
        body = {
            "username": username,
            "force": 'true'
        }

        response = requests.post(url=self.url + "/UPRest/GetUPData", data=json.dumps(body), headers=self.headers, cookies=self.cookies)

        return response


class AuthException(Exception):
    """
    AuthException
    """
    pass

class CookiesException(Exception):
    """
    CookiesException
    """
    pass


class NotEnoughInformationToAdvanceAuthException(Exception):
    """
    NotEnoughInformationToAdvanceAuthException
    """
    pass
