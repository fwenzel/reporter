# Django settings for the reporter project.

import os
import logging

from django.utils.functional import lazy


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

DATABASE_ROUTERS = ('website_issues.db.DatabaseRouter',
                    'multidb.MasterSlaveRouter',)
SLAVE_DATABASES = []

# Caching
#CACHE_BACKEND = 'caching.backends.memcached://127.0.0.1:11211/'
CACHE_DEFAULT_PERIOD = CACHE_MIDDLEWARE_SECONDS = 60 * 5  # 5 minutes
CACHE_COUNT_TIMEOUT = 60  # seconds
CACHE_PREFIX = CACHE_MIDDLEWARE_KEY_PREFIX = 'reporter:'

# L10n

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
LANGUAGE_CODE = 'en-US'

# Site ID.
# Site 1 is the desktop site, site == MOBILE_SITE_ID is the mobile site. This
# is set automatically in input.middleware.MobileSiteMiddleware according to
# the request domain.
DESKTOP_SITE_ID = 1
MOBILE_SITE_ID = 2
# The desktop version is the default.
SITE_ID = DESKTOP_SITE_ID

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Accepted locales
# ar, he: bug 580573
INPUT_LANGUAGES = ('ca', 'cs', 'da', 'de', 'el', 'en-US', 'es', 'fr', 'gl',
                   'hu', 'it', 'nb-NO', 'nl', 'pl', 'pt-PT', 'ru', 'sk', 'sq',
                   'uk', 'vi', 'zh-CN', 'zh-TW')
RTL_LANGUAGES = ('ar', 'he',)  # ('fa', 'fa-IR')


# Override Django's built-in with our native names
class LazyLangs(dict):
    def __new__(self):
        import product_details
        return dict([(lang.lower(), product_details.languages[lang]['native'])
                     for lang in INPUT_LANGUAGES])
LANGUAGES = lazy(LazyLangs, dict)()

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in INPUT_LANGUAGES])

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = ('media', 'admin')

TEXT_DOMAIN = 'messages'
STANDALONE_DOMAINS = []

# Tells the extract script what files to look for l10n in and what function
# handles the extraction. The Tower library expects this.
DOMAIN_METHODS = {
    'messages': [
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],
}

TOWER_KEYWORDS = {'_lazy': None}


# Media

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

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.csrf',

    'input.context_processors.i18n',
    'input.context_processors.mobile',
    'search.context_processors.product_versions',
)


def JINJA_CONFIG():
    import jinja2
    config = {'extensions': ['tower.template.i18n', 'jinja2.ext.loopcontrols',
                             'jinja2.ext.with_', 'caching.ext.cache'],
              'finalize': lambda x: x if x is not None else ''}
    return config

MIDDLEWARE_CLASSES = (
    'input.middleware.MobileSiteMiddleware',
    'input.middleware.LocaleURLMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'reporter.urls'

INSTALLED_APPS = [
    'input',  # comes first so it always takes precedence.
    'dashboard',
    'feedback',
    'search',
    'swearwords',
    'website_issues',

    'annoying',
    'cronjobs',
    'product_details',
    'tower',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
]

# Where to store product details
PROD_DETAILS_DIR = path('lib/product_details_json')

# Setting this to False allows feedback to be collected from any user agent.
# (good for testing)
ENFORCE_USER_AGENT = True

# Term filter options
MIN_TERM_LENGTH = 3
MAX_TERM_LENGTH = 25

# Feedback length restrictions
MAX_FEEDBACK_LENGTH = 140

# Number of items to show in the "Trends" box and Messages box.
MESSAGES_COUNT = 10
TRENDS_COUNT = 10

# Sphinx Search Index
SPHINX_HOST = '127.0.0.1'
SPHINX_PORT = 3314
SPHINXQL_PORT = 3309
SPHINX_SEARCHD = 'searchd'
SPHINX_INDEXER = 'indexer'
SPHINX_CATALOG_PATH = path('tmp/data/sphinx')
SPHINX_LOG_PATH = path('tmp/log/searchd')
SPHINX_CONFIG_PATH = path('configs/sphinx/sphinx.conf')

TEST_SPHINX_PORT = 3414
TEST_SPHINXQL_PORT = 3409
TEST_SPHINX_CATALOG_PATH = path('tmp/test/data/sphinx')
TEST_SPHINX_LOG_PATH = path('tmp/test/log/searchd')

SEARCH_PERPAGE = 20  # results per page

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

import logging
logging.basicConfig()
