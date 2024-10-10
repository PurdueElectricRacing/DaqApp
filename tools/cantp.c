
/**
 * @file cantp.c
 * @author Eileen Yoon (eyn@purdue.edu)
 * @brief
 * @version 0.1
 * @date 2024-11-18
 *
 * @copyright Copyright (c) 2024
 *
 * CAN Transport Protocol (for larger data packets) adapted from ISO 15765-2
 */

#include <assert.h>
#include <stdint.h>

#include <stdio.h>
//#include "common/phal_F4_F7/crc/crc.h"
#include "cantp.h"
#include "crc.h"

#define CAN_FRAME_MAX_SIZE 8
#define CANTP_STREAM_TRANSFER_SIZE (CAN_FRAME_MAX_SIZE)

#define CANTP_FRAME_DIRECTION_TX 0
#define CANTP_FRAME_DIRECTION_RX 1

static volatile uint32_t CRC32_MASTER = 0;

static uint64_t CANTP_FRAMES[256];
static int CANTP_RX_FRAME_INDEX1 = 0;
static int CANTP_RX_FRAME_INDEX2 = 0;

struct cantp_request_frame {
    uint16_t magic;
    uint8_t mode;
    uint8_t direction;
    uint32_t size;
} __attribute__((__packed__));
static_assert(sizeof(struct cantp_request_frame) == CAN_FRAME_MAX_SIZE);

struct cantp_checksum_frame {
    uint8_t mode;
    uint8_t pad1;
    uint32_t checksum;
    uint16_t pad2;
} __attribute__((__packed__));
static_assert(sizeof(struct cantp_checksum_frame) == CAN_FRAME_MAX_SIZE);

static int can_tx_send_u64(uint64_t data)
{
    printf("CAN TX: 0x%016lx\n", data);
    CANTP_FRAMES[CANTP_RX_FRAME_INDEX1++] = data;
    return 0;
}

static int cantp_send_request_frame(uint8_t mode, uint8_t *data, uint32_t size)
{
    struct cantp_request_frame frame = {
        .magic = 0xdead,
        .mode = mode,
        .direction = CANTP_FRAME_DIRECTION_TX,
        .size = size,
    };
    return can_tx_send_u64(*(uint64_t *)&frame);
}

static int cantp_send_checksum(uint32_t checksum)
{
    struct cantp_checksum_frame frame = {
        .mode = CANTP_MODE_CRC32,
        .pad1 = 0,
        .checksum = checksum,
        .pad2 = 0,
    };
    return can_tx_send_u64(*(uint64_t *)&frame);
}

static int cantp_send_single_frame(uint8_t *data, uint32_t size)
{
    uint64_t data64 = 0;
    for (int i = 0; i < size; i++)
        data64 |= ((uint64_t)data[i] << (i * 8)) & 0xff;
    can_tx_send_u64(data64);
}

void PHAL_reset_CRC32()
{
    CRC32_MASTER = 0xffffffff;
}

void PHAL_update_CRC32(uint32_t val)
{
    CRC32_MASTER = crc32_fast(CRC32_MASTER, val);
}

uint32_t PHAL_get_CRC32()
{
    return CRC32_MASTER;
}

static int cantp_send_stream_frames(uint8_t *data, uint32_t size)
{
    PHAL_reset_CRC32();

    uint64_t data64;
    int i;
    int count = size / CANTP_STREAM_TRANSFER_SIZE;
    for (i = 0; i < count; i++)
    {
        data64 = *(uint64_t *)(data + (i * CANTP_STREAM_TRANSFER_SIZE));
        can_tx_send_u64(data64);
        PHAL_update_CRC32(data64 & 0xffffffff);
        PHAL_update_CRC32((data64 >> 32) & 0xffffffff);
    }

    if (size % CANTP_STREAM_TRANSFER_SIZE) // send last frame
    {
        data64 = 0;
        for (i = 0; i < size % CANTP_STREAM_TRANSFER_SIZE; i++)
            data64 |= data[count * CANTP_STREAM_TRANSFER_SIZE + i] << (i * 8);
        can_tx_send_u64(data64);
        PHAL_update_CRC32(data64 & 0xffffffff);
        PHAL_update_CRC32((data64 >> 32) & 0xffffffff);
    }

    cantp_send_checksum(PHAL_get_CRC32());

    PHAL_reset_CRC32();

    return 0;
}

int cantp_send_data(uint8_t mode, uint8_t *data, uint32_t size)
{
    cantp_send_request_frame(CANTP_MODE_STREAM, data, size);
    if (size <= CANTP_STREAM_TRANSFER_SIZE) // single frame takes precedence
    {
        cantp_send_single_frame(data, size);
    }
    else if (mode == CANTP_MODE_STREAM)
    {
        cantp_send_stream_frames(data, size);
    }

    return 0;
}

// RX
uint8_t CANTP_RX_BUFFER[256];

static uint64_t cantp_receive_frame(void)
{
    uint64_t data = CANTP_FRAMES[CANTP_RX_FRAME_INDEX2++];
    printf("CAN RX: 0x%016lx\n", data);
    return data;
}

static uint32_t cantp_receive_checksum(void)
{
    uint64_t data = cantp_receive_frame(); // get CRC
    struct cantp_checksum_frame *frame = (struct cantp_checksum_frame *)(&data);
    if (frame->mode != CANTP_MODE_CRC32)
        return -1;
    return frame->checksum;
}

static int cantp_receive_stream_frames(uint8_t *buffer, uint32_t size)
{
    PHAL_reset_CRC32();

    uint64_t *buffer64 = (uint64_t *)buffer;
    uint64_t data64;
    int count = size / CANTP_STREAM_TRANSFER_SIZE;
    int i;

    // TODO mutex lock
    for (i = 0; i < count; i++)
    {
        data64 = cantp_receive_frame();
        buffer64[i] = data64;
        PHAL_update_CRC32(data64 & 0xffffffff);
        PHAL_update_CRC32((data64 >> 32) & 0xffffffff);
    }

    if (size % CANTP_STREAM_TRANSFER_SIZE) // send last frame
    {
        data64 = cantp_receive_frame();
        for (i = 0; i < size % CANTP_STREAM_TRANSFER_SIZE; i++)
        {
            buffer[count * CANTP_STREAM_TRANSFER_SIZE + i] = (data64 >> (i * 8)) & 0xff;
        }
        PHAL_update_CRC32(data64 & 0xffffffff);
        PHAL_update_CRC32((data64 >> 32) & 0xffffffff);
    }

    uint32_t checksum = cantp_receive_checksum();
    if (checksum != PHAL_get_CRC32())
    {
        printf("crc failed: 0x%08x vs 0x%08x\n", checksum, PHAL_get_CRC32());
        return -1;
    }

    PHAL_reset_CRC32();

    return 0;
}

static int cantp_receive_single_frame(uint8_t *buffer, uint32_t size)
{
    uint64_t data = cantp_receive_frame();
    for (int i = 0; i < size; i++)
    {
        buffer[i] = (data >> (i * 8)) & 0xff;
    }
}

int cantp_receive_data(void)
{
    uint64_t data;

    data = cantp_receive_frame();
    if ((uint16_t)(data & 0xffff) == 0xdead)
    {
        struct cantp_request_frame *frame = (struct cantp_request_frame *)(&data);

        if (frame->size <= CANTP_STREAM_TRANSFER_SIZE) // single frame takes precedence
        {
            cantp_receive_single_frame(CANTP_RX_BUFFER, frame->size);

        }
        else if (frame->mode == CANTP_MODE_STREAM)
        {
            cantp_receive_stream_frames(CANTP_RX_BUFFER, frame->size);
        }
        printf("buffer: 0x%x 0x%x 0x%x\n", CANTP_RX_BUFFER[0], CANTP_RX_BUFFER[1], CANTP_RX_BUFFER[2]);
    }

    return 0;
}

#define DATA_SIZE 15

int main(void)
{
    uint8_t data[DATA_SIZE];
    for (int i = 0; i < DATA_SIZE; i++)
    {
        data[i] = i;
    }
    cantp_send_data(1, data, DATA_SIZE);
    cantp_receive_data();

    return 0;
}
