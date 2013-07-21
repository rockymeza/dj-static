# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.base import get_path_info
from django.contrib.staticfiles.handlers import StaticFilesHandler as DebugHandler

try:
    from urllib.parse import urlparse
except ImportError:     # Python 2
    from urlparse import urlparse
from django.contrib.staticfiles import utils

from werkzeug.wsgi import SharedDataMiddleware


class Cling(WSGIHandler):
    """WSGI middleware that intercepts calls to the static files
    directory, as defined by the STATIC_URL setting, and serves those files.
    """
    def __init__(self, application, base_dir=None):
        self.application = application
        if not base_dir:
            base_dir = self.get_base_dir()
        self.base_url = urlparse(self.get_base_url())

        self.cling = SharedDataMiddleware(application, {
            self.base_url.path: base_dir,
        })
        self.debug_cling = DebugHandler(base_dir)

        super(Cling, self).__init__()

    def get_base_dir(self):
        return settings.STATIC_ROOT

    def get_base_url(self):
        utils.check_settings()
        return settings.STATIC_URL

    @property
    def debug(self):
        return settings.DEBUG

    def _should_handle(self, path):
        """Checks if the path should be handled. Ignores the path if:

        * the host is provided as part of the base_url
        * the request's path isn't under the media path (or equal)
        """
        return path.startswith(self.base_url[2]) and not self.base_url[1]

    def __call__(self, environ, start_response):
        # Hand non-static requests to Django
        if not self._should_handle(get_path_info(environ)):
            return self.application(environ, start_response)

        # Serve static requests from werkzeug.wsgi.SharedDataMiddleware
        if not self.debug:
            return self.cling(environ, start_response)
        # Serve static requests in debug mode from StaticFilesHandler
        else:
            return self.debug_cling(environ, start_response)


class MediaCling(Cling):

    def debug_cling(self, environ, start_response):
        return self.cling(environ, start_response)

    def get_base_dir(self):
        return settings.MEDIA_ROOT

    def get_base_url(self):
        return settings.MEDIA_URL
