from Stream import *
from tkinter import *


def availableStreams() -> list:

    streams = resolve_streams()

    name, inlets = [], []

    for stream in streams:
        inlet = StreamInlet(stream)
        name.append(inlet.info().name())

    return name


def selectStreams(stream):

    # Creating a window
    win = Tk()
    win.geometry("150x150")
    # Here we select multiple mode to select more than one option
    # creating a list of items that we want to display on the window
    opt = Listbox(win, selectmode="multiple")
    lis = stream["name"]
    # Now we will add this into window as it would expand accordingly in both axis
    opt.pack(expand=YES, fill="both")
    # insering each items into options this will add into list that get displayed
    for i in lis:
        opt.insert(END, i)
    # keeping the window into main loop this will keep window displayed
    win.mainloop()

    return
