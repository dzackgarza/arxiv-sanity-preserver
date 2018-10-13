#!/usr/bin/python3
"""
Queries arxiv API and downloads papers (the query is a parameter).
The script is intended to enrich an existing database pickle (by default db.p),
so this file will be loaded first, and then new results will be added to it.
"""

import os
import sys
import yaml
import time
import pickle
import random
import argparse
import feedparser
import urllib.request
from termcolor import colored

from utils import Config, safe_pickle_dump

printgreen = lambda q: print(colored(q, 'green'))
printred = lambda q: print(colored(q, 'red'))

def encode_feedparser_dict(d):
  """
  helper function to get rid of feedparser bs with a deep copy.
  """
  if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
    j = {}
    for k in d.keys():
      j[k] = encode_feedparser_dict(d[k])
    return j
  elif isinstance(d, list):
    l = []
    for k in d:
      l.append(encode_feedparser_dict(k))
    return l
  else:
    return d

def parse_arxiv_url(url):
  """
  examples is http://arxiv.org/abs/1512.08756v2
  we want to extract the raw id and the version
  """
  ix = url.rfind('/')
  idversion = url[ix+1:] # extract just the id (and the version)
  parts = idversion.split('v')
  assert len(parts) == 2, 'error parsing url ' + url
  return parts[0], int(parts[1])

if __name__ == "__main__":
  with open('categories.yaml') as stream:
    s = yaml.load(stream)
  cats = '+OR+'.join(['cat:{}'.format(i) for i in s])

  # parse input arguments
  parser = argparse.ArgumentParser()
  parser.add_argument('--search-query', type=str,
                      default=cats,
                      help='query used for arxiv API. See http://arxiv.org/help/api/user-manual#detailed_examples')
  parser.add_argument('--start-index', type=int, default=0, help='0 = most recent API result')
  parser.add_argument('--max-index', type=int, default=1000, help='upper bound on paper index we will fetch')
  parser.add_argument('--results-per-iteration', type=int, default=100, help='passed to arxiv API')
  parser.add_argument('--wait-time', type=float, default=5.0, help='lets be gentle to arxiv API (in number of seconds)')
  parser.add_argument('--break-on-no-added', type=int, default=1, help='break out early if all returned query papers are already in db? 1=yes, 0=no')
  args = parser.parse_args()

  # misc hardcoded variables
  base_url = 'http://export.arxiv.org/api/query?' # base api query url
  print('Searching arXiv for %s' % (args.search_query, ))

  # lets load the existing database to memory
  try:
    db = pickle.load(open(Config.db_path, 'rb'))
  except Exception as e:
    print('error loading existing database:')
    print(e)
    print('starting from an empty database')
    db = {}

  # -----------------------------------------------------------------------------
  # main loop where we fetch the new results
  print('database has %d entries at start' % (len(db), ))
  num_added_total = 0
  i = args.start_index
  incremental_sleep_time = 0
  sleeptime = 0
  while (i <= args.max_index):
    try:
      print("Results %i - %i" % (i,i+args.results_per_iteration))
      query = 'search_query=%s&sortBy=lastUpdatedDate&start=%i&max_results=%i' % (args.search_query,
                                                         i, args.results_per_iteration)

      print(base_url+query)

      with urllib.request.urlopen(base_url+query) as url:
        response = url.read()
      parse = feedparser.parse(response)
      num_added = 0
      num_skipped = 0

      if len(parse.entries) == 0:
        print(response)
        raise ValueError('No entries received from Arxiv, possibly due to rate limiting. Index: {}'.format(i))
      else:
        print("Entries found: {}".format(len(parse.entries)))

      for e in parse.entries:
        j = encode_feedparser_dict(e)
        # extract just the raw arxiv id and version for this paper
        rawid, version = parse_arxiv_url(j['id'])
        j['_rawid'] = rawid
        j['_version'] = version

        # add to our database if we didn't have it before, or if this is a new version
        with open('arxiv-log.txt', 'a') as outlog:
          if not rawid in db or j['_version'] > db[rawid]['_version']:
            db[rawid] = j
            outlog.write('Updated %s added %s\n' % (j['updated'].encode('utf-8'), j['title'].encode('utf-8')))
            num_added += 1
            num_added_total += 1
          else:
            num_skipped += 1

      # print some information
      if num_added > 0:
        printgreen('Added %d papers, %d were already in database.' % (num_added, num_skipped))
        printgreen('Saving database with %d papers to %s' % (len(db), Config.db_path))
        safe_pickle_dump(db, Config.db_path)
      else:
        printred('Warning: no new papers were added!')

      i = i + args.results_per_iteration
      incremental_sleep_time = 0

      sleeptime = args.wait_time + random.uniform(0,30)
      printgreen('Success, sleeping for {} seconds'.format(sleeptime))
      time.sleep(sleeptime)

    except ValueError as e:
      incremental_sleep_time = incremental_sleep_time + 15
      sleeptime = args.wait_time + incremental_sleep_time + random.uniform(0,30)
      print(e)
      printred("Error, sleeping for {} seconds.".format(sleeptime))
      time.sleep(sleeptime)
    except KeyboardInterrupt:
        if num_added_total > 0:
            printgreen('Saving database with %d papers to %s' % (len(db), Config.db_path))
            safe_pickle_dump(db, Config.db_path)
        else:
            printred("No new papers added to database.")
        print("Exiting.")
        sys.exit()

