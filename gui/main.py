from tkinter import *
import serial
# from picamera import PiCamera
from time import sleep

# connect to serial port (use correct one for connected arduino)
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# create camera object
# camera = PiCamera()

# FUNCTIONS


def send_command(outgoing):
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("1\n".encode()) # Go to Manual Mode
    ser.write("7\n".encode()) # Set Units

    val = xyz_unt.get()
    if val == "step":
        ser.write("1\n".encode())
    elif val == "mm":
        ser.write("2\n".encode())
    elif val == "um":
        ser.write("3\n".encode())

    val = s_unt.get()
    if val == "step":
        ser.write("1\n".encode())
    elif val == "mm":
        ser.write("2\n".encode())
    elif val == "um":
        ser.write("3\n".encode())

    if outgoing == "a": # +x
        ser.write("3\n".encode()) # Move

        ser.write(x_res.get().encode())
        ser.write("\n".encode())

        ser.write("0\n".encode()) # y
        ser.write("0\n".encode()) # z
        ser.write("0\n".encode()) # p
        ser.write("1\n".encode()) # Confirm

    elif outgoing == "b": # -x
        ser.write("3\n".encode()) # Move

        ser.write("-".encode())
        ser.write(x_res.get().encode())
        ser.write("\n".encode())

        ser.write("0\n".encode()) # y
        ser.write("0\n".encode()) # z
        ser.write("0\n".encode()) # p
        ser.write("1\n".encode()) # Confirm

    elif outgoing == "c": # +y
        ser.write("3\n".encode()) # Move

        ser.write("0\n".encode())  # x

        ser.write(y_res.get().encode())
        ser.write("\n".encode())

        ser.write("0\n".encode()) # z
        ser.write("0\n".encode()) # p
        ser.write("1\n".encode()) # Confirm

    elif outgoing == "d": # -y
        ser.write("3\n".encode()) # Move

        ser.write("0\n".encode())  # x

        ser.write("-".encode())
        ser.write(y_res.get().encode())
        ser.write("\n".encode())

        ser.write("0\n".encode()) # z
        ser.write("0\n".encode()) # p
        ser.write("1\n".encode()) # Confirm

    elif outgoing == "e": # +z
        ser.write("3\n".encode()) # Move

        ser.write("0\n".encode())  # x
        ser.write("0\n".encode())  # y

        ser.write(z_res.get().encode())
        ser.write("\n".encode())

        ser.write("0\n".encode()) # p
        ser.write("1\n".encode()) # Confirm

    elif outgoing == "f": # -z
        ser.write("3\n".encode()) # Move

        ser.write("0\n".encode())  # x
        ser.write("0\n".encode())  # y

        ser.write("-".encode())
        ser.write(z_res.get().encode())
        ser.write("\n".encode())

        ser.write("0\n".encode()) # p
        ser.write("1\n".encode()) # Confirm

    elif outgoing == "g": # Dispense
        ser.write("3\n".encode()) # Move

        ser.write("0\n".encode())  # x
        ser.write("0\n".encode())  # y
        ser.write("0\n".encode())  # z

        ser.write(s_res.get().encode())
        ser.write("\n".encode())

        ser.write("1\n".encode()) # Confirm

    elif outgoing == "h": # Raise Plunger
        ser.write("3\n".encode()) # Move

        ser.write("0\n".encode())  # x
        ser.write("0\n".encode())  # y
        ser.write("0\n".encode())  # z

        ser.write("-".encode())
        ser.write(s_res.get().encode())
        ser.write("\n".encode())

        ser.write("1\n".encode()) # Confirm

    # elif outgoing == "i": # Activate Pico
    # waiting for implementation


def dispenseSU8():
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("5\n".encode()) # SU8

def dispenseDowsil():
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("6\n".encode()) # PDMS-1700

def dispenseSylgard():
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("7\n".encode()) # PDMS-184

def zeroAxes():
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("2\n".encode()) # Zeroing


def disableMotors():
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("1\n".encode()) # Go to Manual Mode
    ser.write("9\n".encode()) # Enable/Disable Motors
    ser.write("0\n".encode()) # Disable

def enableMotors():
    for ii in range(5):  # Back to Main Manual
        ser.write("-1\n".encode())

    ser.write("1\n".encode()) # Go to Manual Mode
    ser.write("9\n".encode()) # Enable/Disable Motors
    ser.write("1\n".encode()) # Disable

def get_textbox_input():
    val = command_to_send.get()
    ser.write(val.encode())

def change_fluid():
    val = fluid_sel.get()
    ser.write(val.encode())

def open_camera():
    camera.start_preview(fullscreen=False, window=(1500, 200, 300, 400))


def close_camera():
    camera.stop_preview()
###############################################


# create main window object
mainwin = Tk()
mainwin.title("Dispenser Controls")
mainwin.geometry("800x800")

# VARIABLES
fluid_sel = StringVar()
xyz_unt = StringVar()
s_unt = StringVar()

# create frames
frame_l = Frame(mainwin)
frame_r = Frame(mainwin)

motorcontrol_frame = LabelFrame(frame_l, text="Motor Controls", padx=5, pady=5)
# motorcontrol_frame.pack(side=LEFT, anchor=N, padx=5, pady=5)
motorcontrol_frame.grid(row=0, column=0, sticky=N)

xyzresolution_frame = Frame(frame_l, padx=5, pady=5)
xyzresolution_frame.grid(row=1, column=0)
Xaxisresolution_frame = LabelFrame(xyzresolution_frame, text="X Axis Resolution", padx=5, pady=5)
Yaxisresolution_frame = LabelFrame(xyzresolution_frame, text="Y Axis Resolution", padx=5, pady=5)
Zaxisresolution_frame = LabelFrame(xyzresolution_frame, text="Z Axis Resolution", padx=5, pady=5)
Xaxisresolution_frame.grid(row=0, column=0, sticky=N)
Yaxisresolution_frame.grid(row=1, column=0)
Zaxisresolution_frame.grid(row=2, column=0)
Saxisresolution_frame = LabelFrame(frame_l, text="Syringe Pump Resolution", padx=5, pady=5)
Saxisresolution_frame.grid(row=2, column=0)
# Xaxisresolution_frame.pack(anchor=N, padx=5, pady=5)
# Yaxisresolution_frame.pack(anchor=N, padx=5, pady=5)
# Zaxisresolution_frame.pack(anchor=N, padx=5, pady=5)
# Saxisresolution_frame.pack(anchor=N, padx=5, pady=5)
# axisresolution_frame.columnconfigure(0, weight=1)
# axisresolution_frame.columnconfigure(1, weight=1)
# axisresolution_frame.columnconfigure(2, weight=1)
# axisresolution_frame.columnconfigure(3, weight=1)

cameracontrol_frame = LabelFrame(frame_r, text="Camera Controls", padx=5, pady=5)
# #cameracontrol_frame.pack()
# cameracontrol_frame.grid(row=0, column=1, sticky="")

entercommand_frame = LabelFrame(frame_r, text="Enter Command", padx=5, pady=5)
entercommand_frame.grid(row=1, column=1, sticky=W)

selectfluid_frame = LabelFrame(frame_r, text="Select Working Fluid", padx=5, pady=5)
selectfluid_frame.grid(row=2, column=1, sticky=W)

options_frame = LabelFrame(frame_r, text="Options", padx=5, pady=5)
options_frame.grid(row=3, column=1, sticky=W)


# motor control frame buttons
xposButton = Button(motorcontrol_frame, text="+X",  bg="#f9dfad", fg="black", command= lambda:send_command("a")).grid(row=2, column=2, sticky=W+E, padx=5, pady=5)
xnegButton = Button(motorcontrol_frame, text="-X",  bg="#f9dfad", fg="black", command=lambda:send_command("b")).grid(row=2, column=0, sticky=W+E, padx=5, pady=5)
yposButton = Button(motorcontrol_frame, text="+Y",  bg="#716ff8", fg="black", command=lambda:send_command("c")).grid(row=1, column=1, sticky=W+E, padx=5, pady=5)
ynegButton = Button(motorcontrol_frame, text="-Y", bg="#716ff8", fg="black", command=lambda:send_command("d")).grid(row=3, column=1, sticky=W+E, padx=5, pady=5)
zposButton = Button(motorcontrol_frame, text="+Z", bg="#f8716f", fg="black", command=lambda:send_command("e")).grid(row=0, column=1, sticky=W+E, padx=5, pady=5)
znegButton = Button(motorcontrol_frame, text="-Z", bg="#f8716f", fg="black", command=lambda:send_command("f")).grid(row=4, column=1, sticky=W+E, padx=5, pady=5)
dispenseButton = Button(motorcontrol_frame, text="Dispense", bg="#ade4f9", fg="black", command=lambda:send_command("g")).grid(row=4, column=3, sticky=W+E, padx=5, pady=5)
retractButton = Button(motorcontrol_frame, text="Raise Plunger", bg="#ade4f9", fg="black",  command=lambda:send_command("h")).grid(row=2, column=3, sticky=W+E, padx=5, pady=5)
picoButton = Button(motorcontrol_frame, text="Activate Pico", bg="#ade4f9", fg="black",  command=lambda:send_command("i")).grid(row=0, column=3, sticky=W+E, padx=5, pady=5)

motorcontrol_frame.columnconfigure(0, weight=1)
motorcontrol_frame.columnconfigure(1, weight=1)
motorcontrol_frame.columnconfigure(2, weight=1)
motorcontrol_frame.columnconfigure(3, weight=1)


# axis step resolution frame
x_res = Entry(Xaxisresolution_frame, width=15)
x_res.grid(row=0, column=0)
y_res = Entry(Yaxisresolution_frame, width=15)
y_res.grid(row=0, column=0)
z_res = Entry(Zaxisresolution_frame, width=15)
z_res.grid(row=0, column=0)
s_res = Entry(Saxisresolution_frame, width=15)
s_res.grid(row=0, column=0)
spinX = Spinbox(xyzresolution_frame, values=("um", "mm", "step"), textvariable=xyz_unt, width=5).grid(row=1, column=1)
xyz_unt.set("mm")
spinS = Spinbox(Saxisresolution_frame, values=("um", "mm", "step"), textvariable=s_unt, width=5).grid(row=0, column=1)
s_unt.set("step")


# ##camera frame buttons
# opencameraButton = Button(cameracontrol_frame, text="Open Live View", command = open_camera,  bg="#a6f86f", fg="black").grid(row=0, column=0, sticky=W+E, padx=5, pady=5)
# closecameraButton = Button(cameracontrol_frame, text="Close Live View",  bg="#a6f86f", fg="black", command = close_camera).grid(row=0, column=1, sticky=W+E, padx=5, pady=5)
# takephotoButton = Button(cameracontrol_frame, text="Take Photo",  bg="#a6f86f", fg="black").grid(row=2, column=0, sticky=W+E, padx=5, pady=5)
# startrecordingButton = Button(cameracontrol_frame, text="Start Recording",  bg="#a6f86f", fg="black").grid(row=1, column=0, sticky=W+E, padx=5, pady=5)
# stoprecordingButton = Button(cameracontrol_frame, text="Stop Recording",  bg="#a6f86f", fg="black").grid(row=1, column=1, sticky=W+E, padx=5, pady=5)
# cameracontrol_frame.columnconfigure(0, weight=1)
# cameracontrol_frame.columnconfigure(1, weight=1)
# cameracontrol_frame.columnconfigure(2, weight=1)
# cameracontrol_frame.columnconfigure(3, weight=1)


# Send command frame buttons
command_to_send = Entry(entercommand_frame, width=10)
command_to_send.grid(row=1, column=0, sticky=W)
getcommandButton = Button(entercommand_frame, text="Send", command=get_textbox_input).grid(row=1, column=1, sticky=W)


# Select fluid frame
buttonSU8 = Button(selectfluid_frame, text="SU-8", command=dispenseSU8).grid(row=0, column=0, sticky=W)
buttonDowsil = Button(selectfluid_frame, text="Dowsil SE 1700", command=dispenseDowsil).grid(row=1, column=0, sticky=W)
buttonSylgard = Button(selectfluid_frame, text="Sylgard 184", command=dispenseSylgard).grid(row=2, column=0, sticky=W)

# Options frame
homeButton = Button(options_frame, text="Zero Axes", command=zeroAxes).grid(row=0, column=0, sticky=W)
disablemotorsButton = Button(options_frame, text="Disable Motors",command=disableMotors).grid(row=1, column=0, sticky=W)
enablemotorsButton = Button(options_frame, text="Enable Motors",command=enableMotors).grid(row=2, column=0, sticky=W)


frame_l.grid(row=0, column=0)
frame_r.grid(row=0, column=1)

mainwin.mainloop()
