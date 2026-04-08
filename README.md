# CFD-ML-Surrogate

使用 PyFluent 自动化生成 CFD 数据，并通过机器学习建立流场代理模型

## 项目概述
- **问题**：二维圆柱绕流/方腔流（根据你实际案例改）
- **参数范围**：入口速度 0.01-0.5 m/s（9个工况）
- **预测目标**：压力场 + 速度场

## 已完成
- ✅ PyFluent 自动化多工况计算（带容错）
- ✅ 随机森林代理模型
- ✅ LightGBM 代理模型（NRMSE < X%）

## 文件说明
- `base_2_multiple.py` - PyFluent 批量计算脚本
- `RF_1_baseline.py` - 随机森林模型
- `LGBM_2_improve.py` - LightGBM 模型

## 运行环境
- Python 3.12
- PyFluent, LightGBM, scikit-learn, pandas, numpy,matplotlib

