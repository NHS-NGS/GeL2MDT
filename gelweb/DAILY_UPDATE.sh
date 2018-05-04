#!/bin/bash


cd $HOME
source bin/activate

cd gel2mdt/gelweb
python manage.py shell_plus < run_batch_update.py
