import tkinter
import _tkinter

import vr_lib

CANVAS_W = 256
CANVAS_H = 256


class CUserInterface(object):

    tk_root: tkinter.Tk = None
    tk_canvas: tkinter.Canvas = None
    tk_label_value: tkinter.StringVar = None
    tk_chk_value: tkinter.StringVar = None

    vct_scale: vr_lib.CVector3 = None
    vct_adjust: vr_lib.CVector3 = None

    def __init__(self):
        self.vct_scale = vr_lib.CVector3(1.0, 1.0, 1.0)
        self.vct_adjust = vr_lib.CVector3(0.0, 0.0, 0.0)

        self.tk_root = tkinter.Tk()
        self.tk_root.title("VR CamTrack[MP]")
        self.tk_root.geometry("512x384")

        main_frame = tkinter.Frame(self.tk_root)
        main_frame.grid(column=0, row=0, sticky=tkinter.NSEW, padx=8, pady=8)

        for col, (cmd, v) in enumerate(
            ((self.evt_scl_x, 1.0), (self.evt_scl_y, 1.0), (self.evt_scl_z, 1.0))
        ):
            slider = tkinter.Scale(
                main_frame,
                from_=0.5,
                to=2,
                orient="horizontal",
                resolution=0.1,
                command=cmd,
            )
            slider.set(v)
            slider.grid(column=col, row=0)

        for col, (cmd, v) in enumerate(
            ((self.evt_adj_x, 0.0), (self.evt_adj_y, 0.0), (self.evt_adj_z, 0.0))
        ):
            slider = tkinter.Scale(
                main_frame,
                from_=-2,
                to=2,
                orient="horizontal",
                resolution=0.1,
                command=cmd,
            )
            slider.set(v)
            slider.grid(column=col, row=1)

        self.tk_canvas = tkinter.Canvas(main_frame, width=CANVAS_W, height=CANVAS_H)
        self.tk_canvas.grid(column=1, row=2)

        self.tk_chk_value = tkinter.StringVar()
        self.tk_chk_value.set("0")
        tk_chk_preview = tkinter.Checkbutton(
            main_frame,
            text="Preview",
            onvalue="1",
            offvalue="0",
            variable=self.tk_chk_value,
        )
        tk_chk_preview.grid(column=0, row=2)

        self.tk_label_value = tkinter.StringVar()
        self.tk_label_value.set("")
        tk_label = tkinter.Label(main_frame, textvariable=self.tk_label_value)
        tk_label.grid(column=1, row=3)

    def evt_scl_x(self, v: float):
        self.vct_scale.x = float(v)

    def evt_scl_y(self, v: float):
        self.vct_scale.y = float(v)

    def evt_scl_z(self, v: float):
        self.vct_scale.z = float(v)

    def evt_adj_x(self, v: float):
        self.vct_adjust.x = float(v)

    def evt_adj_y(self, v: float):
        self.vct_adjust.y = float(v)

    def evt_adj_z(self, v: float):
        self.vct_adjust.z = float(v)
