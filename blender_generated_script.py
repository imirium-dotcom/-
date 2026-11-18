
import bpy

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.mesh.primitive_cube_add(
    size=2,
    location=(0, 0, 0)
)

cube = bpy.context.object
cube.name = "AI_Core_Test_Cube"

bpy.ops.wm.save_as_mainfile(
    filepath=r"C:\AI_Core\generated_3d_test.blend"
)

print("AI_CORE_BLENDER_SUCCESS")
