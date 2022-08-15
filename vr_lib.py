import pythonosc.udp_client


class CVector3(object):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __init__(self, _x: float = 0.0, _y: float = 0.0, _z: float = 0.0):
        self.x = float(_x)
        self.y = float(_y)
        self.z = float(_z)

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

    @staticmethod
    def zero():
        return CVector3(0.0, 0.0, 0.0)

    @staticmethod
    def one():
        return CVector3(1.0, 1.0, 1.0)


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
