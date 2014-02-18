# Purpose: selection tools
# which affect what vertices will move when shapekey editing functions will be used
# Keep in mind this has NO relation to Blender selections whatsoever

import bpy, bmesh
import math, random
from math import sqrt
from mathutils import Color, Vector

import util
from util import DebugPrint, GetMillisecs


def DiscardSoft(vtx_weight_dict):
    # Purpose: creates a new selection,
    # only with 1.0 weights
    r = dict()
    for v in vtx_weight_dict:
        if vtx_weight_dict[v] == 1.0:
            r[v] = 1.0
    return r
     
def Select(vtx_index_list):

    # Purpose: hard-select some vertices in a bmesh_in by indices.
    #             Mainly needed to have something selected before passing to BuildSoftSelection
    # Returns: weigthdict wit1.0s by selected indeces
    vwd = dict()
    for i in vtx_index_list:
        vwd[i] = 1.0
    return vwd

def SelectIntersect(vtx_weight_dict_a, vtx_weight_dict_b):
    r = dict()
    for v_i in vtx_weight_dict_a:
        if v_i in vtx_weight_dict_b and vtx_weight_dict_a[v_i] == 1.0 and vtx_weight_dict_b[v_i] == 1.0:
            r[v_i] = 1.0
    return r

def SelectAdd(vtx_weight_dict_a, vtx_weight_dict_b):
    r = dict()
    for v_i in vtx_weight_dict_a:
        if vtx_weight_dict_a[v_i] == 1.0:
            r[v_i] = 1.0
    for v_i in vtx_weight_dict_b:
        if vtx_weight_dict_b[v_i] == 1.0:
            r[v_i] = 1.0
    return r

def SelectSubtract(vtx_weight_dict_a, vtx_weight_dict_b):
    r = dict()
    for v_i in vtx_weight_dict_a:
        if v_i in vtx_weight_dict_b:
            continue
        r[v_i] = vtx_weight_dict_a[v_i]
            
    return r

def SelectAll(bmesh_in):
    vwd = dict()
    
    i = 0
    for v in bmesh_in.verts:
        i += 1
    
    for i in range(i):
        vwd[i] = 1.0
        
    return vwd
             
def BuildSoftSelection(bmesh_in, vtx_weight_dict, falloff_distance, falloff_type):
    # Purpose: builds a soft selection
    # bmesh_in - bbmesh_in object to run on
    # vtx_weight_dict - a weightmap between vtx indices and weights
    # falloff_distance - proportional editing distance
    # falloff_type - 'SPIKE', 'BELL', 'LINEAR', 'RANDOM', 'DOME'
    # use_connected - soft select only connected verts
    # Returns: weights dictionary {vert_index = selection_weight}
    
    DISTANCE_MULTI = 2.0
    falloff_distance *= DISTANCE_MULTI
    
    def GetWeight(distance, max, type):
        if distance <= 0.0001:
            return 1.0
        if distance >= max: 
            return 0.0
        l = distance / max
        if type == 'SPIKE':
           return 1 - math.sqrt(2 * l - l * l)
        if type == 'LINEAR':
           return 1 - l
        if type == 'DOME':
            return sqrt(1 - l * l)
        if type == 'BELL':
            return (1 + 2 * l) * (1 - l) * (1 - l) # hermite h00  
        if type == 'RANDOM':
            return random.random()
        
        return 0.0
    
    def WeightLinkedVtxVec(bmesh_in, index, vtx_weight_dict, falloff_distance, current_falloff_distance, falloff_type):
        vert = bmesh_in.verts[index]
        vtx_distance_dict = dict()
        for e in vert.link_edges:
            other = e.other_vert(vert)
            other_vector = other.co - vert.co
            w = GetWeight((current_falloff_distance + other_vector).length, falloff_distance, falloff_type)
            if other.index in vtx_weight_dict:
                if vtx_weight_dict[other.index] < w:
                    vtx_weight_dict[other.index] = w
                else:
                    continue
            if w > 0.0:
                vtx_distance_dict[other.index] = other_vector + current_falloff_distance
                vtx_weight_dict[other.index] = w
        return vtx_weight_dict, vtx_distance_dict

    # Maybe an overmeasure, but let's 'clean' the select dict from non 1.0 weights
    
    for i in range(len(bmesh_in.verts)):
        if i in vtx_weight_dict:
            if vtx_weight_dict[i] != 1.0:
                vtx_weight_dict.pop(i)
                
    falloff_distance = abs(falloff_distance)
     
    bounces = 0
    startTime = GetMillisecs()
         
    pre_step_dict = dict()    
    distance = dict() # index = distance
    while True:
        # 0. Determine vertices that are 'new' from the last iteration to speed up (could iterate over all vertices -- is this really a speedup?)
        # NB: On fist iteration, they will all be 'new'
        new_vtx = list(set(vtx_weight_dict.keys()) - set(pre_step_dict.keys()))
        pre_step_dict = dict(vtx_weight_dict)
        n_items = len(vtx_weight_dict)
        # Weigth them
        for index in new_vtx:
            bounces += 1
            if vtx_weight_dict[index] == 1.0:
                # distance[index] = 0.0
                distance[index] = Vector((0, 0, 0))
            vtx_weight_dict, new_dists = WeightLinkedVtxVec(   bmesh_in = bmesh_in,
                                                            index = index,
                                                            vtx_weight_dict = vtx_weight_dict,
                                                            falloff_distance = falloff_distance,
                                                            current_falloff_distance = distance[index],
                                                            falloff_type = falloff_type)
            distance.update(new_dists)
        if (len(vtx_weight_dict) == n_items):
            #DebugPrint("BuildSoftSelection --- %i bounces %i" % (bounces, GetMillisecs() - startTime ), 3)
            break
        # If there's nothing added after the iteration, it means we selected everything we could add is added

    return vtx_weight_dict     
             
             
def SelectMore(bmesh_in, vtx_weight_dict):
    # Selects more vertices amount times
    # Takes into consideration only vertices that are 'hard-selected'
    ret = dict()
    for v in bmesh_in.verts:
        if v.index in vtx_weight_dict:
            if vtx_weight_dict[v.index] == 1.0:
                ret[v.index] = 1.0
                for e in v.link_edges:
                    ret[e.other_vert(v).index] = 1.0
    return ret
    
def SelectLess(bmesh_in, vtx_weight_dict):
    vtx_weight_dict = DiscardSoft(vtx_weight_dict)
    ret = dict()
    for v in bmesh_in.verts:
        if v.index in vtx_weight_dict:
            nE = len(v.link_edges)
            nSE = 0
            for e in v.link_edges:
                other_i = e.other_vert(v).index
                if other_i in vtx_weight_dict:
                    nSE += 1
            if nE == nSE:
                ret[v.index] = 1.0          
    return ret
                    
    
def Debug_DictToCols(not_a_bmesh_in, vtx_weight_dict, name):
    # Purpose: writes vertex colors based on weight list to the bmesh_in (not a bbmesh_in please) for visual debugging 
    # White = 1
    # Black = 0
    d = vtx_weight_dict
            
    my_object = not_a_bmesh_in.data
    vert_list = my_object.vertices
    color_map = my_object.vertex_colors.new()
    color_map.name = name
    i = 0
    for poly in my_object.polygons:
        for indx in poly.loop_indices:
            loop = my_object.loops[indx]
            v = loop.vertex_index
            if v in d:
                #print (d[v])
                c = Color((d[v], d[v], d[v]))
            else:
                c = Color((0, 0, 0))
            color_map.data[i].color = c
            i += 1
 
 
DebugPrint('selections.py reloaded...')
 
'''   
if __RunTest:
    # soft-selection tests - runs soft selections based on currently
    # selected vertices in blender, writes selection
    # as vertex colors
    bpy.ops.object.mode_set(mode = 'EDIT', toggle=False)
    from pprint import pprint
    
    b = bmesh.new()
    b = bmesh.from_edit_mesh(bpy.context.scene.objects.active.data)
    
    selected_verts = [vert.index for vert in b.verts if vert.select]
    
    print (selected_verts)
    
    
    b = bmesh.from_edit_mesh(bpy.context.scene.objects.active.data)
    wwd = Select(selected_verts)
    wd = BuildSoftSelection_Old(b, wwd, 1.5, 'BELL', True)
    bpy.ops.object.mode_set(mode = 'VERTEX_PAINT', toggle=False)
    Debug_DictToCols(bpy.context.scene.objects.active, wd, 'Old')
    bpy.ops.object.mode_set(mode = 'EDIT', toggle=False)
   
    b = bmesh.from_edit_mesh(bpy.context.scene.objects.active.data)
    wwd = Select(selected_verts)
    wd = BuildSoftSelection_New(b, wwd, 1.5, 'BELL', True)
    bpy.ops.object.mode_set(mode = 'VERTEX_PAINT', toggle=False)
    Debug_DictToCols(bpy.context.scene.objects.active, wd, 'New')
    bpy.ops.object.mode_set(mode = 'EDIT', toggle=False)
    
    b = bmesh.from_edit_mesh(bpy.context.scene.objects.active.data)
    wwd = Select(selected_verts)
    wd = BuildSoftSelection(b, wwd, 1.5, 'BELL', True)
    bpy.ops.object.mode_set(mode = 'VERTEX_PAINT', toggle=False)
    Debug_DictToCols(bpy.context.scene.objects.active, wd, 'New2')
    bpy.ops.object.mode_set(mode = 'EDIT', toggle=False)
    
    b = bmesh.from_edit_mesh(bpy.context.scene.objects.active.data)
    wwd = Select(selected_verts)
    wd = BuildSoftSelection_NewNewNew(b, wwd, 2, 'BELL', True)
    bpy.ops.object.mode_set(mode = 'VERTEX_PAINT', toggle=False)
    Debug_DictToCols(bpy.context.scene.objects.active, wd, 'New3')
    '''