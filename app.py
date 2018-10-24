from apiserver import RequestHandler, WSGIApplication, run


class IndexHandler(RequestHandler):
    def get(self):
        print(self.get_argument('name'))
        return {'msg': 'get index'}

    def post(self):
        print(self.get_body_argument())
        return 'post index'

    def put(self):
        print(self.get_json_argument())
        return {'msg': 'put index'}


if __name__ == '__main__':
    app = WSGIApplication([('/', IndexHandler)])
    run(app=app)
