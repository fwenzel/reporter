#!/bin/bash

function checkretval()
{
   retval=$?
       if [[ $retval -gt 0 ]]
       then
               $error "Error!!! Exit status of the last command was $retval"
               exit $retval
       fi
}

INPUT_DIR="/data/input/python/input.mozilla.com/reporter"
VENDOR_DIR="$INPUT_DIR/vendor"

SYNC_DIR="/data/input/www/django/input.mozilla.com/reporter/"

echo -e "Updating vendor..."
cd $VENDOR_DIR
git pull
git submodule update --init

echo -e "Updating reporter..."
cd $INPUT_DIR
git fetch origin
git checkout origin/prod
git submodule update --init

cd /data/input;
/usr/bin/rsync -aq --exclude '.git*' --delete /data/input/python/ /data/input/www/django

cd $SYNC_DIR
schematic migrations
checkretval

# Pull in highcharts.src.js - our lawyers make us do this.
/usr/bin/python26 $INPUT_DIR/manage.py cron get_highcharts
/usr/bin/python26 $INPUT_DIR/manage.py compress_assets

if [ -d $SYNC_DIR/migrations/sites ]; then
   schematic migrations/sites
   checkretval
fi

# Clustering commented out because it takes too long during release.
# If urgent, start by hand (in a screen). If not urgent, wait until clustering
# cron job reoccurs.
#su - apache -s /bin/sh -c '/usr/bin/python26 /data/input/www/django/input.mozilla.com/reporter/manage.py cron cluster'

/data/input/deploy
checkretval
#/data/bin/omg_push_generic_live.sh .

#/data/bin/issue-multi-command.py generic 'service httpd reload'

