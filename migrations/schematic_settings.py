import sys
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from migrations import db_command

db = db_command('default')
table = 'schema_version'
