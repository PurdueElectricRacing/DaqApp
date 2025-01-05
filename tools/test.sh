#!/usr/bin/env sh

# daq/uds 'unittest' lol

test1()
{
    # basic connection test
    python3 candump.py -m usb -t 1
    python3 candump.py -m udp -t 1
    python3 link_test.py -u -t
}

test2()
{
    # uds ping
    python3 add_two_numbers.py --node daq -m usb
    python3 add_two_numbers.py --node daq -m tcp
    python3 add_two_numbers.py --node main_module -m usb
    python3 add_two_numbers.py --node main_module -m tcp

    # uds var r/w
    python3 uds_var.py -m usb -n daq
    python3 uds_var.py -m tcp -n daq

    #for n in $(seq 1 10)
    #do
    #	python3 add_two_numbers.py -n daq -m usb && sleep 0.1
    #done
}

test3()
{
    # bootloader
    python3 bootloader.py --node main_module -m usb && sleep 1
    python3 bootloader.py --node main_module -m tcp && sleep 1
    python3 bootloader.py --node daq -m usb -b && sleep 1
    python3 bootloader.py --node daq -m usb -l && sleep 1
    python3 bootloader.py --node daq -m usb -s && sleep 1
    python3 bootloader.py --node daq -m usb -r
    python3 bootloader.py --node daq -m tcp -p
    #python3 bootloader.py --node daq -m tcp
}

$1 $2 $3 $4 $5
