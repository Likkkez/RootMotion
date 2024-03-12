bl_info = {
    "name": "Rootmotion",
    "author": "Likkez",
    "version": (2, 0),
    "blender": (4, 0, 2),
    "description": "Transfer movement from feet to root. Transfer movement from root bone to object root.",
    "wiki_url": "",
    "category": "Animation",
}
import bpy
import mathutils
import math

#TODO: add an unroot for object mode.
#TODO: review the code, make it less retarded.

def spawn_empty(name, display_type='PLAIN_AXES', size=1.0):
    empty = bpy.data.objects.new( name, None )
    bpy.context.scene.collection.objects.link( empty )
    empty.empty_display_size = .2
    empty.empty_display_type = display_type
    empty.empty_display_size = size 
    return empty

def get_master(bone):
    while bone.parent!=None:
        bone=bone.parent
    return bone

def spawn_armature(name,location):
    arm=bpy.data.armatures.new(name)
    arm_obj=bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(arm_obj)
    arm_obj.location=location
    return arm_obj
    
def key_insert(posebone, Loc = True, Rot = True, Scale = True):   
    if Loc:
        posebone.keyframe_insert(data_path="location")
    if Rot:
        if posebone.rotation_mode == "QUATERNION":
            posebone.keyframe_insert(data_path="rotation_quaternion")
        else:
            posebone.keyframe_insert(data_path="rotation_euler")
    if Scale:
        posebone.keyframe_insert(data_path="scale")

def rootmotion_create_proxy(arm, master_bone, no_master_anim=True):
    # #save armature layers
    # arm_layers=[]
    # for layer in arm.data.layers:
    #     arm_layers.append(layer)
    
    
    scene = bpy.context.scene
    
    children=[]
    for bone in master_bone.children:
        children.append(bone)
        for bone in arm.pose.bones:
            if (not bone.parent) and (bone!=master_bone):
                for pbone in bone.children:
                    if (not pbone in children):
                        children.append(pbone)
    all_bones=children.copy()
    all_bones.append(master_bone)
    
    #create armature
    bpy.ops.object.mode_set(mode='OBJECT')

    arm_rm=spawn_armature(arm.name + 'ROOTMOTION_REMOVEME_qwernoinsgSsda',(0,0,0))
    arm_rm.matrix_world=arm.matrix_world


    bpy.ops.object.select_all(action='DESELECT')
    arm_rm.select_set(True)
    bpy.context.view_layer.objects.active=arm_rm
    bpy.ops.object.mode_set(mode='EDIT')


    for bone in all_bones:
        edit_bone=arm_rm.data.edit_bones.new(bone.name)
        edit_bone.tail=(0,0,5)
        edit_bone.head=(0,0,0)

    bpy.ops.object.mode_set(mode='POSE')
    for bone in arm_rm.pose.bones:
        try:
            arm.pose.bones[bone.name]
            # if bone.name!=master_bone.name:
            constr=bone.constraints.new('COPY_TRANSFORMS')
            constr.target=arm
            constr.subtarget=bone.name
        except:
            pass




    #apply pose    
    bpy.ops.pose.armature_apply(selected=False)

    #remove contraint from the master
    if no_master_anim:
        armrm_master = arm_rm.pose.bones.get(master_bone.name)
        for constr in armrm_master.constraints:
            armrm_master.constraints.remove(constr)



    arm.data.pose_position='POSE'
    
    
    #bake action for arm_rm
    bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=False, visual_keying=True, clear_constraints=True, bake_types={'POSE'})




    #add constraints to required bones
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active=arm

    bpy.ops.object.mode_set(mode='POSE')
    # bpy.ops.armature.collection_show_all()
    bpy.ops.pose.select_all(action='DESELECT')
    

    for bone in all_bones:
        if bone.name!=master_bone.name:
            bone.bone.select=True
            constr=bone.constraints.new('COPY_TRANSFORMS')
            constr.target=arm_rm
            constr.subtarget=bone.name
            constr.name="ROOTMOTION_REMOVEME_qwernoinsgSsda"

        
    #restore layers on armature
    # for idx,layer in enumerate(arm_layers):
    #     arm.data.layers[idx]=layer
        
    #select root bone 
    bpy.ops.pose.select_all(action='DESELECT')
    master_bone.bone.select = True
        
        
    #hide proxy armature
    arm_rm.hide_viewport=True
    
    return arm_rm

def bakebones(arm, phrase='ROOTMOTION_REMOVEME_qwernoinsgSsda'):
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='DESELECT')
    for bone in arm.pose.bones:
        for constr in bone.constraints:
            if phrase in constr.name:
                bone.bone.select=True
                pass
    #bake action for armature
    bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=False, use_current_action=True, bake_types={'POSE'})
    
    #remove constraints
    for bone in arm.pose.bones:
        for constr in bone.constraints:
            if phrase in constr.name:
                bone.constraints.remove(constr)

def rootmotion_remove_proxy(arm):
    # #save armature layers
    # arm_layers=[]
    # for layer in arm.data.layers:
    #     arm_layers.append(layer)
            
    bakebones(arm)
                
    #delete temp armature
    arm_rm = bpy.data.objects[arm.name + 'ROOTMOTION_REMOVEME_qwernoinsgSsda']
    if arm_rm.animation_data:
        bpy.data.actions.remove(arm_rm.animation_data.action)
    arm_rm_arm=arm_rm.data
    bpy.data.objects.remove(arm_rm)
    bpy.data.armatures.remove(arm_rm_arm)
    
    
    # #restore layers on armature
    # for idx,layer in enumerate(arm_layers):
    #     arm.data.layers[idx]=layer


def getrootbone_selection():
    rootobject = bpy.data.objects.get(bpy.context.scene.RT_root_object)
    if rootobject:
        if rootobject.type == 'ARMATURE':
            return rootobject.pose.bones.get(bpy.context.scene.RT_root_bone)
    return None

def valid_curve(context, obj, fcurve, ignore_hidden = True, internal_valid = False):
    if fcurve.is_valid and internal_valid or (not ((ignore_hidden and fcurve.hide) or fcurve.lock or fcurve.is_empty)):
        if 'pose.bones' in fcurve.data_path:
            split_data_path = fcurve.data_path.split(sep='"')
            if len(split_data_path) > 1:
                bone_name = split_data_path[1]
                bone = obj.pose.bones.get(bone_name)
            if bone and (bone in context.selected_pose_bones):
                return True
    return False




#TODO: Rewrite this whole chunk, its too bloated. Make it use the rootmotion_create_proxy, rootmotion_remove_proxy
class RT_OT_rootmotion(bpy.types.Operator):
    bl_description = "Select all feet bones and run. Alternatively, select the Root bone"
    bl_idname = 'rootmotion.rootmotion'
    bl_label = "RootMotion"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        
        up_axis=scene.RT_up_axis
        keep_offset=scene.RT_keep_offset
        current_positions=scene.RT_current_positions
        rotation_offset=scene.RT_rotation_offset
        enable_rotation=scene.RT_rotate_root
        limit_location=scene.RT_limit_location
        imprefect_hierarchy=True

        arm=bpy.context.selected_editable_objects[0]

        foot_list=bpy.context.selected_pose_bones.copy() ######
        master_bone=get_master(foot_list[0]) ####

        children=[]
        for bone in master_bone.children:
            children.append(bone)
        if imprefect_hierarchy:
            for bone in arm.pose.bones:
                if (not bone.parent) and (bone!=master_bone):
                    for pbone in bone.children:
                        children.append(pbone)

        all_bones=children.copy()
        all_bones.append(master_bone)
        
        if not current_positions:
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)

        # #save armature layers
        # arm_layers=[]
        # for layer in arm.data.layers:
        #     arm_layers.append(layer)
            
            
        if not current_positions:
            arm.data.pose_position='REST'

        #check if root bone is selected or not
        if foot_list[0].parent:
            constraints_mute=[]
            for bone in all_bones:
                if bone.constraints:
                    for constr in bone.constraints:
                        constraints_mute.append(constr.mute)
                        constr.mute=True

            #create armature
            bpy.ops.object.mode_set(mode='OBJECT')

            arm_rm=spawn_armature('Rootmotion',(0,0,0))
            arm_rm.matrix_world=arm.matrix_world


            bpy.ops.object.select_all(action='DESELECT')
            arm_rm.select_set(True)
            bpy.context.view_layer.objects.active=arm_rm
            bpy.ops.object.mode_set(mode='EDIT')

            feet_bone=arm_rm.data.edit_bones.new('feet_bone')
            feet_bone.tail=(0,0,5)
            feet_bone.head=(0,0,0)
            #bpy.ops.object.mode_set(mode='POSE')



            for bone in all_bones:
                edit_bone=arm_rm.data.edit_bones.new(bone.name)
                edit_bone.tail=(0,0,5)
                edit_bone.head=(0,0,0)
            arm_rm.data.edit_bones[master_bone.name].parent=feet_bone

            bpy.ops.object.mode_set(mode='POSE')
            for bone in arm_rm.pose.bones:
                try:
                    arm.pose.bones[bone.name]
                    constr=bone.constraints.new('COPY_TRANSFORMS')
                    constr.target=arm
                    constr.subtarget=bone.name
                except:
                    pass


            master_bone_temp=arm_rm.pose.bones[master_bone.name]
            #feet constraints
            feet_bone =  arm_rm.pose.bones['feet_bone']


            #check if rotation is enabled
            foot_constraints=['COPY_ROTATION', 'COPY_LOCATION']
            if not enable_rotation:
                foot_constraints=['COPY_LOCATION']


            for idx, foot in enumerate(foot_list):
                for constr_type in foot_constraints:
                    constr=feet_bone.constraints.new(constr_type)
                    constr.target=arm
                    constr.subtarget=foot.name
                    if constr_type=='COPY_ROTATION':
                        constr.use_y=False
                        constr.use_x=False
                    if idx!=0:
                        constr.influence=1/len(foot_list)
            #lock to floor
            if limit_location:
                constr=feet_bone.constraints.new('FLOOR')
                constr.target=arm
                constr.subtarget=''
                constr.floor_location='FLOOR_NEGATIVE_Z'

                constr=feet_bone.constraints.new('FLOOR')
                constr.target=arm
                constr.subtarget=''
                constr.floor_location='FLOOR_Z'

            #master offset constraint
            if not keep_offset:
                constr=master_bone_temp.constraints.new('COPY_LOCATION')
                constr.target=arm_rm
                constr.subtarget=feet_bone.name
                constr.owner_space='WORLD'


            #apply pose    
            bpy.ops.pose.armature_apply(selected=False)

            for constr in master_bone_temp.constraints:
                master_bone_temp.constraints.remove(constr)

            #master constraints (lock to  floor, limit rotation)

            if limit_location:
                constr=master_bone_temp.constraints.new('FLOOR')
                constr.target=arm
                constr.subtarget=''
                constr.floor_location='FLOOR_NEGATIVE_Z'

                constr=master_bone_temp.constraints.new('FLOOR')
                constr.target=arm
                constr.subtarget=''
                constr.floor_location='FLOOR_Z'

#            constr=master_bone_temp.constraints.new('LIMIT_ROTATION')
#            constr.owner_space='LOCAL_WITH_PARENT'
#            constr.use_limit_x = not up_axis == 'X'
#            constr.use_limit_y = not up_axis == 'Y'
#            constr.use_limit_z = not up_axis == 'Z'
            
            #apply rotation offset to master
            master_bone_temp.rotation_mode='XYZ'
            master_bone_temp.rotation_euler=((rotation_offset*(up_axis=='X')),
                                            (rotation_offset*(up_axis=='Y')),
                                            (rotation_offset*(up_axis=='Z')))



            arm.data.pose_position='POSE'
            #bake action for feet_bone
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=False, visual_keying=True, clear_constraints=True, bake_types={'POSE'})




            #add constraints to required bones
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            arm.select_set(True)
            bpy.context.view_layer.objects.active=arm

            bpy.ops.object.mode_set(mode='POSE')
            # bpy.ops.armature.collection_show_all()
            bpy.ops.pose.select_all(action='DESELECT')
            
            copy_transforms_constraints=[]
            for bone in all_bones:
                bone.bone.select=True
                constr=bone.constraints.new('COPY_TRANSFORMS')
                constr.target=arm_rm
                constr.subtarget=bone.name
                copy_transforms_constraints.append(constr)

                
                
                
            #bake action for armature
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=False, use_current_action=True, bake_types={'POSE'})


            #delete copy transforms constraints and unmute others
            i=0
            for idx,bone in enumerate(all_bones):
                if bone.constraints:
                    bone.constraints.remove(copy_transforms_constraints[idx])
                    if bone.constraints:
                        for constr in bone.constraints:
                            constr.mute=constraints_mute[i]
                            i+=1
                        



        #transfering animation from root to object    
        else:
            constraints_mute=[]
            if master_bone.constraints:
                for constr in master_bone.constraints:
                    constraints_mute.append(constr.mute)
                    constr.mute=True
                        
                        
            bpy.ops.object.mode_set(mode='OBJECT')
            empty_ct=spawn_empty('Rootmotion1')
            
            constr=empty_ct.constraints.new('COPY_TRANSFORMS')
            constr.target=arm
            constr.subtarget=master_bone.name
            
            bpy.context.view_layer.update()
            arm_rm=spawn_armature('RootMotion_ObjectTransforms',(0,0,0))
            arm_rm.parent=empty_ct
            arm_rm.matrix_world=arm.matrix_world
            

            bpy.ops.object.select_all(action='DESELECT')
            arm_rm.select_set(True)
            bpy.context.view_layer.objects.active=arm_rm
            bpy.ops.object.mode_set(mode='EDIT')

            master_bone_temp=arm_rm.data.edit_bones.new(master_bone.name)
            master_bone_temp.tail=(0,0,5)
            master_bone_temp.head=(0,0,0)
            
            
            bpy.ops.object.mode_set(mode='POSE')
            master_bone_temp=arm_rm.pose.bones[0]
            constr=master_bone_temp.constraints.new('COPY_TRANSFORMS')
            constr.target=arm
            constr.subtarget=master_bone.name
            
            
            #apply pose    
            bpy.ops.pose.armature_apply(selected=False)
            master_bone_temp.constraints.remove(constr)
            
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            arm.data.pose_position='POSE'
            empty_ct.select_set(True)
            bpy.context.view_layer.objects.active=empty_ct

            #bake action for empty
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'OBJECT'})
            
            
            
            bpy.ops.object.select_all(action='DESELECT')
            arm.data.pose_position='POSE'
            arm.select_set(True)
            bpy.context.view_layer.objects.active=arm
            

            constr=arm.constraints.new('COPY_TRANSFORMS')
            constr.target=arm_rm
            constr.subtarget=''
            
            constr_master_transforms=master_bone.constraints.new('COPY_TRANSFORMS')
            constr_master_transforms.target=arm_rm
            constr_master_transforms.subtarget=master_bone.name
            
            
            #bake action for armature
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'OBJECT'})
            
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='DESELECT')
            master_bone.bone.select=True
            #bake root bone
            
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=False, use_current_action=True, bake_types={'POSE'})
            
            master_bone.constraints.remove(constr_master_transforms)
                        
            if master_bone.constraints:
                i=0
                for idx, constr in enumerate(master_bone.constraints):
                    constr.mute=constraints_mute[i]
                    i+=1

            #delete empty
            if empty_ct.animation_data:
                bpy.data.actions.remove(empty_ct.animation_data.action)
            bpy.data.objects.remove(empty_ct)
        #delete temp armature
        if arm_rm.animation_data:
            bpy.data.actions.remove(arm_rm.animation_data.action)
        arm_rm_arm=arm_rm.data
        bpy.data.objects.remove(arm_rm)
        bpy.data.armatures.remove(arm_rm_arm)



        # #restore layers on armature
        # for idx,layer in enumerate(arm_layers):
        #     arm.data.layers[idx]=layer
        
        
        return {'FINISHED'}



class RT_OT_unroot(bpy.types.Operator):
    bl_description = "This transfers motion from root to it's children"
    bl_idname = 'rootmotion.unroot'
    bl_label = "UnRoot"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        
        arm=bpy.context.selected_editable_objects[0]
        
        master_bone = getrootbone_selection()
        
        if not master_bone:
            return {'CANCELLED'}
        
        
        arm.data.pose_position='REST'

        bpy.context.scene.frame_set(bpy.context.scene.frame_start)



        arm_rm = rootmotion_create_proxy(arm, master_bone)
        
        constr=master_bone.constraints.new('COPY_TRANSFORMS')
        constr.target=arm_rm
        constr.subtarget=master_bone.name
        constr.name="ROOTMOTION_REMOVEME_qwernoinsgSsda"
        
        rootmotion_remove_proxy(arm)

        
        return {'FINISHED'}


class RT_OT_SetRootBone(bpy.types.Operator):
    bl_description = "Select root bone from Active"
    bl_idname = 'rootmotion.setrootbone'
    bl_label = "FromActive"
    bl_options = set({'REGISTER'}) 
    
    
    def execute(self, context):
        if context.active_pose_bone:
            context.scene.RT_root_object = context.object.name
            context.scene.RT_root_bone = context.active_pose_bone.name
            return {'FINISHED'}
        else:
            return {'CANCELLED'}



class RT_OT_ToObject(bpy.types.Operator):
    bl_description = "This transfers Root animation to Object mode animation"
    bl_idname = 'rootmotion.toobject'
    bl_label = "ToObject"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        
        arm=bpy.context.selected_editable_objects[0]
        
        master_bone = getrootbone_selection()
        
        if not master_bone:
            return {'CANCELLED'}
        
        
        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

        bpy.ops.object.mode_set(mode='OBJECT')
        arm.data.pose_position='REST'
        context.view_layer.update()

        #spawn in bone empty
        empty_bone=spawn_empty('Rootmotion_Bone')
        empty_bone.matrix_world = arm.matrix_world @ master_bone.matrix

        #spawn in object empty
        empty_obj=spawn_empty('Rootmotion_Obj')
        empty_obj.parent = empty_bone
        empty_obj.matrix_parent_inverse = empty_bone.matrix_world.inverted()
        empty_obj.matrix_world = arm.matrix_world


        #copy animation to empty
        constr=empty_bone.constraints.new('COPY_TRANSFORMS')
        constr.target=arm
        constr.subtarget=master_bone.name

        arm.data.pose_position='POSE'

        #bake action for empty
        bpy.ops.object.select_all(action='DESELECT')
        empty_bone.select_set(True)
        bpy.context.view_layer.objects.active=empty_bone

        bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'OBJECT'})


        #copy animation to armature object mode
        constr=arm.constraints.new('COPY_TRANSFORMS')
        constr.target=empty_obj

        bpy.ops.object.select_all(action='DESELECT')
        arm.select_set(True)
        bpy.context.view_layer.objects.active=arm
        
        bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'OBJECT'})

        #clear animation on armature root bone
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')
        master_bone.bone.select = True

        constr=master_bone.constraints.new('COPY_TRANSFORMS')
        constr.target=empty_bone
        bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={'POSE'})

        #cleanup
        if empty_obj.animation_data:
            bpy.data.actions.remove(empty_obj.animation_data.action)
        bpy.data.objects.remove(empty_obj)

        if empty_bone.animation_data:
            bpy.data.actions.remove(empty_bone.animation_data.action)
        bpy.data.objects.remove(empty_bone)

        
        return {'FINISHED'}


class RT_OT_SetRootBone(bpy.types.Operator):
    bl_description = "Select root bone from Active"
    bl_idname = 'rootmotion.setrootbone'
    bl_label = "FromActive"
    bl_options = set({'REGISTER'}) 
    
    
    def execute(self, context):
        if context.active_pose_bone:
            context.scene.RT_root_object = context.object.name
            context.scene.RT_root_bone = context.active_pose_bone.name
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


# class RT_OT_SetKeyRange(bpy.types.Operator):
#     bl_description = "Set range to apply effect to."
#     bl_idname = 'rootmotion.setkeyrange'
#     bl_label = "SetStartEnd"
#     bl_options = set({'REGISTER'}) 
    
    
#     def execute(self, context):
#         if context.active_pose_bone:
#             context.scene.RT_root_object = context.object.name
#             context.scene.RT_root_bone = context.active_pose_bone.name
#             return {'FINISHED'}
#         else:
#             return {'CANCELLED'}

class RT_OT_unslide(bpy.types.Operator):
    bl_description = "Select the bones touching the floor. The operator moves the parent to make the bone stable."
    bl_idname = 'rootmotion.unslide'
    bl_label = "UnSlide"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    Limit_X: bpy.props.BoolProperty(
        name="Limit X",
        description="Don't move along X axis",
        default=False
        )
    Limit_Y: bpy.props.BoolProperty(
        name="Limit Y",
        description="Don't move along Y axis",
        default=False
        )
    Limit_Z: bpy.props.BoolProperty(
        name="Limit Z",
        description="Don't move along Z axis",
        default=False
        )
    
    def execute(self, context):

        # arm = bpy.context.object 
        
        targetbone = getrootbone_selection()
        
        if (not targetbone) or (not bpy.context.selected_pose_bones):
            return {'CANCELLED'}
        
        #check if root is also selected
        for bone in bpy.context.selected_pose_bones:
            if bone == targetbone:
                targetbone.bone.select=False
                break
        
        numbones = len(bpy.context.selected_pose_bones)
        
        #check if step is negative
        direction = 1
        if context.scene.RT_step_size < 0:
            direction = -1
        
        for iter_idx in range(0, context.scene.RT_step_size, direction):

            bpy.context.view_layer.update()

            #targetbone insert keyframe
            targetbone.keyframe_insert(data_path="location")

            #frame 1 matrices
            f1_bone2_gloc = mathutils.Vector((0,0,0))
            for bone in bpy.context.selected_pose_bones:
                arm = bone.id_data
                f1_bone2_gloc += arm.convert_space(pose_bone=bone, matrix=bone.matrix.copy(), from_space='POSE', to_space='WORLD').decompose()[0] / numbones

            bpy.context.scene.frame_set(bpy.context.scene.frame_current+direction)

            #frame 2 matrices
            f2_bone2_gloc = mathutils.Vector((0,0,0))
            for bone in bpy.context.selected_pose_bones:
                arm = bone.id_data
                f2_bone2_gloc += arm.convert_space(pose_bone=bone, matrix=bone.matrix.copy(), from_space='POSE', to_space='WORLD').decompose()[0] / numbones

            #find transform of bone2
            limit = mathutils.Vector((not self.Limit_X,not self.Limit_Y,not self.Limit_Z))
            transform = (f1_bone2_gloc-f2_bone2_gloc)*limit
            
            ##apply location to targetbone
            arm = targetbone.id_data
            mat_pose=arm.convert_space(pose_bone=targetbone, matrix=targetbone.matrix.copy(), from_space='POSE', to_space='WORLD')
            mat_pose=mat_pose + mathutils.Matrix.Translation(transform) 
            mat_pose=arm.convert_space(pose_bone=targetbone, matrix=mat_pose, from_space='WORLD', to_space='LOCAL')
            
            
            targetbone_loc = mat_pose.decompose()[0]


            targetbone.location = targetbone_loc


            #targetbone insert keyframe
            targetbone.keyframe_insert(data_path="location")
        
        
        return {'FINISHED'}

class RT_OT_TempParent(bpy.types.Operator):
    bl_description = "Follow selected bone like a parent."
    bl_idname = 'rootmotion.tempparent'
    bl_label = "TempParent"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    
    def execute(self, context):


        targetbone = getrootbone_selection()
        
        if (not targetbone) or (not context.selected_pose_bones):
            return {'CANCELLED'}
        
        #check if step is negative
        direction = 1
        if context.scene.RT_step_size < 0:
            direction = -1
        
        for iter_idx in range(0, context.scene.RT_step_size, direction):
            context.view_layer.update()

            # #targetbone insert keyframe
            key_insert(targetbone)

            bone = context.active_pose_bone

            arm1 = bone.id_data
            arm2 = targetbone.id_data
            
            matrix_1 = arm1.convert_space(pose_bone=bone, matrix=bone.matrix.copy(), from_space='POSE', to_space='WORLD')
            matrix_2 = arm2.convert_space(pose_bone=targetbone, matrix=targetbone.matrix.copy(), from_space='POSE', to_space='WORLD')

            matrix_1.invert()
            matrix_diff = matrix_1 @ matrix_2


            
            context.scene.frame_set(bpy.context.scene.frame_current+direction)

            matrix_trg = arm1.convert_space(pose_bone=bone, matrix=bone.matrix.copy(), from_space='POSE', to_space='WORLD') @ matrix_diff

            targetbone.matrix = arm2.convert_space(pose_bone=targetbone, matrix=matrix_trg, from_space='WORLD', to_space='POSE')

            # #targetbone insert keyframe
            key_insert(targetbone)
        
        
        return {'FINISHED'}


    
class RT_OT_continue(bpy.types.Operator):
    bl_description = "Continue the root motion to the next frame."
    bl_idname = 'rootmotion.continue'
    bl_label = "Continue"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    Limit_X: bpy.props.BoolProperty(
        name="Limit X",
        description="Don't move along X axis",
        default=False
        )
    Limit_Y: bpy.props.BoolProperty(
        name="Limit Y",
        description="Don't move along Y axis",
        default=False
        )
    Limit_Z: bpy.props.BoolProperty(
        name="Limit Z",
        description="Don't move along Z axis",
        default=False
        )
    
    def execute(self, context):

        arm = bpy.context.object 
        
        targetbone = getrootbone_selection()
        
        if not targetbone:
            return {'CANCELLED'}
        
        
#        #targetbone insert keyframe
#        targetbone.keyframe_insert(data_path="location")

        #check if step is negative
        direction = 1
        if context.scene.RT_step_size < 0:
            direction = -1
        
        for iter_idx in range(0, context.scene.RT_step_size, direction):

            bpy.context.view_layer.update()

            #frame 1 matrices
            loc1 = targetbone.location.copy()

            bpy.context.scene.frame_set(bpy.context.scene.frame_current+((-1)*direction))

            #frame 2 matrices
            loc2 = targetbone.location.copy()
            
            bpy.context.scene.frame_set(bpy.context.scene.frame_current+(2*direction))

            #find transform of bone2
            limit = mathutils.Vector((not self.Limit_X,not self.Limit_Y,not self.Limit_Z))
            transform = (loc1-loc2)*limit
            
            #apply location to targetbone

            targetbone.location += transform

            #targetbone insert keyframe
            targetbone.keyframe_insert(data_path="location")
        
        
        return {'FINISHED'}
    
    
    
class RT_OT_snap(bpy.types.Operator):
    bl_description = "Snap a bone to the floor. Can select multiple bones to use as a reference (Active bone gets snapped, reference bones are used to measure distance to the floor)."
    bl_idname = 'rootmotion.snap'
    bl_label = "SnapToFloor"
    bl_options = set({'REGISTER', 'UNDO'})
    
    
    SourceAxis: bpy.props.EnumProperty(
        items =[("0", "X", ""),
                ("1", "Y", ""),
                ("2", "Z", "")],
        default='2',
        name = "Source Axis",
        description="Axis to use for calculating distance."
        )
        
    TargetAxis: bpy.props.EnumProperty(
        items =[("0", "X", ""),
                ("1", "Y", ""),
                ("2", "Z", "")],
        default='2',
        name = "Target Axis",
        description="Axis to use for applying calculated distance."
        )
        
    Invert: bpy.props.BoolProperty(
        name="Invert Target",
        description="Invert target axis",
        default=False
        )
    
    Floor: bpy.props.FloatProperty(
        name="Floor Z Value",
        description="",
        default=0.0
        )
        
    NumIters: bpy.props.IntProperty(
        name="Number of Iterations",
        description="Increase this number if you are trying to land IK knees.",
        default=1,
        min=1,
        soft_max=20
        )
        
    IterInfluence: bpy.props.FloatProperty(
        name="Influence of an iteration.",
        description="Can increase accuracy when remapping between different axis. (If iterations are set to 1 do not change this value.)",
        default=1.0,
        min=0.0,
        max=1.0
        )
        
    Step: bpy.props.BoolProperty(
        name="Step Forward and Key",
        description="Step one frame forward after running and insert a keyframe.",
        default=False
        )
        
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
        
    def execute(self, context):
        arm = bpy.context.object 
        num_refbones=len(bpy.context.selected_pose_bones)-1
        bone1=bpy.context.active_pose_bone

        #check if step is negative
        direction = 1
        if context.scene.RT_step_size < 0:
            direction = -1
        
        for iter_idx in range(0, context.scene.RT_step_size, direction):
              
            for i in range(0,self.NumIters):
                bpy.context.view_layer.update()
                transform=mathutils.Vector((0,0,0))    
    #            bone1_gloc, temp, temp = arm.convert_space(pose_bone=bone1, matrix=bone1.matrix.copy(), from_space='POSE', to_space='WORLD').decompose()
                
                #handling multiple bones.
                for bone in bpy.context.selected_pose_bones:
                    if (num_refbones!=0) and (bone==bone1):
                        continue
                    else:  
                        bone_gloc, temp, temp = arm.convert_space(pose_bone=bone, matrix=bone.matrix.copy(), from_space='POSE', to_space='WORLD').decompose()
                        
                        transform = ((transform - bone_gloc) + mathutils.Vector(((self.SourceAxis=='0') * self.Floor,(self.SourceAxis=='1') * self.Floor,(self.SourceAxis=='2') * self.Floor))) * self.IterInfluence
                
                #calculate offset
                transform = (transform * mathutils.Vector((self.SourceAxis=='0',self.SourceAxis=='1',self.SourceAxis=='2')))/ (num_refbones + (num_refbones==0))
                
                #move to other axis
                print(transform)
                transform_value= (-transform[int(self.SourceAxis)]*self.Invert) + ((not self.Invert) * transform[int(self.SourceAxis)])
                transform=mathutils.Vector((0,0,0))
                transform[int(self.TargetAxis)]=transform_value

                
                #apply location to bone1       
                mat_pose=arm.convert_space(pose_bone=bone1, matrix=bone1.matrix.copy(), from_space='POSE', to_space='WORLD')
                mat_pose=mat_pose + mathutils.Matrix.Translation(transform)
                mat_pose=arm.convert_space(pose_bone=bone1, matrix=mat_pose, from_space='WORLD', to_space='LOCAL')
                
                
                bone1_loc, temp, temp = mat_pose.decompose()


                bone1.location = bone1_loc

                #bone1 insert keyframe
                if self.Step:
                    bone1.keyframe_insert(data_path="location")
                    
            #step forward.
            if self.Step:
                bpy.context.scene.frame_set(bpy.context.scene.frame_current+direction)
            
        return {'FINISHED'}


class RT_OT_liveroot_enable(bpy.types.Operator):
    bl_description = "Select root bone, then activate."
    bl_idname = 'rootmotion.liveroot_enable'
    bl_label = "LiveRootEnable"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        arm=bpy.context.selected_editable_objects[0]
        
        master_bone = getrootbone_selection()
        
        if not master_bone:
            return {'CANCELLED'}
      
        rootmotion_create_proxy(arm, master_bone)
        
        return {'FINISHED'}

class RT_OT_liveroot_disable(bpy.types.Operator):
    bl_description = "Select armature to run."
    bl_idname = 'rootmotion.liveroot_disable'
    bl_label = "LiveRootDisable"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        arm=bpy.context.selected_editable_objects[0]
      
        rootmotion_remove_proxy(arm)
        
        return {'FINISHED'}
 

class RT_OT_emptyroot_enable(bpy.types.Operator):
    bl_description = "Creates an 'Empty' which you can animate and transfer back to root later."
    bl_idname = 'rootmotion.emptyroot_enable'
    bl_label = "EmptyRootEnable"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        arm=bpy.context.selected_editable_objects[0]
        
        master_bone = getrootbone_selection()
        
        if not master_bone:
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')

        rootempty = spawn_empty(arm.name + '__' + master_bone.name, display_type='ARROWS', size=20)
        constr=rootempty.constraints.new('COPY_TRANSFORMS')
        constr.target=arm
        constr.subtarget=master_bone.name

        bpy.ops.object.select_all(action='DESELECT')
        rootempty.select_set(True)
        bpy.context.view_layer.objects.active=rootempty

        bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=True, visual_keying=True, clear_constraints=True, bake_types={'OBJECT'})

        
        return {'FINISHED'}


class RT_OT_emptyroot_disable(bpy.types.Operator):
    bl_description = "Select master bone to run."
    bl_idname = 'rootmotion.emptyroot_disable'
    bl_label = "EmptyRootDisable"
    bl_options = set({'REGISTER', 'UNDO'}) 

    AdjustChildren: bpy.props.BoolProperty(
        name="Adjust Children",
        description="Adjust the children of root bone.",
        default=True
        )

    def execute(self, context):
        scene=bpy.context.scene
        master_bone = getrootbone_selection()
        if not master_bone:
            return {'CANCELLED'}

        arm = master_bone.id_data

        if self.AdjustChildren:
            rootmotion_create_proxy(arm, master_bone)

        rootempty = bpy.data.objects.get(arm.name + '__' + master_bone.name)

        if not rootempty:
            print('Didnt find the empty. Was it renamed?')
            return {'CANCELLED'}
        bakephrase='ROOTMOTION_REMOVEME_qwernoinsgSsda'
        constr = master_bone.constraints.new('COPY_TRANSFORMS')
        constr.name = bakephrase
        constr.target = rootempty

        if self.AdjustChildren:
            rootmotion_remove_proxy(arm)
        else:
            bakebones(arm, phrase = bakephrase)
        
        return {'FINISHED'} 
    
    
class RT_PT_rootmotion_automatic(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "Automatic"
    bl_idname = "SCENE_PT_RootMotion_Automatic"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "posemode"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene=bpy.context.scene
        layout = self.layout
        box = layout.box()
        col = box.column(align = True)
        
        
        col.prop(scene, "RT_up_axis")
        col.prop(scene, "RT_rotation_offset")
        col.prop(scene, "RT_rotate_root")
        
        row = col.row()
        row.prop(scene, "RT_keep_offset")
        row.prop(scene, "RT_current_positions")
        row.prop(scene, "RT_limit_location")
        col.operator('rootmotion.rootmotion', text="RootMotion")
        
        box = box.box()
        box.label(text="Use LiveRoot instead!")
        box.label(text="This operator may not work.")


            
class RT_PT_rootmotion_tools(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "Tools"
    bl_idname = "SCENE_PT_RootMotion_Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "posemode"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene=bpy.context.scene
        layout = self.layout

        box = layout.box()
        col = box.column(align = True)
        
        
        box2 = box.box()
        box2.label(text="Target Bone")
        box2.operator('rootmotion.setrootbone')
        box2.prop_search(scene, "RT_root_object", bpy.data, "objects") 
        trg_obj = bpy.data.objects.get(scene.RT_root_object)
        if trg_obj:
            if trg_obj.type == 'ARMATURE':
                box2.prop_search(scene, "RT_root_bone", trg_obj.data, "bones", text="Bone")
                
        box3 = box.box()        
        box3.prop(scene, "RT_step_size")
        box3.operator('rootmotion.unslide', text="UnSlide")
        box3.operator('rootmotion.tempparent')
        # box3.operator('rootmotion.rotalign', text="RotAlign")
        box3.operator('rootmotion.continue', text="Continue")
        box3.operator('rootmotion.snap', text="Snap to Floor")
        
        box4 = box.box() 
        box4.operator('rootmotion.unroot', text="UnRoot")
        box4.operator('rootmotion.toobject')

        #liveroot
        box5 = box.box()
        col = box5.column(align = True)
        if not bpy.data.objects.get(bpy.context.selected_editable_objects[0].name + 'ROOTMOTION_REMOVEME_qwernoinsgSsda'):
            col.operator('rootmotion.liveroot_enable', text="LiveRoot: Enable")
        else:
            col.operator('rootmotion.liveroot_disable', text="LiveRoot: Disable")

        #emptyroot
        box5 = box.box()
        col = box5.column(align = True)
        col.operator('rootmotion.emptyroot_enable')
        col.operator('rootmotion.emptyroot_disable')
        col.operator('rootmotion.emptyroot_disable', text="EmptyRootDisable (NoChildren)").AdjustChildren = False



class RT_OT_GR_stabilize(bpy.types.Operator):
    bl_description = "Select keyframes where the motion isn't needed. This will also affect the area after the selection (to keep bone from teleporting)."
    bl_idname = 'rootmotion.gr_stabilize'
    bl_label = "Graph Curve Stabilize"
    bl_options = set({'REGISTER', 'UNDO'}) 

    strength: bpy.props.FloatProperty(
        name="Strength",
        description="Effect strength.",
        default=1.0
        )
    falloff: bpy.props.IntProperty(
        name="Falloff",
        description="Number of keys to fade out the adjustment. (The section after selected keyframes.)",
        default=80
        )
    backwards: bpy.props.BoolProperty(
        name="Backwards",
        description="Go back to start of animation instead of forward to the end.",
        default=False
        )
        
    def execute(self, context):   
        # This only works for Pose-Bones for now due to API limitation and cuz lazy
        obj = context.object
        action = obj.animation_data.action
        for fcurve in action.fcurves:
            if valid_curve(context, obj, fcurve):
                y_val = None
                y_diff = 0
                falloff = self.falloff
                strength = self.strength
                # falloff -= 1
                key_range = range(0, len(fcurve.keyframe_points))
                if self.backwards:
                    key_range = reversed(key_range)

                for i in key_range:
                    p = fcurve.keyframe_points[i]
                    if p.select_control_point:
                        if not y_val:
                            y_val = p.co.y
                        else:
                            y_diff =  (y_val - p.co.y) * strength
                            p.co.y += y_diff 
                            p.handle_right.y += y_diff
                            p.handle_left.y += y_diff
                            
                    elif y_val:
                        p.co.y += y_diff
                        p.handle_right.y += y_diff
                        p.handle_left.y += y_diff             
                        if self.falloff:
                            falloff = max((falloff - 1), 0)
                            if falloff <= 0:
                                break
                            y_diff *= falloff/self.falloff
                fcurve.update()

        return {'FINISHED'}


class RT_OT_GR_invertquats(bpy.types.Operator):
    bl_description = "Invert Quats on selected bones throughout the whole length of the animation."
    bl_idname = 'rootmotion.gr_invertquats'
    bl_label = "Invert Quats Whole Anim"
    bl_options = set({'REGISTER', 'UNDO'}) 

    def execute(self, context):   
        obj = context.object
        action = obj.animation_data.action
        for fcurve in action.fcurves:
            if valid_curve(context, obj, fcurve, internal_valid = True):
                if fcurve.data_path.endswith("rotation_quaternion"):
                    for p in fcurve.keyframe_points:
                        p.co.y *= -1.0

        return {'FINISHED'}


class RT_OT_GR_breakdown(bpy.types.Operator):
    bl_description = "Select bones to breakdown then run this. This operator only exists cuz breakdowner is broken when using NLA currently."
    bl_idname = 'rootmotion.gr_breakdown'
    bl_label = "Breakdowner"
    bl_options = set({'REGISTER', 'UNDO'}) 

    forward: bpy.props.FloatProperty(
        name="Forward",
        description="0 - previous frame. 1 - next frame",
        default=0.5,
        # min=0,
        # max=1.0
        )

    def execute(self, context):   
        # This only works for Pose-Bones for now due to API limitation and cuz lazy
        frame = context.scene.frame_current
        for obj in context.selected_editable_objects:
            if obj.type == 'ARMATURE':
                try:
                    action = obj.animation_data.action
                except: 
                    continue
            for fcurve in action.fcurves:
                if len(fcurve.keyframe_points)>1 and valid_curve(context, obj, fcurve, ignore_hidden = False):
                    #get keys
                    y1 = None
                    y2 = None
                    foundkey = None
                    for i, key in enumerate(fcurve.keyframe_points):
                        if key.co.x == frame:
                            foundkey = key
                        elif key.co.x > frame:
                            if i > 0:
                                y2 = key.co.y
                                y1 = fcurve.keyframe_points[i - 1].co.y
                                break
                    if y1 and y2:
                        result = (y1 * (1 - self.forward)) + (y2 * self.forward)
                        if foundkey:
                            foundkey.co.y = result
                        else:
                            fcurve.keyframe_points.insert(frame, result)
                        fcurve.update()

            return {'FINISHED'}

class RT_OT_GR_remove_curve(bpy.types.Operator):
    bl_description = "Remove curves of a certain type on selected bone."
    bl_idname = 'rootmotion.gr_remove_curve'
    bl_label = "Remove Graph Curve"
    bl_options = set({'REGISTER', 'UNDO'}) 

    rotation: bpy.props.BoolProperty(
        name="Rotation",
        description="Remove Rotation curves.",
        default=False
        )
    location: bpy.props.BoolProperty(
        name="Location",
        description="Remove Location Curves.",
        default=False
        )
    scale: bpy.props.BoolProperty(
        name="Scale",
        description="Remove Scale curves.",
        default=False
        )

        
    def execute(self, context):   
        # This only works for Pose-Bones for now due to API limitation and cuz lazy
        obj = context.object
        action = obj.animation_data.action
        for fcurve in action.fcurves:
            if valid_curve(context, obj, fcurve):
                if self.rotation:
                    if fcurve.data_path.endswith("rotation") or fcurve.data_path.endswith("rotation_quaternion"):
                        action.fcurves.remove(fcurve)
                        continue
                if self.location:
                    if fcurve.data_path.endswith("location"):
                        action.fcurves.remove(fcurve)
                        continue
                if self.scale:
                    if fcurve.data_path.endswith("scale"):
                        action.fcurves.remove(fcurve)
                        continue

        return {'FINISHED'}


class RT_OT_GR_hide_channels(bpy.types.Operator):
    bl_description = "Hide curves of a certain type on selected bone."
    bl_idname = 'rootmotion.gr_hide_channel'
    bl_label = "Hide Graph Curve"
    bl_options = set({'REGISTER', 'UNDO'}) 

    rotation: bpy.props.BoolProperty(
        name="Rotation",
        description="Rotation curves.",
        default=False
        )
    location: bpy.props.BoolProperty(
        name="Location",
        description="Location Curves.",
        default=False
        )
    scale: bpy.props.BoolProperty(
        name="Scale",
        description="Scale curves.",
        default=False
        )
    selectedonly: bpy.props.BoolProperty(
        name="Selected only",
        description="Selected curves.",
        default=False
        )
        
    def execute(self, context):   
        # This only works for Pose-Bones for now due to API limitation and cuz lazy
        obj = context.object
        action = obj.animation_data.action
        for fcurve in action.fcurves:
            if valid_curve(context, obj, fcurve, ignore_hidden=False):
                if self.selectedonly:
                    if fcurve.select:
                        fcurve.hide = False
                    else:
                        fcurve.hide = True
                else: # if not selected only mode
                    fcurve.hide = False
                    if self.rotation:
                        if fcurve.data_path.endswith("rotation") or fcurve.data_path.endswith("rotation_quaternion"):
                            fcurve.hide = True
                            continue
                    if self.location:
                        if fcurve.data_path.endswith("location"):
                            fcurve.hide = True
                            continue
                    if self.scale:
                        if fcurve.data_path.endswith("scale"):
                            fcurve.hide = True
                            continue

        return {'FINISHED'}

class RT_PT_GraphTools(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "RootMotion"
    bl_idname = "GRAPHEDITOR_PT_RootMotion"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_context = "posemode"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene=bpy.context.scene
        layout = self.layout

        col = layout.column(align = True)

        col.operator('rootmotion.gr_stabilize', text="Stabilize Forward").backwards = False
        col.operator('rootmotion.gr_stabilize', text="Stabilize Backward").backwards = True
        col.operator('graph.smooth', text="Smooth")
        col.operator('graph.clean', text="Clean").channels=True
        col.operator('rootmotion.gr_breakdown')

class RT_PT_GraphTools_HideCurve(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "Isolate Curves"
    bl_idname = "GRAPHEDITOR_PT_RootMotion_IsolateCurves"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_context = "posemode"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene=bpy.context.scene
        layout = self.layout

        
        box = layout.box()
        col = box.column()

        op = col.operator('rootmotion.gr_hide_channel', text="Un-hide all")
        op.rotation = False
        op.location = False
        op.scale = False
        op.selectedonly = False

        
        col = layout.column(align = True)
        op = col.operator('rootmotion.gr_hide_channel', text="Selected")
        op.selectedonly = True
        op = col.operator('rootmotion.gr_hide_channel', text="Rotation")
        op.rotation = False
        op.location = True
        op.scale = True
        op.selectedonly = False
        op = col.operator('rootmotion.gr_hide_channel', text="Location")
        op.rotation = True
        op.location = False
        op.scale = True
        op.selectedonly = False
        op = col.operator('rootmotion.gr_hide_channel', text="Scale")
        op.rotation = True
        op.location = True
        op.scale = False
        op.selectedonly = False

class RT_PT_GraphTools_RemoveCurve(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "Remove Curves of Type"
    bl_idname = "GRAPHEDITOR_PT_RootMotion_RemoveCurves"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_context = "posemode"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene=bpy.context.scene
        layout = self.layout

        col = layout.column(align = True)
        op = col.operator('rootmotion.gr_remove_curve', text="Rotation")
        op.rotation = True
        op.location = False
        op.scale = False
        op = col.operator('rootmotion.gr_remove_curve', text="Location")
        op.rotation = False
        op.location = True
        op.scale = False
        op = col.operator('rootmotion.gr_remove_curve', text="Scale")
        op.rotation = False
        op.location = False
        op.scale = True


class RT_PT_rootmotion_cursorsnap(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "Tools"
    bl_idname = "SCENE_PT_RootMotion_CursorSnap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "posemode"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene=bpy.context.scene
        layout = self.layout

        box = layout.box()
        col = box.column(align = True)
        
        if CursorSnap_Targets:
            col.operator('rootmotion.cs_disable')
        else:
            col.operator('rootmotion.cs_enable')

        col.prop(scene, "RT_CS_whileplaying")

CursorSnap_Targets = []

class RT_OT_CursorSnap_Enable(bpy.types.Operator):
    bl_description = "Select bones to snap cursor to on every frame."
    bl_idname = 'rootmotion.cs_enable'
    bl_label = "CursorSnap Enable"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        for b in bpy.context.selected_pose_bones:
            CursorSnap_Targets.append(b)
        if CursorSnap_Targets:
            bpy.app.handlers.frame_change_post.append(CursorSnap_handler)
            CursorSnap_handler(bpy.context.scene)
        return {'FINISHED'}


class RT_OT_CursorSnap_Disable(bpy.types.Operator):
    bl_description = "Disable CursorSnap."
    bl_idname = 'rootmotion.cs_disable'
    bl_label = "CursorSnap Disable"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        CursorSnap_Targets.clear()
        bpy.app.handlers.frame_change_post.remove(CursorSnap_handler)
        return {'FINISHED'}


def CursorSnap_handler(scene):
    if CursorSnap_Targets:
        if (not bpy.context.screen.is_animation_playing) or scene.RT_CS_whileplaying:
            FinalVector = mathutils.Vector((0,0,0))
            for b in CursorSnap_Targets:
                arm = b.id_data
                # print(arm)
                FinalVector += arm.convert_space(pose_bone=b, matrix=b.matrix.copy(), from_space='POSE', to_space='WORLD').decompose()[0]

            scene.cursor.location = FinalVector / len(CursorSnap_Targets)






classes = (
    RT_OT_rootmotion,
    RT_OT_unroot,
    RT_OT_SetRootBone,
    RT_OT_unslide,
    RT_OT_TempParent,
    RT_OT_continue,
    RT_OT_snap,
    RT_OT_liveroot_enable,
    RT_OT_liveroot_disable,
    RT_OT_emptyroot_enable,
    RT_OT_emptyroot_disable,
    RT_OT_ToObject,
    RT_PT_rootmotion_automatic,
    RT_PT_rootmotion_tools,
    RT_OT_GR_stabilize,
    RT_OT_GR_invertquats,
    RT_OT_GR_breakdown,
    RT_OT_GR_remove_curve,
    RT_PT_GraphTools,
    RT_PT_GraphTools_HideCurve,
    RT_PT_GraphTools_RemoveCurve,
    RT_OT_GR_hide_channels,
    RT_OT_CursorSnap_Enable,
    RT_OT_CursorSnap_Disable,
    RT_PT_rootmotion_cursorsnap
    )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # RT Automatic
    bpy.types.Scene.RT_up_axis = bpy.props.EnumProperty(
        items =[("X", "X", "", 1),
        ("Y", "Y", "", 2),
        ("Z", "Z", "", 3)],
        default='Y',
        name = "Up Axis",
        description="Root bone's up axis"
        )
    bpy.types.Scene.RT_keep_offset = bpy.props.BoolProperty(
        name="Keep Offset",
        description="Keep offset between root bone and created root position. (from rest pose)",
        default=True
        )
    bpy.types.Scene.RT_current_positions = bpy.props.BoolProperty(
        name="Current Positions",
        description="Offset positions from the current frame.",
        default=False
        )
    bpy.types.Scene.RT_limit_location = bpy.props.BoolProperty(
        name="Snap to Floor",
        description="Snap root to floor. Uses armature object's location as floor",
        default=True
        )
    bpy.types.Scene.RT_rotate_root = bpy.props.BoolProperty(
        name="Rotate Root",
        description="Rotate root bone to face forward. Disable for only root location.",
        default=True
        )
    bpy.types.Scene.RT_rotation_offset = bpy.props.FloatProperty(
        name="Rotation Offset",
        description="Rotate root bone along the up axis",
        default=0.0
        )

    # RT Tools
    bpy.types.Scene.RT_root_object = bpy.props.StringProperty(
        name="Object",
        description="Target root object",
        default=""
        )
    bpy.types.Scene.RT_root_bone = bpy.props.StringProperty(
        name="RootBone Bone",
        description="Target root bone",
        default=""
        )
    bpy.types.Scene.RT_step_size = bpy.props.IntProperty(
        name="StepSize",
        description="How many keyframes to step at a time.",
        default=1,
        # min=1
        )

    #CursorSnap
    bpy.types.Scene.RT_CS_whileplaying = bpy.props.BoolProperty(
        name="Update on playback",
        description="Update cursor position while animation is playing. Keep this disabled for better playback performance! (Setting cursor position is slow for some reason :(( )",
        default=False
        )

    # bpy.app.handlers.frame_change_post.append(CursorSnap_handler)
    
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    # bpy.app.handlers.frame_change_post.remove(CursorSnap_handler)

