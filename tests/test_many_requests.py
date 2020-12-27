from unittest import TestCase
import pytest
from asks.response_objects import Response

from many_requests.many_requests_ import ManyRequests
from many_requests.common import BadResponse
from .mock_server import web_server


@pytest.mark.usefixtures("web_server")
class TestManyRequest(TestCase):

    def test_request(self):
        urls = [f'http://0.0.0.0:8080/' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0)(method='GET', url=urls)
        assert len(responses) == 10
        for response, url in zip(responses, urls):
            assert response.url == url
            assert isinstance(response, Response)

    def test_request_json(self):
        json = True
        urls = [f'http://0.0.0.0:8080/json' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0, json=json)(method='GET', url=urls)
        assert len(responses) == 10
        for response, url in zip(responses, urls):
            assert isinstance(response, dict)
            assert response == {"foo": "bar"}

    def test_json_failure(self):
        json = True
        urls = [f'http://0.0.0.0:8080/' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0, json=json)(method='GET', url=urls)
        assert len(responses) == 10
        for error, url in zip(responses, urls):
            assert isinstance(error, BadResponse)
            assert error.response.url == url
            assert error.reason == 'JSONDecodeError'

    def test_status_code_failure(self):
        urls = [f'https://example.org/bad_request' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0)(method='GET', url=urls)
        assert len(responses) == 10
        for error, url in zip(responses, urls):
            assert isinstance(error, BadResponse)
            assert error.response.url == url
            assert error.reason == 'bad_status_code'

    def test_single_request(self):
        json = False
        ok_code = (200,)
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0, ok_codes=ok_code, json=json)(
            method='GET', url='https://example.org/')
        assert len(responses) == 1
        response = responses[0]
        assert response.url == 'https://example.org/'
        assert isinstance(response, Response)

