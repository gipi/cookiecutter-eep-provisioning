# Very simple WSGI application
#
# Partly inspired from <http://lucumr.pocoo.org/2007/5/21/getting-started-with-wsgi/>
from app.tasks import very_long_task
from cgi import parse_qs, escape
import random
import string
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)


# https://stackoverflow.com/questions/14355409/getting-the-upload-file-content-to-wsgi
def application(env, start_response):
    # first of all, launch the long running task in background
    filename = ''.join([random.choice(string.lowercase) for _ in range(40)])
    very_long_task.delay(filename)

    # then generate the page with a simple message
    parameters = parse_qs(env.get('QUERY_STRING', ''))
    response_text = b'Hello %s: we are generating file %s. We need only 1 minute.' % ('world' if not 'user' in parameters else escape(parameters['user'][0]), filename)
    start_response(
        '200 OK',
        [('Content-Type','text/html')])
    return [response_text]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    srv.serve_forever()
