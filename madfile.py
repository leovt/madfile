import struct

def read(fname):
    '''read a MADSPACK compressed file

    read the file named fname and return a list of sections as uncompressed binary data
    '''

    with open(fname, 'rb') as f:
        data = f.read()
    identifier = data[0:12]
    assert identifier == b'MADSPACK 2.0'
    assert data[12:14] == b'\x1A\x00'
    nb_sections = data[14]+256*data[15]

    section_offset = 0xB0

    sections = []

    for i in range(nb_sections):
        section_header = data[0x10+10*i: 0x1A+10*i]
        assert section_header[0] in (0, 1)
        if fname.lower().endswith('.ss'):
            assert section_header[1] == 4
        elif fname.lower().endswith('.ff'):
            assert section_header[1] == 7
        else:
            pass
            # .pik files have many different values, but
            # all sections in one file have the same value

        original_size = section_header[2]+256*section_header[3] +\
        0x10000*section_header[4] + 0x1000000 * section_header[5]
        compressed_size = section_header[6]+256*section_header[7] +\
        0x10000*section_header[8] + 0x1000000 * section_header[9]
        # print('Section', i+1, original_size, compressed_size)
        if section_header[0] == 0:
            assert original_size == compressed_size
            section_data = data[section_offset:section_offset+compressed_size]
        else:
            section_data = fabdecompress(data[section_offset:section_offset+compressed_size])
        assert len(section_data) == original_size
        section_offset += compressed_size

        sections.append(section_data)
    return sections

def write(fname, sections, header_byte_2=0):
    '''write an uncompressed madspack file containing the sections'''
    UNCOMPRESSED = 0
    with open(fname, 'wb') as f:
        f.write(b'MADSPACK 2.0\x1A\x00')
        f.write(struct.pack('<H', len(sections)))
        for sect in sections:
            f.write(struct.pack('<BBLL', UNCOMPRESSED, header_byte_2, len(sect), len(sect)))
        assert f.tell() <= 0xb0
        f.seek(0xb0)
        for sect in sections:
            f.write(sect)

def fabdecompress(data):
    '''decompress a section of compressed data'''
    #for b in data:
    #    print (b, '0x%02x' % b, format(b, '#010b'))
    assert data[:3] == b'FAB'
    shift = data[3]
    assert 10 <= shift <= 13

    read_bytes = iter(data[4:])
    read_words = ( next(read_bytes) + next(read_bytes) * 256 for _ in range(10**10))

    copy_ofs_shift = 16 - shift
    copy_ofs_mask = (255 << (shift - 8))&255
    copy_len_mask = (1 << copy_ofs_shift) - 1

    bits_left = 16
    bit_buffer = next(read_words)

    output = []

    def get_bit():
        nonlocal bits_left, bit_buffer
        assert bits_left > 0
        bit = bit_buffer & 1
        bit_buffer //= 2
        bits_left -= 1
        if bits_left == 0:
            assert bit_buffer == 0 or bit_buffer == 1
            bit_buffer = next(read_words)
            #print('buffer_charge', bin(bit_buffer))
            bits_left = 16
        return bit


    #print ('start  ', bits_left, bit_buffer)
    while True:
        if get_bit() == 0:
            if get_bit() == 0:
                #print('read 00', bits_left, bin(bit_buffer))
                copy_len = (get_bit() << 1 | get_bit()) + 2
                #print('    len', copy_len-2, bits_left, bin(bit_buffer))
                copy_ofs = next(read_bytes)
                #print('    ofs', hex(tb))
                copy_ofs -= 256 #0xffffff00+tb
            else:
                #print('read 01', bits_left, bin(bit_buffer))
                b1 = next(read_bytes)
                b2 = next(read_bytes)
                #print('    b12', hex(b1), hex(b2))
                #import pdb;pdb.set_trace()
                copy_ofs = (b2 >> copy_ofs_shift) << 8 | b1
                assert 0 <= copy_ofs < 2**shift
                copy_ofs -= 2**shift
                copy_len = b2 & copy_len_mask
                #print('    ofs', copy_ofs)
                #print('    len', copy_len)
                if copy_len == 0:
                    copy_len = next(read_bytes)
                    if copy_len == 0:
                        break
                    if copy_len == 1:
                        continue
                    copy_len += 1
                else:
                    copy_len += 2

            #print('offset', copy_ofs, hex(copy_ofs))
            while copy_len > 0:
                copy_len -= 1
                pos = len(output)
                seek = pos + copy_ofs
                read = output[seek]
                output.append(read)
        else:
            #print('read 1 ', bits_left, bin(bit_buffer))
            direct = next(read_bytes)
            #print('   dir', hex(direct))
            output.append(direct)
    return output
