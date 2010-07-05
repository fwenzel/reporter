Firefox Input
=============

Firefox Input is a [Django][Django]-based web application to gather user
feedback from the [Mozilla][Mozilla] Firefox beta testing program.

For project goals, specifications, etc., check out the
[Reporter Wiki Page][wikimo].

[Mozilla]: http://www.mozilla.org
[Django]: http://www.djangoproject.com/
[wikimo]: https://wiki.mozilla.org/Firefox/Input

Getting Started
---------------
### Python
You need Python 2.6. Also, you probably want to run this application in a
[virtualenv][virtualenv] environment.

Run

    easy_install pip

followed by

    pip install -r requirements/prod.txt -r requirements/compiled.txt

to install the required Python libraries.

[virtualenv]: http://pypi.python.org/pypi/virtualenv

### Sphinx

For searching, we use [Sphinx][sphinx]. Set up an instance of it, and adjust
the SPHINX\_\* settings in settings.py to match your setup. There are three
management commands to go with it:

* ``start_sphinx`` starts the sphinx daemon
* ``stop_sphinx`` stops it
* ``update_index`` updates the search index (see below)

[sphinx]: http://www.sphinxsearch.com/

### Django
Put your database settings in `settings_local.py`:

        from settings import *

        # ...

        DATABASES = {
            'default': {
                'ENGINE': 'mysql',
                'NAME': 'firefox_input',
                'USER': 'root',
                'PASSWORD': '',
                'HOST': 'localhost',
                'PORT': '',
                'OPTIONS': {'init_command': 'SET storage_engine=InnoDB',
                            'charset' : 'utf8',
                            'use_unicode' : True,
                           },
            }
        }

To initialize the database, run:

    ./manage.py syncdb

and to fetch the initial product details data, run:

    ./manage.py update_product_details

Finally, to initialize the search index, run:

    ./manage.py update_index

The Internet has plenty of of documentation on setting up a Django application
with any web server. If you need a wsgi entry point, you can find one in
``wsgi/reporter.wsgi``.

### Cron jobs
There are two jobs you want to run periodically:

    ./manage.py update_product_details  # Mozilla Product Details update
    ./manage.py update_index            # update search index

The frequency is up to you, but you probably want to run the search index
updates relatively frequently, while the product details can wait a little
longer.

License
-------
This software is licensed under the [Mozilla Tri-License][MPL]:

    ***** BEGIN LICENSE BLOCK *****
    Version: MPL 1.1/GPL 2.0/LGPL 2.1

    The contents of this file are subject to the Mozilla Public License Version
    1.1 (the "License"); you may not use this file except in compliance with
    the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS" basis,
    WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
    for the specific language governing rights and limitations under the
    License.

    The Original Code is Firefox Input.

    The Initial Developer of the Original Code is Mozilla.
    Portions created by the Initial Developer are Copyright (C) 2010
    the Initial Developer. All Rights Reserved.

    Contributor(s):
      Frederic Wenzel <fwenzel@mozilla.com>

    Alternatively, the contents of this file may be used under the terms of
    either the GNU General Public License Version 2 or later (the "GPL"), or
    the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
    in which case the provisions of the GPL or the LGPL are applicable instead
    of those above. If you wish to allow use of your version of this file only
    under the terms of either the GPL or the LGPL, and not to allow others to
    use your version of this file under the terms of the MPL, indicate your
    decision by deleting the provisions above and replace them with the notice
    and other provisions required by the GPL or the LGPL. If you do not delete
    the provisions above, a recipient may use your version of this file under
    the terms of any one of the MPL, the GPL or the LGPL.

    ***** END LICENSE BLOCK *****

[MPL]: http://www.mozilla.org/MPL/
