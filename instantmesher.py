import bpy, subprocess, os
from sys import platform as _platform

class InstantMesher(bpy.types.Operator):
    bl_idname = "ops.instantmesher"
    bl_label = "instant-meshes export"
    bl_options = {'REGISTER'}

    # custom variables
    instantmeshesPath = "" # Enter the path to instantmeshes here. For me the full path is '/opt/instant-meshes/Instant 20Meshes' but I made a symbolic link to /usr/local/bin/instantmeshes, so it's just 'instantmeshes'.
    targetDir = "" # If nothing is specified, the 'home' directory is used

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        # Make OS specific changes
        if _platform == "linux" or _platform == "linux2":
            # linux initialization
            pass

        elif _platform == "darwin":
            # OS X initialization
            os.chdir(os.environ['USERPROFILE'])

        elif _platform == "win32":
            # Windows initialization
            os.chdir(os.environ['USERPROFILE'])


        if self.instantmeshesPath == "":
            print("Path to 'instantmeshes' not specified. Terminating...")
            return {'CANCELLED'}

        if self.targetDir != "" and os.path.isdir(self.targetDir):
            os.chdir(self.targetDir)

        name = bpy.context.selected_objects[0].name
        objname = name + ".obj" # The temp object is called the same as the active object you have selected in Blender.
        mtlname = name + ".mtl"
        bpy.ops.export_scene.obj(filepath=objname, use_selection=True) # Exports the *.obj to your home directory (on Linux, at least) or the directory you specified above under the 'targetDir' variable
        subprocess.call([self.instantmeshesPath, objname]) # Calls instantmeshes and appends the temporary *.obj to it

        # IMPORTANT: After remeshing the object in instantmeshes you HAVE TO SAVE IT OVER THE TEMPORARY OBJECT you just created, otherwise it will import the same object you exported, with no changes made

        bpy.ops.import_scene.obj(filepath=objname) # Imports remeshed obj into Blender
        os.remove(objname) # Removes temporary obj
        os.remove(mtlname) # Removes temporary mtl


        return {'FINISHED'}


def register():
    bpy.utils.register_class(InstantMesher)


def unregister():
    bpy.utils.unregister_class(InstantMesher)


if __name__ == "__main__":
    register()
