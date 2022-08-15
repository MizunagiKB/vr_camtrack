"""
https://github.com/yoshihiro1909/mediapipe_to_vrchat
https://github.com/gpsnmeajp/VirtualMotionTracker/

use: VMT 0.12
"""
import time
import argparse
import threading


# KinectV2
from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import pythonosc.udp_client

import vr_lib
import vr_ui

VMT_OSC_HOST = "127.0.0.1"
VMT_OSC_PORT = 39570


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


def th_capture(o_ui: vr_ui.CUserInterface, args: argparse.Namespace):

    osc_cli = pythonosc.udp_client.SimpleUDPClient(VMT_OSC_HOST, VMT_OSC_PORT)

    o_kinect = PyKinectRuntime.PyKinectRuntime(
        PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body
    )

    dict_tracker_history: dict[int, vr_lib.CTrackerHistory] = {}
    for idx in KN_TRACKERS:
        dict_tracker_history[idx] = vr_lib.CTrackerHistory()
    dict_tracker_history[POSE_KN_HIP] = vr_lib.CTrackerHistory()

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

                vct = vr_lib.calc_waist_vector(
                    list_joint[POSE_KN_HIP_L].Position,
                    list_joint[POSE_KN_HIP_R].Position,
                )
                vct *= o_ui.vct_scale
                vct += o_ui.vct_adjust
                vct.z *= -1

                o_ui.tk_label_value.set(
                    "{:2.2f} {:2.2f} {:2.2f}".format(vct.x, vct.y, vct.z)
                )

                dict_tracker_history[POSE_KN_HIP].list_vector3.append(vct)
                vct_avg = dict_tracker_history[POSE_KN_HIP].avg()
                vr_lib.send_osc(osc_cli, POSE_KN_HIP, 1, 0.0, vct_avg)

                for idx in KN_TRACKERS:
                    joint = list_joint[idx]

                    vct = vr_lib.CVector3(
                        joint.Position.x, joint.Position.y, joint.Position.z
                    )
                    vct *= o_ui.vct_scale
                    vct += o_ui.vct_adjust
                    vct.z *= -1

                    dict_tracker_history[idx].list_vector3.append(vct)
                    vct_avg = dict_tracker_history[idx].avg()
                    vr_lib.send_osc(osc_cli, idx, 1, 0.0, vct_avg)


def main():

    parser = argparse.ArgumentParser()
    # fmt: off
    # fmt: on

    args = parser.parse_args()

    o_ui = vr_ui.CUserInterface()

    th = threading.Thread(target=th_capture, args=(o_ui, args))
    th.start()

    o_ui.tk_root.mainloop()


if __name__ == "__main__":
    main()
