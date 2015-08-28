#!/usr/bin/python
import sys
import base64
from datetime import datetime
from config import es as default_es

def search(field, queryStr, fields = [], es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es

    if len(queryStr) > 0:
        query = {
            "query": {
                "query_string": {
                    "fields" : [field],
                    "query": ' and  '.join(queryStr[0:]),
                }
            },
            "fields": fields
        }

        res = es.search(body=query, fields=','.join(fields[0:]), index=es_index, doc_type=es_doc_type, size=500)
        hits = res['hits']['hits']

        results = []
        for hit in hits:
            fields = hit['fields']
            fields['id'] = hit['_id']
            results.append(fields)

        return results

def multifield_query_search(s_fields, pageCount=100, fields = [], es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es

    query = None
    for field, value in s_fields.items():
        if query is None:
            query = "(" + field + ":" + value + ")"
        else:
            query = query + " AND " + "(" + field + ":" + value + ")"

    if not query is None:
        query = {
            "query": {
                "query_string": {
                    "query": query
                }
            },
            "fields": fields
        }

        res = es.search(body=query, fields=','.join(fields[0:]), index=es_index, doc_type=es_doc_type, size=pageCount)
        hits = res['hits']['hits']

        results = []
        for hit in hits:
            fields = hit['fields']
            fields['id'] = hit['_id']
            results.append(fields)

        return results

def term_search(field, queryStr, fields=[], es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es

    if len(queryStr) > 0:
        query = {
            "query" : {
                "match": {
                    field: {
                        "query": ' '.join(queryStr),
                        "minimum_should_match":"100%"
                    }
                }
            },
            "fields": fields
        }

        res = es.search(body=query, index=es_index, doc_type=es_doc_type, size=500)
        hits = res['hits']['hits']

        results = []
        for hit in hits:
            fields = hit['fields']
            fields['id'] = hit['_id']
            results.append(fields)
            
        return results


def multifield_term_search(s_fields, fields=[], es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es
        
    queries = []
    for k,v in s_fields.items():
        query = {
            "match": {
                k: {
                    "query": v,
                    "minimum_should_match":"100%"
                }
            }
        }
        queries.append(query)
        
    query = {
        "query" : {
            "bool": {
                "should": queries
            }
        },
        "fields": fields
    }
    
    res = es.search(body=query, index=es_index, doc_type=es_doc_type, size=500)
    hits = res['hits']['hits']
    
    results = []
    for hit in hits:
        fields = hit['fields']
        fields['id'] = hit['_id']
        results.append(fields)
        
    return results

def get_image(url, es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es

    if url:
        query = {
            "query": {
                "term": {
                    "url": url
                }
            },
            "fields": ["thumbnail", "thumbnail_name"]
        }
        res = es.search(body=query, index=es_index, doc_type=es_doc_type, size=500)

        hits = res['hits']['hits']
        if (len(hits) > 0):
            try:
                img = base64.b64decode(hits[0]['fields']['thumbnail'][0])
                img_name = hits[0]['fields']['thumbnail_name'][0]
                return [img_name, img]
            except KeyError:
                print "No thumbnail found"
        else:
            print "No thumbnail found"
    return [None, None]

def get_context(terms, es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es

    if len(terms) > 0:
        query = {
            "query": { 
                "match": {
                    "text": {
                        "query": ' and  '.join(terms[0:]),
                        "operator" : "and"
                    }
                }
             },
            "highlight" : {
                "fields" : {
                    "text": {
                        "fragment_size" : 100, "number_of_fragments" : 1
                    }
                }
            }
        }

        res = es.search(body=query, index=es_index, doc_type=es_doc_type, size=500)
        hits = res['hits']

        highlights = []
        for hit in hits['hits']:
            highlights.append(hit['highlight']['text'][0])
        return highlights

def range(field, from_val, to_val, ret_fields=[], epoch=None, pagesCount = 200, es_index='memex', es_doc_type='page', es=None):
    if es is None:
        es = default_es_elastic

    if not (epoch is None):
        if epoch:
            from_val = datetime.utcfromtimestamp(long(from_val/1000)).strftime('%Y-%m-%dT%H:%M:%S')
            to_val = datetime.utcfromtimestamp(long(to_val/1000)).strftime('%Y-%m-%dT%H:%M:%S')
            
    query = { 
        "query" : { 
            "range" : { 
                field : {
                    "gt": from_val,
                    "lte": to_val
                }
            },
        },
        "fields": ret_fields
    }

    res = es.search(body=query, index=es_index, doc_type=es_doc_type, size=pagesCount)
    hits = res['hits']['hits']
    
    results = []
    for hit in hits:
        fields = hit['fields']
        fields['id'] = hit['_id']
        results.append(fields)

    return results

if __name__ == "__main__":
    print sys.argv[1:]
    if 'string' in sys.argv[1]:
        print search(sys.argv[2], sys.argv[3:])
    elif 'term' in sys.argv[1]:
        for url in term_search(sys.argv[2], sys.argv[3:]):
            print url
    elif 'context' in sys.argv[1]:
        print get_context(sys.argv[2:])
    elif 'image' in sys.argv[1]:
        get_image(sys.argv[2])
    elif 'range' in sys.argv[1]:
        epoch = True
        if len(sys.argv) == 7:
            if 'False' in sys.argv[6]:
                epoch = False
        print range(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(','), epoch, es_index='memex')

