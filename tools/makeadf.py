"""
Copyright (C) 2014 David Boddie <david@boddie.org.uk>

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

__author__ = "David Boddie <david@boddie.org.uk>"
__date__ = "2014-04-06"
__version__ = "0.1"
__license__ = "GNU General Public License (version 3 or later)"

import StringIO
from diskutils import Directory, DiskError, File, Utilities

class Catalogue(Utilities):

    DirMarkers = ('Hugo',)
    
    def __init__(self, file):
    
        self.file = file
        self.sector_size = 256
        
        # The free space map initially contains all the space after the map
        # itself and the first directory catalogue.
        self.free_space = [(7, 1273)]
        self.level3_sector = 0
        self.disc_size = 320 * self.sector_size
        self.disc_id = 0
        self.boot_option = 0
    
    def read_free_space(self):
    
        # Using notes from http://mdfs.net/Docs/Comp/Disk/Format/ADFS
        
        self.free_space = []
        base = 0
        p = 0
        while self._read(base + p) != chr(0):
        
            self.free_space.append([self._str2num(self._read(base + p, 3))])
            p += 3
        
        # Level 3 partition sector
        level3_sector = self._read(self.sector_size - 10, 2)
        
        self.disc_size = self._str2num(self._read(self.sector_size - 4, 3))
        
        self.checksum0 = self._read_unsigned_byte(self._read(self.sector_size - 1))
        
        base = self.sector_size
        
        p = 0
        i = 0
        while self._read(base + p) != chr(0):
        
            self.free_space[i].append(self._str2num(self._read(base + p, 3)))
            p += 3
            i += 1
        
        self.disc_id = self._str2num(self._read(base + self.sector_size - 5, 2))
        
        self.boot_option = self._read_unsigned_byte(self._read(base + self.sector_size - 3))
        
        self.checksum1 = self._read_unsigned_byte(self._read(base + self.sector_size - 1))
    
    def write_free_space(self):
    
        base = 0
        
        p = 0
        for sector, length in self.free_space:
        
            if p == 0xf6:
                raise DiskError, "Too many free space entries."
            
            self._write(base + p, self._num2str(3, sector))
            p += 3
        
        while p < 0xf6:
            self._write(base + p, self._num2str(3, 0))
            p += 3
        
        # Level 3 partition sector
        self._write(self.sector_size - 10, self._num2str(2, self.level3_sector))
        
        self._write(self.sector_size - 4, self._num2str(3, self.disc_size))
        
        self.checksum0 = self._checksum(0)
        self._write(self.sector_size - 1, chr(self.checksum0))
        
        base = self.sector_size
        
        p = 0
        for sector, length in self.free_space:
        
            self._write(base + p, self._num2str(3, length))
            p += 3
        
        while p < 0xf6:
            self._write(base + p, self._num2str(3, 0))
            p += 3
        
        self._write(base + self.sector_size - 5, self._num2str(2, self.disc_id))
        
        # Boot option
        self._write(base + self.sector_size - 3, chr(self.boot_option))
        
        # Length of free space list
        self._write(base + self.sector_size - 2, chr(3 * len(self.free_space)))
        
        self.checksum1 = self._checksum(1)
        self._write(base + self.sector_size - 1, chr(self.checksum1))
    
    def read(self, offset = 512):
    
        head = offset
        p = 0
        
        dir_seq = self._read(head + p)
        dir_start = self._read(head + p + 1, 4)
        
        if dir_start not in self.DirMarkers:
            raise DiskError, "Not a directory at 0x%x" % (head + p)
        
        p = p + 5
        
        files = []
        
        while ord(self._read(head + p)) != 0:
        
            name = self._safe(self._read(head + p, 10))
            
            load = self._read_unsigned_word(self._read(head + p + 10, 4))
            exe = self._read_unsigned_word(self._read(head + p + 14, 4))
            length = self._read_unsigned_word(self._read(head + p + 18, 4))
            
            inddiscadd = self.sector_size * self._str2num(self._read(head + p + 22, 3))
            
            olddirobseq = self._read_unsigned_byte(self._read(head + p + 25))
            
            # [Needs more accurate check for directories.]
            if load == exe == 0 and length == (self.sector_size * 5):
            
                # A directory has been found.
                lower_dir_name, lower_files = self.read(inddiscadd)
                
                files.append(Directory(name, lower_files))
            
            else:
            
                # A file has been found. Treat it as unlocked for now.
                data = self._read(inddiscadd, length)
                files.append(File(name, data, load, exe, length, False,
                                  inddiscadd))
            
            p = p + 26
        
        # Go to the tail of the directory structure (0x400 - 0x500).
        
        tail = head + (self.sector_size*4)
        
        dir_end = self._read(tail + self.sector_size-5, 4)
        
        if dir_end not in self.DirMarkers:
            raise DiskError, 'Discrepancy in directory structure: [%x, %x]' % (head, tail)
        
        # Read the directory name, its parent and any title given.
        
        dir_name = self._safe(self._read(tail + self.sector_size - 52, 10))
        
        parent = self.sector_size * \
            self._str2num(self._read(tail + self.sector_size - 42, 3))
        
        dir_title = self._safe(self._read(tail + self.sector_size - 39, 19))
        
        endseq = self._read(tail + self.sector_size - 6)
        
        if endseq != dir_seq:
            raise DiskError, 'Broken directory: %s at [%x, %x]' % (dir_title, head, tail)
        
        return dir_name, files
    
    def write(self, dir_name, dir_title, files, offset, parent_address):
    
        if len(files) > 47:
            raise DiskError, "Too many entries to write."
        
        head = offset
        p = 0
        
        dir_seq = (self._read_unsigned_byte(self._read(head + p)) + 1) % 256
        self._write(head + p, chr(dir_seq))
        
        dir_start = self._read(head + p + 1, 4)
        
        if dir_start not in self.DirMarkers:
            dir_start = "Hugo"
            self._write(head + p + 1, dir_start)
        
        p = p + 5
        i = 1
        
        for file in files:
        
            name = map(ord, self._pad(file.name, 10, " "))
            # Readable, publicly readable
            name[0] |= 0x80
            name[5] |= 0x80
            self._write(head + p, "".join(map(chr, name)))
            
            if isinstance(file, File):
                load = file.load_address
                exe = file.execution_address
                length = file.length
            else:
                load = exe = 0
                length = 5 * self.sector_size
            
            self._write(head + p + 10, self._write_unsigned_word(load))
            self._write(head + p + 14, self._write_unsigned_word(exe))
            self._write(head + p + 18, self._write_unsigned_word(length))
            
            disc_address = self._find_space(file)
            inddiscadd = disc_address / self.sector_size
            self._write(head + p + 22, self._num2str(3, inddiscadd))
            
            self._write(disc_address, file.data)
            
            olddirobseq = i
            self._write(head + p + 25, chr(olddirobseq))
            
            if isinstance(file, Directory):
                self.write(file.files, disc_address)
            
            p = p + 26
        
        # Go to the tail of the directory structure (0x400 - 0x500).
        
        tail = head + (self.sector_size*4)
        
        dir_end = self._read(tail + self.sector_size - 5, 4)
        
        if dir_end not in self.DirMarkers:
            dir_end = "Hugo"
            self._write(tail + self.sector_size - 5, dir_end)
        
        # Write the directory name, its parent and any title given.
        
        dir_name = self._pad(self._safe(dir_name), 10, " ")
        self._write(tail + self.sector_size - 52, dir_name)
        
        self._write(tail + self.sector_size - 42,
                    self._num2str(3, parent_address / self.sector_size))
        
        dir_title = self._pad(self._safe(dir_title), 19, " ")
        self._write(tail + self.sector_size - 39, dir_title)
        
        endseq = dir_seq
        self._write(tail + self.sector_size - 6, chr(endseq))
    
    def _find_space(self, file):
    
        for i in range(len(self.free_space)):
        
            sector, length = self.free_space[i]
            file_length = file.length/self.sector_size
            
            if file.length % self.sector_size != 0:
                file_length += 1
            
            if length >= file_length:
            
                if length > file_length:
                    # Update the free space entry to contain the remaining space.
                    self.free_space[i] = (sector + file_length, length - file_length)
                else:
                    # Remove the free space entry.
                    del self.free_space[i]
                
                return sector * self.sector_size
        
        raise DiskError, "Failed to find space for file: %s" % file.name
    
    def _checksum(self, sector):
    
        v = 255
        i = 254
        while i >= 0:
            if v > 255:
                v = (v + 1) & 255
            v += ord(self._read((sector * self.sector_size) + i))
            i -= 1
        
        return v & 255


class Disk:

    DiskSizes = {"M": 327680}
    SectorSizes = {"M": 256}
    Catalogues = {"M": Catalogue}
    
    def __init__(self, format):
    
        self.format = format
    
    def new(self):
    
        self.size = self.DiskSizes[self.format]
        self.data = "\x00" * self.size
        self.file = StringIO.StringIO(self.data)
    
    def open(self, file_object):
    
        self.size = self.DiskSizes[self.format]
        self.file = file_object
    
    def catalogue(self):
    
        sector_size = self.SectorSizes[self.format]
        return self.Catalogues[self.format](self.file)
