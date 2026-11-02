"""Settings for the test suite, which must not depend on a local .env file."""

import os

if not os.environ.get("DJANGO_SECRET_KEY"):
    os.environ["DJANGO_SECRET_KEY"] = "test-secret-key"

from .settings import *  # noqa: E402,F401,F403

TOMTOM_API_KEY = "test-key"
SECURE_SSL_REDIRECT = False
