/**
 * @file    broadcast_can.h
 * @author  Luke Oxley (lukeoxley9@gmail.com)
 * @brief   Broadcast from can socket to UDP
 * @version 0.1
 * @date    2022-04-23
 */

#ifndef _BROADCAST_CAN_H_
#define _BROADCAST_CAN_H_

#include <pthread.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>


#include "can.h"
#include "queue.h"

typedef struct __attribute__((packed))
{
    time_t tv_sec;
    suseconds_t tv_usec;
    canid_t id; 
    uint8_t dlc;
    uint8_t data[CAN_MAX_DLEN];
} timestamped_frame_t;

typedef struct
{
    can_t *hcan;
    int sock;
    int client;
    struct sockaddr_in server_addr;
    pthread_t _bc_read;
    pthread_t _bc_write;
    pthread_t _rx_read;
    pthread_t _rx_write;
    q_handle_t bc_queue; 
    q_handle_t rx_queue; 
    pthread_mutex_t bc_q_lock;
    pthread_mutex_t rx_q_lock;
    pthread_cond_t bc_has_data;
    pthread_cond_t rx_has_data;
} broadcast_t;

typedef enum
{
    BC_SUCCESS = 0,
    BC_ERROR
} broadcast_error_t;

// multigroup i.e. 224.3.29.71
int start_broadcast(broadcast_t *bc, int port, can_t *hcan);
int join_bc_threads(broadcast_t *bc);

#endif