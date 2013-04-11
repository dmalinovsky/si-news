#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Красивая типографика текстов СИ с помощью типографа студии Лебедева."""
import codecs
import os
import sys

from RemoteTypograf import RemoteTypograf

TYPOGRAF_LIMIT = 32000


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print """Usage: %s input_file""" % sys.argv[0]
        sys.exit(64)
    input_file = sys.argv[1]
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
            if len(buffer) + len(line) >= TYPOGRAF_LIMIT:
                html += rt.processText(buffer)
                buffer = ''
            buffer += line + '\n'
        if buffer:
            html += rt.processText(buffer)
    html = html.decode('windows-1251')
    with codecs.open(output_file, mode='w', encoding='windows-1251') as output:
        output.write(html)
