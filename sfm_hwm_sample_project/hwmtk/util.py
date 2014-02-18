import bpy

import time

# I only hope for more

def DebugPrint(msg, level = 1):
    if (level <= int(bpy.app.debug_value)):
        print (msg)
        
def IsDebugging():
    return bpy.app.debug_value > 0

def GetMillisecs():
    return int(round(time.time() * 1000))


DebugPrint('util.py reloaded...')
