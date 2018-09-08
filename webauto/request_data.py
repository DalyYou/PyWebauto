"""
# @Author   : DaoQ You

# @File     : request_data.py

# @Project  : webauto

# @Software : PyCharm Community Edition
"""

# !/usr/bin/python
# -*- coding:utf-8 -*-
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class RequestData(object):
    """
    Get Request Data
    """
    @staticmethod
    def get_header_data():
        '''
        Get header data

        :return:
        '''
        return {'X-CENTRIFY-NATIVE-CLIENT': 'True', 'Content-type': 'application/json'}

    @staticmethod
    def get_start_auth_data(tenant_id, user, application_id=None, mfa_requestor=None, version="1.0"):
        '''
        Get start authentication data

        :param tenant_id:

        :param user:

        :param application_id:

        :param mfa_requestor:

        :param version:

        :return:
        '''
        return {'TenantId': tenant_id,
                'User': user,
                'Version': version,
                'ApplicationId': application_id,
                'MfaRequestor': mfa_requestor}

    @staticmethod
    def get_advance_auth_data(tenantid, sessionid, mechanismid, answer, persistentlogin="True", action="Answer"):
        '''
        Get advance authentication data

        :param tenantid:

        :param sessionid:

        :param mechanismid:

        :param answer:

        :param persistentlogin:

        :param action:

        :return:
        '''
        return {'Action': action,
                'Answer': answer,
                'MechanismId': mechanismid,
                'PersistentLogin': persistentlogin,
                'SessionId': sessionid,
                'TenantId': tenantid}

    @staticmethod
    def get_redrock_query_data(script):
        '''
        Get redrock query data

        :param script:

        :return:
        '''
        return {'Script': script}
