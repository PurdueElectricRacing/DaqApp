from os import listdir, getcwd, system
from os.path import isfile, isdir
from sys import stderr
import glob

def convert():
    ui_dir = './ui'
    ui_files = glob.glob(ui_dir+'/*.ui')
    for file in ui_files:
        system(f'pyuic5 {file} -o {file[:-3] +  ".py"}')
        print(f"converted {file}")

if __name__ == "__main__":
    convert()

# else:
#     for file in args:
#         if file in uifiles:
#             system(f'pyuic5 {file} -o {file[:-3] + ".py"}')
#         else:
#             print(f"Can't fine {file} in the current working directory.", file=stderr)