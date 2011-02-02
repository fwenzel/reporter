cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build on executor $EXECUTOR_NUMBER..."

if [ -z $1 ]; then
    echo "Warning: You should provide a unique name for this job to prevent "
    echo "database collisions."
    echo "Usage: ./build.sh <name>"
    echo "Continuing, but don't say you weren't warned."
fi

# Make sure there's no old pyc files around.
find . -name '*.pyc' | xargs rm

if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV
fi

if [ ! -d "$VENV/vendor" ]; then
    echo "No /vendor... crap."
    git clone git://github.com/fwenzel/reporter-lib vendor
fi

pushd vendor && git pull && git submodule update --init && popd

source $VENV/bin/activate

pip install -q -r requirements/compiled.txt

cat > settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE
LOG_LEVEL = logging.ERROR
# Database name has to be set because of sphinx
DATABASES = {
    'default': {
        'ENGINE': 'mysql',
        'HOST': 'sm-hudson01',
        'NAME': 'input_$1',
        'USER': 'hudson',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
        'TEST_NAME': 'test_input_$1',
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    },
    'website_issues': {
        'ENGINE': 'mysql',
        'HOST': 'sm-hudson01',
        'NAME': 'input_$1',
        'USER': 'hudson',
        'PASSWORD': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
        'TEST_NAME': 'test_input_ws_$1',
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_general_ci',
    }
}

INSTALLED_APPS += ('django_nose',)
SETTINGS

echo "Starting tests..."
export FORCE_DB=1
coverage run manage.py test --noinput --with-xunit
coverage xml $(find apps lib -name '*.py')

# echo "Building documentation..."
# cd docs
# make clean dirhtml SPHINXOPTS='-q'
# cd $WORKSPACE

echo "FIN"
