#!/usr/bin/env python
# -*- coding: utf-8 -*-

import filecmp
import os
import shutil
import re
import unittest

from antiformat import Antiformat

HERE = os.path.abspath(os.path.dirname(__file__))

class TestsContainer(unittest.TestCase):
    longMessage = True

def make_test(path, input_path, output_path):
    def test(self):
        if not filecmp.cmp(input_path, output_path):
            self.fail('File {} differs'.format(path))
    return test

def make_fail(path):
    def test(self):
        self.fail('expect file was not configured for {}'.format(path))
    return test

if __name__ == '__main__':
    def safe(value):
        return re.sub(r'[\.\/]', '_', value)

    for test_set in os.listdir(HERE):
        base_path = os.path.join(HERE, test_set)
        input_path = os.path.join(base_path, 'input')
        work_path = os.path.join(base_path, 'work')
        expect_path = os.path.join(base_path, 'expect')

        if not os.path.isdir(base_path):
            continue

        if os.path.exists(work_path):
            shutil.rmtree(work_path)
        shutil.copytree(input_path, work_path)
        shutil.copy(os.path.join(base_path, '.antiformat'), work_path)

        Antiformat(work_path).patch_files()
        os.unlink(os.path.join(work_path, '.antiformat'))

        for dirname, dirs, files in os.walk(work_path):
            for filename in files:
                input_full_path = os.path.join(dirname, filename)
                input_rel_path = os.path.relpath(input_full_path, work_path)
                expect_full_path = os.path.join(expect_path, input_rel_path)

                if os.path.exists(expect_full_path):
                    test_func = make_test(input_rel_path, input_full_path, expect_full_path)
                else:
                    test_func = make_fail(input_rel_path)

                setattr(TestsContainer, 'test_{0}'.format(safe(input_rel_path)), test_func)

    unittest.main()
