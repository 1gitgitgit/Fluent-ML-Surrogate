"""
PyFluent 自动化脚本：二维管道基础计算
功能：网格缩放、层流模型、批量速度扫描、数据导出
"""

import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples
import os

# ======================== 配置参数 ========================
MESH_FILE = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\project2dimandball_files\dp0\FFF\Fluent\FFF-Setup-Output.cas.h5"
OUTPUT_DIR = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\data"
VELOCITY_LIST = [0.01, 0.0325, 0.055, 0.0775, 0.1]  # m/s
ITERATIONS = 100

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================== 1. 启动 Fluent ========================
print("=" * 60)
print("启动 Fluent (2D 双精度, 无 GUI)...")
print("=" * 60)

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


# ======================== 3. 网格缩放检查 ========================
print("\n检查网格尺度...")
mesh_info = solver.settings.mesh.mesh_info()
print(f"网格信息: {mesh_info}")

# ======================== 4. 物理模型设置 ========================
print("\n设置物理模型...")
solver.setup.models.viscous.model = "laminar"
print("  ✓ 层流模型已启用")

# 设置材料为 water-liquid
print("\n设置材料...")

solver.setup.cell_zone_conditions.fluid["fff___"].material = "water-liquid"


print("  ✓ 材料设为 water-liquid")

# ======================== 5. 边界条件设置 ========================
print("\n设置边界条件...")

# 设置 inlet (速度入口 - 初始值)
try:
    solver.setup.boundary_conditions.velocity_inlet["inlet"] = {
        "momentum": {
            "velocity": {
                "value": VELOCITY_LIST[0]  # 初始速度
            }
        }
    }
    print(f"  ✓ inlet: Velocity Inlet = {VELOCITY_LIST[0]} m/s")
except Exception as e:
    print(f"  ⚠ inlet 设置失败: {e}")

# 设置 outlet (压力出口)
try:
    solver.setup.boundary_conditions.pressure_outlet["outlet"] = {
        "momentum": {
            "gauge_pressure": {
                "value": 0
            }
        }
    }
    print("  ✓ outlet: Pressure Outlet = 0 Pa")
except Exception as e:
    print(f"  ⚠ outlet 设置失败: {e}")

# ======================== 6. 创建报告定义 ========================
print("\n创建报告定义...")

# 创建 inlet 压力报告
try:
    solver.solution.report_definitions.surface["inlet_pressure"] = {
        "report_type": "surface-areaavg",
        "field": "pressure",
        "surface_names": ["inlet"]
    }
    print("  ✓ inlet_pressure: 入口面积加权平均静压")
except Exception as e:
    print(f"  ⚠ inlet_pressure 创建失败: {e}")

# 创建 outlet 速度报告
try:
    solver.solution.report_definitions.surface["outlet_velocity"] = {
        "report_type": "surface-areaavg",
        "field": "velocity-magnitude",
        "surface_names": ["outlet"]
    }
    print("  ✓ outlet_velocity: 出口面积加权平均速度")
except Exception as e:
    print(f"  ⚠ outlet_velocity 创建失败: {e}")

# ======================== 7. 求解器设置 ========================
print("\n设置求解器...")
solver.settings.solution.methods.p_v_coupling.flow_scheme = "Coupled"
# 删除这些
# solver.tui.solve.set.discretization_scheme("pressure", "second-order")

# 改用数字索引（通常 second-order 是索引 2 或 12）
solver.tui.solve.set.discretization_scheme("pressure", 12)  # 12 = second-order
solver.tui.solve.set.discretization_scheme("mom", 1)        # 1 = second-order upwind
print("设置求解器...")

# 检查求解器类型
print("求解器类型:", solver.settings.setup.general.solver.type)
print("粘性模型:", solver.settings.setup.models.viscous.model)

# 只设置压力和动量
solver.tui.solve.set.discretization_scheme("pressure", 12)
solver.tui.solve.set.discretization_scheme("mom", 1)

print("基本离散格式设置完成")



# ======================== 8. 批量计算循环 ========================
print("\n" + "=" * 60)
print("开始批量计算循环")
print("=" * 60)

for i, velocity in enumerate(VELOCITY_LIST):
    print(f"\n{'─' * 60}")
    print(f"工况 {i+1}/{len(VELOCITY_LIST)}: 入口速度 = {velocity} m/s")
    print(f"{'─' * 60}")
    
    # 更新入口速度
    solver.setup.boundary_conditions.velocity_inlet["inlet"].momentum.velocity.value = velocity
    print(f"  ✓ 更新入口速度: {velocity} m/s")
    
    # 仅首次初始化
    if i == 0:
        print("  ⏳ 执行 Hybrid Initialization...")
        solver.solution.initialization.hybrid_initialize()
        print("  ✓ 初始化完成")
    
    # 迭代计算
    print(f"  ⏳ 迭代 {ITERATIONS} 步...")
    solver.solution.run_calculation.iterate(iter_count=ITERATIONS)
    print("  ✓ 计算完成")
    
    # 获取报告值
    try:
        inlet_p = solver.solution.report_definitions.surface["inlet_pressure"].get_values()
        outlet_v = solver.solution.report_definitions.surface["outlet_velocity"].get_values()
        outlet_p = 0  # 出口压力设为 0 (表压)
        
        pressure_drop = inlet_p - outlet_p
        
        print(f"\n  📊 结果:")
        print(f"     入口压力:   {inlet_p:.4f} Pa")
        print(f"     出口压力:   {outlet_p:.4f} Pa")
        print(f"     压降:       {pressure_drop:.4f} Pa")
        print(f"     出口速度:   {outlet_v:.6f} m/s")
    except Exception as e:
        print(f"  ⚠ 报告读取失败: {e}")
    
    # 导出 outlet 面速度剖面 (CSV)
    csv_filename = os.path.join(OUTPUT_DIR, f"outlet_v{velocity}.csv")
    try:
        solver.file.export.ascii(
            file_name=csv_filename,
            surfaces=["outlet"],
            variables=["x-coordinate", "y-coordinate", "velocity-magnitude", 
                      "x-velocity", "y-velocity", "pressure"]
        )
        print(f"  ✓ 导出 CSV: {csv_filename}")
    except Exception as e:
        print(f"  ⚠ CSV 导出失败: {e}")

# ======================== 9. 导出全场数据 (第一个工况) ========================
print("\n" + "=" * 60)
print("导出全场数据 (v=0.01 m/s 工况)")
print("=" * 60)

# 重新运行第一个工况以确保数据正确
solver.setup.boundary_conditions.velocity_inlet["inlet"].momentum.velocity.value = 0.01
solver.solution.run_calculation.iterate(iter_count=ITERATIONS)

# 导出全场压力和速度 (整个计算域)
full_field_file = os.path.join(OUTPUT_DIR, "full_field_v0.01.dat")
try:
    solver.file.export.ascii(
        file_name=full_field_file,
        cell_zones="*",
        surfaces=[],
        variables=["x-coordinate", "y-coordinate", "pressure", 
                  "velocity-magnitude", "x-velocity", "y-velocity"]
    )
    print(f"  ✓ 全场数据导出: {full_field_file}")
except Exception as e:
    print(f"  ⚠ 全场数据导出失败: {e}")

# ======================== 10. 保存结果 ========================
print("\n保存最终结果...")
case_file = os.path.join(OUTPUT_DIR, "final.cas.h5")
data_file = os.path.join(OUTPUT_DIR, "final.dat.h5")

solver.file.write_case_data(file_name=case_file)
print(f"  ✓ 保存: {case_file}")
print(f"  ✓ 保存: {data_file}")

# ======================== 11. 关闭 Fluent ========================
print("\n关闭 Fluent 会话...")
solver.exit()
print("✅ 脚本执行完成！")
print("=" * 60)
