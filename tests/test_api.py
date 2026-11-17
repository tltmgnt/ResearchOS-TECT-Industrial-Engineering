import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from researchos.core import Store
from researchos.server import handler


class APITests(unittest.TestCase):
    def setUp(self):
        self.store=Store(':memory:')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.store,{'researcher':'research-key','reviewer':'review-key'}))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.store.close()

    def request(self,path, data=None, token='research-key'):
        request=urllib.request.Request(self.url+path, data=json.dumps(data).encode() if data is not None else None,
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status,json.load(response)
        except urllib.error.HTTPError as error:
            return error.code,json.load(error)

    def test_authenticated_workflow_and_role_spoofing(self):
        self.assertEqual(self.request('/api/claims',token='wrong')[0],403)
        status,c=self.request('/api/claims',{'statement':'capacity claim','provenance':'fixture'})
        self.assertEqual(status,201)
        status,result=self.request('/api/claims/'+c['id']+'/transition',{'target':'ASSURED','role':'admin'})
        self.assertEqual(status,409)
        self.assertFalse(result['accepted'])
        self.assertEqual(self.request('/api/claims/'+c['id']+'/check',{'role':'reviewer'})[0],403)
        self.assertEqual(self.request('/api/claims/'+c['id']+'/assurance')[1]['claim']['id'],c['id'])
        self.assertTrue(self.request('/api/ledger')[1]['valid'])

    def test_errors_and_static_assets(self):
        self.assertEqual(self.request('/api/claims/no-such-id')[0],404)
        self.assertEqual(self.request('/api/claims',{'statement':'','provenance':'test'})[0],400)
        self.assertEqual(self.request('/not-found')[0],404)
        with urllib.request.urlopen(self.url) as response:
            self.assertIn(b'ResearchOS',response.read())
            self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])


if __name__ == '__main__':
    unittest.main()
