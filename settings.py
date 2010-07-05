# Django settings for the reporter project.

import os
import logging

# Make filepaths relative to settings.
ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

ROOT_PACKAGE = os.path.basename(ROOT)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

LOG_LEVEL = logging.DEBUG
SYSLOG_TAG = "http_app_reporter"

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB',
                    'charset' : 'utf8',
                    'use_unicode' : True,
                   },
    }
}

# Caching
#CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
CACHE_DEFAULT_PERIOD = 60 * 5  # 5 minutes

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^e*0du@u83$de+==+x$5k%x#+4v7&nm-_sggrr(t!&@kufz87n'

# Templates

TEMPLATE_DIRS = (
    path('templates'),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

def JINJA_CONFIG():
    import jinja2
    config = {'extensions': ['jinja2.ext.with_', 'jinja2.ext.loopcontrols',
                             'jinja2.ext.i18n'],
              'finalize': lambda x: x if x is not None else ''}
    return config

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'reporter.urls'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',

    'annoying',
    'product_details',

    'dashboard',
    'feedback',
    'search',
    'swearwords',
]

# Where to store product details
PROD_DETAILS_DIR = path('lib/product_details_json')

# Setting this to False allows feedback to be collected from any user agent.
# (good for testing)
ENFORCE_USER_AGENT = True

# Term filter options
MIN_TERM_LENGTH = 3
MAX_TERM_LENGTH = 25

# Number of items to show in the "Trends" box and Messages box.
MESSAGES_COUNT = 10
TRENDS_COUNT = 10

# Sphinx Search Index
SPHINX_HOST = '127.0.0.1'
SPHINX_PORT = 3314
SPHINX_SEARCHD = 'searchd'
SPHINX_INDEXER = 'indexer'
SPHINX_CATALOG_PATH = path('tmp/data/sphinx')
SPHINX_LOG_PATH = path('tmp')
SPHINX_CONFIG_PATH = path('configs/sphinx/sphinx.conf')

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'
