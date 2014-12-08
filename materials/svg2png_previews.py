#!/usr/bin/env python

import glob, os, sys

if __name__ == "__main__":

    if not 1 <= len(sys.argv) <= 2:
    
        sys.stderr.write("Usage: %s [resolution in dpi]\n" % sys.argv[0])
        sys.exit(1)
    
    elif len(sys.argv) == 2:
        resolution = int(sys.argv[1])
    else:
        resolution = 144
    
    if not os.path.exists("png"):
        os.mkdir("png")
    
    for i in range(4):
        os.system("inkscape -e png/page-%i.png -d %i -y 255 svg/page-%i.svg" % (i, resolution, i))
    
    for name in glob.glob("svg/*-inlay.svg"):
        os.system("inkscape -e %s -d %i -y 255 %s" % (name.replace("svg", "png"), resolution, name))
        
    sys.exit()
