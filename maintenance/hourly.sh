#!/bin/bash                                                                                          

DATE=$(date +'%Y-%m-%d')
python $PYTHONPATH/scrapers/vienna/orf_at.py $ORF_AT_PROJECT $DATE --articleset $ORF_AT_ARTICLESET
python $PYTHONPATH/scrapers/tv/teletekst.py $TELETEKST_PROJECT --articleset $TELETEKST_ARTICLESET
wait
python $PYTHONPATH/amcat/scripts/maintenance/deduplicate.py $TELETEKST_ARTICLESET
python $PYTHONPATH/amcat/scripts/maintenance/deduplicate.py $ORF_AT_ARTICLESET
wait
kill `ps -ef |grep twitter_statuses_filter|grep -v grep|awk '{print $2}'`
wait
python $PYTHONPATH/scrapers/social/twitter/twitter_statuses_filter.py $DATE
