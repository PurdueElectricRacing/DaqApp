from ftplib import FTP
import ftplib

ftp = FTP('192.168.10.41')  # connect to host, default port
ftp.login("PER", "PER2025") # user anonymous, passwd anonymous@
#ftp.retrlines('LIST') # list directory contents
ftp.cwd("/")
ftp.set_debuglevel(10)
ftp.set_pasv(False)

ls = []
ftp.retrlines('MLSD', ls.append)
for entry in ls:
    print(entry)

myList = list(ftp.mlsd(path=""))
for item in myList:
   print(item)
#ftp.quit()

if 0:
    A = "log-2024-02-27--23-28-41.log"
    try:
        ftp.retrbinary("RETR " +  A, open(A, 'wb').write)
    except Exception as e:
        print("Error:", e)

try:
    while True:
        pass
except KeyboardInterrupt:
    pass
ftp.quit()
