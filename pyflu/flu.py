import os
import ansys.fluent.core as pyfluent

try:
    solver = pyfluent.launch_fluent(
        mode="solver",
        dimension=pyfluent.Dimension.TWO,
        precision=pyfluent.Precision.DOUBLE,
        processor_count=2
    )
    print("Fluent 启动成功")

    cas_path = r"D:\VScode\project\2026\demo1\flu\case\res.cas.h5"
    solver.tui.file.read_case(cas_path)
    print("case 文件读取成功")

    # 目标目录
    report_dir = r"D:\VScode\project\2026\demo1\flu\report_files"
    os.makedirs(report_dir, exist_ok=True)

    # 查看当前已有的 report file 名称
    names = solver.settings.solution.monitor.report_files.get_object_names()
    print("现有 report files:", names)

    # 把已有对象的输出路径从 C 盘改到 D 盘
    for name in names:
        rf = solver.settings.solution.monitor.report_files[name]
        rf.file_name = os.path.join(report_dir, f"{name}.out")
        rf.print = True
        print(f"{name} -> {rf.file_name}")

    solver.tui.solve.initialize.hyb_initialization()
    print("初始化完成")

    solver.tui.solve.iterate(20)
    print("计算完成")

except Exception as e:
    print("出错了：", e)
