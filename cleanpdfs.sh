#!/usr/bin/zsh
echo "Loading colors...";
autoload colors
colors

echo "Counting files...";
i=0
n=$(ls -l ./data/pdf | wc -l)

echo "Starting...";
find ./data/pdf -iname '*.pdf' | while read -r f
  let 'i=i+1'
  do
    if pdftotext "$f" &> /dev/null; then
      mv $f ./data/processed_pdfs;
      echo -n $fg[green] "$i|";
    else
      echo $fg[red] "$i/$n: $f bad";
      rm "$f";
    fi;
done
