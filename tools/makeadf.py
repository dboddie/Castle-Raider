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

import StringIO, struct, time

class DiskError(Exception):
    pass


class Utilities:

    # Little endian reading
    
    def _read_signed_word(self, s):
    
        return struct.unpack("<i", s)[0]
    
    def _read_unsigned_word(self, s):
    
        return struct.unpack("<I", s)[0]
    
    def _read_signed_byte(self, s):
    
        return struct.unpack("<b", s)[0]
    
    def _read_unsigned_byte(self, s):
    
        return struct.unpack("<B", s)[0]
    
    def _read_unsigned_half_word(self, s):
    
        return struct.unpack("<H", s)[0]
    
    def _read_signed_half_word(self, s):
    
        return struct.unpack("<h", s)[0]
    
    def _read(self, offset, length = 1):
    
        self.file.seek(offset, 0)
        return self.file.read(length)
    
    def _write(self, offset, data):
    
        self.file.seek(offset, 0)
        self.file.write(data)
    
    def _str2num(self, s):
    
        i = 0
        n = 0
        while i < len(s):
        
            n = n | (ord(s[i]) << (i*8))
            i = i + 1
        
        return n
    
    def _binary(self, size, n):
    
        new = ""
        while (n != 0) & (size > 0):
        
            if (n & 1)==1:
                new = "1" + new
            else:
                new = "0" + new
            
            n = n >> 1
            size = size - 1
        
        if size > 0:
            new = ("0"*size) + new
        
        return new
    
    def _safe(self, s, with_space = 0):
    
        new = ""
        if with_space == 1:
            lower = 31
        else:
            lower = 32
        
        for c in s:
        
            if ord(c) >= 128:
                i = ord(c) ^ 128
                c = chr(i)
            
            if ord(c) <= lower:
                break
            
            new = new + c
        
        return new


class Directory:

    """directory = Directory(name, address)
    
    The directory created contains name and files attributes containing the
    directory name and the objects it contains.
    """
    
    def __init__(self, name, files):
    
        self.name = name
        self.files = files
    
    def __repr__(self):
    
        return '<%s instance, "%s", at %x>' % (self.__class__, self.name, id(self))


class File:

    """file = File(name, data, load_address, execution_address, length)
    """
    
    def __init__(self, name, data, load_address, execution_address, length):
    
        self.name = name
        self.data = data
        self.load_address = load_address
        self.execution_address = execution_address
        self.length = length
    
    def __repr__(self):
    
        return '<%s instance, "%s", at %x>' % (self.__class__, self.name, id(self))
    
    def has_filetype(self):
    
        """Returns True if the file's meta-data contains filetype information."""
        return self.load_address & 0xfff00000 == 0xfff00000
    
    def filetype(self):
    
        """Returns the meta-data containing the filetype information.
        
        Note that a filetype can be obtained for all files, though it may not
        necessarily be valid. Use has_filetype() to determine whether the file
        is likely to have a valid filetype."""
        
        return "%03x" % ((self.load_address >> 8) & 0xfff)
    
    def time_stamp(self):
    
        """Returns the time stamp for the file as a tuple of values containing
        the local time, or an empty tuple if the file does not have a time stamp."""
        
        # RISC OS time is given as a five byte block containing the
        # number of centiseconds since 1900 (presumably 1st January 1900).
        
        # Convert the time to the time elapsed since the Epoch (assuming
        # 1970 for this value).
        date_num = struct.unpack("<Q",
            struct.pack("<IBxxx", self.execution_address, self.load_address & 0xff))[0]
        
        centiseconds = date_num - between_epochs
        
        # Convert this to a value in seconds and return a time tuple.
        try:
            return time.localtime(centiseconds / 100.0)
        except ValueError:
            return ()


class Catalogue(Utilities):

    DirMarkers = ('Hugo',)
    
    def __init__(self, file):
    
        self.file = file
        self.sector_size = 256
    
    def read_free_space(self):
    
        # Currently unused
        
        base = 0
        free_space = []
        p = 0
        while self._read(base + p) != chr(0):
        
            free_space.append(self._str2num(self._read(base + p, 3)))
            p += 3
        
        name = self._read(self.sector_size - 9, 5)
        
        disc_size = self._str2num(self._read(self.sector_size - 4, 3))
        
        checksum0 = self._read_unsigned_byte(self._read(self.sector_size-1))
        
        base = self.sector_size
        
        p = 0
        while self._read(base + p) != chr(0):
        
            free_space.append(self._str2num(self._read(base + p, 3)))
            p += 3
        
        name = name + self._read(base + self.sector_size - 10, 5)
        
        disc_id = self._str2num(self._read(base + self.sector_size - 5, 2))
        
        boot = self._read_unsigned_byte(self._read(base + self.sector_size - 3))
        
        checksum1 = self._read_unsigned_byte(self._read(base + self.sector_size - 1))
        
        return free_space
    
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
            
            print hex(head + p), name, map(hex, (load, exe, length, inddiscadd))
            
            olddirobseq = self._read_unsigned_byte(self._read(head + p + 25))
            
            # [Needs more accurate check for directories.]
            if length == (self.sector_size * 5):
            
                # A directory has been found.
                lower_dir_name, lower_files = self.read(inddiscadd)
                print "Entering", lower_dir_name
                
                files.append(Directory(name, lower_files))
            
            else:
            
                # A file has been found.
                data = self._read(inddiscadd, length)
                files.append(File(name, data, load, exe, length))
            
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
    
    def write(self, files, offset = 512):
    
        head = offset
        p = 0
        
        dir_seq = (self._read_unsigned_byte(self._read(head + p)) + 1) % 256
        self._write(head + p, chr(dir_seq))
        
        dir_start = self._read(head + p + 1, 4)
        
        if dir_start not in self.DirMarkers:
            dir_start = "Hugo"
            self._write(head + p + 1, dir_start)
        
        p = p + 5
        
        files = []
        
        while ord(self._read(head + p)) != 0:
        
            old_name = self.data[head+p:head+p+10]
            top_set = 0
            counter = 1
            for i in old_name:
                if (ord(i) & 128) != 0:
                    top_set = counter
                counter = counter + 1
            
            name = self._safe(self.data[head+p:head+p+10])
            
            load = self._read_unsigned_word(self.data[head+p+10:head+p+14])
            exe = self._read_unsigned_word(self.data[head+p+14:head+p+18])
            length = self._read_unsigned_word(self.data[head+p+18:head+p+22])
            
            inddiscadd = self.sector_size * self._str2num(
                3, self.data[head+p+22:head+p+25]
                )
            
            olddirobseq = self._read_unsigned_byte(self.data[head+p+25])
            
            # [Needs more accurate check for directories.]
            if (load == 0 and exe == 0 and top_set > 2) or \
                (top_set > 0 and length == (self.sector_size * 5)):
            
                # A directory has been found.
                lower_dir_name, lower_files = \
                    self._read_old_catalogue(inddiscadd)
                
                files.append(Directory(name, lower_files))
            
            else:
            
                # A file has been found.
                data = self.data[inddiscadd:inddiscadd+length]
                files.append(File(name, data, load, exe, length))
            
            p = p + 26
        
        # Go to the tail of the directory structure (0x400 - 0x500).
        
        tail = head + (self.sector_size*4)
        
        dir_end = self.data[tail+self.sector_size-5:tail+self.sector_size-1]
        
        if dir_end not in self.DirMarkers:
            raise DiskError, 'Discrepancy in directory structure: [%x, %x]' % (head, tail)
        
        # Read the directory name, its parent and any title given.
        
        dir_name = self._safe(
            self.data[tail+self.sector_size-52:tail+self.sector_size-42]
            )
        
        parent = self.sector_size*self._str2num(
            3,
            self.data[tail+self.sector_size-42:tail+self.sector_size-39]
            )
        
        dir_title = self._safe(
            self.data[tail+self.sector_size-39:tail+self.sector_size-20]
            )
        
        endseq = self.data[tail+self.sector_size-6]
        
        if endseq != dir_seq:
            raise DiskError, 'Broken directory: %s at [%x, %x]' % (dir_title, head, tail)
        
        return dir_name, files


class Disk:

    DiskSizes = {"M": 327680}
    SectorSizes = {"M": 256}
    Catalogues = {"M": Catalogue}
    
    def __init__(self, format):
    
        self.format = format
    
    def new(self):
    
        self.size = self.DiskSizes[self.format]
        self.data = "\x00" * size
        self.file = StringIO.StringIO(self.data)
    
    def open(self, file_object):
    
        self.size = self.DiskSizes[self.format]
        self.file = file_object
    
    def read_catalogue(self):
    
        sector_size = self.SectorSizes[self.format]
        catalogue = self.Catalogues[self.format](self.file)
        return catalogue.read()
