# VR CameraTracking for VRChat

MotionTracking for VRChat

## About VR CameraTrack

[Google MediaPipe](https://google.github.io/mediapipe/) Google MediaPipe、Microsoft KinectV2を使用してモーショントラッキングをするためのソフトウェアで、主にVRChatでの使用を想定しています。

このソフトウェアは、トラッキングポイントの取得とOSCの送信しか行いません。
VRChat側にTracker情報を送信するには、別途 [Virtual Motion Tracker](https://github.com/gpsnmeajp/VirtualMotionTracker) が必要となります。

## 同梱のPyKinectV2について

vr_camtrack_kn.py の内部で [PyKinectV2](https://github.com/Kinect/PyKinect2) を使用しています。

このモジュールは古いため、手元の環境（Windows 10 64bit + Python 3.9.12）で動作しなかったため、モジュールを同梱しています。
