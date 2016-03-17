import os
import sys
from django.core.handlers.wsgi import WSGIHandler

reload(sys)
sys.setdefaultencoding('utf8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emsg_simple_api.settings")

application = WSGIHandler()
