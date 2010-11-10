#!/bin/bash

# Update script for staging server. Takes care of updating code repo, vendor
# dir, and running DB migrations.

HERE=`dirname $0`
GIT=`which git`
PYTHON=`which python2.6`

pushd "$HERE/../" > /dev/null

# pull actual code
$GIT pull -q origin master
$GIT submodule update --init

# pull vendor repo
pushd vendor > /dev/null
$GIT pull -q origin master
$GIT submodule update --init
popd > /dev/null

# Run database migrations.
$PYTHON vendor/src/schematic/schematic migrations/
$PYTHON vendor/src/schematic/schematic migrations/sites

# Minify assets.
$PYTHON manage.py compress_assets

# Fix mobile and desktop site domains in database. Bug 608581.
$PYTHON ./manage.py cron set_domains input.stage.mozilla.com m.input.stage.mozilla.com

popd > /dev/null
