#!/bin/bash

# HEAVILY influenced by Brandon Rhodes pandas python tutorial
# available at https://github.com/brandon-rhodes/pycon-pandas-tutorial

FILE="data/genres.list.gz"

if [ -e "$FILE" ]
then
    echo "Already got genres"
else
    echo "Need genres"
    curl ftp://ftp.fu-berlin.de/pub/misc/movies/database/genres.list.gz -o data/genres.list.gz
fi

FILE="data/release-dates.list.gz"

if [ -e "$FILE" ]
then
    echo "Already got release dates"
else
    echo "Need release dates"
    curl ftp://ftp.fu-berlin.de/pub/misc/movies/database/release-dates.list.gz -o data/release-dates.list.gz
fi

FILE="data/writers.list.gz"

if [ -e "$FILE" ]
then
    echo "Already got writers"
else
    echo "Need writers"
    curl ftp://ftp.fu-berlin.de/pub/misc/movies/database/writers.list.gz -o data/writers.list.gz
fi

FILE="data/ratings.list.gz"

if [ -e "$FILE" ]
then
    echo "Already got ratings"
else
    echo "Need ratings"
    curl ftp://ftp.fu-berlin.de/pub/misc/movies/database/ratings.list.gz -o data/ratings.list.gz
fi

python ./parseRawFiles.py
python ./combineData.py