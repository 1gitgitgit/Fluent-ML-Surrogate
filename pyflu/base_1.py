"""
PyFluent 自动化脚本：二维管道流动（修复数据导出问题）
功能：自动缩放网格、层流计算、修复 CSV 导出（含坐标与物理场）
"""

import ansys.fluent.core as pyfluent
import os

# ======================== 配置参数 ========================
# 建议使用绝对路径，确保无误
MESH_FILE = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\project2dimandball_files\dp0\FFF\Fluent\FFF-Setup-Output.cas.h5"
OUTPUT_DIR = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\data"
VELOCITY = 0.01  # m/s
ITERATIONS = 100

# 确保输出目录存在
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

# ======================== 2. 读取网格 ========================
print("\n读取网格文件...")
solver.file.read_case(file_name=MESH_FILE)

# ======================== 3. 网格缩放 (关键步骤) ========================
# 假设你的网格在 CAD 中是以 mm 为单位画的，这里将其缩放到 m
print("\n执行网格缩放: mm -> m")
solver.mesh.scale(x_scale=0.001, y_scale=0.001)

# 检查缩放后的范围
print(f"网格检查完成，请确认范围是否符合物理实际。")

# ======================== 4. 物理模型与材料 ========================
print("\n设置物理模型与材料...")
solver.setup.models.viscous.model = "laminar"

# 尝试添加 water-liquid 材料（如果数据库中没有则从数据库复制）
solver.tui.define.materials.copy("fluid", "water-liquid")
# 将区域设定为水
# 注意：请确保你的 cell zone 名称是 "fff___"，如果报错，请检查 solver.setup.cell_zone_conditions.fluid.keys()
solver.setup.cell_zone_conditions.fluid["fff___"].material = "water-liquid"

# ======================== 5. 边界条件 ========================
print("\n设置边界条件...")
# Inlet
solver.setup.boundary_conditions.velocity_inlet["inlet"] = {
    "momentum": {"velocity": {"value": VELOCITY}}
}
# Outlet
solver.setup.boundary_conditions.pressure_outlet["outlet"] = {
    "momentum": {"gauge_pressure": {"value": 0}}
}

# ======================== 6. 初始化与计算 ========================
print("\n开始初始化与计算...")
solver.solution.initialization.hybrid_initialize()
solver.solution.run_calculation.iterate(iter_count=ITERATIONS)

# ======================== 7. 导出完整单元中心数据 (修复版) ========================
print("\n" + "=" * 60)
print("导出流场数据到 CSV（单元中心数据）...")
full_field_csv = os.path.join(OUTPUT_DIR, f"full_field_v{VELOCITY}.csv")

# 使用 PyFluent API 方式导出（推荐）
try:
    solver.file.export.ascii(
        file_name=full_field_csv,
        surface_name_list=[],  # 空列表表示导出所有单元
        delimiter="space",
        cell_func_domain=[
            "x-coordinate",
            "y-coordinate", 
            "pressure",
            "velocity-magnitude",
            "x-velocity",
            "y-velocity"
        ],
        location="cell-center"  # 关键：指定单元中心数据
    )
    print(f"✅ 数据成功导出至: {full_field_csv}")
except Exception as e:
    print(f"❌ 导出失败: {e}")

# ======================== 8. 保存与退出 ========================
case_path = os.path.join(OUTPUT_DIR, f"final_result_v{VELOCITY}.cas.h5")
solver.file.write_case_data(file_name=case_path)
print(f"项目已保存: {case_path}")

solver.exit()
print("=" * 60)
print("所有任务已完成！")
