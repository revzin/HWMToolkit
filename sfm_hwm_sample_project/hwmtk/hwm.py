import bpy, bmesh
import obtools, shapescripting, shapetools, facerules, util
import os

from shapetools import *

from bpy.props import * 

from util import DebugPrint, GetMillisecs

if (util.IsDebugging()):
    import imp
    import op_softblend
    imp.reload(obtools)
    imp.reload(shapetools)
    imp.reload(facerules)
    imp.reload(util)
    imp.reload(shapescripting)
    imp.reload(op_softblend)


# This is a dictionary that exports the internal dmxedit emulation
# methods to the executed preprocess script
ShapeInterfaceDict = {
    "Add"               :   shapescripting.Add,
    "AddCorrected"      :   shapescripting.AddCorrected,
    "GrowSelection"     :   shapescripting.GrowSelection,
    "Interp"            :   shapescripting.Interp,
    "OverrideCorrector" :   shapescripting.OverrideCorrector,
    "ResetState"        :   shapescripting.ResetState,
    "SaveDelta"         :   shapescripting.SaveDelta,
    "Select"            :   shapescripting.Select,
    "SelectHalf"        :   shapescripting.SelectHalf,
    "SetState"          :   shapescripting.SetState,
    "ShrinkSelection"   :   shapescripting.ShrinkSelection,
    "DeleteDelta"       :   shapescripting.DeleteDelta,
    "Translate"         :   shapescripting.Translate,
    "bpy"               :   bpy,
    "GetMesh"           :   shapescripting.GetMesh,
    "PrintSel"          :   shapescripting.Debug_PrintSelection,
    "VisualiseSel"      :   shapescripting.Debug_WriteDownSelection
}


def PreprocessMesh(meshName, scriptFile = None):  
    # Purpose: preprocesses a HWM mesh by name either according to the specified script,
    # or just by converting every corrector to relative mode if no script is specified
    # There must be a '_raw' postfix in the mesh name.
    # A duplicate will be created.
    
    import traceback
    
    def Execute(script_path, var_dict):
        # Executes a script file
        if not os.path.exists(script_path):
            raise ValueError("Script file does not exist.")
        with open(script_path) as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, var_dict)
           
    
    DebugPrint("hwm.PreprocessMesh: meshName = %s scriptFile = %s" % (meshName, scriptFile))
            
    mesh_in = obtools.FindObject(meshName)
    
    print ("Preprocessing mesh %s" % meshName)
    
    if (not mesh_in):
        print ('Error: mesh %s not found!' % meshName)
        return None
        
    if not (mesh_in.name.endswith('_abs')):
        print ('Error: Please add "_abs" postfix to your absolute mesh name to avoid any confusion!')
        return None
    
    if (not shapetools.HasShapes(mesh_in)):
        print ('Error: mesh %s does not have any relative shape keys!' % mesh_in.name)
        return None
    
    if (not shapetools.ValidateShapeNames(mesh_in)):
        print ('Error: mesh %s has a shape with an invalid name!' % mesh_in.name)
        return None
    
    if (not shapetools.CheckForRedundantCorrectives(mesh_in)):
        print ('Error: mesh %s has redundant corrective shapes!' % mesh_in.name)  
        return None 
    
    # Create the new mesh
    mesh_out = obtools.DuplicateObject(mesh_in.name, 
                                        mesh_in.name.replace('_abs', '_rel'))
                                        
         
    if (not mesh_out):
        print ('Failed to duplcate the mesh, aborting...')
        return None
    
    DebugPrint("Duplicated to %s" % mesh_out.name)    
    
    if scriptFile:    
        if shapescripting.OperateOnMesh(mesh_out) == None: # Set up the mesh
            print("Invalid object specified!")
            return None
        print ('Executing', scriptFile)
        failed = False
        try:
            Execute(bpy.path.abspath(scriptFile), ShapeInterfaceDict)
        except:
            traceback.print_exc()
            failed = True
        finally:
            if failed:
                print ('Script execution failed, restoring...')
                obtools.DeleteObject(mesh_out.name)
                return None
        shapescripting.Cleanup()  
        return None    
    else:
        maxRank = 1
        for shape in mesh_out.data.shape_keys.key_blocks:
            shape.value = 0.0
            if (shapescripting.SELECTOR_PREFIX in shape.name):
                DebugPrint("Removing selector %s" % shape.name)
                RemoveShapeKey(mesh_out, shape.name)
            rank = GetShapeRank(shape.name)
            if rank > maxRank:
                maxRank = rank
                
        for i in range(2, maxRank + 1):
            rankStartTime = GetMillisecs()
            rankShapeCount = 0
            for shape in mesh_out.data.shape_keys.key_blocks:
                if GetShapeRank(shape.name) == i:
                    rankShapeCount += 1
                    if (not Corr_AbsToRel(mesh_out, mesh_out, shape, shape)):
                        DebugPrint('Deleting mesh_out')
                        obtools.DeleteObject(mesh_out.name)
                        return None
                    DebugPrint('Converted %s to relative' % shape.name, 2)
            deltaTime = GetMillisecs() - rankStartTime
            DebugPrint('Rank %i took %i msec, avg %i msec' % (i, deltaTime, deltaTime / rankShapeCount))       

    for key in mesh_out.data.shape_keys.key_blocks:
        key.value = 0.0
              
    DebugPrint ('PreprocessMesh done')

    return mesh_out
    
    
def RebuildAbsoluteMesh(mesh_in):
    print ('\nRebuilding correctors mesh from', mesh_in.name)
    mesh_out = obtools.DuplicateObject(mesh_in.name, mesh_in.name + '_absolute_correctors', False)
    maxRank = 1
    for shape in mesh_out.data.shape_keys.key_blocks:
        rank = GetShapeRank(shape.name)
        if rank > maxRank:
            maxRank = rank
    if maxRank == 1:
        print ('Nothing to convert here...')
        return
    
    for i in reversed(range(2, maxRank)): 
        print ('On to rank {} shapes...'.format(i))
        for shape in mesh_out.data.shape_keys.key_blocks:
            if GetShapeRank(shape.name) == i and IsCorrectorShapeName(shape.name):
                Corr_RelToAbs(mesh_out, mesh_out, shape, shape)
                print ('Converted', shape.name)
    print ('Done converting, created', mesh_out.name)
    
     
    
def EnsureCorrectorsAreUnique(mesh_in):
    pass

DebugPrint('hwm.py reloaded...')