from math import ceil
from construct import *
import struct

# CANTP: CAN transfer protocol adapted from ISO 15765-2
# https://en.wikipedia.org/wiki/ISO_15765-2
# https://stackoverflow.com/questions/34783297/can-for-large-packets-of-data-exchange-without-using-standard-protocols

CAN_FRAME_MAX_SIZE = 8

CANTP_MODE_STREAM = 1
CANTP_MODE_CHUNKS = 2
CANTP_MODE_CRC32  = 4

CANTP_BUFFER_SIZE = 32
CANTP_STREAM_TRANSFER_SIZE = 8

CANTPSingleFrame = Struct(
    "code" / Const(0, Hex(Int8ul)),
    "data0" / Hex(Int8ul),
    "data1" / Hex(Int8ul),
    "data2" / Hex(Int8ul),
    "data3" / Hex(Int8ul),
    "data4" / Hex(Int8ul),
    "data5" / Hex(Int8ul),
    "data6" / Hex(Int8ul),
)
assert(CANTPSingleFrame.sizeof() == CAN_FRAME_MAX_SIZE)

CANTPStreamFrame = Struct(
    "data" / Hex(Int64ul),
)
assert(CANTPStreamFrame.sizeof() == CAN_FRAME_MAX_SIZE)

CANTPChunkedFrame = Struct(
    "code" / Const(CANTP_MODE_CHUNKS, Hex(Int8ul)),
    "size" / Hex(Int8ul),
    "index" / Hex(Int16ul),
    "data" / Hex(Int32ul),
)
assert(CANTPChunkedFrame.sizeof() == CAN_FRAME_MAX_SIZE)

CANTPRequest = Struct(
    "magic" / Const(0xdead, Hex(Int16ul)),
    "mode" / Hex(Int8ul),
    "pad" / Const(0, Hex(Int8ul)),
    "size" / Hex(Int32ul),
)
assert(CANTPRequest.sizeof() == CAN_FRAME_MAX_SIZE)

CANTPChecksum = Struct(
    "mode" / Const(CANTP_MODE_CRC32, Hex(Int8ul)),
    "pad1" / Const(0, Hex(Int8ul)),
    "crc" / Hex(Int32ul),
    "pad2" / Const(0, Hex(Int16ul)),
)
assert(CANTPChecksum.sizeof() == CAN_FRAME_MAX_SIZE)

# https://en.wikipedia.org/wiki/ISO_15765-2

can_frames = []
buffer = [0] * CANTP_BUFFER_SIZE

def crc_update(data, prev):
    crc = prev ^ data
    idx = 0
    while (idx < 32):
        if (crc & 0x80000000): crc = ((crc << 1) ^ 0x04C11DB7) & 0xFFFFFFFF
        else: crc = (crc << 1) & 0xFFFFFFFF
        idx += 1
    return crc

def send_frame(data, cls):
    assert(len(data) <= CAN_FRAME_MAX_SIZE)
    #print(cls.parse(data))
    x = struct.unpack("<Q", data)
    print("CAN TX: 0x%016x" % (x))
    can_frames.append(cls.parse(data))

def cantp_send_request_frame(mode, data, size):
    assert(size >= 0)
    frame = CANTPRequest.build(dict(
        size=size,
        mode=mode,
    ))
    send_frame(frame, CANTPRequest)

def cantp_send_single_frame(data, size):
    assert(len(data) <= 7)
    if (len(data) < 7):
        data += [0] * (7 - len(data))
    data = CANTPSingleFrame.build(dict(
        data0 = data[0],
        data1 = data[1],
        data2 = data[2],
        data3 = data[3],
        data4 = data[4],
        data5 = data[5],
        data6 = data[6],
    ))
    send_frame(data, CANTPSingleFrame)

def cantp_send_chunked_frames(data, size):
    assert(size >= 8)
    count = int(ceil(size / 4))
    remaining = size
    bitpos = 0
    for n in range(count):
        s = min(remaining, 4)
        u32data = data[bitpos:bitpos+s]
        u32data = u32data[3] << 24 | u32data[2] << 16 | u32data[1] << 8 | u32data[0]
        frame = CANTPChunkedFrame.build(dict(code=2, size=s, index=n, data=u32data))
        send_frame(frame, CANTPChunkedFrame)
        remaining -= s
        bitpos += 4

def cantp_send_checksum(crc):
    frame = CANTPChecksum.build(dict(crc=crc))
    send_frame(frame, CANTPChecksum)

def cantp_send_stream_frames(data, size):
    assert(size >= 8)
    transfer_size = CANTP_STREAM_TRANSFER_SIZE  # 64 bits

    crc = 0xFFFFFFFF
    count = int(size // transfer_size)
    for n in range(count):
        u64data = data[n * transfer_size:(n + 1) * transfer_size]
        u64data1 = u64data[3] << 24 | u64data[2] << 16 | u64data[1] << 8 | u64data[0]
        u64data2 = u64data[7] << 24 | u64data[6] << 16 | u64data[5] << 8 | u64data[4]
        u64data = u64data2 << 32 | u64data1
        frame = CANTPStreamFrame.build(dict(data=u64data))
        send_frame(frame, CANTPStreamFrame)
        crc = crc_update(u64data1, crc)
        crc = crc_update(u64data2, crc)

    remaining = len(data) % transfer_size
    if (remaining): # send last frame
        u64data = 0
        for n in range(remaining):
            u64data |= data[count * transfer_size + n] << (n * 8)
        frame = CANTPStreamFrame.build(dict(data=u64data))
        send_frame(frame, CANTPStreamFrame)
        crc = crc_update(u64data & 0xffffffff, crc)
        crc = crc_update((u64data << 32) & 0xffffffff, crc)
    cantp_send_checksum(crc)

def cantp_send_data(mode, data, size):
    assert(len(data) == size)

    cantp_send_request_frame(mode, data, size)
    if (len(data) <= 7):
        cantp_send_single_frame(data, size) # take precedence
    elif (mode == CANTP_MODE_STREAM):
        cantp_send_stream_frames(data, size)
    elif (mode == CANTP_MODE_CHUNKS):
        cantp_send_chunked_frames(data, size)
    else:
        raise RuntimeError("wtf")

def main_tx():
    DATA_SIZE = 27
    data = [0] * DATA_SIZE
    for i in range(DATA_SIZE):
        data[i] = i
    size = len(data)
    cantp_send_data(CANTP_MODE_STREAM, data, size)

def cantp_receive_frame():
    global can_frames
    frame = can_frames[0]
    can_frames = can_frames[1:]
    return frame

def cantp_receieve_stream(size):
    if (size > CANTP_BUFFER_SIZE):
        raise ValueError("TODO error message")

    # TODO mutex lock
    crc = 0xFFFFFFFF
    count = int(ceil(size / CANTP_STREAM_TRANSFER_SIZE))
    for n in range(count):
        frame = cantp_receive_frame()
        buffer[n] = int(frame.data)
        data = int(frame.data)
        crc = crc_update(data & 0xffffffff, crc)
        crc = crc_update((data >> 32) & 0xffffffff, crc)

    frame = cantp_receive_frame() # crc
    assert(int(frame.mode) == CANTP_MODE_CRC32)
    assert(int(frame.crc) == crc)
    # TODO mutex unlock

    return buffer

def main_rx():
    frame = cantp_receive_frame()
    if (int(frame.magic) == 0xDEAD): # request
        if (int(frame.mode) == CANTP_MODE_STREAM):
            data = cantp_receieve_stream(int(frame.size))
        elif (int(frame.mode) == CANTP_MODE_CHUNKS):
            raise ValueError("TODO")
            #data = cantp_receieve_stream(int(frame.size))

main_tx()
main_rx()
