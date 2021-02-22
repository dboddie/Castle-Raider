#!/usr/bin/env python

"""
Copyright (C) 2015 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, shutil, sys

def system(command):

    if os.system(command):
        sys.exit(1)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <version>\n" % sys.argv[0])
        sys.exit(1)
    
    version = sys.argv[1]
    release_dir = os.path.join("releases", "CastleRaider-%s" % version)
    
    if not os.path.exists(release_dir):
        os.mkdir(release_dir)
    
    build_py = os.path.join(os.curdir, "build.py")
    
    # Make cassette, ADFS, DFS and ROM versions for the Electron.
    system(build_py + " -e -t " + os.path.join(release_dir, "CastleRaider-%s-Electron.uef" % version))
    system(build_py + " -e -a " + os.path.join(release_dir, "CastleRaider-%s-Electron.adf" % version))
    system(build_py + " -e -d " + os.path.join(release_dir, "CastleRaider-%s-Electron.ssd" % version))
    system(build_py + " -e -r " + os.path.join(release_dir, "CastleRaider-%s-Electron.rom" % version))
    
    # Make cassette, DFS and ROM versions for the BBC Micro.
    system(build_py + " -b -t " + os.path.join(release_dir, "CastleRaider-%s-BBC.uef" % version))
    system(build_py + " -b -d " + os.path.join(release_dir, "CastleRaider-%s-BBC.ssd" % version))
    system(build_py + " -b -r " + os.path.join(release_dir, "CastleRaider-%s-BBC.rom" % version))

    # Make the ADFS version for the Master Compact.
    system(build_py + " -b -a " + os.path.join(release_dir, "CastleRaider-%s-Compact.adf" % version))
    
    # Copy the instructions and license files into the archive.
    shutil.copy2("README.txt", os.path.join(release_dir, "README.txt"))
    shutil.copy2("COPYING", os.path.join(release_dir, "COPYING"))
    
    # Copy an archive of the sources into the release directory.
    #system("hg archive -t files " + os.path.join(release_dir, "sources"))
    
    # Archive the release directory.
    os.chdir("releases")
    system("zip -9r CastleRaider-%s.zip CastleRaider-%s" % (version, version))
    
    sys.exit()
