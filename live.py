import os
import time
import pickle
import shutil

from utils import Config, safe_pickle_dump

db = pickle.load(open(Config.db_path, 'rb'))
pdf_have = set(os.listdir(Config.pdf_dir))
thumbnails_have = set([p[0:-4] for p in os.listdir(Config.thumbs_dir) if p.endswith(".pdf.jpg")])

dbl = list(sorted(db.values(), key = lambda v: v['updated']))
print("Latest paper: %s" % dbl[-1]['updated'])

print("Variables loaded, 'db': database, 'dbl': database sorted by updated date, 'pdf_have': contents of PDF directory, 'thumbnails_have': contents of thumbnails directory")

print("Item keys: ['id', 'guidislink', 'link', 'updated', 'updated_parsed', 'published', 'published_parsed', 'title', 'title_detail', 'summary', 'summary_detail', 'authors', 'author_detail', 'author', 'arxiv_comment', 'links', 'arxiv_primary_category', 'tags', '_rawid', '_version']")
