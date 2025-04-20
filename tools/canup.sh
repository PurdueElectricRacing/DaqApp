#!/usr/bin/env sh

# socketcan
usb() {
    ip link set can0 up type can bitrate 500000
	ifconfig can0 txqueuelen 10000
}

# udp
udp() {
    ip addr add 192.168.10.1/24 dev eth0
    ifconfig eth0 192.168.10.255 netmask 255.255.255.0
}

tcp() {
    ip addr add 192.168.10.1/24 dev eth0
    #ifconfig eth0 192.168.10.255 netmask 255.255.255.0
}

if [ $# -eq 0 ]; then
    udp
    usb
fi

$1 $2 $3 $4 $5

# ./canup.sh usb
