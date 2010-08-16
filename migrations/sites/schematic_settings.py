import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))
from migrations import db_command

db = db_command('website_issues')
table = 'schema_version'
