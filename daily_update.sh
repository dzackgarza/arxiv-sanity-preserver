#!/bin/bash

set -e

export NVM_DIR="/home/zack/.nvm "
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

echo $(date +%x_%H:%M:%S:%N)
SECONDS=0

python3 fetch_papers.py
#python3 download_pdfs.py &&
python3 tor_download.py
python3 parse_pdf_to_text.py
find ./data/pdf -name "*.txt" -exec mv -t ./data/txt {} +
find ./data -size 0 -type f -delete
python3 thumb_pdf.py
python3 analyze.py
python3 buildsvm.py
python3 make_cache.py
find ./data -size 0 -type f -delete

pm2 reload serve
echo $(date +%x_%H:%M:%S:%N)
echo "DONE"
echo $SECONDS
