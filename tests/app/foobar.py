# Very simple WSGI application
#
# Partly inspired from <http://lucumr.pocoo.org/2007/5/21/getting-started-with-wsgi/>
from app.tasks import very_long_task, app
from cgi import parse_qs, escape
import random
import string
import logging
from operator import itemgetter
import pprint


logging.basicConfig()
logger = logging.getLogger(__name__)

TEMPLATE = '''<html>
    <body>%(body)s</body>
</html>
'''
logging.basicConfig()
logger = logging.getLogger(__name__)

TEMPLATE = '''<html>
    <body>%(body)s</body>
</html>
'''

def _render_template(params):
    '''dirty way to do template rendering, no escaping and stuffs, very insecure'''
    return TEMPLATE % params

def not_found(environ, start_response):
    """Called if no URL matches."""
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']

def taskme(env, start_response):
    # first of all, launch the long running task in background
    filename = ''.join([random.choice(string.lowercase) for _ in range(40)])
    very_long_task.delay(filename)

    # then generate the page with a simple message
    parameters = parse_qs(env.get('QUERY_STRING', ''))
    response_text = b'<p>we are generating file %s. We need only 1 minute. Come back to the <a href="/">main page</a></p>' % filename
    start_response(
        '200 OK',
        [('Content-Type','text/html')])
    return [_render_template({'body': response_text})]

def root(env, start_response):
    # then generate the page with a simple message
    parameters = parse_qs(env.get('QUERY_STRING', ''))
    response_text = b'<p>Hello %s. if you want to create a new task go <a href="/new">here</a>' % ('world' if not 'user' in parameters else escape(parameters['user'][0]))

    celery_inspect = app.control.inspect()

    response_text += '<pre>%s</pre>' % escape(pprint.pformat(celery_inspect.registered()))
    response_text += '<pre>%s</pre>' % escape(pprint.pformat(celery_inspect.active()))
    start_response(
        '200 OK',
        [('Content-Type','text/html')])
    return [_render_template({'body': response_text})]

ALLOWED_PATHS = {
    '/': root,
    '/new': taskme,
}

# https://stackoverflow.com/questions/14355409/getting-the-upload-file-content-to-wsgi
def application(env, start_response):

    # check if the PATH_INFO is correct
    path = env.get('PATH_INFO', '/')

    if path not in ALLOWED_PATHS.keys():
        return not_found(env, start_response)

    logger.info('requested path \'%s\'' % path)

    return ALLOWED_PATHS.get(path)(env, start_response)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    srv.serve_forever()

