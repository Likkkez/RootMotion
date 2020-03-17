bl_info = {
    "name": "Rootmotion",
    "author": "Likkez",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "description": "Transfer movement from feet to root. Transfer movement from root bone to object root.",
    "warning": "Be wary of Likkez's good looks! They are dangerously appealing!",
    "wiki_url": "",
    "category": "Animation",
}
import bpy


def spawn_empty(name):
    empty = bpy.data.objects.new( name, None )
    bpy.context.scene.collection.objects.link( empty )
    empty.empty_display_size = .2
    empty.empty_display_type = 'PLAIN_AXES'   
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
        
        
        

class RT_OT_rootmotion(bpy.types.Operator):
    bl_description = "Select all feet bones and run. Alternatively, select the Root bone"
    bl_idname = 'rootmotion.rootmotion'
    bl_label = "RootMotion"
    bl_options = set({'REGISTER', 'UNDO'}) 
    
    def execute(self, context):
        scene=bpy.context.scene
        
        up_axis=scene.RT_up_axis
        keep_offset=scene.RT_keep_offset
        rotation_offset=scene.RT_rotation_offset
        limit_location=scene.RT_limit_location
        imprefect_hierarchy=True

        arm=bpy.context.selected_editable_objects[0]

        foot_list=bpy.context.selected_pose_bones.copy()
        master_bone=get_master(foot_list[0])

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

        bpy.context.scene.frame_set(bpy.context.scene.frame_start)

        #save armature layers
        arm_layers=[]
        for layer in arm.data.layers:
            arm_layers.append(layer)
            
            
            
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


            for idx, foot in enumerate(foot_list):
                for constr_type in ['COPY_ROTATION', 'COPY_LOCATION']:
                    constr=feet_bone.constraints.new(constr_type)
                    constr.target=arm
                    constr.subtarget=foot.name
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

            constr=master_bone_temp.constraints.new('LIMIT_ROTATION')
            constr.owner_space='LOCAL_WITH_PARENT'
            if up_axis=='Y':
                constr.use_limit_x=True
                constr.use_limit_z=True
            elif up_axis=='X':
                constr.use_limit_y=True
                constr.use_limit_z=True
            elif up_axis=='Z':
                constr.use_limit_y=True
                constr.use_limit_x=True

            #apply rotation offset to master
            master_bone_temp.rotation_mode='XYZ'
            if up_axis=='X':
                rotation_offset_vector=(rotation_offset,0,0)
            elif up_axis=='Y':
                rotation_offset_vector=(0,rotation_offset,0)
            elif up_axis=='Z':
                rotation_offset_vector=(0,0,rotation_offset)
            master_bone_temp.rotation_euler=rotation_offset_vector



            arm.data.pose_position='POSE'
            #bake action for feet_bone
            bpy.ops.nla.bake(frame_start=bpy.context.scene.frame_start, frame_end=bpy.context.scene.frame_end, only_selected=False, visual_keying=True, clear_constraints=True, bake_types={'POSE'})




            #add constraints to required bones
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            arm.select_set(True)
            bpy.context.view_layer.objects.active=arm

            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.armature.layers_show_all()
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
            for idx,bone in enumerate(all_bones):
                if bone.constraints:
                    bone.constraints.remove(copy_transforms_constraints[idx])
                    if bone.constraints:
                        for constr in bone.constraints:
                            constr.mute=constraints_mute[idx]
                        
                        



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
                for idx, constr in enumerate(master_bone.constraints):
                    constr.mute=constraints_mute[idx]

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



        #restore layers on armature
        for idx,layer in enumerate(arm_layers):
            arm.data.layers[idx]=layer
        
        
        return {'FINISHED'}

    
class RT_PT_rootmotion(bpy.types.Panel):
    bl_category = "RootMotion"
    bl_label = "RootMotion"
    bl_idname = "SCENE_PT_RootMotion"
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
        
        
        col.prop(scene, "RT_up_axis")
        col.prop(scene, "RT_rotation_offset")
        
        row = col.row()
        row.prop(scene, "RT_keep_offset")
        row.prop(scene, "RT_limit_location")
        layout.operator('rootmotion.rootmotion', text="RootMotion")
        

classes = (
    RT_OT_rootmotion,
    RT_PT_rootmotion
    )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
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
    bpy.types.Scene.RT_limit_location = bpy.props.BoolProperty(
        name="Snap to Floor",
        description="Snap root to floor. Uses armature object's location as floor",
        default=True
        )
    bpy.types.Scene.RT_rotation_offset = bpy.props.FloatProperty(
        name="Rotation Offset",
        description="Rotate root bone along the up axis",
        default=0.0
        )
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

