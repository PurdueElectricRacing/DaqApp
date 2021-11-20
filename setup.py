from cx_Freeze import setup, Executable

__version__ = "0.1"
base = "Win32GUI"

executables = [Executable("main.py", base=base)]

packages = ['os', 'PyQt5', 'cantools', 'jsonschema', 
            'pyusb', 'qdarkstyle', 'pyqtgraph', 'numpy', 'time',
            'datetime', 'threading', 'math', 'usb', 'sys', 'json',
            'socket', 'queue', 'pyusb']
options = {
    'build_exe': {    
        'packages':packages,
    },    
}

setup(
    name = "DAQ Dashboard",
    description = 'Data Acquisition via Usb CAN adapter or TCP socket',
    options = options,
    version = __version__,
    executables = executables
)