# niced_url_request

A simple wrapper class to "nice" url requests in python by setting a maximum frequency to url requests, and using a disk cache.

## Motivation

I have needed several times lately to get some relatively large dataset from the net as a series of smaller http requests. This class is a convenient small wrapper for doing so without annoying the server.

## Functionalities

- limit request rate
- cache the answers on disk
- perform up to 10 re-tries waiting 10 seconds in between if request fails to make querying large quantities of requests robust to minor network / service interruptions

## Installation

```
pip install niced_url_request
```

## Tests and example

To run tests: ```pytest -v .``` from the present folder.

For a detailed example: see ```examples``` folder.

Small start up example:

```
from niced_url_request import NicedUrlRequest

niced_requester = NicedUrlRequest()

request_result = niced_requester.perform_request("http://httpbin.org/get?bla1=blabla1")

print(request_result.decode("ASCII"))
```

