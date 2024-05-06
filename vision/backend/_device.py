from enum import IntEnum, IntFlag
import fcntl
from fractions import Fraction
import os
from pathlib import Path
from typing import Generator, NamedTuple, Sequence, Tuple, Union

from ._ioctl import (
    v4l2_capability, vidioc_querycap,
    v4l2_fmtdesc, vidioc_enum_fmt,
    v4l2_frmsizeenum, vidioc_enum_framesizes,
    v4l2_frmivalenum, vidioc_enum_frameintervals,
    v4l2_format, vidioc_g_fmt, vidioc_s_fmt, vidioc_try_fmt,
    v4l2_streamparm, vidioc_g_param, vidioc_s_param,
)


class Capabilities(IntFlag):
    VIDEO_CAPTURE = 0x00000001
    VIDEO_OUTPUT = 0x00000002
    VIDEO_OVERLAY = 0x00000004
    VBI_CAPTURE = 0x00000010
    VBI_OUTPUT = 0x00000020
    SLICED_VBI_CAPTURE = 0x00000040
    SLICED_VBI_OUTPUT = 0x00000080
    RDS_CAPTURE = 0x00000100
    VIDEO_OUTPUT_OVERLAY = 0x00000200
    HW_FREQ_SEEK = 0x00000400
    RDS_OUTPUT = 0x00000800
    VIDEO_CAPTURE_MPLANE = 0x00001000
    VIDEO_OUTPUT_MPLANE = 0x00002000
    VIDEO_M2M_MPLANE = 0x00004000
    VIDEO_M2M = 0x00008000
    TUNER = 0x00010000
    AUDIO = 0x00020000
    RADIO = 0x00040000
    MODULATOR = 0x00080000
    SDR_CAPTURE = 0x00100000
    EXT_PIX_FORMAT = 0x00200000
    SDR_OUTPUT = 0x00400000
    META_CAPTURE = 0x00800000
    READWRITE = 0x01000000
    ASYNCIO = 0x02000000
    STREAMING = 0x04000000
    META_OUTPUT = 0x08000000
    TOUCH = 0x10000000
    DEVICE_CAPS = 0x80000000


class BufferType(IntEnum):
    VIDEO_CAPTURE = 1
    VIDEO_OUTPUT = 2
    VIDEO_OVERLAY = 3
    VBI_CAPTURE = 4
    VBI_OUTPUT = 5
    SLICED_VBI_CAPTURE = 6
    SLICED_VBI_OUTPUT = 7
    VIDEO_OUTPUT_OVERLAY = 8
    VIDEO_CAPTURE_MPLANE = 9
    VIDEO_OUTPUT_MPLANE = 10
    SDR_CAPTURE = 11
    SDR_OUTPUT = 12
    META_CAPTURE = 13
    META_OUTPUT = 14


def v4l2_fourcc(a, b, c, d) -> int:
    return (
        ord(a)
        | (ord(b) << 8)
        | (ord(c) << 16)
        | (ord(d) << 24))


def v4l2_fourcc_be(a, b, c, d) -> int:
    return (
        v4l2_fourcc(a, b, c, d)
        | (1 << 31))


class PixelFormat(IntEnum):
    RGB332 = v4l2_fourcc('R', 'G', 'B', '1')  # 8  RGB-3-3-2
    RGB444 = v4l2_fourcc('R', '4', '4', '4')  # 16  xxxxrrrr ggggbbbb
    ARGB444 = v4l2_fourcc('A', 'R', '1', '2')  # 16  aaaarrrr ggggbbbb
    XRGB444 = v4l2_fourcc('X', 'R', '1', '2')  # 16  xxxxrrrr ggggbbbb
    RGBA444 = v4l2_fourcc('R', 'A', '1', '2')  # 16  rrrrgggg bbbbaaaa
    RGBX444 = v4l2_fourcc('R', 'X', '1', '2')  # 16  rrrrgggg bbbbxxxx
    ABGR444 = v4l2_fourcc('A', 'B', '1', '2')  # 16  aaaabbbb ggggrrrr
    XBGR444 = v4l2_fourcc('X', 'B', '1', '2')  # 16  xxxxbbbb ggggrrrr

    # Originally this had 'BA12' as fourcc, but this clashed with the older
    # V4L2_PIX_FMT_SGRBG12 which inexplicably used that same fourcc.
    # So use 'GA12' instead for V4L2_PIX_FMT_BGRA444.
    BGRA444 = v4l2_fourcc('G', 'A', '1', '2')  # 16  bbbbgggg rrrraaaa
    BGRX444 = v4l2_fourcc('B', 'X', '1', '2')  # 16  bbbbgggg rrrrxxxx
    RGB555 = v4l2_fourcc('R', 'G', 'B', 'O')  # 16  RGB-5-5-5
    ARGB555 = v4l2_fourcc('A', 'R', '1', '5')  # 16  ARGB-1-5-5-5
    XRGB555 = v4l2_fourcc('X', 'R', '1', '5')  # 16  XRGB-1-5-5-5
    RGBA555 = v4l2_fourcc('R', 'A', '1', '5')  # 16  RGBA-5-5-5-1
    RGBX555 = v4l2_fourcc('R', 'X', '1', '5')  # 16  RGBX-5-5-5-1
    ABGR555 = v4l2_fourcc('A', 'B', '1', '5')  # 16  ABGR-1-5-5-5
    XBGR555 = v4l2_fourcc('X', 'B', '1', '5')  # 16  XBGR-1-5-5-5
    BGRA555 = v4l2_fourcc('B', 'A', '1', '5')  # 16  BGRA-5-5-5-1
    BGRX555 = v4l2_fourcc('B', 'X', '1', '5')  # 16  BGRX-5-5-5-1
    RGB565 = v4l2_fourcc('R', 'G', 'B', 'P')  # 16  RGB-5-6-5
    RGB555X = v4l2_fourcc('R', 'G', 'B', 'Q')  # 16  RGB-5-5-5 BE
    ARGB555X = v4l2_fourcc_be('A', 'R', '1', '5')  # 16  ARGB-5-5-5 BE
    XRGB555X = v4l2_fourcc_be('X', 'R', '1', '5')  # 16  XRGB-5-5-5 BE
    RGB565X = v4l2_fourcc('R', 'G', 'B', 'R')  # 16  RGB-5-6-5 BE
    BGR666 = v4l2_fourcc('B', 'G', 'R', 'H')  # 18  BGR-6-6-6
    BGR24 = v4l2_fourcc('B', 'G', 'R', '3')  # 24  BGR-8-8-8
    RGB24 = v4l2_fourcc('R', 'G', 'B', '3')  # 24  RGB-8-8-8
    BGR32 = v4l2_fourcc('B', 'G', 'R', '4')  # 32  BGR-8-8-8-8
    ABGR32 = v4l2_fourcc('A', 'R', '2', '4')  # 32  BGRA-8-8-8-8
    XBGR32 = v4l2_fourcc('X', 'R', '2', '4')  # 32  BGRX-8-8-8-8
    BGRA32 = v4l2_fourcc('R', 'A', '2', '4')  # 32  ABGR-8-8-8-8
    BGRX32 = v4l2_fourcc('R', 'X', '2', '4')  # 32  XBGR-8-8-8-8
    RGB32 = v4l2_fourcc('R', 'G', 'B', '4')  # 32  RGB-8-8-8-8
    RGBA32 = v4l2_fourcc('A', 'B', '2', '4')  # 32  RGBA-8-8-8-8
    RGBX32 = v4l2_fourcc('X', 'B', '2', '4')  # 32  RGBX-8-8-8-8
    ARGB32 = v4l2_fourcc('B', 'A', '2', '4')  # 32  ARGB-8-8-8-8
    XRGB32 = v4l2_fourcc('B', 'X', '2', '4')  # 32  XRGB-8-8-8-8

    # Grey formats
    GREY = v4l2_fourcc('G', 'R', 'E', 'Y')  # 8  Greyscale
    Y4 = v4l2_fourcc('Y', '0', '4', ' ')  # 4  Greyscale
    Y6 = v4l2_fourcc('Y', '0', '6', ' ')  # 6  Greyscale
    Y10 = v4l2_fourcc('Y', '1', '0', ' ')  # 10  Greyscale
    Y12 = v4l2_fourcc('Y', '1', '2', ' ')  # 12  Greyscale
    Y16 = v4l2_fourcc('Y', '1', '6', ' ')  # 16  Greyscale
    Y16_BE = v4l2_fourcc_be('Y', '1', '6', ' ')  # 16  Greyscale BE

    # Grey bit-packed formats
    Y10BPACK = v4l2_fourcc('Y', '1', '0', 'B')  # 10  Greyscale bit-packed
    Y10P = v4l2_fourcc('Y', '1', '0', 'P')  # 10  Greyscale, MIPI RAW10 packed

    # Palette formats
    PAL8 = v4l2_fourcc('P', 'A', 'L', '8')  # 8  8-bit palette

    # Chrominance formats
    UV8 = v4l2_fourcc('U', 'V', '8', ' ')  # 8  UV 4:4

    # Luminance+Chrominance formats
    YUYV = v4l2_fourcc('Y', 'U', 'Y', 'V')  # 16  YUV 4:2:2
    YYUV = v4l2_fourcc('Y', 'Y', 'U', 'V')  # 16  YUV 4:2:2
    YVYU = v4l2_fourcc('Y', 'V', 'Y', 'U')  # 16 YVU 4:2:2
    UYVY = v4l2_fourcc('U', 'Y', 'V', 'Y')  # 16  YUV 4:2:2
    VYUY = v4l2_fourcc('V', 'Y', 'U', 'Y')  # 16  YUV 4:2:2
    Y41P = v4l2_fourcc('Y', '4', '1', 'P')  # 12  YUV 4:1:1
    YUV444 = v4l2_fourcc('Y', '4', '4', '4')  # 16  xxxxyyyy uuuuvvvv
    YUV555 = v4l2_fourcc('Y', 'U', 'V', 'O')  # 16  YUV-5-5-5
    YUV565 = v4l2_fourcc('Y', 'U', 'V', 'P')  # 16  YUV-5-6-5
    YUV32 = v4l2_fourcc('Y', 'U', 'V', '4')  # 32  YUV-8-8-8-8
    AYUV32 = v4l2_fourcc('A', 'Y', 'U', 'V')  # 32  AYUV-8-8-8-8
    XYUV32 = v4l2_fourcc('X', 'Y', 'U', 'V')  # 32  XYUV-8-8-8-8
    VUYA32 = v4l2_fourcc('V', 'U', 'Y', 'A')  # 32  VUYA-8-8-8-8
    VUYX32 = v4l2_fourcc('V', 'U', 'Y', 'X')  # 32  VUYX-8-8-8-8
    HI240 = v4l2_fourcc('H', 'I', '2', '4')  # 8  8-bit color
    HM12 = v4l2_fourcc('H', 'M', '1', '2')  # 8  YUV 4:2:0 16x16 macroblocks
    M420 = v4l2_fourcc('M', '4', '2', '0')  # 12  YUV 4:2:0 2 lines y, 1 line uv interleaved

    # two planes -- one Y, one Cr + Cb interleaved
    NV12 = v4l2_fourcc('N', 'V', '1', '2')  # 12  Y/CbCr 4:2:0
    NV21 = v4l2_fourcc('N', 'V', '2', '1')  # 12  Y/CrCb 4:2:0
    NV16 = v4l2_fourcc('N', 'V', '1', '6')  # 16  Y/CbCr 4:2:2
    NV61 = v4l2_fourcc('N', 'V', '6', '1')  # 16  Y/CrCb 4:2:2
    NV24 = v4l2_fourcc('N', 'V', '2', '4')  # 24  Y/CbCr 4:4:4
    NV42 = v4l2_fourcc('N', 'V', '4', '2')  # 24  Y/CrCb 4:4:4

    # two non contiguous planes - one Y, one Cr + Cb interleaved
    NV12M = v4l2_fourcc('N', 'M', '1', '2')  # 12  Y/CbCr 4:2:0
    NV21M = v4l2_fourcc('N', 'M', '2', '1')  # 21  Y/CrCb 4:2:0
    NV16M = v4l2_fourcc('N', 'M', '1', '6')  # 16  Y/CbCr 4:2:2
    NV61M = v4l2_fourcc('N', 'M', '6', '1')  # 16  Y/CrCb 4:2:2
    NV12MT = v4l2_fourcc('T', 'M', '1', '2')  # 12  Y/CbCr 4:2:0 64x32 macroblocks
    NV12MT_16X16 = v4l2_fourcc('V', 'M', '1', '2')  # 12  Y/CbCr 4:2:0 16x16 macroblocks

    # three planes - Y Cb, Cr
    YUV410 = v4l2_fourcc('Y', 'U', 'V', '9')  # 9  YUV 4:1:0
    YVU410 = v4l2_fourcc('Y', 'V', 'U', '9')  # 9  YVU 4:1:0
    YUV411P = v4l2_fourcc('4', '1', '1', 'P')  # 12  YVU411 planar
    YUV420 = v4l2_fourcc('Y', 'U', '1', '2')  # 12  YUV 4:2:0
    YVU420 = v4l2_fourcc('Y', 'V', '1', '2')  # 12  YVU 4:2:0
    YUV422P = v4l2_fourcc('4', '2', '2', 'P')  # 16  YVU422 planar

    # three non contiguous planes - Y, Cb, Cr
    YUV420M = v4l2_fourcc('Y', 'M', '1', '2')  # 12  YUV420 planar
    YVU420M = v4l2_fourcc('Y', 'M', '2', '1')  # 12  YVU420 planar
    YUV422M = v4l2_fourcc('Y', 'M', '1', '6')  # 16  YUV422 planar
    YVU422M = v4l2_fourcc('Y', 'M', '6', '1')  # 16  YVU422 planar
    YUV444M = v4l2_fourcc('Y', 'M', '2', '4')  # 24  YUV444 planar
    YVU444M = v4l2_fourcc('Y', 'M', '4', '2')  # 24  YVU444 planar

    # Bayer formats - see http://www.siliconimaging.com/RGB%20Bayer.htm
    SBGGR8 = v4l2_fourcc('B', 'A', '8', '1')  # 8  BGBG.. GRGR..
    SGBRG8 = v4l2_fourcc('G', 'B', 'R', 'G')  # 8  GBGB.. RGRG..
    SGRBG8 = v4l2_fourcc('G', 'R', 'B', 'G')  # 8  GRGR.. BGBG..
    SRGGB8 = v4l2_fourcc('R', 'G', 'G', 'B')  # 8  RGRG.. GBGB..
    SBGGR10 = v4l2_fourcc('B', 'G', '1', '0')  # 10  BGBG.. GRGR..
    SGBRG10 = v4l2_fourcc('G', 'B', '1', '0')  # 10  GBGB.. RGRG..
    SGRBG10 = v4l2_fourcc('B', 'A', '1', '0')  # 10  GRGR.. BGBG..
    SRGGB10 = v4l2_fourcc('R', 'G', '1', '0')  # 10  RGRG.. GBGB..

    # 10bit raw bayer packed, 5 bytes for every 4 pixels
    SBGGR10P = v4l2_fourcc('p', 'B', 'A', 'A')
    SGBRG10P = v4l2_fourcc('p', 'G', 'A', 'A')
    SGRBG10P = v4l2_fourcc('p', 'g', 'A', 'A')
    SRGGB10P = v4l2_fourcc('p', 'R', 'A', 'A')

    # 10bit raw bayer a-law compressed to 8 bits
    SBGGR10ALAW8 = v4l2_fourcc('a', 'B', 'A', '8')
    SGBRG10ALAW8 = v4l2_fourcc('a', 'G', 'A', '8')
    SGRBG10ALAW8 = v4l2_fourcc('a', 'g', 'A', '8')
    SRGGB10ALAW8 = v4l2_fourcc('a', 'R', 'A', '8')

    # 10bit raw bayer DPCM compressed to 8 bits
    SBGGR10DPCM8 = v4l2_fourcc('b', 'B', 'A', '8')
    SGBRG10DPCM8 = v4l2_fourcc('b', 'G', 'A', '8')
    SGRBG10DPCM8 = v4l2_fourcc('B', 'D', '1', '0')
    SRGGB10DPCM8 = v4l2_fourcc('b', 'R', 'A', '8')
    SBGGR12 = v4l2_fourcc('B', 'G', '1', '2')  # 12  BGBG.. GRGR..
    SGBRG12 = v4l2_fourcc('G', 'B', '1', '2')  # 12  GBGB.. RGRG..
    SGRBG12 = v4l2_fourcc('B', 'A', '1', '2')  # 12  GRGR.. BGBG..
    SRGGB12 = v4l2_fourcc('R', 'G', '1', '2')  # 12  RGRG.. GBGB..

    # 12bit raw bayer packed, 6 bytes for every 4 pixels
    SBGGR12P = v4l2_fourcc('p', 'B', 'C', 'C')
    SGBRG12P = v4l2_fourcc('p', 'G', 'C', 'C')
    SGRBG12P = v4l2_fourcc('p', 'g', 'C', 'C')
    SRGGB12P = v4l2_fourcc('p', 'R', 'C', 'C')

    # 14bit raw bayer packed, 7 bytes for every 4 pixels
    SBGGR14P = v4l2_fourcc('p', 'B', 'E', 'E')
    SGBRG14P = v4l2_fourcc('p', 'G', 'E', 'E')
    SGRBG14P = v4l2_fourcc('p', 'g', 'E', 'E')
    SRGGB14P = v4l2_fourcc('p', 'R', 'E', 'E')
    SBGGR16 = v4l2_fourcc('B', 'Y', 'R', '2')  # 16  BGBG.. GRGR..
    SGBRG16 = v4l2_fourcc('G', 'B', '1', '6')  # 16  GBGB.. RGRG..
    SGRBG16 = v4l2_fourcc('G', 'R', '1', '6')  # 16  GRGR.. BGBG..
    SRGGB16 = v4l2_fourcc('R', 'G', '1', '6')  # 16  RGRG.. GBGB..

    # HSV formats
    HSV24 = v4l2_fourcc('H', 'S', 'V', '3')
    HSV32 = v4l2_fourcc('H', 'S', 'V', '4')

    # compressed formats
    MJPEG = v4l2_fourcc('M', 'J', 'P', 'G')  # Motion-JPEG
    JPEG = v4l2_fourcc('J', 'P', 'E', 'G')  # JFIF JPEG
    DV = v4l2_fourcc('d', 'v', 's', 'd')  # 1394
    MPEG = v4l2_fourcc('M', 'P', 'E', 'G')  # MPEG-1/2/4 Multiplexed
    H264 = v4l2_fourcc('H', '2', '6', '4')  # H264 with start codes
    H264_NO_SC = v4l2_fourcc('A', 'V', 'C', '1')  # H264 without start codes
    H264_MVC = v4l2_fourcc('M', '2', '6', '4')  # H264 MVC
    H263 = v4l2_fourcc('H', '2', '6', '3')  # H263
    MPEG1 = v4l2_fourcc('M', 'P', 'G', '1')  # MPEG-1 ES
    MPEG2 = v4l2_fourcc('M', 'P', 'G', '2')  # MPEG-2 ES
    MPEG2_SLICE = v4l2_fourcc('M', 'G', '2', 'S')  # MPEG-2 parsed slice data
    MPEG4 = v4l2_fourcc('M', 'P', 'G', '4')  # MPEG-4 part 2 ES
    XVID = v4l2_fourcc('X', 'V', 'I', 'D')  # Xvid
    VC1_ANNEX_G = v4l2_fourcc('V', 'C', '1', 'G')  # SMPTE 421M Annex G compliant stream
    VC1_ANNEX_L = v4l2_fourcc('V', 'C', '1', 'L')  # SMPTE 421M Annex L compliant stream
    VP8 = v4l2_fourcc('V', 'P', '8', '0')  # VP8
    VP9 = v4l2_fourcc('V', 'P', '9', '0')  # VP9
    HEVC = v4l2_fourcc('H', 'E', 'V', 'C')  # HEVC aka H.265
    FWHT = v4l2_fourcc('F', 'W', 'H', 'T')  # Fast Walsh Hadamard Transform (vicodec)
    FWHT_STATELESS = v4l2_fourcc('S', 'F', 'W', 'H')  # Stateless FWHT (vicodec)

    # Vendor-specific formats
    CPIA1 = v4l2_fourcc('C', 'P', 'I', 'A')  # cpia1 YUV
    WNVA = v4l2_fourcc('W', 'N', 'V', 'A')  # Winnov hw compress
    SN9C10X = v4l2_fourcc('S', '9', '1', '0')  # SN9C10x compression
    SN9C20X_I420 = v4l2_fourcc('S', '9', '2', '0')  # SN9C20x YUV 4:2:0
    PWC1 = v4l2_fourcc('P', 'W', 'C', '1')  # pwc older webcam
    PWC2 = v4l2_fourcc('P', 'W', 'C', '2')  # pwc newer webcam
    ET61X251 = v4l2_fourcc('E', '6', '2', '5')  # ET61X251 compression
    SPCA501 = v4l2_fourcc('S', '5', '0', '1')  # YUYV per line
    SPCA505 = v4l2_fourcc('S', '5', '0', '5')  # YYUV per line
    SPCA508 = v4l2_fourcc('S', '5', '0', '8')  # YUVY per line
    SPCA561 = v4l2_fourcc('S', '5', '6', '1')  # compressed GBRG bayer
    PAC207 = v4l2_fourcc('P', '2', '0', '7')  # compressed BGGR bayer
    MR97310A = v4l2_fourcc('M', '3', '1', '0')  # compressed BGGR bayer
    JL2005BCD = v4l2_fourcc('J', 'L', '2', '0')  # compressed RGGB bayer
    SN9C2028 = v4l2_fourcc('S', 'O', 'N', 'X')  # compressed GBRG bayer
    SQ905C = v4l2_fourcc('9', '0', '5', 'C')  # compressed RGGB bayer
    PJPG = v4l2_fourcc('P', 'J', 'P', 'G')  # Pixart 73xx JPEG
    OV511 = v4l2_fourcc('O', '5', '1', '1')  # ov511 JPEG
    OV518 = v4l2_fourcc('O', '5', '1', '8')  # ov518 JPEG
    STV0680 = v4l2_fourcc('S', '6', '8', '0')  # stv0680 bayer
    TM6000 = v4l2_fourcc('T', 'M', '6', '0')  # tm5600/tm60x0
    CIT_YYVYUY = v4l2_fourcc('C', 'I', 'T', 'V')  # one line of Y then 1 line of VYUY
    KONICA420 = v4l2_fourcc('K', 'O', 'N', 'I')  # YUV420 planar in blocks of 256 pixels
    JPGL = v4l2_fourcc('J', 'P', 'G', 'L')  # JPEG-Lite
    SE401 = v4l2_fourcc('S', '4', '0', '1')  # se401 janggu compressed rgb
    S5C_UYVY_JPG = v4l2_fourcc('S', '5', 'C', 'I')  # S5C73M3 interleaved UYVY/JPEG
    Y8I = v4l2_fourcc('Y', '8', 'I', ' ')  # Greyscale 8-bit L/R interleaved
    Y12I = v4l2_fourcc('Y', '1', '2', 'I')  # Greyscale 12-bit L/R interleaved
    Z16 = v4l2_fourcc('Z', '1', '6', ' ')  # Depth data 16-bit
    MT21C = v4l2_fourcc('M', 'T', '2', '1')  # Mediatek compressed block mode
    INZI = v4l2_fourcc('I', 'N', 'Z', 'I')  # Intel Planar Greyscale 10-bit and Depth 16-bit
    SUNXI_TILED_NV12 = v4l2_fourcc('S', 'T', '1', '2')  # Sunxi Tiled NV12 Format
    CNF4 = v4l2_fourcc('C', 'N', 'F', '4')  # Intel 4-bit packed depth confidence information

    # 10bit raw bayer packed, 32 bytes for every 25 pixels, last LSB 6 bits unused
    IPU3_SBGGR10 = v4l2_fourcc('i', 'p', '3', 'b')  # IPU3 packed 10-bit BGGR bayer
    IPU3_SGBRG10 = v4l2_fourcc('i', 'p', '3', 'g')  # IPU3 packed 10-bit GBRG bayer
    IPU3_SGRBG10 = v4l2_fourcc('i', 'p', '3', 'G')  # IPU3 packed 10-bit GRBG bayer
    IPU3_SRGGB10 = v4l2_fourcc('i', 'p', '3', 'r')  # IPU3 packed 10-bit RGGB bayer

    # priv field value to indicates that subsequent fields are valid.
    PRIV_MAGIC = 0xfeedcafe

    # Flags
    FLAG_PREMUL_ALPHA = 0x00000001


class ImageFormatDescriptionFlags(IntFlag):
    COMPRESSED = 0x0001
    EMULATED = 0x0002
    CONTINUOUS_BYTESTREAM = 0x0004
    DYN_RESOLUTION = 0x0008
    ENC_CAP_FRAME_INTERVAL = 0x0010
    CSC_COLORSPACE = 0x0020
    CSC_XFER_FUNC = 0x0040
    CSC_YCBCR_ENC = 0x0080
    CSC_HSV_ENC = 0x0080
    CSC_QUANTIZATION = 0x0100


class ImageFormat(NamedTuple):
    type: BufferType
    flags: ImageFormatDescriptionFlags
    pixel_format: PixelFormat
    description: str
    mbus_code: int


class FrameSizeType(IntEnum):
    DISCRETE = 1
    CONTINUOUS = 2
    STEPWISE = 3


class DiscreteFrameSize(NamedTuple):
    pixel_format: PixelFormat
    width: int
    height: int

    def __repr__(self):
        return f"{self.height}x{self.width}"


class StepwiseFrameSize(NamedTuple):
    pixel_format: PixelFormat
    min_width: int
    max_width: int
    step_width: int
    min_height: int
    max_height: int
    step_height: int

    def __repr__(self):
        return "x".join([
            f"{self.min_height}/{self.max_height}/{self.step_height}",
            f"{self.min_width}/{self.max_width}/{self.step_width}",
        ])


def iter_image_formats(fd, buffer_type: BufferType) -> Generator[ImageFormat, None, None]:
    index = 0

    while True:
        buf = v4l2_fmtdesc()
        buf.index = index
        buf.type = buffer_type

        try:
            vidioc_enum_fmt(fd, buf)
            yield ImageFormat(
                type=buffer_type,
                flags=ImageFormatDescriptionFlags(buf.flags),
                description=buf.description.decode(),
                pixel_format=PixelFormat(buf.pixelformat),
                mbus_code=buf.mbus_code)
            index += 1
        except OSError:
            break


def iter_frame_sizes(fd, pixel_format: PixelFormat) -> Generator[Union[DiscreteFrameSize, StepwiseFrameSize], None, None]:
    index = 0

    while True:
        buf = v4l2_frmsizeenum()
        buf.index = index
        buf.pixel_format = pixel_format

        try:
            vidioc_enum_framesizes(fd, buf)

            if FrameSizeType(buf.type) == FrameSizeType.STEPWISE:
                yield StepwiseFrameSize(
                    pixel_format=pixel_format,
                    min_width=buf.m.stepwise.min_width,
                    max_width=buf.m.stepwise.max_width,
                    step_width=buf.m.stepwise.step_width,
                    min_height=buf.m.stepwise.min_height,
                    max_height=buf.m.stepwise.max_height,
                    step_height=buf.m.stepwise.step_height,
                )
            elif FrameSizeType(buf.type) == FrameSizeType.DISCRETE:
                yield DiscreteFrameSize(
                    pixel_format=pixel_format,
                    width=buf.m.discrete.width,
                    height=buf.m.discrete.height,
                )

            index += 1
        except OSError:
            break


class FrameIntervalType(IntEnum):
    DISCRETE = 1
    CONTINUOUS = 2
    STEPWISE = 3


class DiscreteFrameInterval(NamedTuple):
    pixel_format: PixelFormat
    width: int
    height: int
    fraction: Fraction

    def __float__(self):
        return self.fraction.denominator / self.fraction.numerator


class StepwiseFrameInterval(NamedTuple):
    pixel_format: PixelFormat
    width: int
    height: int
    min: Fraction
    max: Fraction
    step: Fraction


def iter_frame_intervals(fd, pixel_format: PixelFormat, width: int, height: int) -> Generator[None, None, None]:
    index = 0

    while True:
        buf = v4l2_frmivalenum()
        buf.index = index
        buf.pixel_format = pixel_format
        buf.width = width
        buf.height = height

        try:
            vidioc_enum_frameintervals(fd, buf)

            if FrameIntervalType(buf.type) == FrameIntervalType.DISCRETE:
                yield DiscreteFrameInterval(
                    pixel_format=pixel_format,
                    width=width,
                    height=height,
                    fraction=Fraction(buf.m.discrete.numerator, buf.m.discrete.denominator))
            elif FrameIntervalType(buf.type) == FrameIntervalType.STEPWISE:
                yield StepwiseFrameInterval(
                    pixel_format=pixel_format,
                    width=width,
                    height=height,
                    min=Fraction(buf.m.stepwise.min.numerator, buf.m.stepwise.min.denominator),
                    max=Fraction(buf.m.stepwise.max.numerator, buf.m.stepwise.max.denominator),
                    step=Fraction(buf.m.stepwise.step.numerator, buf.m.stepwise.step.denominator),
                )

            index += 1
        except OSError:
            break


class DeviceInfo(NamedTuple):
    driver: str
    card: str
    bus_info: str
    version: Tuple[int, int, int]
    capabilities: Capabilities
    device_capabilities: Capabilities
    image_formats: Sequence[ImageFormat]
    frame_sizes: Sequence[Union[DiscreteFrameSize, StepwiseFrameSize]]
    frame_intervals: Sequence[Union[DiscreteFrameInterval, StepwiseFrameInterval]]

    @classmethod
    def from_file(cls, fd):
        buf = v4l2_capability()
        vidioc_querycap(fd, buf)

        # What formats does the device support?
        device_capabilities = Capabilities(buf.device_caps)
        supported_buffer_types = {
            BufferType.VIDEO_CAPTURE, BufferType.VIDEO_CAPTURE_MPLANE,
            BufferType.VIDEO_OUTPUT, BufferType.VIDEO_OUTPUT_MPLANE,
            BufferType.VIDEO_OVERLAY,
            BufferType.SDR_CAPTURE, BufferType.SDR_OUTPUT,
            BufferType.META_CAPTURE, BufferType.META_OUTPUT,
        }
        device_buffer_types = {typ for typ in BufferType if Capabilities[typ.name] in device_capabilities}

        image_formats = []
        pixel_formats = set()
        for buffer_type in (supported_buffer_types & device_buffer_types):
            for image_format in iter_image_formats(fd, buffer_type):
                image_formats.append(image_format)
                pixel_formats.add(image_format.pixel_format)

        frame_sizes = [frame_size for pixel_format in pixel_formats for frame_size in iter_frame_sizes(fd, pixel_format)]

        frame_intervals = []
        for frame_size in frame_sizes:
            if isinstance(frame_size, DiscreteFrameSize):
                frame_intervals.extend([frame_interval for frame_interval in
                                        iter_frame_intervals(fd, frame_size.pixel_format, frame_size.width, frame_size.height)])

        return cls(
            driver=buf.driver.decode(),
            card=buf.card.decode(),
            bus_info=buf.bus_info.decode(),
            version=(
                (buf.version >> 16) & 0xFF,
                (buf.version >> 8) & 0xFF,
                buf.version & 0xFF),
            capabilities=Capabilities(buf.capabilities),
            device_capabilities=Capabilities(buf.device_caps),
            image_formats=image_formats,
            frame_sizes=frame_sizes,
            frame_intervals=frame_intervals,
        )

    @property
    def pixel_formats(self):
        return {fmt.pixel_format for fmt in self.image_formats}

    def get_frame_sizes_for_pixel_format(self, pixel_format: PixelFormat):
        pass

    def get_frame_intervals_for_frame_size(self, pixel_format: PixelFormat, width: int, height: int):
        pass


class Field(IntEnum):
    ANY = 0
    NONE = 1
    TOP = 2
    BOTTOM = 3
    INTERLACED = 4
    SEQ_TB = 5
    SEQ_BT = 6
    ALTERNATE = 7
    INTERLACED_TB = 8
    INTERLACED_BT = 9


class ColorSpace(IntEnum):
    DEFAULT = 0
    SMPTE170M = 1
    SMPTE240M = 2
    REC709 = 3
    BT878 = 4
    SYSTEM_M_470 = 5
    SYSTEM_BG_470 = 6
    JPEG = 7
    SRGB = 8
    OPRGB = 9
    BT2020 = 10
    RAW = 11
    DCI_P3 = 12


PRIV_MAGIC = 0xfeedcafe


class FormatFlags(IntFlag):
    PREMUL_ALPHA = 0x00000001
    SET_CSC = 0x00000002


class Quantization(IntEnum):
    DEFAULT = 0
    FULL_RANGE = 1
    LIM_RANGE = 2


class XferFunc(IntEnum):
    DEFAULT = 0
    _709 = 1
    SRGB = 2
    OPRGB = 3
    SMPTE240M = 4
    NONE = 5
    DCI_P3 = 6
    SMPTE2084 = 7


class Format:
    width: int
    height: int
    pixel_format: PixelFormat
    field: Field
    bytes_per_line: int
    size_image: int
    color_space: ColorSpace
    flags: FormatFlags
    quantization: Quantization
    xfer_func: XferFunc


class CaptureParm(NamedTuple):
    capability: int
    capture_mode: int
    time_per_frame: Fraction
    extended_mode: int
    read_buffers: int


class OutputParm(NamedTuple):
    capability: int
    output_mode: int
    time_per_frame: Fraction
    extended_mode: int
    write_buffers: int


class Device:
    @classmethod
    def from_file(cls, path: Path):
        return cls(path=path)

    def __init__(self, path: Path):
        self.path = path

        self.info = None
        self.fd = None

    def __enter__(self):
        if self.fd is None:
            self.fd = open(self.path, "r")
            fl_flag = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, fl_flag | os.O_NONBLOCK)

            self.info = DeviceInfo.from_file(self.fd)

            return self

    def __exit__(self, *exc):
        if self.fd is not None:
            self.fd.close()

    def get_format(self, buffer_type: BufferType):
        buf = v4l2_format()
        buf.type = buffer_type
        vidioc_g_fmt(self.fd, buf)

        return None
        # return Format(
        #     width=buf.fmt.pix.width,
        #     height=buf.fmt.pix.height,
        #     pixel_format=PixelFormat(buf.fmt.pix.pixelformat),
        #     field=Field(buf.fmt.pix.field),
        #     bytes_per_line=buf.fmt.pix.bytesperline,
        #     size_image=buf.fmt.pix.sizeimage,
        #     color_space=ColorSpace(buf.fmt.pix.colorspace),
        #     flags=
        # )

    def set_format(self, buffer_type: BufferType, pixel_format: PixelFormat, width: int, height: int):
        buf = v4l2_format()
        buf.type = buffer_type
        buf.fmt.pix.pixelformat = pixel_format
        buf.fmt.pix.width = width
        buf.fmt.pix.height = height
        vidioc_s_fmt(self.fd, buf)

    def get_param(self, buffer_type: BufferType):
        buf = v4l2_streamparm()
        buf.type = buffer_type
        vidioc_g_param(self.fd, buf)

        if BufferType(buf.type) == BufferType.VIDEO_CAPTURE:
            return CaptureParm(
                capability=buf.parm.capture.capability,
                capture_mode=buf.parm.capture.capturemode,
                time_per_frame=Fraction(
                    buf.parm.capture.timeperframe.numerator,
                    buf.parm.capture.timeperframe.denominator),
                extended_mode=buf.parm.capture.extendedmode,
                read_buffers=buf.parm.capture.readbuffers,
            )
        elif BufferType(buf.type) == BufferType.VIDEO_OUTPUT:
            return OutputParm(
                capability=buf.parm.output.capability,
                capture_mode=buf.parm.output.outputmode,
                time_per_frame=Fraction(
                    buf.parm.output.timeperframe.numerator,
                    buf.parm.output.timeperframe.denominator),
                extended_mode=buf.parm.output.extendedmode,
                read_buffers=buf.parm.output.writebuffers,
            )

    def set_param(self):
        pass


def iter_video_capture_files(root: Path = Path("/dev"), prefix: str = "video") -> Generator[Path, None, None]:
    for g in root.glob(f"{prefix}*"):
        with open(g, "r") as fd:
            buf = v4l2_capability()
            vidioc_querycap(fd, buf)

            caps = Capabilities(buf.device_caps)

            if Capabilities.VIDEO_CAPTURE in caps:
                yield g


def iter_video_capture_devices(root: Path = Path("/dev"), prefix: str = "video") -> Generator[Device, None, None]:
    yield from (Device.from_file(g) for g in iter_video_capture_files(root, prefix))
