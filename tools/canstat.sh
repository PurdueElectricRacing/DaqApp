#!/usr/bin/env sh

usb() {
    echo ""
    echo "USB:"

    lsusb | grep --color=always -iF can
    ip link show can0 | grep --color=always "UP\|DOWN"

    echo ""
}

udp() {
    echo ""
    echo "UDP:"

    ip addr show eth0 | grep --color=always "UP\|DOWN"
    timeout 0.5 tcpdump -i eth0 udp port 5005
    ip route
    ip route | grep --color=always eth0
    #python3 link_test.py -u

    echo ""
}

tcp() {
    echo ""
    echo "TCP:"

    ip addr show eth0 | grep --color=always "UP\|DOWN"
    timeout 0.5 tcpdump -i eth0 tcp port 5005
    ip route
    ip route | grep --color=always eth0
    #python3 link_test.py -t

    echo ""
}

bus() {
    # https://canable.io/getting-started.html

    # sudo slcand -o -c -s0 /dev/ttyACM0 can0
    # sudo ifconfig can0 up
    # sudo ifconfig can0 txqueuelen 1000

    # cansend can0 999#DEADBEEF   # Send a frame to 0x999 with payload 0xdeadbeef
    # candump can0                # Show all traffic received by can0
    # canbusload can0 500000      # Calculate bus loading percentage on can0
    # cansniffer can0             # Display top-style view of can traffic
    # cangen can0 -D 11223344DEADBEEF -L 8    # Generate fixed-data CAN messages

    canbusload can0@500000 -t -b -c -r
}

if [ $# -eq 0 ]; then
    usb
    udp
    tcp
fi

$1 $2 $3 $4 $5
