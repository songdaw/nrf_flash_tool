#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from tkinter import ttk
from library.flash_tool import *
import time

class FlashGui:
    def __init__(self, debug=True):
        self.debug = debug
        self.flashtool = FlashTool(self.debug)
        self.gui = None

    def handle_err_status(self, err_code, err_msg):
        canvas = self.gui['canvas']
        work_per = self.gui['work_per']

        canvas.itemconfig(work_per, fill='red')
        tk.messagebox.showerror(title="Error", message= err_msg + ":" + hex(err_code))

    def wait_work_done(self):
        lb_result_var = self.gui['lb_result_var']
        sts = -1
        while True:
            sts, per = self.flashtool.get_work_percent()
            self.update_progress(per)
            if sts:
                lb_result_var.set("Fail")
                break
            if per == 100:
                lb_result_var.set("Success")
                break
            time.sleep(0.01)
        return sts

    def add_device_enum(self):
        self.flashtool.enum()
        sts = self.wait_work_done()
        if sts:
            self.handle_err_status(sts, "Enum device error")
        enum_devs = self.flashtool.get_devs()

        window = self.gui['window']
        lb_filename = tk.Label(window,
                               text="Dev:",
                               font=('Arial', 10))
        lb_filename.place(x=10, y=10)

        cb_dev = ttk.Combobox(window,
                                  font=('Arial', 10),
                                  width=40,
                                  state="normal")
        cb_dev.place(x=50, y=10)
        if enum_devs is not None and len(enum_devs) > 0:
            cb_dev["value"] = enum_devs
            cb_dev.current(0)

        cb_family = ttk.Combobox(window,
                                   font=('Arial', 10),
                                   width = 7,
                                   state="normal")
        cb_family.place(x=360, y=10)
        cb_family["value"] = ["NRF52", "NRF51"]
        cb_family.current(0)
        self.gui['cb_dev'] = cb_dev             # Display devices
        self.gui['cb_family'] = cb_family       # Display family

    def btn_select_file(self):
        entry_name_var = self.gui['entry_name_var']
        entry_address = self.gui['entry_address']
        entry_addr_var = self.gui['entry_addr_var']
        btn_dl = self.gui['btn_dl']

        filename = tkinter.filedialog.askopenfilename(filetypes=[("BIN",".bin"),("HEX",".hex")])
        if filename is not None and len(filename) > 0:
            entry_name_var.set(filename)
            if filename[-3:] == "bin":
                entry_address["state"] = "normal"
                entry_addr_var.set("0x00000000")
            else:
                entry_addr_var.set("")
                entry_address["state"] = "disabled"
            #btn_dl["state"] = "normal"

    def add_select_file(self):
        window = self.gui['window']

        lb_filename = tk.Label(window,
                               text="File:",
                               font=('Arial', 10))
        lb_filename.place(x=10, y=40)

        entry_name_var = tk.StringVar()
        entry_filename = tk.Entry(window,
                                    font=('Arial', 10),
                                    width = 45,
                                    state = "normal",
                                    textvariable = entry_name_var)
        entry_filename.place(x=50, y=40)
        entry_name_var.set("Select file...")

        btn_select = tk.Button(window, text="Select",
                               font=('Arial', 8),
                                width=7,
                                command=self.btn_select_file)
        btn_select.place(x=380, y=38)
        self.gui['entry_name_var'] = entry_name_var     # Display filename selected

    def add_down_addr(self):
        window = self.gui['window']

        lb_addr = tk.Label(window,
                               text="Addr:",
                               font=('Arial', 10))
        lb_addr.place(x=8, y=70)

        entry_addr_var = tk.StringVar()
        entry_address = tk.Entry(window,
                                  font=('Arial', 10),
                                  width=20,
                                  state="disabled",
                                  textvariable=entry_addr_var)
        entry_address.place(x=50, y=70)
        self.gui['entry_addr_var'] = entry_addr_var         # Get input download address
        self.gui['entry_address'] = entry_address            # Display download address

    def btn_conn_func(self):
        cb_dev = self.gui['cb_dev']
        lb_result_var = self.gui['lb_result_var']
        btn_conn_var = self.gui['btn_conn_var']
        btn_lock = self.gui['btn_lock']
        btn_dl = self.gui['btn_dl']
        #btn_recover = self.gui['btn_recover']
        btn_reset = self.gui['btn_reset']
        cb_family = self.gui['cb_family']

        select_dev = cb_dev.get()
        btn_var = btn_conn_var.get()
        if len(select_dev) > 0:
            lb_result_var.set(btn_var)
            if btn_var == "Connect":
                self.flashtool.connect(int(select_dev))
                sts = self.wait_work_done()
                if sts:
                    self.handle_err_status(sts, "Connect error")
                else:
                    device_family = self.flashtool.get_device_family()
                    if device_family == "NRF52":
                        cb_family.current(0)
                    elif device_family == "NRF51":
                        cb_family.current(1)
                    else:
                        self.handle_err_status(-1, "Device family not found")
                        return
                    btn_conn_var.set("Disconnect")
                    btn_lock["state"] = "normal"
                    btn_reset["state"] = "normal"
                    btn_dl["state"] = "normal"
                    device_version = self.flashtool.get_device_version()
                    lb_result_var.set("Success " + device_version)
            else:
                self.flashtool.disconnect()
                sts = self.wait_work_done()
                if sts:
                    self.handle_err_status(sts, "Disconnect error")
                else:
                    btn_conn_var.set("Connect")
                    btn_lock["state"] = "disabled"
                    btn_reset["state"] = "disabled"
                    btn_dl["state"] = "disabled"

    def add_conn_btn(self):
        window = self.gui['window']
        cb_dev = self.gui['cb_dev']

        btn_conn_var = tk.StringVar()
        btn_conn = tk.Button(window,
                                font=('Arial', 10),
                                width=8,
                                  textvariable=btn_conn_var,
                                command=self.btn_conn_func)
        btn_conn_var.set("Connect")
        btn_conn.place(x=10, y=100)
        select_dev = cb_dev.get()
        if len(select_dev) > 0:
            btn_conn["state"] = "normal"
        else:
            btn_conn["state"] = "disabled"

        self.gui['btn_conn_var']= btn_conn_var      # Button display text
        self.gui['btn_conn'] = btn_conn             # Button: Connect

    def btn_dl_func(self):
        entry_name_var = self.gui['entry_name_var']
        entry_addr_var = self.gui['entry_addr_var']
        lb_result_var = self.gui['lb_result_var']
        btn_dl = self.gui['btn_dl']

        file_name = entry_name_var.get()
        if file_name[-3:] == "bin":
            file_address_var = entry_addr_var.get()
            if file_address_var is None or len(file_address_var) == 0:
                self.handle_err_status(-1, "Address error.")
                return
            if len(file_address_var) > 2 and file_address_var[0:2] =="0x":
                file_address = int(file_address_var, 16)
            else:
                file_address = int(file_address_var, 10)
            # check address
            if not self.flashtool.check_address_limit(file_address):
                self.handle_err_status(-4, "Address error")
                return
        elif file_name[-3:] == "hex":
            file_address = 0
        else:
            raise Exception("File unknow")
        self.flashtool.download(file_name, file_address)
        lb_result_var.set("Downloading...")

        btn_dl["state"] = "disabled"
        sts = self.wait_work_done()
        if sts:
            self.handle_err_status(sts, "Download error")
        btn_dl["state"] = "normal"

    def add_dl_btn(self):
        window = self.gui['window']
        btn_dl = tk.Button(window, text="Download",
                                font=('Arial', 10),
                                width=8,
                                command=self.btn_dl_func)
        btn_dl.place(x=90, y=100)
        btn_dl["state"] = "disabled"
        self.gui['btn_dl'] = btn_dl             # Button: Download

    def btn_lock_func(self):
        lb_result_var = self.gui['lb_result_var']
        lb_result_var.set("Lock")
        self.flashtool.lock()
        sts = self.wait_work_done()
        if sts:
            self.handle_err_status(sts, "Lock error")

    def add_lock_btn(self):
        window = self.gui['window']
        btn_lock = tk.Button(window, text="Lock",
                                font=('Arial', 10),
                                width=8,
                                command=self.btn_lock_func)
        btn_lock.place(x=170, y=100)
        btn_lock["state"] = "disabled"
        self.gui['btn_lock'] = btn_lock         # Button: Lock device

    def btn_recver_func(self):
        cb_dev = self.gui['cb_dev']
        select_dev = cb_dev.get()
        if len(select_dev) > 0:
            lb_result_var = self.gui['lb_result_var']
            lb_result_var.set("Recover")
            self.flashtool.recover(int(select_dev))
            sts = self.wait_work_done()
            if sts:
                self.handle_err_status(sts, "Recover error")

    def add_recover_btn(self):
        window = self.gui['window']
        btn_recover = tk.Button(window, text="Recover",
                                  font=('Arial', 10),
                                  width=8,
                                  command=self.btn_recver_func)
        btn_recover.place(x=250, y=100)
        btn_recover["state"] = "normal"
        self.gui['btn_recover'] = btn_recover           # Button: Recover device

    def btn_reset_func(self):
        lb_result_var = self.gui['lb_result_var']
        lb_result_var.set("Reset device")
        self.flashtool.reset()
        sts = self.wait_work_done()
        if sts:
            self.handle_err_status(sts, "Reset error")

    def add_reset_btn(self):
        window = self.gui['window']
        btn_reset = tk.Button(window, text="Reset",
                                     font=('Arial', 10),
                                     width=8,
                                     command=self.btn_reset_func)
        btn_reset.place(x=330, y=100)
        btn_reset["state"] = "disabled"
        self.gui['btn_reset'] = btn_reset           # Button: Reset device

    def add_result(self):
        window = self.gui['window']
        lb_result_var = tk.StringVar()
        lb_result = tk.Label(window,
                               text="File:",
                               font=('Arial', 10),
                               textvariable = lb_result_var)
        lb_result.place(x=10, y=140)
        lb_result_var.set("Initial")
        self.gui['lb_result_var'] = lb_result_var           # Display operation result

    def add_progress(self):
        window = self.gui['window']

        canvas = tk.Canvas(window, bg='white', height=10, width=400)
        canvas.place(x=10, y=160)
        work_per = canvas.create_rectangle(0, 0, 0, 10, width=0, fill="blue")

        lb_per_var = tk.StringVar()
        lb_per = tk.Label(window,
                             text="File:",
                             font=('Arial', 10),
                             textvariable=lb_per_var)
        lb_per.place(x=410, y=155)
        lb_per_var.set("0%")

        self.gui['canvas'] = canvas
        self.gui['lb_per_var'] = lb_per_var         # Display percent of progressbar
        self.gui['work_per'] = work_per

    def update_progress(self, per):
        window = self.gui['window']
        canvas = self.gui['canvas']
        work_per = self.gui['work_per']
        lb_per_var = self.gui['lb_per_var']

        per_x2 = per / 100 * 400
        canvas.itemconfig(work_per, fill='blue')
        canvas.coords(work_per, (0, 0, per_x2, 10))
        window.update()
        lb_per_var.set(str(per) + "%")

    def show_window(self):
        self.flashtool.open()

        window = tk.Tk()
        window.title('Flash Tool v0.1 --By Awei')
        window.geometry('450x180')
        window.resizable(0, 0)

        self.gui = dict()
        self.gui['window'] = window
        self.add_result()
        self.add_progress()

        self.add_device_enum()
        self.add_select_file()
        self.add_down_addr()

        self.add_conn_btn()
        self.add_dl_btn()
        self.add_lock_btn()
        self.add_recover_btn()
        self.add_reset_btn()

        window.mainloop()

        self.gui.clear()
        self.gui = None

        self.flashtool.close()


if __name__ == '__main__':
    flashgui = FlashGui()
    flashgui.show_window()


