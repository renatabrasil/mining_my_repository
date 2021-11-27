# from mining_my_repository.settings.servers import get_server_type
#
# # exec("from %s import *" % get_server_type())
#
#
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mining_my_repository.settings")
application = get_wsgi_application()
