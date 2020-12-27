from asks import BasicAuth

from unittest import TestCase
import pytest
from asks.response_objects import Response

from many_requests.many_requests_ import ManyRequests
from many_requests.common import BadResponse
from .mock_server import web_server

@pytest.mark.usefixtures("web_server")
class TestManyRequestAuth(TestCase):

    def test_basic_auth(self):
        auths = [
            BasicAuth(auth_info=(("username", "password"))), # ok
            BasicAuth(auth_info=(("username", "bad_password")))  # bad
        ]
        url = 'http://0.0.0.0:8080/basic_auth'
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0)(method='GET', url=url, auth=auths)
        assert len(responses) == 2

        ok_res = responses[0]
        assert isinstance(ok_res, Response)
        assert ok_res.url == url

        bad_res = responses[1]
        assert isinstance(bad_res, BadResponse)
        assert bad_res.response.status_code == 401
        assert bad_res.response.url == url


