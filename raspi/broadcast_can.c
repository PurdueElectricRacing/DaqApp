#include "broadcast_can.h"

// Can send and receive from socket at same time

// Static Prototypes
static void *_read_can_poll(void *args);
static void *_write_udp_poll(void *args);
static void *_read_udp_poll(void *args);
static void *_write_can_poll(void *args);

static sig_atomic_t _poll = true;

int start_broadcast(broadcast_t *bc, int port, can_t *hcan)
{
    bc->hcan = hcan;

    /* Create UDP Multicast Socket */
    //bc->udp_sock = socket(AF_INET, SOCK_DGRAM, 0);
    bc->sock = socket(AF_INET, SOCK_STREAM, 0);
    if (bc->sock < 0) 
    {
        fprintf(stderr, "Failed to create socket.\n");
        return -BC_ERROR;
    }

    /* Define server address */
    memset((char *) &bc->server_addr, 0, sizeof(bc->server_addr));
    bc->server_addr.sin_family = AF_INET;
    bc->server_addr.sin_port = htons(port);
    bc->server_addr.sin_addr.s_addr = INADDR_ANY;//inet_addr(multi_group);

    int opt = 1;
    if (setsockopt(bc->sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0)
    {
        fprintf(stderr, "Failed to set sock opt\n");
        return -BC_ERROR;
    }

    /* Bind the socket to the IP and port */
    if (bind(bc->sock, (struct sockaddr*) &bc->server_addr, sizeof(bc->server_addr)) < 0)
    {
        fprintf(stderr, "Failed to bind socket.\n");
        return -BC_ERROR;
    }

    if (listen(bc->sock, 3) < 0)
    {
        fprintf(stderr, "Failed to listen.\n");
        return -BC_ERROR;
    }

    bc->client = accept(bc->sock, NULL, NULL);
    if (bc->client < 0)
    {
        fprintf(stderr, "Failed to accept.\n");
        return -BC_ERROR;
    }
    fprintf(stderr, "Connected to client.\n");

    /* UDP MULTICAST ATTEMPT
    // Local interface
    struct in_addr local_if;
    // TODO: get local interface (must be associated with a local, 
    // multicast capable interface)
    local_if.s_addr = inet_addr("10.42.0.1");//203.106.93.94");
    if (setsockopt(bc->udp_sock, IPPROTO_IP, IP_MULTICAST_IF, 
                   (char *)&local_if, sizeof(local_if)) < 0)
    {
        fprintf(stderr, "Failed to set local interface.\n");
        return BC_ERROR;
    }
    */

    /* Construct Queue */
    qConstruct(&bc->bc_queue, sizeof(timestamped_frame_t));
    qConstruct(&bc->rx_queue, sizeof(struct can_frame));

    /* Thread Setup */
    _poll = true;
    if (pthread_cond_init(&bc->bc_has_data, NULL) != 0)
    {
        fprintf(stderr, "Failed to initialize condition var.\n");
        return BC_ERROR;
    }
    if (pthread_cond_init(&bc->rx_has_data, NULL) != 0)
    {
        fprintf(stderr, "Failed to initialize condition var.\n");
        return BC_ERROR;
    }
    if (pthread_mutex_init(&bc->bc_q_lock, NULL) != 0)
    {
        fprintf(stderr, "Failed to initialize mutex.\n");
        return BC_ERROR;
    }
    if (pthread_mutex_init(&bc->rx_q_lock, NULL) != 0)
    {
        fprintf(stderr, "Failed to initialize mutex.\n");
        return BC_ERROR;
    }
    if (pthread_create(&bc->_bc_read, NULL, _read_can_poll, (void*) bc) < 0)
    {
        fprintf(stderr, "Failed to create read can poll thread \n");
    }
    if (pthread_create(&bc->_bc_write, NULL, _write_udp_poll, (void*) bc) < 0)
    {
        fprintf(stderr, "Failed to create write udp poll thread \n");
    }
    if (pthread_create(&bc->_rx_read, NULL, _read_udp_poll, (void*) bc) < 0)
    {
        fprintf(stderr, "Failed to create read udp poll thread \n");
    }
    if (pthread_create(&bc->_rx_write, NULL, _write_can_poll, (void*) bc) < 0)
    {
        fprintf(stderr, "Failed to create write can poll thread \n");
    }
    return BC_SUCCESS;
}

// Reads from can socket, put on buffer
static void *_read_can_poll(void *args)
{
    broadcast_t *bc = (broadcast_t *) args;

    while (_poll)
    {
        /* Read can message */
        struct can_frame frame;
        struct timeval tv;
        if (can_read(bc->hcan, &frame, &tv) < 0)
        {
            fprintf(stderr, "Failed to read can frame\n");
            break;
        }

        /* Combine frame and time */
        timestamped_frame_t t_frame = {
            .tv_sec  = tv.tv_sec,
            .tv_usec = tv.tv_usec,
            .id      = frame.can_id,
            .dlc     = frame.can_dlc
        }; 
        memcpy(t_frame.data, frame.data, sizeof(frame.data[0]) * CAN_MAX_DLEN);

        /* Place on buffer */
        pthread_mutex_lock(&bc->bc_q_lock);
        if (qSendToBack(&bc->bc_queue, &t_frame) != SUCCESS_G)
        {
            pthread_mutex_unlock(&bc->bc_q_lock);
            fprintf(stderr, "Failed to place can frame on queue.\n");
            continue;
        }
        if (pthread_cond_signal(&bc->bc_has_data) < 0)
        {
            pthread_mutex_unlock(&bc->bc_q_lock);
            fprintf(stderr, "Failed signal from read can poll\n");
            break;
        }
        pthread_mutex_unlock(&bc->bc_q_lock);
    }

    _poll = false;
    pthread_mutex_lock(&bc->bc_q_lock);
    pthread_cond_signal(&bc->bc_has_data);
    pthread_mutex_unlock(&bc->bc_q_lock);
    fprintf(stderr, "_read_can_poll\n");
    return NULL;
}

// Read from buffer, write to UDP
static void *_write_udp_poll(void *args)
{
    broadcast_t *bc = (broadcast_t *) args;

    while (_poll)
    {
        timestamped_frame_t t_frame;
        /* Read from buffer */
        pthread_mutex_lock(&bc->bc_q_lock);
        while (bc->bc_queue.item_count == 0 && _poll)
        {
            if (pthread_cond_wait(&bc->bc_has_data, &bc->bc_q_lock) < 0)
            {
                pthread_mutex_unlock(&bc->bc_q_lock);
                fprintf(stderr, "Failed to resume write udp poll\n");
                break;
            }
        }
        if (!_poll)
        {
            fprintf(stderr, "Received signal on stop poll\n");
            pthread_mutex_unlock(&bc->bc_q_lock);
            break;
        }
        if (qReceive(&bc->bc_queue, &t_frame) != SUCCESS_G) 
        {
            pthread_mutex_unlock(&bc->bc_q_lock);
            fprintf(stderr, "Queue receive failed\n");
            break;
        }
        pthread_mutex_unlock(&bc->bc_q_lock);

        /* Write to UDP :(*/
        // int cnt = sendto(bc->udp_sock, &t_frame, sizeof(t_frame), 0,
        //                  (struct sockaddr *) &bc->server_addr, sizeof(bc->server_addr));

        int cnt = write(bc->client, &t_frame, sizeof(t_frame));
        if (cnt < 0)
        {
            fprintf(stderr, "Failed to send to tcp \n");
            break;
        }
        else if (cnt != sizeof(t_frame))
        {
            fprintf(stderr, "Failed to send entire frame to tcp\n");
            break;
        }
    }

    _poll = false;
    fprintf(stderr, "_write_udp_poll\n");
    return NULL;
}

static void *_read_udp_poll(void *args)
{

    broadcast_t *bc = (broadcast_t *) args;
    struct can_frame frame;
    int total_read = 0;
    int struct_size = 13;
    uint8_t frame_buff[13];

    while (_poll)
    {
        int num_read = read(bc->client, frame_buff + total_read, struct_size - total_read);
        if (num_read <= 0)
        {
            fprintf(stderr, "Failed to read from tcp.\n");
            break;
        }
        total_read += num_read;

        // If only part of frame read, continue reading
        if (total_read < struct_size) continue;
        else if (total_read > struct_size) 
        {
            fprintf(stderr, "Invalid state (1)\n");
            break;
        }
        // reset counter
        total_read = 0;

        /*
        frame.can_id = ((uint32_t)frame_buff[0] << 0) | ((uint32_t)frame_buff[1] << 8) | ((uint32_t)frame_buff[2] << 16) | ((uint32_t)frame_buff[3] << 24);
        frame.can_dlc = (uint8_t)frame_buff[4];
        memcpy(frame.data,&frame_buff[5],frame.can_dlc);
        printf("ID: %x | DLC: %d | Data:", frame.can_id,frame.can_dlc);
        for (int m = 0;m < frame.can_dlc;m++)
        {
            printf("%02x ",frame.data[m]);
        }
        printf("\n");
        */

        /* Place on buffer */
        pthread_mutex_lock(&bc->rx_q_lock);
        if (qSendToBack(&bc->rx_queue, &frame) != SUCCESS_G)
        {
            pthread_mutex_unlock(&bc->rx_q_lock);
            fprintf(stderr, "Failed to place can frame from tcp on queue.\n");
            continue;
        }
        if (pthread_cond_signal(&bc->rx_has_data) < 0)
        {
            fprintf(stderr, "Failed to signal from read udp poll\n");
            pthread_mutex_unlock(&bc->rx_q_lock);
            break;
        }
        pthread_mutex_unlock(&bc->rx_q_lock);

    }
    _poll = false;
    pthread_mutex_lock(&bc->rx_q_lock);
    pthread_cond_signal(&bc->rx_has_data);
    pthread_mutex_unlock(&bc->rx_q_lock);
    fprintf(stderr, "_read_udp_poll\n");
    return NULL;
}

static void *_write_can_poll(void *args)
{
    broadcast_t *bc = (broadcast_t *) args;

    while (_poll)
    {
        struct can_frame frame;
        /* Read from buffer */
        pthread_mutex_lock(&bc->rx_q_lock);
        while (bc->rx_queue.item_count == 0 && _poll) 
        {
            if (pthread_cond_wait(&bc->rx_has_data, &bc->rx_q_lock) < 0)
            {
                fprintf(stderr, "Failed to resume write can poll\n");
                pthread_mutex_unlock(&bc->rx_q_lock);
                break;
            }
        }
        if (!_poll) 
        {
            fprintf(stderr, "Received signal on stop poll\n");
            pthread_mutex_unlock(&bc->rx_q_lock);
            break;
        }
        if (qReceive(&bc->rx_queue, &frame) != SUCCESS_G) 
        {
            pthread_mutex_unlock(&bc->rx_q_lock);
            fprintf(stderr, "Queue receive failed\n");
            break;
        }
        pthread_mutex_unlock(&bc->rx_q_lock);

        if (can_send(bc->hcan, &frame) != CAN_SUCCESS)
        {
            fprintf(stderr, "Failed to send can frame\n");
            break;
        }
    }

    _poll = false;
    fprintf(stderr, "_write_can_poll\n");
    return NULL;
}

int join_bc_threads(broadcast_t *bc)
{
    pthread_join(bc->_bc_read, NULL);
    fprintf(stderr, "stopping 1, ");
    pthread_join(bc->_bc_write, NULL);
    fprintf(stderr, "2, ");
    pthread_join(bc->_rx_write, NULL);
    fprintf(stderr, "3, ");
    pthread_join(bc->_rx_read, NULL);
    fprintf(stderr, "4\n");
    pthread_mutex_destroy(&bc->bc_q_lock);
    pthread_mutex_destroy(&bc->rx_q_lock);
    close(bc->client);
    close(bc->sock);
    return BC_SUCCESS;
}
