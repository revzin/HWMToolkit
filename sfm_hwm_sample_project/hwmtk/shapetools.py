import selections
from selections import *

import bpy, bmesh

from mathutils import Vector

import obtools, util
from util import DebugPrint, GetMillisecs

import re
__validShapeRegexp = re.compile(
            "^([A-Z|a-z]{1,100}[0-9]{0,100}_){0,50}(([A-Z|a-z]{1,100}[0-9]{0,100}){1,100})$")
            
# ^([A-Z|a-z]{1,100}[0-9]{0,25}_) : e. g. CloseLid25_CloseLidLo12_, A_B_C_D_...

# Interp and Add operations involve a dictionary that maps vertex indices to their weights: index = weight (vtx_weight_dict)
# All these are operating on regular meshes

def IsCorrectorShapeName(shapeName):
    return (__validShapeRegexp.match(shapeName) and ('_' in shapeName))

def FindShapeKey(mesh, name, exact_mode = False):   
    name = name.lower()
    if exact_mode:
        for shape in mesh.data.shape_keys.key_blocks:
            if shape.name.lower() == name.lower():
                return shape
        return None
          
    affControllersSearch = set(name.split('_'))
    for shape in mesh.data.shape_keys.key_blocks:
        affControllersCandidate = set(shape.name.lower().split('_'))
        if affControllersCandidate == affControllersSearch:
            return shape
    return None
  
def GetShapeRank(name):
    # Returns the shape's rank by its name
    # The rank is how many shapes are in there:
    #   GetShapeRank('A')       =   1
    #   GetShapeRank('A_B')     =   2
    #   GetShapeRank('A_B_C')   =   3
    return len(name.split('_'))
             
def AddShapeKey(mesh, name, overwrite = False):
    # Adds a shape key named name on the mesh
    # Can overwrite
    if mesh:
        if len(name) > 0:
            
            if FindShapeKey(mesh, name):
                if overwrite:
                    RemoveShapeKey(mesh, name)
                else:
                    raise ValueError('Cannot overwrite shape key %s on mesh %s \
                                - use overwrite = True!' % (name, mesh.name))
            
            orig_area = bpy.context.area.type
            orig_scene = bpy.context.scene
            orig_active_obj = bpy.context.active_object
            
            bpy.context.screen.scene = obtools.GetObjectScene(mesh)
            bpy.context.scene.objects.active = mesh
            
            bpy.context.area.type = "VIEW_3D"
            old = mesh.active_shape_key
            
            bpy.context.scene.objects.active = mesh
            bpy.ops.object.shape_key_add(from_mix = False)
            new = mesh.active_shape_key
            mesh.active_shape_key.name = name
            
            bpy.context.area.type = orig_area
            bpy.context.screen.scene = orig_scene
            bpy.context.scene.objects.active = orig_active_obj
            return new
    
def RemoveShapeKey(mesh, name):
    if mesh:
        if name:
            if (len(name) > 0):
                delkey = FindShapeKey(mesh, name)
                if delkey:
                    orig_area = bpy.context.area.type
                    orig_scene = bpy.context.scene
                    orig_active_obj = bpy.context.active_object
                    
                    bpy.context.screen.scene = obtools.GetObjectScene(mesh)
                    bpy.context.scene.objects.active = mesh
            
                    mesh.active_shape_key_index = mesh.data.shape_keys.key_blocks.keys().index(delkey.name)
                    bpy.ops.object.shape_key_remove()
                    
                    bpy.context.area.type = orig_area
                    bpy.context.screen.scene = orig_scene
                    bpy.context.scene.objects.active = orig_active_obj
                    
def HasShapes(mesh):
    return mesh.type == 'MESH' and mesh.data.shape_keys and len(mesh.data.shape_keys.key_blocks) > 1 and \
            mesh.data.shape_keys.use_relative
    # play it safe
   

def GetDeltaCoords(mesh, shape):
    # Gets a list of delta vectors for that shape against the base mesh state
    c = []
    for i in range(len(mesh.data.vertices)):
        c.append(shape.data[i].co - mesh.data.vertices[i].co)
    return c
    
def YeildSubShapeNames(name):
     # Purpose: for A_B, generates A & B, for A_B_C generates A, B, C, A_B, A_C, B_C etc
    
    def NameSet2ShapeName(nameSet):
        return '_'.join(list(nameSet))
    
    def Combinations(iter):
        # Some super-code 
        from itertools import compress, product
        return ( set(compress(iter,mask)) for mask in product(*[[0,1]]*len(iter)) )
        
    if not IsCorrectorShapeName(name):
        return
    
    rank = GetShapeRank(name)
    
    baseShapes = name.split('_')
    for subShapeSet in Combinations(baseShapes):
        if len(subShapeSet) < 1 or len(subShapeSet) == rank:
            continue
        yield NameSet2ShapeName(subShapeSet)

       
def Interp(mesh, vtx_weight_dict, shapekey_in, shapekey_out, amount):
    # Purpose: interprets shapekey_out towards shapekey_in, 
    # is controlled by amount and index-weight dict
    if (shapekey_out not in mesh.data.shape_keys.key_blocks.values()):
        return None
    
    if (shapekey_in not in mesh.data.shape_keys.key_blocks.values()):
        return None 
    
    vw = vtx_weight_dict
    in_verts = shapekey_in.data
    out_verts = shapekey_out.data

    for i in range(len(in_verts)):
        if i in vw:
            diff = in_verts[i].co - out_verts[i].co
            out_verts[i].co += diff * amount * vw[i]
        else:
            continue

def Add(mesh, vtx_weight_dict, shapekey_in, shapekey_out, amount):
    # Purpose: adds delta displacements from shapekey_in to shapekey_out
    # is controlled by amount and index-weight dict
    in_verts_co = GetDeltaCoords(mesh, shapekey_in)
    out_verts = shapekey_out.data
    vwd = vtx_weight_dict
    n = len(in_verts_co)
    for i in range(n):
        if i in vwd:
            diff = vwd[i] * amount * in_verts_co[i]
            out_verts[i].co = out_verts[i].co + diff
        else:
            # if not weighed, it's zero and not to be moved
            continue 

def Translate(mesh, vtx_weight_dict, shapekey_out, dx, dy, dz):
    # Purpose: translate vertices in the weight dict somewhere
    verts = shapekey_out.data
    vwd = vtx_weight_dict
    
    d = Vector((0,0,0))
    
    for i in range(len(verts)):
        if i in vwd:
            d.x = dx
            d.y = dy
            d.z = dz
            verts[i].co += vwd[i] * d
        else:
            continue


def CopyShapeKey(shape_in, shape_out):
    # Copies shape_in to shape_out
    # The indices between the meshes MUST match
    for i in range(len(shape_in.data)):
        shape_out.data[i].co = shape_in.data[i].co
        
        
def ValidateShapeNames(mesh):
    
    if (not mesh):
        return False
      
    for s in mesh.data.shape_keys.key_blocks:
        match = __validShapeRegexp.match(s.name)
        if (not match):
            print ("Invalid shape name %s!" %  s.name)
            return False
    
    return True    
        
def CheckForRedundantCorrectives(mesh):
    
    if (not mesh):
        return False
    
    shapes = mesh.data.shape_keys.key_blocks
    
    for i in range(len(shapes)):
        if (GetShapeRank(shapes[i].name) < 2):
            continue
        
        nameSet = set(shapes[i].name.split('_'))
        
        for j in range(i + 1, len(shapes)): 
            
            if (GetShapeRank(shapes[j].name) < 2):
                continue
            
            searchNameSet = set(shapes[j].name.split('_'))
            
            if (nameSet == searchNameSet):
                print ('Ambiguous corrective shapes found: %s and %s!' %
                                 (shapes[i].name, shapes[j].name))
                return False
            
    return True
                
                   
def Corr_RelToAbs(mesh_in, mesh_out, shapekey_in_rel, shapekey_out_abs):
    ''' Purpose: saves this corrector as an abs shape,
                    apporopriately checks for sub-shapes ON THE OUT MESH
                    under the assumption they all are RELATIVE
                    That means you MUST covnert all lower-rank shapes FIRST! '''
    
    if len(mesh_in.data.vertices) != len(mesh_out.data.vertices):
        raise ValueError('Different meshes specified.')
        
    subKeys = []                   
    for subKeyName in YeildSubShapeNames(shapekey_in_rel.name):
        key = FindShapeKey(mesh_out, subKeyName)
        if key:
            subKeys.append(key)
        else:
            if (GetShapeRank(subKeyName) < 2):
                print ('Base shape %s not found while processing corrective shape %s' % (subKeyName, shapekey_in_abs.name) )
                return None

    subMix_co = []
    # Can loop on key-vtx, or on vtx-key. This is the latter, 
    
    for i in range(len(shapekey_out_abs.data)):
        subMix_co.append(Vector((0,0,0)))
    
    for k in subKeys:
        delta_co = GetDeltaCoords(mesh_in, k)
        for i in range(len(shapekey_out_abs.data)):
            subMix_co[i] += delta_co[i]
                  
    CopyShapeKey(shapekey_in_rel, shapekey_out_abs)
    
    for i in range(len(shapekey_out_abs.data)):
        shapekey_out_abs.data[i].co += subMix_co[i]
                

def Corr_AbsToRel(mesh_in, mesh_out, shapekey_in_abs, shapekey_out_rel):
    ''' Purpose: saves this corrector as a rel shape,
                 apporopriately checks for sub-shapes ON THE IN MESH
                 under the assumption they all are RELATIVE (to keep things simple)
    '''
    
    DebugPrint("Corr_AbsToRel %s %s" % (mesh_in.name, shapekey_in_abs.name), 3)
    
    if len(mesh_in.data.vertices) != len(mesh_out.data.vertices):
        raise ValueError('Different meshes specified.')       
        
    subKeys = []   
    
    startTime = GetMillisecs()
             
    for subKeyName in YeildSubShapeNames(shapekey_in_abs.name):
        key = FindShapeKey(mesh_out, subKeyName)
        if key:
            subKeys.append(key)
        else:
            if (GetShapeRank(subKeyName) < 2):
                print ('Base shape %s not found while processing corrective shape %s' % (subKeyName, shapekey_in_abs.name) )
                return None
           
    [DebugPrint(" " + subKey.name, 3) for subKey in subKeys]
    
    subMix_co = []
    # Can loop on key-vtx, or on vtx-key. This is the latter, 
    for i in range(len(shapekey_in_abs.data)):
        subMix_co.append(Vector((0,0,0)))
    
    for k in subKeys:
        delta_co = GetDeltaCoords(mesh_in, k)
        for i in range(len(shapekey_in_abs.data)):
            subMix_co[i] += delta_co[i]
            
    CopyShapeKey(shapekey_in_abs, shapekey_out_rel)
    
    for i in range(len(shapekey_out_rel.data)):
        shapekey_out_rel.data[i].co -= subMix_co[i]  
    
    DebugPrint("AbsToRel: %i" % (GetMillisecs() - startTime), 2)
    
    return True 
    
def EstimateWrinkleScale(mesh, shapekey):
    ''' Purpose: returns wrinklemap scale based on vertices displacement '''
    raise ValueError('Not implemented')
    pass
    
def CreateSelectorBySelection(mesh, selector_name):
    raise ValueError('Not implemented')
    pass

def SelectByShape(shape):
    raise ValueError('Not implemented')
    pass
    
DebugPrint('shapetools.py reloaded...')