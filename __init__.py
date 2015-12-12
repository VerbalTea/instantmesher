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
            name="folder to store temp objs",
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
    bl_label = "instant meshes export"
    bl_options = {'REGISTER', 'UNDO'}

    operation = bpy.props.StringProperty()

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

        if self.operation == "shrinkwrap":
            self.shrinkwrap()
        elif self.operation == "clearsharp":
            self.clearsharp()
        elif self.operation == "triangulate":
            self.triangulate()

        self.setUpPaths(context)

        active_object = bpy.context.active_object
        name = active_object.name
        objname = name + ".obj" # The temp object is called the same as the active object you have selected in Blender.
        bpy.ops.view3d.snap_cursor_to_selected()

        try:
            bpy.ops.export_scene.obj(filepath=objname, use_selection=True, use_materials=False) # Exports the *.obj to your home directory (on Linux, at least) or the directory you specified above under the 'targetDir' variable
        except Exception as e:
            printErrorMessage("Could not create OBJ", e)
            return {'CANCELLED'}

        if self.operation == "cmd":
            self.cmd(objname, context)

        elif self.operation == "regular":
            self.regular(objname, context)

        bpy.ops.object.ogtc()

        return {'FINISHED'}



    def setUpPaths(self, context):
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



    def cmd(self, objname, context):
        wm = context.window_manager

        smoothingIts = str(wm.instantMesherSmoothingInt)
        allQuads = bool(wm.instantMesherQuadsBool)
        vertsAmount = wm.instantMesherVertexCountInt


        try:
            if allQuads:
                vertsAmount = str(int(vertsAmount/4))
                subprocess.call([self.instantmeshesPath,  "-o", objname, "-S", str(smoothingIts), "-v", vertsAmount, objname]) # Calls Instant Meshes and appends the temporary *.obj to it
            else:
                subprocess.call([self.instantmeshesPath,  "-o", objname, "-S", str(smoothingIts), "-v", str(vertsAmount), "-D", objname]) # Calls Instant Meshes and appends the temporary *.obj to it

        except Exception as e:
            printErrorMessage("Could not execute Instant Meshes", e)

        try:
            bpy.ops.import_scene.obj(filepath=objname) # Imports remeshed obj into Blender
        except Exception as e:
            printErrorMessage("Could not import OBJ", e)
            return {'CANCELLED'}

        try:
            os.remove(objname) # Removes temporary obj
        except Exception as e:
            printErrorMessage("Could not remove OBJ", e)


    def regular(self, objname, context):
        creationTime = os.path.getmtime(objname) # Get creation time of obj for later comparison

        try:
            subprocess.call([self.instantmeshesPath, objname]) # Calls Instant Meshes and appends the temporary *.obj to it

        except Exception as e:
            printErrorMessage("Could not execute 'Instant Meshes'", e)

        if(os.path.getmtime(objname) != creationTime):
            try:
                bpy.ops.import_scene.obj(filepath=objname) # Imports remeshed obj into Blender
            except Exception as e:
                printErrorMessage("Could not import OBJ", e)
                return {'CANCELLED'}
        else:
            print("Object has not changed. Skipping import...")
            pass

        try:
            os.remove(objname) # Removes temporary obj
        except Exception as e:
            printErrorMessage("Could not remove OBJ", e)



    def shrinkwrap(self):
        try:
            remeshed_object = ""
            target_object = bpy.context.active_object

            for obj in bpy.context.selected_objects:
                if obj is not target_object:
                    remeshed_object = obj
                    break

            bpy.context.scene.objects.active = remeshed_object

            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
            bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
            bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects[target_object.name]
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Shrinkwrap")
        except Exception as e:
            printErrorMessage("Shrinkwrap-operation failed.", e)
            return {'CANCELLED'}


        return {'FINISHED'}



    def clearsharp(self):
        try:
            bpy.ops.object.editmode_toggle()

            bpy.ops.mesh.select_all(action="SELECT")

            bpy.ops.mesh.mark_sharp(clear=True)
            bpy.ops.object.editmode_toggle()
        except Exception as e:
            printErrorMessage("Clearsharp-operation failed.", e)
            return {'CANCELLED'}

        return {'FINISHED'}


    def triangulate(self):
        try:
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            bpy.ops.object.editmode_toggle()

        except Exception as e:
            printErrorMessage("Triangulation failed", e)
            return {'CANCELLED'}




class InstantMesherPanel(bpy.types.Panel):
    """ """
    bl_label = "Instant Mesher"
    bl_idname = "OBJECT_PT_instantmesher"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Retopology"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        wm = context.window_manager

        row = layout.row()
        layout.operator("ops.instantmesher", text="Send to Instant Meshes", icon="LINK_AREA").operation = "regular"

        layout.separator()
        layout.separator()

        row = layout.row()
        row.label(text="Native Tools")

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
        layout.operator("ops.instantmesher", text="Remesh", icon="PLAY").operation = "cmd"

        layout.separator()
        layout.separator()

        row = layout.row()
        row.label(text="Utilities (experimental)")
        row = layout.row()
        layout.operator("ops.instantmesher", text="Clear Sharp Edges", icon="WORLD").operation = "clearsharp"

        row = layout.row()
        layout.operator("ops.instantmesher", text="Shrinkwrap to target(active) object", icon="MOD_SHRINKWRAP").operation = "shrinkwrap"
        row = layout.row()
        layout.operator("ops.instantmesher", text="Triangulate Mesh", icon="MESH_DATA").operation = "triangulate"


# Utility functions
def printErrorMessage(msg, e):
    print("-- Error ---- !")
    print(msg, "\n", str(e))
    print("------\n\n")



def register():
    bpy.utils.register_class(InstantMesher)
    bpy.utils.register_class(InstantMesherPanel)
    bpy.utils.register_class(InstantMesherPreferences)

    bpy.types.WindowManager.instantMesherSmoothingInt = IntProperty(min = 0, max = 10, default = 0)
    bpy.types.WindowManager.instantMesherVertexCountInt = IntProperty(min = 10, max = 100000000, default = 100)
    bpy.types.WindowManager.instantMesherQuadsBool = BoolProperty(default = False)


def unregister():
    bpy.utils.unregister_class(InstantMesher)
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
