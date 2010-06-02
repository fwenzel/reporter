import os
import site

import django.core.handlers.wsgi

# Add the parent dir to the python path so we can import manage
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../../')))

# manage.py adds the `apps` and `lib` directories to the path
ROOT = os.path.abspath(os.path.join(wsgidir, '../'))
ROOT_PACKAGE = os.path.basename(ROOT)
__import__('%s.manage' % ROOT_PACKAGE)

# for mod-wsgi
application = django.core.handlers.wsgi.WSGIHandler()
