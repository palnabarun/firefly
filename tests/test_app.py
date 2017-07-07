import sys
from webob import Request, Response
from firefly.app import Firefly, FireflyFunction

PY2 = (sys.version_info.major == 2)
PY3 = (sys.version_info.major == 3)

def square(a):
    '''Computes square'''
    return a**2

class TestFirefly:
    def test_generate_function_list(self):
        firefly = Firefly()
        assert firefly.generate_function_list() == {}

        firefly.add_route("/square", square, "square")
        returned_dict = {
                "square": {
                    "path": "/square",
                    "doc": "Computes square",
                    "parameters": [
                        {
                            "name": "a",
                            "kind": "POSITIONAL_OR_KEYWORD"
                        }
                    ]
                }
            }
        assert firefly.generate_function_list() == returned_dict

    def test_generate_function_list_for_func_name(self):
        firefly = Firefly()
        firefly.add_route("/sq2", square, "sq")
        returned_dict = {
                "sq": {
                    "path": "/sq2",
                    "doc": "Computes square",
                    "parameters": [
                        {
                            "name": "a",
                            "kind": "POSITIONAL_OR_KEYWORD"
                        }
                    ]
                }
            }
        assert firefly.generate_function_list() == returned_dict

    def test_function_call(self):
        app = Firefly()
        app.add_route("/", square)

        request = Request.blank("/", POST='{"a": 3}')
        response = app.process_request(request)
        assert response.status == '200 OK'
        assert response.text == '9'

    def test_auth_failure(self):
        app = Firefly(auth_token='abcd')
        app.add_route("/", square)

        request = Request.blank("/", POST='{"a": 3}')
        response = app.process_request(request)
        print(response.text)
        assert response.status == '403 Forbidden'

        headers = {
            "Authorization": "token bad-token"
        }
        request = Request.blank("/", POST='{"a": 3}', headers=headers)
        response = app.process_request(request)
        assert response.status == '403 Forbidden'

    def test_http_error_404(self):
        app = Firefly()
        app.add_route("/", square)

        request = Request.blank("/sq", POST='{"a": 3}')
        response = app.process_request(request)
        assert response.status == '404 Not Found'

class TestFireflyFunction:
    def test_call(self):
        func = FireflyFunction(square)
        request = Request.blank("/square", POST='{"a": 3}')
        response = func(request)
        assert response.status == '200 OK'
        assert response.text == '9'

    if PY2:
        def test_generate_signature(self):
            def sample_function(x, one="hey", **kwargs):
                pass
            func = FireflyFunction(sample_function)
            assert len(func.sig) == 3
            assert func.sig[0]['name'] == 'x'
            assert func.sig[0]['kind'] == 'POSITIONAL_OR_KEYWORD'
            assert func.sig[1]['name'] == 'one'
            assert func.sig[1]['kind'] == 'POSITIONAL_OR_KEYWORD'
            assert func.sig[1]['default'] == 'hey'
            assert func.sig[2]['name'] == 'kwargs'
            assert func.sig[2]['kind'] == 'VAR_KEYWORD'
    if PY3:
        def test_generate_signature_py3(self):
            # work-around to avoid syntax error in python 2
            code = 'def f(x, y=1, *, one="hey", **kwargs): pass'
            env = {}
            exec(code, env, env)
            f = env['f']

            func = FireflyFunction(f)
            assert len(func.sig) == 4
            assert func.sig[0]['name'] == 'x'
            assert func.sig[0]['kind'] == 'POSITIONAL_OR_KEYWORD'
            assert func.sig[1]['default'] == 1
            assert func.sig[2]['name'] == 'one'
            assert func.sig[2]['kind'] == 'KEYWORD_ONLY'
            assert func.sig[2]['default'] == 'hey'
            assert func.sig[3]['name'] == 'kwargs'
            assert func.sig[3]['kind'] == 'VAR_KEYWORD'
