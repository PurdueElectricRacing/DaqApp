# to run on startup, edit /etc/rc.local

#sudo slcand -o -c -s6 /dev/ttyACM0 can0
#sudo ifconfig can0 up
#sudo ifconfig can0 txqueuelen 1000

# candlelight
ip link set can0 up type can bitrate 500000

