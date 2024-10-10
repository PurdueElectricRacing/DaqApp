/**
 * @file cantp.h
 * @author Eileen Yoon (eyn@purdue.edu)
 * @brief
 * @version 0.1
 * @date 2024-11-18
 *
 * @copyright Copyright (c) 2024
 *
 * CAN Transport Protocol (for larger data packets) adapted from ISO 15765-2
 */

#ifndef __CANTP_H__
#define __CANTP_H__

#include <stdint.h>

#define CANTP_MODE_STREAM 1
#define CANTP_MODE_CHUNKS 2
#define CANTP_MODE_CRC32  4

int cantp_send_data(uint8_t mode, uint8_t *data, uint32_t size);

#endif /* __CANTP_H__ */
