import tempfile
import time
from bs4 import BeautifulSoup as bfls4
import json
from pathlib import Path

from niced_url_request import NicedUrlRequest

# a few helpers from SO:
# https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python

# prefix components:
space = '    '
branch = '│   '
# pointers:
tee = '├── '
last = '└── '


def tree(dir_path: Path, prefix: str=''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """
    contents = list(dir_path.iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        yield prefix + pointer + path.name
        if path.is_dir():  # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from tree(path, prefix=prefix+extension)


# perform a double request using a publicly available url, as recommended on:
# https://stackoverflow.com/questions/5725430/http-test-server-accepting-get-post-requests


def cache_organizer(request):
    """a simple dummy organizer, request -> path"""

    # the requests we perform look like:
    # http://httpbin.org/get?bla1=blabla
    # so this means that the folder to use will be in this case 'bla1',
    # which is the value returned by the slicing

    return(request[23:27])


with tempfile.TemporaryDirectory() as tmpdirname:
    print("using temp dir: {}".format(tmpdirname))

    # we use ta tmp dir to not clutter the HOME;
    # using cache_folder = "default" would
    # put the files in the HOME/.NicedUrlRequest/cache folder instead
    cache_folder = tmpdirname  # this will put the files in tmpdirname;

    niced_requester = NicedUrlRequest(cache_folder=cache_folder,
                                      cache_organizer=cache_organizer)
    time_start = time.time()

    # perform the requests 1 and 2 once

    # request 1 ##################################################
    html_string = niced_requester.perform_request(
        "http://httpbin.org/get?bla1=blabla"
    )

    time_request_1 = time.time()

    # a bit of hand-made work to get the data out of the answer
    soup = bfls4(html_string, features="lxml")
    dict_data_html = json.loads(soup.findAll("p")[0].text)

    assert dict_data_html["args"]["bla1"] == "blabla"

    # request 2 ##################################################
    html_string = niced_requester.perform_request(
        "http://httpbin.org/get?bla2=blabla2"
    )

    soup = bfls4(html_string, features="lxml")
    dict_data_html = json.loads(soup.findAll("p")[0].text)
    assert dict_data_html["args"]["bla2"] == "blabla2"

    time_request_2 = time.time()

    # repeat the requests; should be in cache now

    # request 1 ##################################################
    html_string = niced_requester.perform_request(
        "http://httpbin.org/get?bla1=blabla"
    )

    time_request_1_repeat = time.time()

    soup = bfls4(html_string, features="lxml")
    dict_data_html = json.loads(soup.findAll("p")[0].text)

    assert dict_data_html["args"]["bla1"] == "blabla"

    # request 2 ##################################################
    html_string = niced_requester.perform_request(
        "http://httpbin.org/get?bla2=blabla2"
    )

    soup = bfls4(html_string, features="lxml")
    dict_data_html = json.loads(soup.findAll("p")[0].text)
    assert dict_data_html["args"]["bla2"] == "blabla2"

    time_request_2_repeat = time.time()

    # a bit of summary:
    print("")
    print("the tmp dir looks like:")
    for line in tree(Path(tmpdirname)):
        print(line)

    print("")
    print("the time taken by the requests are:")
    print("request 1: {}".format(time_request_1 - time_start))
    print("request 2: {}".format(time_request_2 - time_request_1))
    print("request 1 repeat: {}".format(
        time_request_1_repeat - time_request_2)
    )
    print("request 1 repeat: {}".format(
        time_request_2_repeat - time_request_1_repeat)
    )
    print("this is because:")
    print("- it takes a bit of time to fetch request 1 from internet")
    print("- then when performing reques 2, one has to wait so that "
          "the time between requests is at least 1 second")
    print("- when re-doing the requests, thing go fast, as the results "
          "are in cache")

    # give the user the time to explore the results if wanted
    print("")
    input("Press Enter to continue...")

