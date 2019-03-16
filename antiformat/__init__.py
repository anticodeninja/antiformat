#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright 2019 Artem Yamshanov, me [at] anticode.ninja

import collections
import difflib
import fnmatch
import yaml
import os
import textwrap

from antiformat.std_variables import *

THRESHOLD = 0.9
COPYRIGHT_DELTA = 3

class CustomLoader(yaml.Loader):

    @staticmethod
    def detect_ordered_dict(loader, node):
        return collections.OrderedDict(loader.construct_pairs(node))

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

        self.yaml_constructors = self.yaml_constructors.copy()
        self.yaml_constructors['tag:yaml.org,2002:map'] = CustomLoader.detect_ordered_dict


class Antiformat:

    def __init__(self, basepath=None):
        self.expath = lambda x: os.path.join(basepath, x) if basepath else x
        self.init()
        self.load_config()

    def init(self):
        self.headers = {}
        for key, value in HEADERS.items():
            self.headers[key] = textwrap.dedent(value).strip().split('\n')
        self.last_header = None

        self.formats = {
            '*.cs': [
                self.universal_remover(),
                self.universal_appender(None, '// ', None)
            ],
            '*.js': [
                self.universal_remover(),
                self.universal_appender(None, '// ', None)
            ],
            '*.py': [
                self.universal_remover(),
                self.shebang_appender(None, '# ', None)
            ],
        }

    def load_config(self):
        def header_parser(value):
            return [x.strip() for x in value.format(**variables).strip().split('\n')]

        def load_param(section, name, default=None, parser=None):
            if not section:
                return default

            value = section.get(name, None)
            if not value:
                return default

            return parser(value) if parser else value

        def load_params(section, default={}):
            return dict(
                header=load_param(section, 'header', default.get('header', None), header_parser),
                rstrip=load_param(section, 'rstrip', default.get('rstrip', False)),
            )

        with open(self.expath('.antiformat'), 'r', encoding='utf8') as config_file:
            temp = yaml.load(config_file,Loader=CustomLoader)

        variables = dict()
        for key, value in self.headers.items():
            variables[key] = '\n'.join(value)
        for key, value in temp.get('variables', {}).items():
            variables[key] = value.format(**variables)

        g_conf = load_params(temp.get('global', {}))

        files = dict()
        for key, value in temp.get('files', {}).items():
            files[key] = load_params(value, g_conf)

        self.config = dict(
            variables=variables,
            files=files,
            ignore=temp['ignore']
        )


    def patch_files(self):
        basepath = os.path.abspath(self.expath('.'))
        for dirname, dirs, files in os.walk(basepath):
            for filename in files:
                fullpath = os.path.join(dirname, filename)
                relpath = os.path.relpath(fullpath, basepath)
                if any(fnmatch.fnmatch(relpath, exception)
                       for exception in self.config['ignore']):
                    continue

                for wildcard, rule in self.config['files'].items():
                    if fnmatch.fnmatch(relpath, wildcard):
                        self.patch_file(fullpath, wildcard, rule)

    def patch_file(self, path, wildcard, rule):
        handlers = self.formats.get(wildcard, None)
        if not handlers:
            for wildcard, temp in self.formats.items():
                if fnmatch.fnmatch(path, wildcard):
                    handlers = temp

        if not handlers:
            print('{} cannot be patched'.format(path))
            return

        with open(path, 'r', encoding='utf8') as input_file:
            data = [x.rstrip('\r\n') for x in input_file.readlines()]

        if rule['rstrip']:
            data = [x.rstrip() for x in data]

        if rule['header']:
            if not handlers[0](data):
                print('Old header is not found in {}'.format(path))
            handlers[1](data, rule['header'])

        with open(path, 'w', encoding='utf8') as output_file:
            output_file.write('\n'.join(data))
            output_file.write('\n')

        print('{} was patched'.format(path))


    def universal_remover(self):
        def impl(data):
            ranges = None
            if self.last_header:
                ranges = self.find_block(self.last_header, data)
            if not ranges:
                for header in self.headers.values():
                    ranges = self.find_block(header, data)
                    if ranges:
                        self.last_header = header
                        break
            if not ranges:
                return None

            offset = ranges[0] - 1
            while offset >= 0 and (ranges[0] - offset) < COPYRIGHT_DELTA:
                if 'copyright' in data[offset].lower():
                    ranges = (offset, ranges[1])
                offset -= 1

            offset = ranges[1]
            while offset < len(data) and (offset - ranges[1]) < COPYRIGHT_DELTA:
                if 'copyright' in data[offset].lower():
                    ranges = (ranges[0], offset + 1)
                offset += 1

            while len(data[ranges[0]].strip()) == 0:
                ranges = (ranges[0] - 1, ranges[1])
            while len(data[ranges[1]].strip()) == 0:
                ranges = (ranges[0], ranges[1] + 1)

            del data[ranges[0]:ranges[1]]

            return ranges

        return impl


    def universal_appender(self, start, row, end):
        def impl(data, header):
            temp = self.generate_header(start, row, end, header)
            temp.append('')
            data[0:0] = temp

        return impl

    def shebang_appender(self, start, row, end):
        def impl(data, header):
            temp = self.generate_header(start, row, end, header)

            index = 0
            while data[index].startswith('#'):
                index += 1

            if index > 0:
                temp.insert(0, '')
            if len(data[index].strip()) != 0:
                temp.append('')

            data[index:index] = temp

        return impl


    def generate_header(self, start, row, end, header):
        # TODO Add caching
        temp, last = [], len(header) - 1
        for i, line in enumerate(header):
            if i > 0 and i < last: temp.append(row + line)
            elif i == 0: temp.append((start if start else row) + line)
            elif i == last: temp.append((line if end else row) + (end if end else line))
        return temp


    def find_block(self, header, data):
        if len(data) < len(header):
            return None

        last = len(data) - len(header)
        header_len = len(header)
        for i in range(last):
            ratio = 0
            for j in range(header_len):
                ratio += difflib.SequenceMatcher(None, a=data[i+j], b=header[j]).ratio()
            ratio /= header_len

            if ratio > THRESHOLD:
                return (i, i+header_len)


def main():
    Antiformat().patch_files()

if __name__ == '__main__':
    main()

