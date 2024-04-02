import mmap

#file_loc = 'D:\Downloads\dd-0.5\sd_card_dump'
file_loc = 'D:\Downloads\dd-0.5\sd_card_dump_ext'
out_file_dir = 'D:\log_recovery\\'

clst_size = 0x8000

offset = 10 # bytes
start_addr = 0x17d8000

msg_size = 18

rp = start_addr + offset
#stop_addr = 0x30d3fee
#stop_addr = 0x61a8000 - msg_size
#stop_addr = 0x01818000 - msg_size
stop_addr = 0x3b08000 - msg_size

max_jump_ms = 100

write_files = False

with open(file_loc, 'rb') as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    ba = bytearray(mm)
    #val = int.from_bytes(ba[0x10:0x14], "little")
    #print(val)
    last_t = 0
    last_t_valid = False
    start_t = 0
    start_p = rp
    start_c = 0 # not same as cluster numbers used in fat32, (start_c = 0 is address 0)

    spans = 0
    file_count = 0

    while rp < stop_addr:

        # get timestamp
        t = int.from_bytes(ba[rp:(rp+4)], 'little')
        #print(t)

        if (last_t_valid and (t < last_t or abs(t - last_t) >= max_jump_ms)) or (rp+msg_size >= stop_addr):
            if (rp+msg_size >= stop_addr):
                print("stopping early to not go past end")
            # Invalid time
            print(f"Stop time: {last_t/1000.0} s, duration: {(last_t - start_t) / 1000.0} s")
            print(f"invalid time, curr: {t} last: {last_t}, at read pointer {rp:08x}, ended at cluster {rp//clst_size}, total clusters: {(rp//clst_size) - start_c + 1}")
            if (last_t - start_t) > 0:
                spans = spans + 1

            if write_files:
                out_fp.close()

            # jump to next cluster (assuming its the start of new file)
            # repeats cluster if you didn't get very far into it
            if (rp % clst_size < msg_size*3 and (rp//clst_size != start_c)):
                rp = (rp // clst_size) * clst_size # repeat current cluster
            else:
                if (rp//clst_size == start_c): 
                    print(f"CLUSTER {rp//clst_size} had no info")
                rp = ((rp // clst_size) + 1) * clst_size # round up to next cluster
            last_t_valid = False
            print("")

        else:
            last_t = t

            if not last_t_valid:
                last_t_valid = True
                start_t = t
                start_c = rp // clst_size
                print(f"Start time: {t/1000.0} s, at read pointer {rp:08x}, cluster {start_c}")

                if write_files:
                    out_fp = open(f"{out_file_dir}out_file_{file_count}.log", 'wb')
                file_count = file_count + 1

            if write_files:
                out_fp.write(ba[rp:(rp+msg_size)]) # write message
            rp = rp + msg_size
    
    print(f"Found {spans} runs with >0 dur")




