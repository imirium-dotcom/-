
import bpy

# Очистка сцены
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Создание куба
bpy.ops.mesh.primitive_cube_add(
    location=(0, 0, 0)
)

cube = bpy.context.active_object
cube.name = "AI_Core_Test_Cube"

# Сохранение результата
bpy.ops.wm.save_as_mainfile(
    filepath=r"C:\AI_Core\generated_3d_test.blend"
)

print("AI Core Blender test completed")
print("Saved:", r"C:\AI_Core\generated_3d_test.blend")
