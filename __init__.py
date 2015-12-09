import subprocess, os, bpy
from bpy.types import Operator, AddonPreferences, Panel
from bpy.props import StringProperty, IntProperty, BoolProperty
from sys import platform as _platform


bl_info = {
    'name': 'InstantMesher',
    'description': 'automates the exporting and importing process to "Instant Meshes"',
    'author': 'tealeaf',
    'version': (1,0),
    'blender': (2, 75, 0),
    'warning': "",
    'location': 'View3D',
    'category': '3D View'
}


class InstantMesherPreferences(AddonPreferences):
    bl_idname = __name__
    instant_path = StringProperty(
            name="Instant Meshes-executable path",
            subtype='FILE_PATH',
            )

    temp_folder = StringProperty(
            name="temp folder to store objs",
            subtype='DIR_PATH',
            )

    def draw(self, context):
            layout = self.layout

            split = layout.split(percentage=1)

            col = split.column()
            sub = col.column(align=True)
            sub.prop(self, "instant_path")
            sub.separator()
            sub.prop(self, "temp_folder")



class InstantMesher(bpy.types.Operator):
    bl_idname = "ops.instantmesher"
    bl_label = "instant-meshes export"
    bl_options = {'REGISTER'}

    # custom variables
    # Defined in the Blender addon preferences
    instantmeshesPath = "" # Path to the "instant Meshes"-executable
    targetDir = "" # If nothing is specified, the 'home' directory is used

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if len(bpy.context.selected_objects) < 1:
            return {'CANCELLED'}

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        self.instantmeshesPath = str(addon_prefs.instant_path) # Set path for instant meshes
        self.targetDir = str(addon_prefs.temp_folder) # Set path for temp dir to store objs in

        info = ("Path: %s" % (addon_prefs.instant_path))

        if self.instantmeshesPath == "":
            print("Path to 'instant Meshes' not specified. Terminating...")
            return {'CANCELLED'}

        if self.targetDir != "" and os.path.isdir(self.targetDir):
            os.chdir(self.targetDir)
        else:
            os.chdir(os.path.expanduser("~"))
            # if _platform == "linux" or _platform == "linux2":
            #     os.chdir(os.path.expanduser("~"))
            # elif _platform == "darwin":
            #     os.chdir(os.path.expanduser("~"))
            # elif _platform == "win32":
            #     os.chdir(os.path.expanduser("~"))

        name = bpy.context.active_object.name
        objname = name + ".obj" # The temp object is called the same as the active object you have selected in Blender.

        try:
            bpy.ops.export_scene.obj(filepath=objname, use_selection=True, use_materials=False) # Exports the *.obj to your home directory (on Linux, at least) or the directory you specified above under the 'targetDir' variable
        except:
            print("Could not create OBJ")
            return {'CANCELLED'}

        creationTime = os.path.getmtime(objname) # Get creation time of obj for later comparison

        subprocess.call([self.instantmeshesPath, objname]) # Calls Instant Meshes and appends the temporary *.obj to it

        if(os.path.getmtime(objname) != creationTime):
            try:
                bpy.ops.import_scene.obj(filepath=objname) # Imports remeshed obj into Blender
            except:
                print("Could not import OBJ")
                return {'CANCELLED'}
        else:
            print("Object has not changed. Skipping import...")
            pass

        try:
            os.remove(objname) # Removes temporary obj
        except:
            print("Could not remove OBJ")

        return {'FINISHED'}


class InstantMesherCMD(bpy.types.Operator):
    bl_idname = "ops.instantmeshercmd"
    bl_label = "instant-meshes cmd"
    bl_options = {'REGISTER'}

    # custom variables
    # Defined in the Blender addon preferences
    instantmeshesPath = "" # Path to the "instant Meshes"-executable
    targetDir = "" # If nothing is specified, the 'home' directory is used

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if len(bpy.context.selected_objects) < 1:
            return {'CANCELLED'}

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        self.instantmeshesPath = str(addon_prefs.instant_path) # Set path for instant meshes
        self.targetDir = str(addon_prefs.temp_folder) # Set path for temp dir to store objs in

        info = ("Path: %s" % (addon_prefs.instant_path))

        if self.instantmeshesPath == "":
            print("Path to 'instant Meshes' not specified. Terminating...")
            return {'CANCELLED'}

        if self.targetDir != "" and os.path.isdir(self.targetDir):
            os.chdir(self.targetDir)
        else:
            if _platform == "linux" or _platform == "linux2":
                os.chdir(os.path.expanduser("~"))
            elif _platform == "darwin":
                if self.targetDir == "":
                    os.chdir(os.path.expanduser("~"))
            elif _platform == "win32":
                if self.targetDir == "":
                    os.chdir(os.path.expanduser("~"))

        name = bpy.context.active_object.name
        objname = name + ".obj" # The temp object is called the same as the active object you have selected in Blender.

        try:
            bpy.ops.export_scene.obj(filepath=objname, use_selection=True, use_materials=False) # Exports the *.obj to your home directory (on Linux, at least) or the directory you specified above under the 'targetDir' variable
        except:
            print("Could not create OBJ")
            return {'CANCELLED'}

        creationTime = os.path.getmtime(objname) # Get creation time of obj for later comparison

        wm = context.window_manager

        smoothingIts = str(wm.instantMesherSmoothingInt)
        allQuads = wm.instantMesherQuadsBool
        vertsAmount = str(wm.instantMesherVertexCountInt)

        # placeholder values
        # smoothingIts = 2
        # allQuads = True
        # vertsAmount = 5000

        try:
            if not allQuads:
                subprocess.call([self.instantmeshesPath,  "-o", objname, "-S", str(smoothingIts), "-v", vertsAmount, "-D", objname]) # Calls Instant Meshes and appends the temporary *.obj to it
            else:
                subprocess.call([self.instantmeshesPath,  "-o", objname, "-S", str(smoothingIts), "-v", vertsAmount, objname]) # Calls Instant Meshes and appends the temporary *.obj to it

        except:
            print("Could not execute Instant Meshes")


        if(os.path.getmtime(objname) != creationTime):
            try:
                bpy.ops.import_scene.obj(filepath=objname) # Imports remeshed obj into Blender
            except:
                print("Could not import OBJ")
                return {'CANCELLED'}
        else:
            print("Object has not changed. Skipping import...")
            pass

        try:
            os.remove(objname) # Removes temporary obj
        except:
            print("Could not remove OBJ")

        return {'FINISHED'}



class InstantMesherPanel(bpy.types.Panel):
    """ """
    bl_label = "Instant Mesher"
    bl_idname = "OBJECT_PT_instantmesher"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Instant Mesher"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        wm = context.window_manager

        row = layout.row()
        layout.operator("ops.instantmesher", text="Launch Instant Meshes")

        layout.separator()
        layout.separator()
        layout.separator()

        row = layout.row()

        row = layout.row()
        row.alignment = "EXPAND"
        row.prop(wm, 'instantMesherVertexCountInt', text="vertices")

        row = layout.row()
        row.alignment = "EXPAND"
        row.prop(wm, 'instantMesherSmoothingInt', text="smoothing")

        row = layout.row()
        row.alignment = "EXPAND"
        row.prop(wm, 'instantMesherQuadsBool', text="All Quads")

        row = layout.row()
        layout.operator("ops.instantmeshercmd", text="Remesh")



def register():
    bpy.utils.register_class(InstantMesher)
    bpy.utils.register_class(InstantMesherCMD)
    bpy.utils.register_class(InstantMesherPanel)
    bpy.utils.register_class(InstantMesherPreferences)

    bpy.types.WindowManager.instantMesherSmoothingInt = IntProperty(min = 0, max = 10, default = 0)
    bpy.types.WindowManager.instantMesherVertexCountInt = IntProperty(min = 10, max = 100000000, default = 100)
    bpy.types.WindowManager.instantMesherQuadsBool = BoolProperty(default = False)


def unregister():
    bpy.utils.unregister_class(InstantMesher)
    bpy.utils.unregister_class(InstantMesherCMD)
    bpy.utils.unregister_class(InstantMesherPanel)
    bpy.utils.unregister_class(InstantMesherPreferences)

    try:
        del bpy.types.WindowManager.instantMesherSubdivInt
        del bpy.types.WindowManager.instantMesherVertexCountInt
        del bpy.types.WindowManager.instantMesherQuadsBool

    except:
        pass


if __name__ == "__main__":
    register()
