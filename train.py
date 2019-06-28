#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import glob
import sys
import subprocess
import shutil as sh

# Note:
# /usr/share/tesseract-ocr/tessdata
# /usr/share/openalpr/runtime_data

# Execute shell command
def do(command):
    print(command)
    try:
        r = subprocess.run(command, shell=True).returncode
        if r != 0:
            raise("%s => %d" % (command, r))
    except Exception as e:
        print(e)
        sys.exit(1)

# Command locations
tesseract = sh.which('tesseract')
unicharset_extractor = sh.which('unicharset_extractor')
mftraining = sh.which('mftraining')
cntraining = sh.which('cntraining')
combine_tessdata = sh.which('combine_tessdata')
if not all([tesseract, unicharset_extractor, mftraining, cntraining, combine_tessdata]):
    print('Command not found.')
    sys.exit(0)

country = input("Two-Letter Country Code to Train: ").lower()
lang = 'l' + country

box_files = glob.glob('./' + country + '/input/*.box')
if not box_files:
    print("Cannot find input files")
    sys.exit(1)

for f in glob.glob('./tmp/*'):
    os.remove(f)

with open('./tmp/font_properties','w') as f:

    for box_file in box_files:
        print("Processing: " + box_file)

        file_without_dir = os.path.split(box_file)[1]
        file_without_ext = os.path.splitext(file_without_dir)[0]
        input_dir = os.path.dirname(box_file)
        tif_file = input_dir + '/' + file_without_ext + ".tif"

        if do('%s %s %s -l jpn nobatch box.train.stderr' % (tesseract, tif_file, file_without_ext)):
            sys.exit(1)
        if os.path.exists("./" + file_without_ext + ".tr"):
            sh.move("./" + file_without_ext + ".tr", "./tmp/" + file_without_ext + ".tr")
        if os.path.exists("./" + file_without_ext + ".txt"):
            sh.move("./" + file_without_ext + ".txt", "./tmp/" + file_without_ext + ".txt")

        font_name=file_without_dir.split('.')[1]
        f.write(font_name + ' 0 0 1 0 0\n')

do('%s ./%s/input/*.box' % (unicharset_extractor, country))

# Shape clustering should currently only be used for the "indic" languages
#train_cmd = TESSERACT_TRAINDIR + '/shapeclustering -F ./' + country + '/input/font_properties -U unicharset ./' + country + '/input/*.tr'
#print "Executing: " + train_cmd
#do(train_cmd)

do('%s -F ./tmp/font_properties -U unicharset -O ./tmp/%s.unicharset ./tmp/*.tr' % (mftraining, lang))
os.remove('./unicharset')
sh.move('./tmp/%s.unicharset' % lang, './%s.unicharset' % lang)

do('%s ./tmp/*.tr' % cntraining)
sh.move("./shapetable", "./" + lang + ".shapetable")
sh.move("./pffmtable", "./" + lang + ".pffmtable")
sh.move("./inttemp", "./" + lang + ".inttemp")
sh.move("./normproto", "./" + lang + ".normproto")

do('%s %s.' % (combine_tessdata, lang))

config_file = os.path.join('./', country, country + '.config')
if os.path.isfile(config_file):
    # If a config file is in the country's directory, use that.
    do('%s -o %s.traineddata %s' % (combine_tessdata, lang, config_file))

sh.move("./" + lang + ".unicharset", "./tmp/")
sh.move("./" + lang + ".shapetable", "./tmp/")
sh.move("./" + lang + ".pffmtable", "./tmp/")
sh.move("./" + lang + ".inttemp", "./tmp/")
sh.move("./" + lang + ".normproto", "./tmp/")

sys.exit(0)

