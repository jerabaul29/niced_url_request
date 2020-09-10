"""A few helper functions to work with url requests."""

import urllib.request

import time
import datetime

from pathlib import Path

from raise_assert import ras

import logging


class NicedUrlRequest():
    """A simple wrapper to nice url requests.
    Make sure that the caller has to wait for a minimum amount of time between requests.
    Use disk caching of the requests."""

    def __init__(self, min_wait_time_s=1, cache_folder="default", cache_organizer=None,
                 request_callback=None, cache_warning=True):
        """
        - min_wait_time_s: minimum time interval between requests.
        - cache_folder: properties for caching the data. Can be: None (no caching),
            "default" (use ./NicedUrlRequest/cache folder in home dir), or any custom
            valid path.
        - cache_organizer: a function that takes in an URL request and returns the
            folder, which will be followed relative to the root
            of the cache_folder, where the request should be stored. This
            way, allows to keep a balanced cache folder structure, and to avoid having
            very many files in one folder. Default is None, i.e. everything is dumped
            into the cache_folder, which may result in many files in a single folder.
            For balancing properties, this function should be usercase specific, and
            it is let to the user to implement.
        - request_callback: a callback function to be called if a url request is performed.
            The callback is performed just before the request. By default None (i.e., nothing).
        - cache_warning: if the cache should be checked for some metrics and some cache
            warnings should be produced at class init. Default True.
        """

        ras(min_wait_time_s >= 0)

        self.min_wait_time_s = min_wait_time_s
        self.time_last = None

        # initialize with the start time -min_wait_time_s, so that immediately ready to use
        self.update_time()
        self.time_last -= self.min_wait_time_s

        # use the right cache folder, make sure valid / terminated both if default
        # and user specified
        if cache_folder == "default":
            self.cache_folder = Path.home().joinpath(".NicedUrlRequest").joinpath("cache")
        elif cache_folder is not None:
            self.cache_folder = Path(cache_folder)
        else:
            self.cache_folder = None

        if self.cache_folder is not None and not self.cache_folder.is_dir():
            self.cache_folder.mkdir(parents=True)

        self.cache_organizer = cache_organizer

        logging.info("the cache folder is set to {}".format(self.cache_folder))

        self.request_callback = request_callback

        self.cache_warning_flag = cache_warning

        if self.cache_warning_flag:
            self.cache_warning()

    def cache_warning(self, cache_warning_size=50*(2.0**30), age_warning_days=90, nbr_files_warning=10000):
        """warns if cache reaches some given metrics.

        - cache_warning_size: the size above which we get a cache warning due to the size in bits.
            Default is 50 GB.
        - age_warning_days: the age above which we get a cache warning due to old age file. Default
            is 90 days.
        - nbr_files_warning: the number of files in the specific cache folder used by the instance. Default
            warns if over 10000 files.
        """

        cache_warning_met = False

        if self.cache_folder is not None:
            size_cache_content = sum(f.stat().st_size for f in self.cache_folder.glob('**/*') if f.is_file())

            if size_cache_content > cache_warning_size:
                logging.warning(
                    "large NicedUrlRequest cache of {}GB at {}".format(size_cache_content / 2.0**30, self.cache_folder)
                )
                cache_warning_met = True

            sorted_files_time = sorted(self.cache_folder.glob('**/*'), key=lambda x: x.stat().st_ctime)

            now = datetime.datetime.now()

            for crrt_file in sorted_files_time:
                crrt_age_in_days = (datetime.datetime.fromtimestamp(crrt_file.stat().st_ctime)-now).days
                if crrt_age_in_days < -age_warning_days:
                    logging.warning("NicedUrlRequest cache file {} is old: {} days".format(crrt_file, crrt_age_in_days))
                    cache_warning_met = True

            if len(sorted_files_time) > nbr_files_warning:
                logging.warning("large NicedUrlRequest cache number of files: {}".format(len(sorted_files_time)))
                cache_warning_met = True

            if cache_warning_met:
                logging.warning("you should maybe clean your cache at: {}".format(self.cache_folder))

    def update_time(self):
        """Update the time corresponding to the last request."""
        self.time_last = time.time()

    def elapsed_since_last_request(self):
        """Time elapsed since the last request."""
        return time.time() - self.time_last

    def path_in_cache(self, request):
        """Find the path in the cache for the present request. This is a concatenation of the cache
        root folder and the relative path in cache if a cache_organizer is used.
        Input:
            - request: the request to consider
        Output:
            - the path where the request should be stored.
        """
        if self.cache_folder is None:
            return(None)
        else:
            if self.cache_organizer is None:
                return(self.cache_folder.joinpath(request.replace("/", "").replace("\\", "")))
            else:
                path_within_cache = self.cache_organizer(request)
                ras(path_within_cache[0] != "/",
                    "the cache_organizer must return a relative path, like for example '2020/02'")
                ras(path_within_cache[-1] != "/",
                    "the cache_organizer must return a relative path, like for example '2020/02'")
                complete_path = self.cache_folder.joinpath(path_within_cache)

                if not complete_path.is_dir():
                    complete_path.mkdir()

                return(complete_path.joinpath(request.replace("/", "").replace("\\", "")))

    def perform_request(self, request, ignore_cache=False, allow_caching=True, max_retries=60):
        """Perform the request, after checking if the data are available in cache,
        and making sure we are not too hard on the server. If necessary, sleep a bit to
        avoid overwhelming the server with too many requests.

        Input:
            - request: the request to perform
            - ignore_cache: boolean, if True ignore the cache entry and perform the request
                anyways, if False uses cached value if available.
            - allow_caching: boolean, if True allow caching, if False not, default True.
            - max_retries: the maximum number of retries. Default is 10. Wait 10 second between
                consecutive retries.

        Output:
            - html_string: the answer html
        """

        if not isinstance(request, str):
            raise ValueError("request should be a string, but got {}".format(request))

        if not isinstance(ignore_cache, bool):
            raise ValueError("ignore_cache should be a bool, but got {}".format(ignore_cache))

        if not isinstance(allow_caching, bool):
            raise ValueError("allow_caching should be a bool, but got {}".format(allow_caching))

        logging.info("go through request {}".format(request))

        crrt_path_in_cache = self.path_in_cache(request)
        if crrt_path_in_cache is not None and not ignore_cache and crrt_path_in_cache.is_file():
            logging.info("the request is already available in cache, and we are allowed to use it")

            with open(crrt_path_in_cache, 'rb') as fh:
                html_string = fh.read()

        else:
            remaining_sleep = self.min_wait_time_s - self.elapsed_since_last_request()
            logging.info("remaining_sleep (negative is none needed): {}".format(remaining_sleep))

            if remaining_sleep > 0:
                logging.info("sleeping")
                time.sleep(remaining_sleep)

            if self.request_callback is not None:
                logging.info("call request callback")
                self.request_callback()

            logging.info("perform request")
            self.update_time()

            number_retries_left = max_retries
            status = None

            while number_retries_left > 0 and status != 200:
                try:
                    number_retries_left -= 1
                    logging.info("attempt to request...")

                    with urllib.request.urlopen(request) as response:
                        status = response.status

                        if not status == 200:
                            raise ValueError("got status {} on request {}".format(response.status, request))

                        html_string = response.read()

                except Exception as crrt_exception:
                    logging.warning(
                        "Exception {} during http request: {}".format(crrt_exception.__class__, str(crrt_exception))
                    )
                    time.sleep(10.0)

                if number_retries_left == 0 and status != 200:
                    raise ValueError("url request retries exhausted, but still have an error code: {}".format(status))

            logging.info("successful request")

            if crrt_path_in_cache is not None and allow_caching:
                logging.info("we are allowed to cache this request; caching")

                with open(crrt_path_in_cache, "wb") as fh:
                    fh.write(html_string)

        return html_string
