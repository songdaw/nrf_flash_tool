#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import threading
import configparser
import time
import queue
from library.common import *

# Import pynrfjprog API module and HEX parser module
from pynrfjprog import LowLevel, Hex

class FlashTool:
    DO_WORK_OK = 0
    ERR_NO_DEV = 1
    ERR_NOT_CONN = 2
    ERR_CONN_FAIL = 3
    FLASH_PAGE_SIZE = 4096
    INTERNAL_FLASH_ADDR = 0
    QSPI_FLASH_ADDR = 0x12000000

    def __init__(self, debug=True):
        self.debug = debug
        self.worker = None
        self.running = False
        self.api = None
        self.opened = False
        self.device_version = None
        self.device_family = None
        self.status = 0
        self.dl_percent = 0
        self.dl_dev_enum = None

    def open(self):
        self.running = True
        self.dl_dev_enum = None
        self.worker = self.WorkHandler(self)
        self.worker.start()
        if self.debug:
            print("Open flash tool")

    def close(self):
        self.dl_dev_enum = None
        self.running = False
        if self.worker is not None:
            self.worker.resume()
            self.worker.join()
            self.worker = None
        self.opened = False
        if self.api is not None:
            self.api.close()
            self.api = None
        if self.debug:
            print("Close flash tool")

    def set_stats_percent(self, sts, per):
        self.status = sts
        self.dl_percent = per

    def get_work_percent(self):
        return self.status, self.dl_percent

    def get_status(self):
        return self.status

    def get_devs(self):
        return self.dl_dev_enum

    def get_device_version(self):
        return self.device_version

    def get_device_family(self):
        return self.device_family

    def check_address_limit(self, addr):
        if self.get_device_family() == "NRF52":
            if (addr >= 0x12000000 and addr <= 0x19FFFFFF) or \
                    (addr >= 0 and addr < 0x10000000):
                return True
            else:
                return False
        else:
            return True

    def download(self, filename, dl_addr):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["download", filename, dl_addr])

    def enum(self):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["enum"])

    def connect(self, snr):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["connect", snr])

    def disconnect(self):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["disconnect"])

    def reset(self):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["reset"])

    def lock(self):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["lock"])

    def recover(self, snr):
        self.set_stats_percent(0, 0)
        self.worker.add_work(["recover", snr])

    class WorkHandler(threading.Thread):
        def __init__(self, upper, debug=True):
            threading.Thread.__init__(self)
            self.event = threading.Event()
            self.event.set()
            self.threadlock = threading.Lock()
            # To support command queue
            self.msgqueue = queue.Queue(10)
            self.debug = debug
            self.upper = upper

        def add_work(self, work):
            self.threadlock.acquire()
            self.msgqueue.put(work)
            self.threadlock.release()
            self.resume()

        def _enum_dev(self):
            if self.debug:
                print('# Opening API with device family UNKNOWN.')
            try:
                with LowLevel.API(LowLevel.DeviceFamily.UNKNOWN) as api:
                    api.connect_to_emu_without_snr()
                    self.upper.dl_dev_enum = api.enum_emu_snr()
            except Exception as e:
                print(e)

            if self.upper.dl_dev_enum is not None:
                self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)
            else:
                self.upper.set_stats_percent(FlashTool.ERR_NO_DEV, 100)

        def _program_data(self, dest_addr, wdata, is_qspi, in_size, total_size):
            data_down = in_size
            address = dest_addr
            length = len(wdata)
            data_idx = 0

            # process data before page
            if address % FlashTool.FLASH_PAGE_SIZE:
                first = FlashTool.FLASH_PAGE_SIZE - address % FlashTool.FLASH_PAGE_SIZE
                if first > length:
                    first = length

                page_address = address // FlashTool.FLASH_PAGE_SIZE
                if is_qspi:
                    page_data = list(self.upper.api.qspi_read(page_address, FlashTool.FLASH_PAGE_SIZE))
                else:
                    page_data = self.upper.api.read(page_address, FlashTool.FLASH_PAGE_SIZE)
                page_data[address-page_address:address-page_address+first] = \
                    wdata[data_idx:data_idx+first]
                if is_qspi:
                    self.upper.api.qspi_erase(page_address, 0)
                    self.upper.api.qspi_write(page_address, page_data)
                else:
                    self.upper.api.erase_page(page_address)
                    self.upper.api.write(page_address, page_data, True)

                address += first
                length -= first
                data_idx += first

                data_down += first
                self.upper.set_stats_percent(0, data_down * 100 // total_size)

            page_cnt = length // FlashTool.FLASH_PAGE_SIZE
            left = length % FlashTool.FLASH_PAGE_SIZE

            for idx in range(page_cnt) :
                if is_qspi:
                    self.upper.api.qspi_erase(address, 0)
                    self.upper.api.qspi_write(address,
                                              wdata[data_idx:data_idx + flashtool.FLASH_PAGE_SIZE])
                else:
                    self.upper.api.erase_page(address)
                    self.upper.api.write(address,
                                         wdata[data_idx:data_idx+flashtool.FLASH_PAGE_SIZE],
                                         True)
                data_idx += flashtool.FLASH_PAGE_SIZE
                address += flashtool.FLASH_PAGE_SIZE

                data_down += FlashTool.FLASH_PAGE_SIZE
                self.upper.set_stats_percent(0, data_down * 100 // total_size)

            if left:
                if is_qspi:
                    page_data = list(self.upper.api.qspi_read(address, FlashTool.FLASH_PAGE_SIZE))
                else:
                    page_data = self.upper.api.read(address, FlashTool.FLASH_PAGE_SIZE)
                page_data[address % FlashTool.FLASH_PAGE_SIZE : \
                        address % FlashTool.FLASH_PAGE_SIZE + left] = \
                        wdata[data_idx:data_idx + left]
                if is_qspi:
                    self.upper.api.qspi_erase(address, 0)
                    self.upper.api.qspi_write(address, page_data)
                else:
                    self.upper.api.erase_page(address)
                    self.upper.api.write(address, page_data, True)

                data_down += left
                self.upper.set_stats_percent(0, data_down * 100 // total_size)
            return data_down

        def _download_data(self, work):
            if not self.upper.opened:
                self.upper.set_stats_percent(FlashTool.ERR_NOT_CONN, 100)
                return
            if self.upper.api is None:
                self.upper.set_stats_percent(FlashTool.ERR_CONN_FAIL, 100)
                return

            file_name = work[1]
            dl_addr = work[2]

            file_data_sum = 0
            file_data_down = 0
            dl_qspi = 0

            if file_name[-3:] == "hex":
                if self.debug:
                    print('# Parsing hex file into segments.')
                file_program = Hex.Hex(file_name)
                # Program the parsed hex into the device's memory.
                if self.debug:
                    print('# Writing %s to device.' % file_name)
                for segment in file_program:
                    file_data_sum += len(segment.data)

                for segment in file_program:
                    if segment.address >= FlashTool.QSPI_FLASH_ADDR:
                        start_address = segment.address & 0x00FFFFFF
                        dl_qspi = 1
                        if not self.upper.api.is_qspi_init():
                            self.upper.api.qspi_init()
                    else:
                        start_address = segment.address
                        dl_qspi = 0

                    self._program_data(start_address,
                                       segment.data,
                                       dl_qspi,
                                       file_data_down,
                                       file_data_sum)
                    file_data_down += len(segment.data)
                    #time.sleep(0.1)
            else:
                file_data = read_bin_file(file_name)

                if dl_addr >= FlashTool.QSPI_FLASH_ADDR:
                    start_address = dl_addr & 0x00FFFFFF
                    dl_qspi = 1
                    if not self.upper.api.is_qspi_init():
                        self.upper.api.qspi_init()
                else:
                    start_address = dl_addr
                    dl_qspi = 0

                self._program_data(start_address,
                                   file_data,
                                   dl_qspi,
                                   0,
                                   len(file_data))

            if dl_qspi:
                if self.upper.api.is_qspi_init():
                    self.upper.api.qspi_uninit()

        def _connect_dev(self, work):
            if self.upper.opened:
                self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)
                return

            snr = work[1]
            if self.debug:
                print('# Opening API with device family UNKNOWN, reading the device family.')
            with LowLevel.API(LowLevel.DeviceFamily.UNKNOWN) as api:
                # Using with construction so there is no need to open or close the API class.
                if snr is not None:
                    api.connect_to_emu_with_snr(snr)
                else:
                    api.connect_to_emu_without_snr()
                device_family = api.read_device_family()

            self.upper.device_family = device_family
            self.upper.api = LowLevel.API(device_family)
            self.upper.api.open()
            try:
                self.upper.api.connect_to_emu_with_snr(snr)
                self.upper.device_version = self.upper.api.read_device_version()
                self.upper.opened = True
                self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)
            except LowLevel.APIError:
                self.upper.set_stats_percent(FlashTool.ERR_CONN_FAIL, 100)
                self.upper.api.close()
                self.upper.api = None

        def _disconnect_dev(self):
            if self.upper.api is None:
                self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)
                return

            self.upper.api.close()
            self.upper.api = None
            self.upper.opened = False
            self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)

        def _lock_dev(self):
            if not self.upper.opened:
                self.upper.set_stats_percent(FlashTool.ERR_NOT_CONN, 100)
                return
            self.upper.api.readback_protect(LowLevel.ReadbackProtection.ALL)
            rbp_status = self.upper.api.readback_status()
            if rbp_status == "ALL":
                self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)
            else:
                self.upper.set_stats_percent(FlashTool.ERR_CONN_FAIL, 100)

        def _recover_dev(self, work):
            snr = work[1]
            try:
                if self.upper.opened:
                    self.upper.api.recover()
                else:
                    with LowLevel.API(LowLevel.DeviceFamily.UNKNOWN) as api:
                        if snr is not None:
                            api.connect_to_emu_with_snr(snr)
                        else:
                            api.connect_to_emu_without_snr()
                        device_family = api.read_device_family()

                    local_api = LowLevel.API(device_family)
                    local_api.open()
                    local_api.connect_to_emu_with_snr(snr)
                    local_api.recover()
                    local_api.sys_reset()
                    local_api.close()

                self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)
            except LowLevel.APIError:
                self.upper.set_stats_percent(FlashTool.ERR_CONN_FAIL, 100)

        def _reset_dev(self):
            if not self.upper.opened:
                self.upper.set_stats_percent(FlashTool.ERR_NOT_CONN, 100)
                return
            # Reset the device and run.
            self.upper.api.sys_reset()
            self.upper.api.go()
            self.upper.set_stats_percent(FlashTool.DO_WORK_OK, 100)

        def do_work(self, work):
            if self.debug:
                print(work[0])
            if work[0] == "download":
                self._download_data(work)
            elif work[0] == "enum":
                self._enum_dev()
            elif work[0] == "connect":
                self._connect_dev(work)
            elif work[0] == "disconnect":
                self._disconnect_dev()
            elif work[0] == "lock":
                self._lock_dev()
            elif work[0] == "recover":
                self._recover_dev(work)
            elif work[0] == "reset":
                self._reset_dev()

        def run(self):
            while self.upper.running:
                if self.debug:
                    print("ready to pause")
                self.event.wait()

                while True:
                    self.threadlock.acquire()
                    if not self.msgqueue.empty():
                        if self.debug:
                            print("get work")
                        work = self.msgqueue.get()
                        self.threadlock.release()

                        self.do_work(work)
                    else:
                        self.threadlock.release()
                        self.pause()
                        break
                    time.sleep(0.1)

        def pause(self):
            self.event.clear()

        def resume(self):
            self.event.set()

