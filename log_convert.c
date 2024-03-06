/**
 * @brief Convert CAN log format to a readable file
 * 
 * @param argc 
 * @param argv 
 * @return int 
 */

#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>

/* Begin CAN Definitions from <linux/can.h> */

/* special address description flags for the CAN_ID */
#define CAN_EFF_FLAG 0x80000000U /* EFF/SFF is set in the MSB */
#define CAN_RTR_FLAG 0x40000000U /* remote transmission request */
#define CAN_ERR_FLAG 0x20000000U /* error frame */

/* valid bits in CAN ID for frame formats */
#define CAN_SFF_MASK 0x000007FFU /* standard frame format (SFF) */
#define CAN_EFF_MASK 0x1FFFFFFFU /* extended frame format (EFF) */
#define CAN_ERR_MASK 0x1FFFFFFFU /* omit EFF, RTR, ERR flags */

/*
 * Controller Area Network Identifier structure
 *
 * bit 0-28      : CAN identifier (11/29 bit)
 * bit 29        : error frame flag (0 = data frame, 1 = error frame)
 * bit 30        : remote transmission request flag (1 = rtr frame)
 * bit 31        : frame format flag (0 = standard 11 bit, 1 = extended 29 bit)
 */
typedef uint32_t canid_t;

/* End CAN Definitions from <linux/can.h> */

// 0 = CAN1, 1 = CAN2, 
// TODO: add like UDP, USB, etc. ?
typedef uint8_t busid_t;

typedef struct __attribute__((packed))
{
    uint32_t tick_ms;      //!< ms timestamp of reception
    canid_t  msg_id;       //!< message id
    busid_t  bus_id;       //!< bus the message was rx'd on
    uint8_t  dlc;          //!< data length code
    uint8_t  data[8];      //!< message data
} timestamped_frame_t;

int main (int argc, char **argv)
{
    if (argc != 2) 
    {
        printf("Usage: log_convert <file_name> ...\n");
    }
   
    FILE *fp = fopen(argv[1], "rb");
    if (fp == NULL)
    {
        printf("Failed to open file \'%s\'\n", argv[1]);
    }

    bool print_msg = true;

    timestamped_frame_t tf;
    char *bus_str;
    float dt_avg = 0.0;
    float dt = 0.0;
    uint32_t dt_count = 0;
    float dt_max = 0.0;
    float last_time = 0.0;
    uint32_t last_val = 0;
    uint32_t first_val = 0;
    uint32_t skips = 0;
    uint32_t time_skips = 0;
    while(fread(&tf, sizeof(tf), 1, fp) > 0)
    {
        float time_s = tf.tick_ms / 1000.0;
        if (tf.dlc > 8)
        {
            printf("Error: dlc=%d > 8\n", tf.dlc);
            continue;
        }
        switch(tf.bus_id)
        {
            case 0:
                bus_str = "can0";
                break;
            case 1:
                bus_str = "can1";
                break;
            default:
                bus_str = "unknown";
            break;
        }
        if (print_msg) printf("(%f) %s %08x#", time_s, bus_str, 
                                  tf.msg_id & CAN_EFF_MASK);
        uint32_t val = 0;
        for (uint8_t i = 0; i < tf.dlc; ++i)
        {
            if (print_msg) printf("%02x", tf.data[i]);
            val = val | (tf.data[i] << (i*8));
        }
        if (print_msg) printf("\n");

        if (last_time != 0.0)
        {
            dt = time_s - last_time;
            if (dt < 0) 
            {
                if (!print_msg) printf("Time skip from %f to %f\n", last_time, time_s);
                ++time_skips;
            }
            dt_avg += dt;
            dt_count++;
            dt_max = (dt > dt_max) ? dt : dt_max;
            if (val != last_val + 1) 
	    {
		if (!print_msg) printf("Value skip from %d to %d (time %f to %f)\n", last_val, val, last_time, time_s);
	    	++skips;
	    }
        }
        else
        {
            first_val = val;
        }
        last_time = time_s;
        last_val = val;
    }
    
    dt_avg /= dt_count;
    printf("Average dt: %f\n", dt_avg);
    printf("Max: %f\n", dt_max);
    printf("Count: %lu\n", dt_count);
    printf("First value %lu\n", first_val);
    printf("Last value %lu\n", last_val);
    printf("Value Skips: %d\n", skips);
    printf("Time Skips: %d\n", time_skips);
}
