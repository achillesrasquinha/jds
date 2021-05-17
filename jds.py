import sys
import os, os.path as osp

from gevent import monkey as curious_george
curious_george.patch_all(thread=False, select=False)

import requests as req
import grequests as greq
from bs4 import BeautifulSoup

from random_proxies import random_proxy
from fake_useragent import UserAgent

from pipupgrade.util.request import proxy_request, proxy_grequest

USER_AGENT = UserAgent()

def url_join(*paths):
    url = osp.join(*paths)
    return url

JDS_URL_BASE    = "https://www.journalofdairyscience.org"
JDS_URL_SEARCH  = url_join(JDS_URL_BASE, "action", "doSearch?text1={query}&startPage=0&pageSize=25")

def strip(string):
    return string.strip()

def greq_exception_handler(req, exception):
    print("Request %s failed with error: %s" % (req, exception))

def search(query):
    data = [ ]

    url_search  = JDS_URL_SEARCH.format(query = query)

    print("Fetching data from url...")
    response    = proxy_request("GET", url_search)
    response.raise_for_status()

    content     = response.content

    print("Formatting Data...")

    soup    = BeautifulSoup(content, 'html.parser')

    links   = [ ]
    
    for element in soup.find_all("h2", class_ = "meta__title"):
        a       = element.find("a", href = True)
        link    = "%s%s" % (JDS_URL_BASE, a["href"])

        element_data = { "title": strip(a.text), "link": link }

        links.append(link)
        data.append(element_data)

    request_map = (proxy_grequest("GET", url) for url in links)
    responses   = greq.map(request_map, exception_handler = greq_exception_handler)

    for i, response in enumerate(responses):
        if response and response.ok:
            content = response.content
            soup    = BeautifulSoup(content, "html.parser")

            references = [ ]

            for element in soup.find_all("div", class_ = "ref__title"):
                element_data = { "title": strip(element.text) }
                references.append(element_data)

            data[i]["doi"]          = strip(soup.find("a", class_ = "article-header__doi__value").text)
            data[i]["references"]   = references

    return data
    
def main(*args, **kwargs):
    code    = os.EX_OK
    
    query   = args[0]

    data    = search(query)

    from pprint import pprint
    pprint(data)

    return code

if __name__ == "__main__":
    args = sys.argv[1:]
    code = main(*args)
    sys.exit(code)