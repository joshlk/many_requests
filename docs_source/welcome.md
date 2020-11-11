# Welcome to many-requests's documentation!

Dead easy interface for executing many HTTP requests asynchronously.
It has been tested in the wild with over 10 million requests.
Automatically handles errors and executes retries.

Built on-top of [Trio](https://github.com/python-trio/trio) and [asks](https://github.com/theelous3/asks).

Also provides helper functions for executing [embarrassingly parallel](https://en.wikipedia.org/wiki/Embarrassingly_parallel) async coroutines.

To install:

```bash
pip install many-requests
```

## Example Usage

Execute 10 GET requests for example.org:

```python
from many_requests import ManyRequests
responses = ManyRequests(n_workers=5, n_connections=5)(
                 method='GET', url=['https://example.org' for i in range(10)])
```

Query HackNews API for 10 items and parse JSON output:

```python
responses = ManyRequests(n_workers=5, n_connections=5, json=True)(
                 method='GET',
                 url=[f'https://hacker-news.firebaseio.com/v0/item/{i}.json?print=pretty' for i in range(10)])
```

To execute embarrassingly parallel async coroutines:

```python
from many_requests import EasyAsync, delayed
import trio
EasyAsync(n_workers = 4)(delayed(trio.sleep)(i) for i in range(10))
```