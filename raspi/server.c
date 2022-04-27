#include "server.h"

// have select run in thread to receive tcp from clients
// https://www.geeksforgeeks.org/socket-programming-in-cc-handling-multiple-clients-on-server-without-multi-threading/
// have multicast udp for sending data
// https://www.tenouk.com/Module41c.html

int main(int argc, char* argv[])
{
    int port;

    /* Parse Arguments */
    if (argc != 3)
    {
        fprintf(stderr, "usage %s can-name port\n", argv[0]);
        return 0;
    }
    port = atoi(argv[2]);

    

    //char* multi_group = "224.3.29.71";
    can_t hcan;
    broadcast_t bc;
    while (true)
    {
        if (can_init(&hcan, argv[1], true) != CAN_SUCCESS)
        {
            fprintf(stderr, "CAN init failure\n");
            return EXIT_FAILURE;
        }

        memset((char *) &bc, 0, sizeof(bc));
        if (start_broadcast(&bc, port, &hcan) != BC_SUCCESS)
        {
            fprintf(stderr, "Failed to start broadcast\n");
            return EXIT_FAILURE;
        }

        /* Wait for threads to finish */
        join_bc_threads(&bc);
        can_close(&hcan);
        fprintf(stderr, "Client disconnect or error, restarting...\n");
    }

    // They should never finish RIP
    return EXIT_FAILURE;
}