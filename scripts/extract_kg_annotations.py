#!env python
# -*- coding: utf-8 -*-

##### Wikipedia articles annotation script
##### Takes all articles from dump and ask Knowledge Graph for entity type
##### 2016 (c) Anatolii Stehnii <tsademon@gmail.com>

##### Usage: ./extract_kg_annotations.py wikidump_path output_path
##### Result: result file in output_path
##### Result format: %original_title%\t%query%\t%response_title%\t%categories%\t%kg_id%\t%wiki_link%\t%link%\t%score%

import sys, io, os, urllib, json, re

api_keys = [u"AIzaSyDHCunhP-oL2cXrk_Ow5MsVnYSfEEaQXBw",
        u"AIzaSyCR25QkEvLWfYUq4BNJtRqUBBWpDlveXn4",
        u"AIzaSyDjD-B3-hRHGwNhxrTH4m1NZbq5bMPQqmw"]
url = u"https://kgsearch.googleapis.com/v1/entities:search?query={0}&key={1}&limit=10&indent=True&languages=uk"
wiki_url = u"https://uk.wikipedia.org/wiki/{0}"

current_key = 0
def knowlege_query(title):
    global current_key
    query = url.format(urllib.parse.quote(title), urllib.parse.quote(api_keys[current_key]))
    try:
        with urllib.request.urlopen(query) as response:
            str_response = response.read().decode('utf-8')
            return json.loads(str_response), query
    except Exception:
        current_key += 1
        if(current_key >= len(api_keys)):
            raise Exception("No more keys!")
        else:
            return knowlege_query(title), query

def process_title(title, out_f):
    graph_result, query = knowlege_query(title)
    for item in graph_result["itemListElement"]:
        types = ""
        for type in item["result"]["@type"]:
            types += type + ","
        types = types[0:len(types)-1]

        line = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n"\
            .format(title, query, item["result"].get("name"), types, item["result"].get("@id"),
                    wiki_url.format(title), item["result"].get("url"), item["result"].get("score"))
        out_f.write(line)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: ./extract_kg_annotations.py wikidump_path output_path")
    else:
        output_path = sys.argv[2]
        titles_ready = 0
        print('Checking already processed... ')
        if(os.path.isfile(output_path)):
            with io.open(output_path, mode='r', encoding='utf-8') as out_f:
                previous_title = ""
                for line in out_f:
                    original_title = line.split("\t")[0]
                    if(original_title != previous_title):
                        previous_title = original_title
                        titles_ready += 1
        print('Done: already processed {0} articles.\n'.format(titles_ready))

        with io.open(output_path, mode='a', encoding='utf-8') as out_f:
            print('Starting annotation process from article #{0}\n'.format(titles_ready))
            current_title = 0
            with io.open(sys.argv[1], mode='r', encoding='utf-8') as wiki_f:
                for line in wiki_f:
                    match = re.search(r"<(\w+)>(.+)</\w+>", line, re.U)
                    if match:
                        tag = match.group(1)
                        if(tag == "title"):
                            title = match.group(2)
                            if(current_title >= titles_ready):
                                process_title(title, out_f)
                                if(current_title % 100 == 0):
                                    print("{0}/~613k, last {1}\n".format(current_title+1, title))

                            current_title += 1

