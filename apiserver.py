import logging
import traceback
import json
import http
from cgi import parse_qs, FieldStorage
from wsgiref.simple_server import make_server


class HTTPError(Exception):
    def __init__(self, status, text=None):
        self.status = status
        self.text = text


class RequestHandler:
    def __init__(self, application, request, environ):
        self.application = application
        self.request = request
        self.environ = environ

    def get(self, *args, **Kwargs):
        raise HTTPError(405)

    def post(self, *args, **Kwargs):
        raise HTTPError(405)

    def put(self, *args, **Kwargs):
        raise HTTPError(405)

    def delete(self, *args, **Kwargs):
        raise HTTPError(405)

    def get_argument(self, name=None):
        argument = parse_qs(self.environ.get('QUERY_STRING', {}))
        if name is not None:
            return argument.get(name, [None])[0]
        return argument

    def get_json_argument(self, name=None):
        content_length = int(self.environ.get('CONTENT_LENGTH', 0))
        raw_data = self.environ.get('wsgi.input').read(content_length)
        data = json.loads(raw_data)
        if name is not None:
            return data.get(name)

        return data

    def get_body_argument(self, name=None):
        raw_data = FieldStorage(
            fp=self.environ.get('wsgi.input'),
            environ=self.environ,
            keep_blank_values=1)

        data = {}
        for key in raw_data:
            if isinstance(raw_data[key], list):
                data[key] = [v.value for v in raw_data[key]]
            else:
                data[key] = raw_data[key].value

        if name is not None:
            return data.get(name, None)

        return data

    def set_status(self, status_code):
        self.request.status_code = status_code


class HTTPRequest:
    def __init__(self, environ):
        self.method = environ['REQUEST_METHOD']
        self.PATH_INFO = environ['PATH_INFO']
        self.status_code = 200


class WSGIApplication:
    def __init__(self, handlers):
        self.handlers = handlers
        self.route_handlers = {}
        self.add_handlers()

    def add_handlers(self):
        for handler in self.handlers:
            self.route_handlers[handler[0]] = handler[1]

    def __call__(self, environ, start_response):
        request = HTTPRequest(environ)

        try:
            handler = self.route_handlers.get(request.PATH_INFO)
            if not handler:
                raise HTTPError(404)

            output = getattr(
                handler(self, request, environ), request.method.lower())()
            status_code = request.status_code
        except Exception as e:
            logging.warning(traceback.format_exc())
            if isinstance(e, HTTPError):
                output = 'HTTP {status}: {text}'.format(
                    status=e.status,
                    text=e.text or http.HTTPStatus(e.status).phrase)
                status_code = e.status
            else:
                output = 'HTTP {status}: {text}'.format(
                    status=500, text=http.HTTPStatus(500).phrase)
                status_code = 500

        header = ('Content-Type', 'text/html; charset=UTF-8')

        if isinstance(output, dict):
            header = ('Content-Type', 'application/json; charset=UTF-8')
            output = json.dumps(output)

        # to bytes
        if isinstance(output, str):
            output = str.encode(output)

        status = '{code} {desc}'.format(
            code=status_code, desc=http.HTTPStatus(status_code).phrase)
        response_headers = [header]
        start_response(status, response_headers)

        yield output


class ServerAdapter:
    def __init__(self, host='127.0.0.1', port=9000, **kwargs):
        self.host = host
        self.port = int(port)
        self.options = kwargs

    def __repr__(self):
        return "%s (%s:%d)" % (self.__class__.__name__, self.host, self.port)

    def run(self, handler):
        pass


class WSGIRefServer(ServerAdapter):
    def run(self, handler):
        with make_server(self.host, self.port, handler) as httpd:
            httpd.serve_forever()


class BjoernServer(ServerAdapter):
    def run(self, handler):
        from bjoern import run
        run(handler, self.host, self.port)


def run(server=WSGIRefServer, host='localhost', port=9000, app=None):
    httpd = server(host=host, port=port)
    httpd.run(app)
