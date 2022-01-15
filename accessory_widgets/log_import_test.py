import can

path = './logs/candump-2021-11-18_151119.log'

with open(path, 'r') as log:
            for line in log.readlines():
                cols = line.split(" ")
                time = float(cols[0][1:-2])
                id, data = cols[2].split('#')
                dlc = int(len(data)/2)
                msg = can.Message(timestamp=time,
                                  is_extended_id=True,
                                  dlc=dlc,
                                  data=int(data, base=16).to_bytes(dlc, 'little'),
                                  arbitration_id=int(id, base=16))
                print(msg)