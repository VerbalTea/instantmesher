import subprocess, os, bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty
from sys import platform as _platform


bl_info = {
    'name': 'InstantMesher',
    'description': 'automates the exportingn and import process to "instant-meshes"',
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
            name="instant-meshes-executable path",
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
            sub.prop(self, "temp_folder")

            sub.separator()


class InstantMesher(bpy.types.Operator):
    bl_idname = "ops.instantmesher"
    bl_label = "instant-meshes export"
    bl_options = {'REGISTER'}

    # custom variables
    # Defined in the Blender addon preferences
    instantmeshesPath = "" # Path to the "instant Meshes"-executable
    targetDir = "" # If nothing is specified, the 'home' directory is used
    print(targetDir)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences

        self.instantmeshesPath = str(addon_prefs.instant_path) # Set path for instant meshes
        self.targetDir = str(addon_prefs.temp_folder) # Set path for temp dir to store objs in

        info = ("Path: %s" % (addon_prefs.instant_path))

        if self.instantmeshesPath == "":
            print("Path to 'instantmeshes' not specified. Terminating...")
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

        name = bpy.context.selected_objects[0].name
        objname = name + ".obj" # The temp object is called the same as the active object you have selected in Blender.
        mtlname = name + ".mtl"
        bpy.ops.export_scene.obj(filepath=objname, use_selection=True, use_materials=False) # Exports the *.obj to your home directory (on Linux, at least) or the directory you specified above under the 'targetDir' variable
        subprocess.call([self.instantmeshesPath, objname]) # Calls Instant Meshes and appends the temporary *.obj to it

        bpy.ops.import_scene.obj(filepath=objname) # Imports remeshed obj into Blender
        os.remove(objname) # Removes temporary obj

        return {'FINISHED'}


def register():
    bpy.utils.register_class(InstantMesher)
    bpy.utils.register_class(InstantMesherPreferences)


def unregister():
    bpy.utils.unregister_class(InstantMesher)
    bpy.utils.unregister_class(InstantMesherPreferences)


if __name__ == "__main__":
    register()
