"""
PyFluent 自动化脚本：增强容错版多工况计算
功能：遍历速度列表，若单个工况报错（计算崩溃等），自动跳过并执行下一个
"""

import ansys.fluent.core as pyfluent
import os

# ======================== 配置参数 ========================
MESH_FILE = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\project2dimandball_files\dp0\FFF\Fluent\FFF-Setup-Output.cas.h5"
OUTPUT_DIR = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\data"
VELOCITY_LIST = [0.2, 0.3, 0.5] 
ITERATIONS = 100

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================== 1. 启动 Fluent ========================
print("=" * 60)
print("启动 Fluent (2D, Double Precision)...")
solver = pyfluent.launch_fluent(
    precision="double",
    processor_count=4,
    mode="solver",
    show_gui=False,
    dimension=2
)

# ======================== 2. 读取网格与基础设置 ========================
print("\n读取网格文件...")
solver.file.read_case(file_name=MESH_FILE)
# 网格缩放mm→m
solver.mesh.scale(x_scale=0.001, y_scale=0.001)

print("\n设置物理模型与材料...")
solver.setup.models.viscous.model = "laminar"
solver.tui.define.materials.copy("fluid", "water-liquid")
solver.setup.cell_zone_conditions.fluid["fff___"].material = "water-liquid"

# ======================== 3. 循环执行多工况计算 ========================
success_count = 0

for v in VELOCITY_LIST:
    print("\n" + "-" * 40)
    print(f"开始尝试工况：v = {v} m/s")
    
    # 使用 Try 包裹整个工况流程
    try:
        # 3.1 修改边界条件
        solver.setup.boundary_conditions.velocity_inlet["inlet"] = {
            "momentum": {"velocity": {"value": v}}
        }
        
        # 3.2 初始化与计算
        print(f"正在初始化并计算 v={v}...")
        solver.solution.initialization.hybrid_initialize()
        solver.solution.run_calculation.iterate(iter_count=ITERATIONS)
        
        # 3.3 导出流场数据
        full_field_csv = os.path.join(OUTPUT_DIR, f"full_field_v{v}.csv")
        solver.file.export.ascii(
            file_name=full_field_csv,
            surface_name_list=[],
            delimiter="space",
            cell_func_domain=[
                "x-coordinate", "y-coordinate", "pressure",
                "velocity-magnitude", "x-velocity", "y-velocity"
            ],
            location="cell-center"
        )
        
        # 3.4 保存结果文件
        case_path = os.path.join(OUTPUT_DIR, f"result_v{v}.cas.h5")
        solver.file.write_case_data(file_name=case_path)
        
        print(f"✅ 工况 v={v} 计算并保存成功！")
        success_count += 1

    except Exception as e:
        # 捕获异常，打印错误信息，但不退出程序
        print(f"⚠️ 工况 v={v} 运行出错，已跳过。")
        print(f"错误详情: {e}")
        # 这里可以选择是否保存一份报错时的 Case 以供后续排查
        continue 

# ======================== 4. 退出 ========================
solver.exit()
print("\n" + "=" * 60)
print(f"任务结束！总工况数: {len(VELOCITY_LIST)}, 成功完成: {success_count}")