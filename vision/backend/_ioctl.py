import ctypes
from enum import IntFlag
from fcntl import ioctl
from typing import Generic, Type, TypeVar


IOC_STRUCT = TypeVar("IOC_STRUCT", bound=ctypes.Structure)


class IOCDirection(IntFlag):
    NONE = 0
    WRITE = 1
    READ = 2


NRBITS = 8
TYPEBITS = 8
SIZEBITS = 14
DIRBITS = 2

NRSHIFT = 0
TYPESHIFT = NRSHIFT + NRBITS
SIZESHIFT = TYPESHIFT + TYPEBITS
DIRSHIFT = SIZESHIFT + SIZEBITS


class IOC(Generic[IOC_STRUCT]):
    def __init__(self, direction: IOCDirection, number: int, size: Type):
        magic = ord("V")

        self.request = (
            ctypes.c_int32(direction << DIRSHIFT).value
            | ctypes.c_int32(magic << TYPESHIFT).value
            | ctypes.c_int32(number << NRSHIFT).value
            | ctypes.c_int32(ctypes.sizeof(size) << SIZESHIFT).value
        )

    def __call__(self, fd: int, arg: IOC_STRUCT):
        ioctl(fd, self.request, arg)


class IOR(IOC):
    def __init__(self, number: int, size: Type):
        super(IOR, self).__init__(IOCDirection.READ, number, size)


class IOW(IOC):
    def __init__(self, number: int, size: Type):
        super(IOW, self).__init__(IOCDirection.WRITE, number, size)


class IOWR(IOC):
    def __init__(self, number: int, size: Type):
        super(IOWR, self).__init__(IOCDirection.WRITE | IOCDirection.READ, number, size)


class v4l2_capability(ctypes.Structure):
    _fields_ = [
        ("driver", ctypes.c_char * 16),
        ("card", ctypes.c_char * 32),
        ("bus_info", ctypes.c_char * 32),
        ("version", ctypes.c_uint32),
        ("capabilities", ctypes.c_uint32),
        ("device_caps", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 3),
    ]


vidioc_querycap = IOR(0, v4l2_capability)


class v4l2_fmtdesc(ctypes.Structure):
    _fields_ = [
        ("index", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("description", ctypes.c_char * 32),
        ("pixelformat", ctypes.c_uint32),
        ("mbus_code", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 3),
    ]


vidioc_enum_fmt = IOWR(2, v4l2_fmtdesc)


class v42l_frmsize_discrete(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
    ]


class v4l2_frmsize_stepwise(ctypes.Structure):
    _fields_ = [
        ("min_width", ctypes.c_uint32),
        ("max_width", ctypes.c_uint32),
        ("step_width", ctypes.c_uint32),
        ("min_height", ctypes.c_uint32),
        ("max_height", ctypes.c_uint32),
        ("step_height", ctypes.c_uint32),
    ]


class v42l_frmsizeenum_anon(ctypes.Union):
    _fields_ = [
        ("discrete", v42l_frmsize_discrete),
        ("stepwise", v4l2_frmsize_stepwise)
    ]


class v4l2_frmsizeenum(ctypes.Structure):
    _fields_ = [
        ("index", ctypes.c_uint32),
        ("pixel_format", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("m", v42l_frmsizeenum_anon),
        ("reserved", ctypes.c_uint32 * 2),
    ]


vidioc_enum_framesizes = IOWR(74, v4l2_frmsizeenum)


class v4l2_fract(ctypes.Structure):
    _fields_ = [
        ("numerator", ctypes.c_uint32),
        ("denominator", ctypes.c_uint32),
    ]


class v4l2_frmival_stepwise(ctypes.Structure):
    _fields_ = [
        ("min", v4l2_fract),
        ("max", v4l2_fract),
        ("step", v4l2_fract),
    ]


class v4l2_frmivalenum_anon(ctypes.Union):
    _fields_ = [
        ("discrete", v4l2_fract),
        ("stepwise", v4l2_frmival_stepwise)
    ]


class v4l2_frmivalenum(ctypes.Structure):
    _fields_ = [
        ("index", ctypes.c_uint32),
        ("pixel_format", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("m", v4l2_frmivalenum_anon),
        ("reserved", ctypes.c_uint32 * 2),
    ]


vidioc_enum_frameintervals = IOWR(75, v4l2_frmivalenum)


class v4l2_pix_format_anon(ctypes.Union):
    _fields_ = [
        ("ycbcr_enc", ctypes.c_uint32),
        ("hsv_enc", ctypes.c_uint32),
    ]


class v4l2_pix_format(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("pixelformat", ctypes.c_uint32),
        ("field", ctypes.c_uint32),
        ("bytesperline", ctypes.c_uint32),
        ("sizeimage", ctypes.c_uint32),
        ("colorspace", ctypes.c_uint32),
        ("priv", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("m", v4l2_pix_format_anon),
        ("quantization", ctypes.c_uint32),
        ("xfer_func", ctypes.c_uint32),
    ]


class v4l2_plane_pix_format(ctypes.Structure):
    _fields_ = [
        ("sizeimage", ctypes.c_uint32),
        ("bytesperline", ctypes.c_uint32),
        ("reserved", ctypes.c_uint16 * 6),
    ]


class v4l2_pix_format_mplane(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("pixelformat", ctypes.c_uint32),
        ("field", ctypes.c_uint32),
        ("colorspace", ctypes.c_uint32),
        ("plane_fmt", v4l2_plane_pix_format * 8),
        ("num_planes", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("m", v4l2_pix_format_anon),
        ("quantization", ctypes.c_uint8),
        ("xfer_func", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 7),
    ]


class v4l2_rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_uint32),
        ("top", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32)
    ]


class v4l2_clip(ctypes.Structure):
    pass


v4l2_clip._fields_ = [
        ("c", v4l2_rect),
        ("next", ctypes.POINTER(v4l2_clip))
    ]


class v4l2_window(ctypes.Structure):
    _fields_ = [
        ("w", v4l2_rect),
        ("field", ctypes.c_uint32),
        ("chromakey", ctypes.c_uint32),
        ("clips", ctypes.POINTER(v4l2_clip)),
        ("clipcount", ctypes.c_uint32),
        ("bitmap", ctypes.POINTER(None)),
        ("global_alpha", ctypes.c_uint8),
    ]


class v4l2_vbi_format(ctypes.Structure):
    _fields_ = [
        ("sampling_rate", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("samples_per_line", ctypes.c_uint32),
        ("sample_format", ctypes.c_uint32),
        ("start", ctypes.c_int32 * 2),
        ("count", ctypes.c_uint32 * 2),
        ("flags", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 2),
    ]


class v4l2_sliced_vbi_format(ctypes.Structure):
    _fields_ = [
        ("service_set", ctypes.c_uint16),
        ("service_lines", ctypes.c_uint16 * 24 * 2),
        ("io_size", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 2),
    ]


class v4l2_sdr_format(ctypes.Structure):
    _fields_ = [
        ("pixelformat", ctypes.c_uint32),
        ("buffersize", ctypes.c_uint32),
        ("reserved", ctypes.c_uint8 * 24)
    ]


class v4l2_meta_format(ctypes.Structure):
    _fields_ = [
        ("dataformat", ctypes.c_uint32),
        ("buffersize", ctypes.c_uint32)
    ]


class v4l2_format_fmt(ctypes.Union):
    _fields_ = [
        ("pix", v4l2_pix_format),
        ("pix_mp", v4l2_pix_format_mplane),
        ("win", v4l2_window),
        ("vbi", v4l2_vbi_format),
        ("sliced", v4l2_sliced_vbi_format),
        ("sdr", v4l2_sdr_format),
        ("meta", v4l2_meta_format),
        ("raw_data", ctypes.c_uint8 * 200),
    ]


class v4l2_format(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("fmt", v4l2_format_fmt)
    ]


vidioc_g_fmt = IOWR(4, v4l2_format)
vidioc_s_fmt = IOWR(5, v4l2_format)
vidioc_try_fmt = IOWR(64, v4l2_format)


class v4l2_captureparm(ctypes.Structure):
    _fields_ = [
        ("capability", ctypes.c_uint32),
        ("capturemode", ctypes.c_uint32),
        ("timeperframe", v4l2_fract),
        ("extendedmode", ctypes.c_uint32),
        ("readbuffers", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 4)
    ]


class v4l2_outputparam(ctypes.Structure):
    _fields_ = [
        ("capability", ctypes.c_uint32),
        ("outputmode", ctypes.c_uint32),
        ("timeperframe", v4l2_fract),
        ("extendedmode", ctypes.c_uint32),
        ("writebuffers", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 4)
    ]


class v4l2_streamparm_parm(ctypes.Union):
    _fields_ = [
        ("capture", v4l2_captureparm),
        ("output", v4l2_outputparam),
    ]


class v4l2_streamparm(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("parm", v4l2_streamparm_parm),
        ("raw_data", ctypes.c_uint8 * 200)
    ]


vidioc_g_param = IOWR(21, v4l2_streamparm)
vidioc_s_param = IOWR(22, v4l2_streamparm)
