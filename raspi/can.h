/**
 * @file    can.h
 * @author  Luke Oxley (lukeoxley9@gmail.com)
 * @brief   Connection to linux can socket
 * @version 2.0
 * @date    2022-04-23
 */
#ifndef _CAN_H_
#define _CAN_H_

#include <linux/can.h>
#include <linux/can/raw.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <stdint.h>
#include <stdbool.h>
#include <net/if.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>


typedef struct
{
    int socket;
    bool tx_lock_;
} can_t;

typedef enum 
{
    CAN_SUCCESS = 0,
    CAN_BUSY,
    CAN_ERROR
} can_error_t;

/**
 * @brief           Connects to can socket
 * @param hcan      Can struct
 * @param port_name Can port name, i.e. vcan0
 * @param loopback  Receive own messages
 * @return          CAN_SUCCESS or -CAN_ERROR 
 */
int can_init(can_t *hcan, const char* port_name, bool loopback);
/**
 * @brief       Reads a can frame and its timestamp
 * @param hcan  Can struct
 * @param frame Received can frame
 * @param tv    Timestamp of packet 
 * @return      CAN_SUCCESS or -CAN_ERROR
 */
int can_read(can_t *hcan, struct can_frame* frame, struct timeval* tv);
/**
 * @brief       Sends a can frame
 * @param hcan  Can struct
 * @param frame Can frame to send
 * @return      CAN_SUCCESS, -CAN_ERROR, or -CAN_BUSY
 */
int can_send(can_t *hcan, struct can_frame* frame);
int can_close(can_t *hcan);

#endif