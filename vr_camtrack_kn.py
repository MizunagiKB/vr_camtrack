"""
https://github.com/yoshihiro1909/mediapipe_to_vrchat
https://github.com/gpsnmeajp/VirtualMotionTracker/

use: VMT 0.12
"""
import threading
import tkinter
import _tkinter

import PIL
import PIL.Image
import PIL.ImageTk

# KinectV2
from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import pythonosc.udp_client

VMT_OSC_HOST = "127.0.0.1"
VMT_OSC_PORT = 39570


PREVIEW_W = 256
PREVIEW_H = 256


POSE_KN_HEAD = 3
POSE_KN_SHOULDER_L = 4
POSE_KN_SHOULDER_R = 8
POSE_KN_ELBOW_L = 5
POSE_KN_ELBOW_R = 9
POSE_KN_HIP_L = 12
POSE_KN_HIP_R = 16
POSE_KN_KNEE_L = 13
POSE_KN_KNEE_R = 17
POSE_KN_ANKLE_L = 14
POSE_KN_ANKLE_R = 18
POSE_KN_HIP = 0


KN_TRACKERS = [
    POSE_KN_SHOULDER_L,
    POSE_KN_SHOULDER_R,
    POSE_KN_ELBOW_L,
    POSE_KN_ELBOW_R,
    POSE_KN_KNEE_L,
    POSE_KN_KNEE_R,
    POSE_KN_ANKLE_L,
    POSE_KN_ANKLE_R,
]


class CVector3(object):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __init__(self, _x: float = 0.0, _y: float = 0.0, _z: float = 0.0):
        self.x = _x
        self.y = _y
        self.z = _z

    def __add__(self, other):
        return CVector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return CVector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        if isinstance(other, float):
            return CVector3(self.x * other, self.y * other, self.z * other)
        else:
            return CVector3(self.x * other.x, self.y * other.y, self.z * other.z)

    def __imul__(self, other):
        if isinstance(other, (int, float)):
            self.x *= float(other)
            self.y *= float(other)
            self.z *= float(other)
        else:
            self.x *= other.x
            self.y *= other.y
            self.z *= other.z

        return self


class CTrackerHistory(object):
    list_vector3: list[CVector3]
    history_size: int = 3

    def __init__(self, _history_size: int = 3):
        self.list_vector3 = []
        self.history_size = _history_size

    def avg(self) -> CVector3:

        self.list_vector3 = self.list_vector3[self.history_size * -1 :]

        v = len(self.list_vector3)
        return CVector3(
            sum([vct.x for vct in self.list_vector3]) / v,
            sum([vct.y for vct in self.list_vector3]) / v,
            sum([vct.z for vct in self.list_vector3]) / v,
        )


def calc_waist_vector(hip_l, hip_r) -> CVector3:
    return CVector3(
        (hip_l.x + hip_r.x) * 0.5,
        (hip_l.y + hip_r.y) * 0.5,
        (hip_l.z + hip_r.z) * 0.5,
    )


def send_osc(
    osc_cli: pythonosc.udp_client.SimpleUDPClient,
    idx: int,
    enable: int,
    time_offset: float,
    vct: CVector3,
):

    msg_type = "/VMT/Room/Unity"
    msg_body = [idx, enable, time_offset, vct.x, vct.y, vct.z, 0.0, 0.0, 0.0, 0.0]

    osc_cli.send_message(msg_type, msg_body)


tk_canvas: tkinter.Canvas = None
tk_label_value: tkinter.StringVar = None
tk_chk_value: tkinter.StringVar = None
vct_scale = CVector3(1.0, 1.0, 1.0)
vct_adjust = CVector3(0.0, 0.0, 0.0)


def init_mp():
    pass


def init_kn():
    pass


def th_capture():

    osc_cli = pythonosc.udp_client.SimpleUDPClient(VMT_OSC_HOST, VMT_OSC_PORT)

    o_kinect = PyKinectRuntime.PyKinectRuntime(
        PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body
    )

    dict_tracker_history: dict[int, CTrackerHistory] = {}
    for idx in KN_TRACKERS:
        dict_tracker_history[idx] = CTrackerHistory()
    dict_tracker_history[POSE_KN_HIP] = CTrackerHistory()

    import time

    while True:

        time.sleep(0)

        if o_kinect.has_new_body_frame():
            o_bodies = o_kinect.get_last_body_frame()
            if o_bodies is None:
                continue

            for n in range(0, o_kinect.max_body_count):
                o_body = o_bodies.bodies[n]

                if not o_body.is_tracked:
                    continue

                list_joint = o_body.joints

                vct = calc_waist_vector(
                    list_joint[POSE_KN_HIP_L].Position,
                    list_joint[POSE_KN_HIP_R].Position,
                )
                vct *= vct_scale
                vct += vct_adjust
                vct.z *= -1

                tk_label_value.set(
                    "{:2.2f} {:2.2f} {:2.2f}".format(vct.x, vct.y, vct.z)
                )

                dict_tracker_history[POSE_KN_HIP].list_vector3.append(vct)
                vct_avg = dict_tracker_history[POSE_KN_HIP].avg()
                send_osc(osc_cli, POSE_KN_HIP, 1, 0.0, vct_avg)

                for idx in KN_TRACKERS:
                    joint = list_joint[idx]

                    vct = CVector3(joint.Position.x, joint.Position.y, joint.Position.z)
                    vct *= vct_scale
                    vct += vct_adjust
                    vct.z *= -1

                    dict_tracker_history[idx].list_vector3.append(vct)
                    vct_avg = dict_tracker_history[idx].avg()
                    send_osc(osc_cli, idx, 1, 0.0, vct_avg)


def scl_x(v: float):
    vct_scale.x = float(v)


def scl_y(v: float):
    vct_scale.y = float(v)


def scl_z(v: float):
    vct_scale.z = float(v)


def adj_x(v: float):
    vct_adjust.x = float(v)


def adj_y(v: float):
    vct_adjust.y = float(v)


def adj_z(v: float):
    vct_adjust.z = float(v)


def main():
    global tk_canvas
    global tk_label_value
    global tk_chk_value

    tk_root = tkinter.Tk()
    tk_root.title("VR CamTrack[KN]")
    tk_root.geometry("512x384")

    main_frame = tkinter.Frame(tk_root)
    main_frame.grid(column=0, row=0, sticky=tkinter.NSEW, padx=8, pady=8)

    for col, (cmd, v) in enumerate(((scl_x, 1.0), (scl_y, 1.0), (scl_z, 1.0))):
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

    for col, (cmd, v) in enumerate(((adj_x, 0.0), (adj_y, 0.0), (adj_z, 0.0))):
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

    tk_canvas = tkinter.Canvas(main_frame, width=PREVIEW_W, height=PREVIEW_H)
    tk_canvas.grid(column=1, row=2)

    tk_chk_value = tkinter.StringVar()
    tk_chk_value.set("0")
    tk_chk_preview = tkinter.Checkbutton(
        main_frame,
        text="Preview",
        onvalue="1",
        offvalue="0",
        variable=tk_chk_value,
    )
    tk_chk_preview.grid(column=0, row=2)

    tk_label_value = tkinter.StringVar()
    tk_label_value.set("")
    tk_label = tkinter.Label(main_frame, textvariable=tk_label_value)
    tk_label.grid(column=1, row=3)

    tk_root.columnconfigure(0, weight=1)
    tk_root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

    th = threading.Thread(target=th_capture)
    th.start()

    tk_root.mainloop()


if __name__ == "__main__":
    main()
