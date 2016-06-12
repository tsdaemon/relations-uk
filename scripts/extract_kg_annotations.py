#!env python
# -*- coding: utf-8 -*-

##### Wikipedia articles annotation script
##### Takes all articles from dump and ask Knowledge Graph for entity types
##### 2016 (c) Anatolii Stehnii <tsademon@gmail.com>

##### Usage: ./extract_kg_annotations.py api_keys_path wikidump_path output_path
##### Result: result file at output_path
##### Result format: %original_title%\t%query%\t%response_title%\t%categories%\t%kg_id%\t%wiki_link%\t%link%\t%score%

import sys, io, os, urllib.request, urllib.parse, json, re, time

api_keys = []

url = u"https://kgsearch.googleapis.com/v1/entities:search?query={0}&key={1}&limit=10&indent=True&languages=uk"
wiki_url = u"https://uk.wikipedia.org/wiki/"

current_key = 0
def knowlege_query(title):
    global current_key
    query = url.format(urllib.parse.quote(title), urllib.parse.quote(api_keys[current_key]))
    try:
        with urllib.request.urlopen(query) as response:
            str_response = response.read().decode('utf-8')
            return json.loads(str_response), query
    except Exception as e:
        current_key += 1
        if current_key >= len(api_keys):
            current_key = 0
            raise Exception("No more keys!")
        else:
            return knowlege_query(title), query

def process_title(title, out_f):
    graph_result, query = knowlege_query(title)
    for item in graph_result["itemListElement"]:
        if(knowldge_record_filter(item,title)):
            types = ""
            for type in item["result"]["@type"]:
                types += type + ","
            types = types[0:len(types)-1]

            line = "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\n"\
                .format(title,
                        query,
                        item["result"].get("name"),
                        types,
                        item["result"].get("@id"),
                        get_wiki_url(title),
                        item["result"].get("detailedDescription",{}).get("url"),
                        item["resultScore"])
            out_f.write(line)

def knowldge_record_filter(graph_result_item, title):
    return True

def get_wiki_url(title):
    return wiki_url + re.sub(r"\s", "_", title)

def read_till_title(last_title, wiki_f):
    titles = 0
    for line in wiki_f:
        match = re.search(r"<(\w+)>(.+)</\w+>", line, re.U)
        if match:
            tag = match.group(1)
            if(tag == "title"):
                titles += 1
                title = match.group(2)
                if(title == last_title):
                    return titles

def read_to_annotate(index, wiki_f):
    print('Starting annotation process from title #{0}'.format(index))
    curr_index = 0
    start = time.time()
    for line in wiki_f:
        match = re.search(r"<(\w+)>(.+)</\w+>", line, re.U)
        if match:
            tag = match.group(1)
            if(tag == "title"):
                title = match.group(2)
                try:
                    process_title(title, out_f)
                except Exception as e:
                    print(e)

                index += 1
                curr_index += 1
                if(curr_index % 100 == 0):
                    elapsed = time.time() - start
                    print("{0}/~613k, processed {1}, elapsed {2}.".format(index, curr_index, elapsed))

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: ./extract_kg_annotations.py api_keys_path wikidump_path output_path")
    else:
        # get kg keys from config file
        with io.open(sys.argv[1], mode='r', encoding='utf-8') as api_f:
            for line in api_f:
                api_keys.append(line.strip())

        output_path = sys.argv[3]
        last_title = ""
        # get last processed title to continue
        print('Checking already processed... ')
        if(os.path.isfile(output_path)):
            with io.open(output_path, mode='r', encoding='utf-8') as out_f:
                last_title = out_f.readlines()[-1].split('\t')[0]
                print('Done: last processed title is {0}.'.format(last_title))

        with io.open(output_path, mode='a', encoding='utf-8') as out_f:
            with io.open(sys.argv[2], mode='r', encoding='utf-8') as wiki_f:
                # moving wiki file position to last processed title
                index = 0
                if(len(last_title)):
                    index = read_till_title(last_title, wiki_f)

                read_to_annotate(index, wiki_f)


