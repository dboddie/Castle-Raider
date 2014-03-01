#!/usr/bin/env python

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

class Compressor:

    def __init__(self):
    
        pass
    
    def create_index(self, data):
    
        index = {}
        i = 0
        for byte in data:
        
            index.setdefault(ord(byte), []).append(i)
            i += 1
        
        return index
    
    def compress(self, data, block_size = 256):
    
        output = ""
        i = 0
        if not 1 <= block_size <= 256:
            block_size = 256
        
        while i < len(data):
        
            # Take a maximum of 256 bytes at a time because we can't use
            # offsets larger than a byte.
            block = data[i:i + block_size]
            index = self.create_index(block)
            
            # Find the most common byte and use it as the default byte.
            items = map(lambda (value, offsets): (len(offsets), value),
                        index.items())
            items.sort()
            number, default = items.pop()
            
            # Remove the default value from the index.
            del index[default]
            
            # Count the remaining items.
            remaining = len(index)
            
            # Calculate the total size the encoded data would have.
            size = 4 + remaining + sum(map(lambda (n, v): n, items)) + 1
            if size > len(block):
            
                # Just write the data uncompressed.
                output += chr(0)
                output += chr(len(block) - 1)
                output += block
                i += len(block)
                continue
            
            # Write a value indicating that the data is compressed.
            output += chr(1)
            
            # Write the default value and the number of bytes in the block
            # minus 1.
            output += chr(default) + chr(len(block) - 1)
            
            # Write the number of entries remaining in the index minus 1.
            output += chr(remaining - 1)
            
            # Each item will be written as a value and an increasing sequence
            # of offsets. Arrange the sequence of items so that each value
            # following a sequence of offsets is lower than the last offset,
            # implicitly marking the end of the sequence.
            # We could instead write a series of descending sequences where
            # their last values are sorted in ascending order.
            
            max_offsets = map(lambda (value, offsets): (max(offsets), value),
                              index.items())
            
            max_offsets.sort()
            max_offsets.reverse()
            
            # Write the values corresponding to the entries.
            for maximum, value in max_offsets:
                output += chr(value)
            
            # Start with the last item in the sequence and work backwards.
            
            for maximum, value in max_offsets:
            
                offsets = index[value]
                
                # Write the offsets.
                for offset in offsets:
                    output += chr(offset)
            
            # Write a terminating 0 value.
            output += chr(0)
            
            i += len(block)
        
        return output
    
    def uncompress(self, data):
    
        output = ""
        i = 0
        
        while i < len(data):
        
            # Read the compression byte.
            compression = ord(data[i])
            
            if compression == 0:
            
                # Read the uncompressed data.
                length = ord(data[i + 1]) + 1
                output += data[i + 2:i + 2 + length]
                i += 2 + length
                continue
            
            # Read the default value and length minus 1.
            default, length = data[i + 1], ord(data[i + 2]) + 1
            
            # Create data for the block using the default value.
            block = [default] * length
            
            # Read the number of remaining entries minus 1.
            remaining = ord(data[i + 3]) + 1
            
            # Read the entries.
            entries = []
            i += 4
            j = 0
            while j < remaining:
            
                entries.append(data[i])
                i += 1
                j += 1
            
            # Read the offsets for each value and apply the value to those
            # entries in the block.
            for entry in entries:
            
                previous = ord(data[i])
                block[previous] = entry
                
                i += 1
                
                while True:
                
                    offset = ord(data[i])
                    if offset <= previous:
                        break
                    
                    block[offset] = entry
                    previous = offset
                    i += 1
            
            # Skip the terminating 0 byte.
            i += 1
            
            output += "".join(block)
        
        return output


if __name__ == "__main__":

    import sys
    if not 4 <= len(sys.argv) <= 5:
        sys.stderr.write("Usage: %s -c|-d [block size] <input file> <output file>\n" % sys.argv[0])
        sys.exit(1)
    
    c = Compressor()
    method = sys.argv[1]
    
    if len(sys.argv) == 4:
        size = 256
        i = 2
    else:
        size = int(sys.argv[2])
        i = 3
    
    data = open(sys.argv[i]).read()
    
    if method == "-c":
        open(sys.argv[i + 1], "w").write(c.compress(data, size))
    elif method == "-d":
        open(sys.argv[i + 1], "w").write(c.uncompress(data))
    
    sys.exit()
