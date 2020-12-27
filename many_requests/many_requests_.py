
import logging
from json import JSONDecodeError
from typing import List, Optional, Dict, Union

import asks
import trio
from asks import AuthBase
from asks.errors import BadHttpResponse
from asks.response_objects import Response
from h11 import RemoteProtocolError

from .easy_async import EasyAsync, delayed, zip_kw
from .common import BadResponse, N_WORKERS_DEFAULT, N_CONNECTIONS_DEFAULT, is_collection


class ManyRequests:
    def __init__(
        self,
        n_workers=N_WORKERS_DEFAULT,
        n_connections=N_CONNECTIONS_DEFAULT,
        retries=10,
        retry_sleep=3,
        ok_codes=(200,),
        ok_response_func=None,
        json=False,
    ):
        """
        Dead easy interface for executing many HTTP requests asynchronously.

        Args:
            n_workers: Max number of workers to use. Too many workers will use a lot of memory and increase startup
                time, too few can lead to slower execution.
            n_connections: Max number of open connections to have open at once. The number of connections is also
                limited by the OS. For example, by default MacOS has a limit of 256 and Ubuntu has ~66k. These limits
                can be changed with OS configuration.
            retries: Number of retries to attempt if a request fails
            retry_sleep: How long to wait in seconds before retrying a request
            ok_codes: A sequence of HTTP status codes to accept as ok. If `any`, all responses will be assumed to be ok
            ok_response_func: A function to apply to the response to determine if ok. Should return True/False.
            json: Parse response body as json and return instead of full Responce object

        Examples:
            Execute 10 GET requests to https://example.org

            >>> responses = ManyRequests(n_workers=5, n_connections=5)(
            >>>                 method='GET', url=[f'https://example.org' for i in range(10)])
        """
        self.n_workers = n_workers
        self.n_connections = n_connections
        self.session = None
        self.retries = retries
        self.retry_sleep = retry_sleep
        self.ok_codes = ok_codes
        self.ok_response_func = ok_response_func
        self.json = json

        self.requests = None
        self.responses = None

    def __call__(
        self,
        method: Union[str, List[str]],
        url: Union[str, List[str]],
        params: Union[None, str, Dict, List[str], List[Dict]] = None,
        data: Union[None, str, Dict, List[str], List[Dict]] = None,
        json: Union[None, Dict, List[Dict]] = None,
        headers: Union[None, Dict, List[Dict]] = None,
        cookies: Union[None, Dict, List[Dict]] = None,
        auth: Union[None, AuthBase, List[AuthBase]] = None,
    ) -> List[Union[Response, BadResponse]]:
        """
        Process asynchronously many requests, handling bad responses. Return the responses in the same order.
        If no ok response was obtained after retires a `BadResponse` will be included in the corresponding position of
        the output. A `BadResponse` will contain the last response and error reason.

        Arguments mimic `asks.request`_, which in turn mimics `requests.request`_.

        **Each argument can be a single item or a list of N items, where N is the number of requests.
        When the argument is a single item, that attribute is duplicated N times for every request.**

        Args:
            method: HTTP method type `GET`, `OPTIONS`, `HEAD`, `POST`, `PUT`, `PATCH`, or `DELETE`.
            url: URL of the Request
            params: Data to send in the query string of the Request. Dictionary or string.
            data: Data to send in the body of the Request. Dictionary or string.
            json: A JSON serializable dictionary to send as JSON in the body of the Request.
            headers: Dictionary of HTTP Headers to send with the Request
            cookies: Dictionary object to send with the Request
            auth: Enable Basic/Digest/Custom HTTP Auth. Should be a child of `asks.AuthBase`

        Returns:
            responses: A list of responses in the same order of the requests. Will include a `BadResponse` in the
            position of a request where no good response was obtained.

        .. _asks.request:
            https://asks.readthedocs.io/en/latest/overview-of-funcs-and-args.html
        .. _requests.request:
            https://2.python-requests.org/en/master/api/#requests.request
        """

        length = None
        for e in (method, url, params, data, json, headers, cookies, auth):
            if not is_collection(e):
                continue
            try:
                l = len(e)
                if length is None or l < length:
                    length = l
            except TypeError:
                pass

        self.session = asks.Session(connections=self.n_connections)
        responses = EasyAsync(n_workers=self.n_workers)(
            tasks=(
                delayed(self._runner)(request_kwargs=kwargs)
                for kwargs in zip_kw(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=headers,
                    cookies=cookies,
                    auth=auth,
                )
            ),
            length=length,
        )

        return responses

    async def _runner(self, request_kwargs):
        """Task which handles completing a HTTP request and errors that arise"""

        last_error = None

        for attempt_i in range(0, self.retries+1):
            try:
                try:
                    response = await self.session.request(**request_kwargs)
                except RemoteProtocolError as e:
                    raise BadResponse('RemoteProtocolError', reason='RemoteProtocolError', attempt_num=attempt_i)
                except BadHttpResponse as e:
                    raise BadResponse('BadHttpResponse', reason='BadHttpResponse', attempt_num=attempt_i)

                if self.ok_codes != "any" and response.status_code not in self.ok_codes:
                    raise BadResponse(f"Bad response status code: {response.status_code}. Should be in {self.ok_codes}",
                                      response=response, reason='bad_status_code', attempt_num=attempt_i)

                if self.ok_response_func is not None and not self.ok_response_func(response):
                    raise BadResponse('Not OK response determined by `ok_response_func`', response=response,
                                      reason='ok_response_func', attempt_num=attempt_i)

                if self.json:
                    try:
                        response = response.json()
                    except JSONDecodeError as e:
                        raise BadResponse('Cannot decode JSON', response=response, reason='JSONDecodeError',
                                          attempt_num=attempt_i)

                logging.debug(f"OK Response {request_kwargs}")
                return response

            except BadResponse as e:
                try:
                    code, text = response.status_code, response.text
                except NameError:
                    code, text = None, None

                logging.info(
                    f"BAD Response {request_kwargs}: Attempt {attempt_i}. Error {type(e).__name__}. Code: {code}. Body: {text}"
                )

                last_error = e
                await trio.sleep(self.retry_sleep)

        logging.warning(
            f"FAILED Request {request_kwargs}: Permanently failed. Last error: {last_error.description}"
        )
        return last_error
