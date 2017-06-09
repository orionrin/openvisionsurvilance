import ivision
from ivision import survilance as s
import tkinter as tk
from tkinter import filedialog

cp=s.PeopleCount()

confpath=filedialog.askopenfilename()
cp.start(confpath)
