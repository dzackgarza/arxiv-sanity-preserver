#!/usr/bin/zsh
echo "Loading colors...";
autoload colors
colors

pdf_dir="/var/www/html/math-arxiv-sanity/data/pdf"

echo "Counting files...";
i=0
n=$(ls -l $pdf_dir | wc -l)
echo "$n total files."

#find ./data/pdf -iname '*.pdf' | while read -r f
#
echo "Starting...";
for f in $pdf_dir/*.pdf; do
  let 'i=i+1'
  if pdftotext "$f" &> /dev/null; then
    #mv $f ./data/processed_pdfs/$f;
    echo -n $fg[green] "$i|";
    echo $f >> goodpdfs.log;
  else
    echo $fg[red] "$i/$n: $f bad";
    echo $f >> badpdfs.log;
    # rm $f
  fi;
done

sort -u -o goodpdfs.log;
sort -u -o badpdfs.log;
