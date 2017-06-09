import ivision
from ivision import survilance as s
import tkinter as tk
from tkinter import filedialog

dt=s.DwellTimer()

confpath=filedialog.askopenfilename()
dt.start(confpath)
