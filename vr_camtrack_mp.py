"""
https://github.com/yoshihiro1909/mediapipe_to_vrchat
https://github.com/gpsnmeajp/VirtualMotionTracker/

use: VMT 0.12
"""
import argparse
import threading
import tkinter
import _tkinter

import PIL
import PIL.Image
import PIL.ImageTk

# MediaPipe
import cv2
import mediapipe as mp
import numpy as np

import pythonosc.udp_client

import vr_lib

VMT_OSC_HOST = "127.0.0.1"
VMT_OSC_PORT = 39570

CAPTURE_DEVICE = 2
CAPTURE_W = 640
CAPTURE_H = 480
CAPTURE_FPS = 60

PREVIEW_W = 256
PREVIEW_H = 256

POSE_MP_NOSE = 0
POSE_MP_SHOULDER_L = 11
POSE_MP_SHOULDER_R = 12
POSE_MP_ELBOW_L = 13
POSE_MP_ELBOW_R = 14
POSE_MP_WRIST_L = 15
POSE_MP_WRIST_R = 16
POSE_MP_HIP_L = 23
POSE_MP_HIP_R = 24
POSE_MP_KNEE_L = 25
POSE_MP_KNEE_R = 26
POSE_MP_ANKLE_L = 27
POSE_MP_ANKLE_R = 28
POSE_MP_HIP = 0

MP_TRACKERS = [
    POSE_MP_SHOULDER_L,
    POSE_MP_SHOULDER_R,
    POSE_MP_ELBOW_L,
    POSE_MP_ELBOW_R,
    POSE_MP_KNEE_L,
    POSE_MP_KNEE_R,
    POSE_MP_ANKLE_L,
    POSE_MP_ANKLE_R,
]


tk_canvas: tkinter.Canvas = None
tk_label_value: tkinter.StringVar = None
tk_chk_value: tkinter.StringVar = None
vct_scale = vr_lib.CVector3(1.0, 1.0, 1.0)
vct_adjust = vr_lib.CVector3(0.0, 0.0, 0.0)


def th_capture():

    parser = argparse.ArgumentParser()
    # fmt: off
    parser.add_argument(
        "-d", "--device", type=int, default=CAPTURE_DEVICE,
        help="VideoCapture Device."
    )
    # fmt: on

    args = parser.parse_args()

    osc_cli = pythonosc.udp_client.SimpleUDPClient(VMT_OSC_HOST, VMT_OSC_PORT)

    #
    cam = cv2.VideoCapture(args.device)
    # cam.set(cv2.CAP_PROP_FPS, CAPTURE_FPS)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_W)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_H)

    print(
        "CAP_PROP: Decice {:d}, {:f} x {:f} {:f}fps".format(
            args.device,
            cam.get(cv2.CAP_PROP_FRAME_WIDTH),
            cam.get(cv2.CAP_PROP_FRAME_HEIGHT),
            cam.get(cv2.CAP_PROP_FPS),
        )
    )

    detector = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        smooth_segmentation=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    dict_tracker_history: dict[int, vr_lib.CTrackerHistory] = {}
    for idx in MP_TRACKERS:
        dict_tracker_history[idx] = vr_lib.CTrackerHistory()
    dict_tracker_history[POSE_MP_HIP] = vr_lib.CTrackerHistory()

    while cam.isOpened():

        success, image = cam.read()

        if success is False:
            break

        # 上下左右反転
        # image = cv2.flip(image, -1)

        # rot +90
        # image = image.transpose(1, 0, 2)[:, ::-1]
        # rot -90
        # image = image.transpose(1, 0, 2)[::-1]

        res = detector.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if res.pose_landmarks is None:
            continue

        if True:
            res_lm = res.pose_world_landmarks.landmark
        else:
            res_lm = res.pose_landmarks.landmark

        vct = vr_lib.calc_waist_vector(res_lm[POSE_MP_HIP_L], res_lm[POSE_MP_HIP_R])
        vct *= vct_scale
        vct *= -1
        vct += vct_adjust

        tk_label_value.set("X:{:2.2f} Y:{:2.2f} Z:{:2.2f}".format(vct.x, vct.y, vct.z))

        dict_tracker_history[POSE_MP_HIP].list_vector3.append(vct)
        vct_avg = dict_tracker_history[POSE_MP_HIP].avg()
        vr_lib.send_osc(osc_cli, POSE_MP_HIP, 1, 0.0, vct_avg)

        for idx in MP_TRACKERS:
            landmark = res_lm[idx]
            if landmark.visibility < 0.2:
                continue

            vct = vr_lib.CVector3(landmark.x, landmark.y, landmark.z)
            vct *= vct_scale
            vct *= -1
            vct += vct_adjust

            dict_tracker_history[idx].list_vector3.append(vct)
            vct_avg = dict_tracker_history[idx].avg()
            vr_lib.send_osc(osc_cli, idx, 1, 0.0, vct_avg)

        # Preview
        screen = np.zeros(image.shape, dtype=np.uint8)

        if tk_chk_value.get() == "1":

            mp.solutions.drawing_utils.draw_landmarks(
                screen,
                res.pose_landmarks,
                mp.solutions.holistic.POSE_CONNECTIONS,
            )

        pil_image = PIL.Image.fromarray(cv2.flip(screen, 1))
        pil_image.thumbnail((PREVIEW_W, PREVIEW_H), PIL.Image.Resampling.LANCZOS)

        x = int((PREVIEW_W - pil_image.width) / 2)
        y = int((PREVIEW_H - pil_image.height) / 2)

        try:
            tk_resource = PIL.ImageTk.PhotoImage(image=pil_image)
            tk_canvas.create_image(x, y, image=tk_resource, anchor="nw")
        except _tkinter.TclError:
            break
        except AttributeError:
            break

    cam.release()


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
    tk_root.title("VR CamTrack[MP]")
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
