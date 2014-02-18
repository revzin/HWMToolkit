# ====================================
# Face rules
# ====================================

import bpy, inspect

'''

def __ImportDatamodelPy():
    import os, imp
    appdata = os.getenv("APPDATA")
    blender = os.path.join(appdata, "Blender Foundation\\Blender", str(bpy.app.version[0]) + '.' + str(bpy.app.version[1]))
    dm_path = os.path.join(blender, "scripts\\addons\\io_scene_valvesource", "datamodel.py")
    print (dm_path)
    if os.path.exists(dm_path):
        datamodel = imp.load_source("datamodel", dm_path)
        return datamodel
    else:
        return None
    
datamodel = __ImportDatamodelPy()
if (not datamodel):
    raise ArgumentError('Datamodel.py not preset where it should be -- check your Blender Source Tools?')

'''
    
dm_rules = None

def __GetRawControl(dm, name):
    pass

def __GetDmeCIC(dm, name):
    pass

def __GetDmeDR(dm, name):
    pass

def __Finalize():
    dm_rules = None
    mesh = None

def UsePassthroughs():
    ''' Purpose: '''    

def LoadFaceRules(dmxName):
    pass
    
def SaveFaceRules(dmxName):
    pass
    
def NewFaceRules(HWMDefaults = True):
    pass
  
def AddDominationRule(listDominators, listSuppressed):
    pass

def ReorderControls(*controlNames):
    ''' Reorders DmeCombinationInputControls by name '''
    pass

def GroupControls(groupName, *rawControlNames):
    ''' Creates a DmeCombinationInputControl groupName for rawControlNames'''
    pass
    
def SetWrinkleScale(controlName, rawControlName, scale):
    pass

# ===========================s