import bpy

import util
from util import DebugPrint, GetMillisecs

def FindObject(Name):
    for o in bpy.data.objects:
        if o.name == Name:
            return o
    return None

def DeleteObject(Name):
    # Courtesy of littleneo from blenderartists
    # Thanks there!
    
    def wipeOutData(data) :
        if data.users == 0 :
            try : 
                data.user_clear()
                # mesh
                if type(data) == bpy.types.Mesh :
                    bpy.data.meshes.remove(data)
            except :
                # empty, field
                print('%s has no user_clear attribute.'%data.name)
        else :
            print('%s has %s user(s) !'%(data.name,data.users))
            
    def wipeOutObject(ob,and_data=True) :
        
        data = bpy.data.objects[ob.name].data
        
        # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2) 
        # so if there's more than one user for this data, never wipeOutData. will be done with the last user
        # if in the list
        if data.users > 1 :
            and_data=False
        
        # odd :    
        ob=bpy.data.objects[ob.name]    
        # if the ob (board) argument comes from bpy.data.groups['aGroup'].objects,
        #  bpy.data.groups['board'].objects['board'].users_scene
    
        for sc in ob.users_scene :
            sc.objects.unlink(ob)
    
        try : bpy.data.objects.remove(ob)
        except : print('data.objects.remove issue with %s'%ob.name)
        
        # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2) 
        if and_data :
            wipeOutData(data)    
    o = FindObject(Name)
    if o:
        if (o.type == 'MESH'):
            DebugPrint('Deleting %s' % Name)        
            wipeOutObject(o, True)

def DuplicateObject(fromName, toName, overwrite = True):  
    
    
    if (fromName == toName): 
        print ('obtools.DuplicateObject: source and destination must differ...')
        return None
    
    from_ob = FindObject(fromName)
    
    if not from_ob:
        return None
    
    if overwrite:
        to_ob = FindObject(toName)
        if to_ob:
            DeleteObject(toName)
    
    old_scene = bpy.context.scene
    
    bpy.context.screen.scene = from_ob.users_scene[0]
    
    for ob in bpy.data.objects:
        ob.select = False
        
    from_ob.select = True
    
    bpy.context.scene.objects.active = from_ob    
    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
    to_ob = bpy.context.scene.objects.active
    to_ob.name = toName
    
    from_ob.select = False  
    to_ob.select = True
     
    bpy.context.screen.scene = old_scene
     
    return to_ob

def GetObjectScene(obj):
    if (len(obj.users_scene)):
        return obj.users_scene[0]
    else:
        return None

DebugPrint("obtools.py reloaded...")