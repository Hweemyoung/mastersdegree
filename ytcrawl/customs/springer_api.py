import requests

class SpringerAPIHandler:
    list_api_keys = [
        "db9bce7b96bc2ccf8490b966bdb110f4"
    ]
    url_get_path = "http://api.springernature.com/meta/v2/json"
    
    def __init__(self):
        pass

    def __build_url(self, dict_queries):
        _query_string = '&'.join(list(map(lambda _key: "%s=%s"%(_key, dict_queries[_key]), dict_queries)))
        return self.url_get_path + '?' + _query_string
        # http://api.springernature.com/meta/v2/json?q=doi:10.1038/srep07601&api_key=fb5a1e18b045e8f68ed94f53ddc2ebfb
    
    def curl_get(self, dict_queries):
        _url = self.__build_url(dict_queries)
        print("\t[+]GET: %s", _url)
        return requests.get(_url)
    
    def get_list_subjects(self, args):
        # Get subject fields for a specific record.
        # Returns str:r.status_code or list
        r = self.curl_get(args["dict_queries"])
        if not r.ok:
            return r.status_code
            
        _list_subjects = list()
        _json_get = r.json()
        for _facet in _json_get["facets"]:
            if _facet["name"] != "subject":
                continue
            
        

