#!/usr/bin/env python3
import sys


def unpack(input_image):
    # TODO
    return input_image


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
