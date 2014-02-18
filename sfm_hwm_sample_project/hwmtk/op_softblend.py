import bpy

from bpy.props import *

import hwm

import shapetools, selections, obtools
from selections import *
from shapetools import *

        

class ValveHWM_UL_ShapeKeys(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align = True)
        row.label(item.name, icon = 'SHAPEKEY_DATA')
        

falloff_types_items = [ ('SPIKE', 'SPIKE', 'SPIKE'),
                        ('BELL', 'BELL', 'BELL'),
                        ('DOME', 'DOME', 'DOME'),
                        ('LINEAR', 'LINEAR', 'LINEAR'), 
                        ('RANDOM', 'RANDOM', 'RANDOM')]
                        

class ValveHWM_SoftBlendFromShape(bpy.types.Operator):
    """This is Blend from Shape, but with Soft Selection!"""
    bl_idname = "mesh.softblendfromshape"
    bl_label = "Soft Blend from Shape"
    bl_options = {'REGISTER', 'UNDO'}
    
    prAdd = bpy.props.BoolProperty(
        name = "Add",
        description = "Will we add the shape or blend towards it?",
        default = True )
    
    prShapeIndex = IntProperty(name = "Shapekey index", default = 0)
    
    prAmount = bpy.props.FloatProperty(
        name = "Amount", 
        description = "How much shall we blend?", 
        default = 0.5, 
        min = -2.0, 
        max =  2.0,
        soft_min = -1.0,
        soft_max = 1.0, 
        step = 0.01, 
        precision = 3)
        
    prUseSoft = bpy.props.BoolProperty(
        name = "Soft",
        description = "Will we use proportional selection?",
        default = True )    
    
    prFalloffDistance = bpy.props.FloatProperty(
        name = "Proportional distance", 
        description = "How fast the falloff would be?", 
        default = 1.0, 
        min = 0.0, 
        max =  40.0,
        step = 0.01, 
        precision = 3)
    
    prFalloffType = bpy.props.EnumProperty(
        name = 'Falloff type',
        description = 'What falloff type to use?',
        items = falloff_types_items,
        default = 'BELL')
    
    @classmethod
    def poll(cls, context):
        o = context.active_object
        if context.active_object.mode != 'EDIT':
            return False
        if (o is None) or not HasShapes(o):
            return False
         
        return True
    
    def execute(self, context):
        
        if (util.IsDebugging()):
            import imp
            imp.reload (hwm)
              
        o = context.active_object
        
        toKey = o.active_shape_key
        fromKey = o.data.shape_keys.key_blocks[self.prShapeIndex]
        
        if (toKey == fromKey):
            return {'FINISHED'}
    
            
        bm = bmesh.new()
        bm = bmesh.from_edit_mesh(o.data)
         
        selverts = [vert.index for vert in bm.verts if vert.select]
        weights = Select(selverts)
        
        if self.prUseSoft: 
            weights = BuildSoftSelection(bmesh_in = bm, 
                vtx_weight_dict = weights, falloff_distance = self.prFalloffDistance, 
                falloff_type = self.prFalloffType)
        
        bpy.ops.object.mode_set(mode='OBJECT') 
                        
        if self.prAdd:
            Add(o, weights, fromKey, toKey, self.prAmount)
        else:
            Interp(o, weights, fromKey, toKey, self.prAmount)
        
        bpy.ops.object.mode_set(mode='EDIT') 
        
             
        return {'FINISHED'}
    
    
    def draw(self, context):
        l = self.layout
        r = l.row()

        r.template_list("ValveHWM_UL_ShapeKeys", 
                "", context.active_object.data.shape_keys, "key_blocks", self, "prShapeIndex")  
        r = l.row()
        r.label("From: " + context.active_object.data.shape_keys.key_blocks[self.prShapeIndex].name)
        r.label("To: " + context.active_object.active_shape_key.name)
        r = l.row()
        r.prop(self, "prAdd") 
        r.prop(self, "prUseSoft")
        r = l.row()
        r.prop(self, "prAmount")
        r = l.row()
        if (self.prUseSoft):
            r.prop(self, "prFalloffDistance")
            r = l.row()
            r.prop_menu_enum(self, "prFalloffType")
            r.label(self.prFalloffType)
			
def register(): 
    # Soft Blend from Shape
    bpy.utils.register_class(ValveHWM_UL_ShapeKeys)
    bpy.utils.register_class(ValveHWM_SoftBlendFromShape)
    

register()
	