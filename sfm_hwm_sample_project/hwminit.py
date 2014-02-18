absoluteMeshName = "head_abs" # Adjust this line if your character’s head mesh isn’t named ’head_abs’

import sys, bpy

# Expose the HWMTK pyfiles to the interpreter
# Path to the HWMTK folder relative to the .blend file
sys.path.append(bpy.path.abspath('//hwmtk\\'))

# Enable the Soft Blend from Shape op
import op_softblend
# Import the main toolkit module
import hwm

class HwmOps_PreprocessHeadOp(bpy.types.Operator):
    """Preprocess abs correctors to rel correctors"""
    bl_idname = "object.hwm_hwmpreproc"
    bl_label = "HWM: Preprocess Head for Export"
    
    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'OBJECT'
    def execute(self, context):
        relMesh = hwm.PreprocessMesh(absoluteMeshName)
        if (not relMesh):
            self.report({'WARNING'}, 'Failed to preprocess the %s mesh. Look in the console for now...' % absoluteMeshName)
        else:
            self.report({'INFO'}, "Successfully updated %s..." % relMesh.name)
        return {'FINISHED'}  
    
bpy.utils.register_class(HwmOps_PreprocessHeadOp)      