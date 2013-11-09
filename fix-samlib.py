#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Красивая типографика текстов СИ с помощью типографа студии Лебедева."""
import codecs
import os
import re
import sys

from RemoteTypograf import RemoteTypograf

TYPOGRAF_LIMIT = 32000


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print """Usage: %s input_file""" % sys.argv[0]
        sys.exit(64)
    input_file = sys.argv[1]
    print input_file
    sys.stdout.flush()
    (input_name, _) = os.path.splitext(input_file)
    output_file = '%s.html' % input_name

    rt = RemoteTypograf('windows-1251')

    rt.noEntities()
    rt.br(0)
    rt.p(0)
    rt.nobr(0)
    html = ''
    with open(input_file, mode='r') as input:
        buffer = ''
        for line in input.readlines():
            line = line.replace("'", '"').replace(chr(3), '').replace(chr(7), '')
            # Use nice apostrophes in cp1251 encoding
            line = re.sub(r'(?<=\w)"(?=\w)', chr(146), line, flags=re.U)
            if len(buffer) + len(line) >= TYPOGRAF_LIMIT:
                chunk = rt.processText(buffer)
                # Remove nbsp
                chunk = chunk.replace(chr(160), '')
                if len(chunk) < min(len(buffer) / 2, 512):
                    print chunk
                    print "Unable to process HTML"
                    sys.exit(1)
                html += chunk
                buffer = ''
                print '%dK' % (len(html) / 1024),
                sys.stdout.flush()
            buffer += line + '\n'
        if buffer:
            html += rt.processText(buffer)
    html = html.decode('windows-1251')
    with codecs.open(output_file, mode='w', encoding='windows-1251') as output:
        output.write(html)
    print ''
