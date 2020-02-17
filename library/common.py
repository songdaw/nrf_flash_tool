#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os

def list_to_str(in_data):
    if type(in_data) is str:
        w_data = in_data
    elif type(in_data) is bytes:
        w_data = "".join([chr(x) for x in list(in_data)])
    else:
        w_data = "".join([chr(x) for x in in_data])

    return w_data


def str_to_list(in_data):
    if type(in_data) is list:
        w_data = in_data
    elif type(in_data) is bytes:
        w_data = list(in_data)
    else:
        w_data = [ord(x) for x in in_data]

    return w_data


def list_to_int(in_data):
    return in_data[0] | (in_data[1] << 8) | \
            (in_data[2] << 16) | (in_data[2] << 24)


def int_to_list(in_data):
    return [in_data & 0xff, (in_data >> 8) & 0xff,
            (in_data >> 16) & 0xff, (in_data >> 24) & 0xff]


def read_bin_file(file):
    if os.path.exists(file) == 0:
        raise Exception('file ' + file + " does not exist!")

    f = open(file, 'rb')
    data = f.read()
    f.close()

    return list(data)
