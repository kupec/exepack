#!/usr/bin/env python3
import sys
from struct import unpack_from, pack_into


MZ_RELOCATION_COUNT = 0x06
MZ_HEADER_SIZE = 0x08
MZ_SS = 0x0E
MZ_SP = 0x10
MZ_IP = 0x14
MZ_CS = 0x16
MZ_RELOCATION_OFFSET = 0x18

EXEPACK_HEADER_SIZE = 0x10
EXEPACK_IP = 0x00
EXEPACK_CS = 0x02
EXEPACK_SP = 0x08
EXEPACK_SS = 0x0A
EXEPACK_RELOCATION_OFFSET = 0x132

def unpack_word(buffer, offset):
    x, = unpack_from('<H', buffer, offset)
    return x

def pack_word(buffer, offset, word):
    pack_into('<H', buffer, offset, word)

def unpack_body(packed_body):
    tail_align = 0
    for i in range(len(packed_body)):
        if packed_body[-i-1] != 0xFF:
            tail_align = i
            break
    remain_bytes = packed_body[0:len(packed_body)-tail_align]

    print(f'tail_align = {tail_align:x}')
    print(f'packed data length = {len(packed_body):x}')

    unpacked_chunks = []
    is_end = 0

    while not is_end and len(remain_bytes) > 0:
        code = remain_bytes[-1]
        is_end = code & 1
        operation = code & 0xFE
        print('code', operation)

        if operation == 0xB0:
            count = unpack_word(remain_bytes, -3)
            fill_byte = remain_bytes[-4]
            chunk = bytes([fill_byte] * count)
            remain_bytes = remain_bytes[0:-4]
        elif operation == 0xB2:
            count = unpack_word(remain_bytes, -3)
            chunk = remain_bytes[-3-count:-3]
            remain_bytes = remain_bytes[0:-3-count]
        else:
            raise ValueError(f'File is corrupted. We expect 0xB0 or 0xB2 codes but found byte={code}')

        unpacked_chunks.insert(0, chunk)

    if len(remain_bytes) > 0:
        unpacked_chunks.insert(0, remain_bytes)

    return bytes().join(unpacked_chunks)


def unpack_relocation_table(table, header):
    entries = []

    index = 0
    header_offset = unpack_word(header, MZ_RELOCATION_OFFSET)
    reloc_count = 0
    for seg in range(0x10):
        count = unpack_word(table, index)
        index += 2
        for i in range(count):
            addr_offset = unpack_word(table, index)
            index += 2
            pack_word(header, header_offset, addr_offset)
            pack_word(header, header_offset + 2, seg << 12)
            header_offset += 4
        reloc_count += count

    pack_word(header, MZ_RELOCATION_COUNT, reloc_count)



def unpack(input_image):
    header_size = unpack_word(input_image, MZ_HEADER_SIZE) << 4
    header = bytearray(input_image[0:header_size])
    exepack_cs = unpack_word(header, MZ_CS)
    exepack_unpacker_offset = header_size + (exepack_cs << 4)
    exepack_header = input_image[exepack_unpacker_offset:exepack_unpacker_offset + EXEPACK_HEADER_SIZE]
    exepack_relocation_table = input_image[exepack_unpacker_offset + EXEPACK_RELOCATION_OFFSET:]

    print(f'header_size = {header_size:x}')
    print(f'exepack_cs = {exepack_cs:x}')
    print(f'exepack_unpacker_offset = {exepack_unpacker_offset:x}')

    packed_body = input_image[header_size:exepack_unpacker_offset]
    unpacked_body = unpack_body(packed_body)

    pack_word(header, MZ_CS, unpack_word(exepack_header, EXEPACK_CS))
    pack_word(header, MZ_IP, unpack_word(exepack_header, EXEPACK_IP))
    pack_word(header, MZ_SS, unpack_word(exepack_header, EXEPACK_SS))
    pack_word(header, MZ_SP, unpack_word(exepack_header, EXEPACK_SP))

    unpack_relocation_table(exepack_relocation_table, header)

    return bytes().join([header, unpacked_body])


def print_error(error):
    print(error, file=sys.stderr)


def usage():
    print_error(f'USAGE: {sys.argv[0]} EXE')
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        return usage()

    input_exe = args[0]
    output_exe = input_exe + '.unpacked';

    with open(input_exe, 'rb') as f:
        input_image = f.read()
    output_image = unpack(input_image)
    with open(output_exe, 'wb') as f:
        f.write(output_image)


if __name__ == '__main__':
    main()
