#!/bin/bash

mkdir -p printed

while [[ true ]]
    do
        for f in *.html
        do
          if [ "$f" != "*.html" ]
          then
            echo $f
            pdf=${f/%.html/.pdf}
            if [[ $f == match* ]]
            then
              wkhtmltopdf -O Landscape "$f" "$pdf"
              lpr -o landscape "$pdf"
            else
              wkhtmltopdf "$f" "$pdf"
              lpr "$pdf"
            fi
            #cp "$pdf" "/Volumes/Users/joze1/Dropbox/PrintQueue/"
            mv "$f" "printed/$f"
          fi
        done

        sleep 2
    done
