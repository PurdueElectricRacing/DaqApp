#include "can.h"

int can_init(can_t *hcan, const char* port_name, bool loopback)
{
    // open socket
    hcan->socket = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (hcan->socket < 0) 
    {
        hcan->socket = 0;
        return -CAN_ERROR;
    }

    // configure loopback
    setsockopt(hcan->socket, SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS,
               &loopback, sizeof(loopback));

    struct ifreq ifr;
    struct sockaddr_can addr;
    addr.can_family = AF_CAN;

    // get interface index based on port name 
    strcpy(ifr.ifr_name, port_name);
    if (ioctl(hcan->socket, SIOCGIFINDEX, &ifr) < 0)
    {
        close(hcan->socket);
        return -CAN_ERROR;
    }
    addr.can_ifindex = ifr.ifr_ifindex;

    // bind socket to address
    if (bind(hcan->socket, (struct sockaddr *)&addr, sizeof(addr)) < 0)
    {
        close(hcan->socket);
        return -CAN_ERROR;
    }

    hcan->tx_lock_ = false;

    printf("Connected to can socket on port %s\n", port_name);

    return CAN_SUCCESS;
}

int can_read(can_t *hcan, struct can_frame* frame, struct timeval* tv)
{
    if (read(hcan->socket, frame, sizeof(*frame)) !=
        sizeof(*frame)) return -CAN_ERROR;
    return ioctl(hcan->socket, SIOCGSTAMP_OLD, tv) < 0 ? -CAN_ERROR : CAN_SUCCESS;
}

int can_send(can_t *hcan, struct can_frame* frame)
{
    if (hcan->tx_lock_) 
    {
        fprintf(stderr, "Can busy\n");
        return -CAN_BUSY;
    }
    hcan->tx_lock_ = true;
    int bytes = write(hcan->socket, frame, sizeof(*frame));
    hcan->tx_lock_ = false;
    if (bytes < 0)
    {
        fprintf(stderr, "Can send error\n");
        return -CAN_ERROR;
    }
    else if (bytes != sizeof(*frame)) 
    {
        fprintf(stderr, "Only sent %d bytes\n", bytes);
        return -CAN_ERROR;
    }
    return CAN_SUCCESS;
}

int can_close(can_t *hcan)
{
    close(hcan->socket);
    hcan->tx_lock_ = false;
    return CAN_SUCCESS;
}