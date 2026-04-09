import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time  # 导入时间模块
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import lightgbm as lgb
import os

# ========= 1. 配置 =========
DATA_DIR = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\data"
VELOCITY_LIST = [0.01, 0.02, 0.05, 0.06, 0.08, 0.1, 0.2, 0.3, 0.5]

# ========= 2. 读取多工况数据 =========
dfs = []
print("开始读取数据并监测质量...")
for v in VELOCITY_LIST:
    file_path = os.path.join(DATA_DIR, f"full_field_v{v}.csv")
    if not os.path.exists(file_path):
        print(f"找不到文件: {file_path}，已跳过。")
        continue
        
    df = pd.read_csv(
        file_path,
        delim_whitespace=True,
        skiprows=1,
        header=None
    )
    df.columns = [
        "cellnumber", "x1", "y1", "x2", "y2",
        "pressure", "vel_mag", "vx", "vy"
    ]
    
    # --- 数据清洗与 5% 阈值监测 ---
    original_count = len(df)
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    dropped_count = original_count - len(df)
    drop_rate = dropped_count / original_count
    
    status_msg = f"工况 v={v}: 清洗掉 {dropped_count} 个异常点 (占比: {drop_rate:.2%})"
    if drop_rate > 0.05:
        print(f"❗❗❗ 警告: {status_msg} -> 超过5%阈值，请检查CFD收敛性！")
    else:
        print(f"✅ {status_msg}")
    
    df["x"] = df["x1"]
    df["y"] = df["y1"]
    df["velocity"] = v
    df = df.drop(columns=["cellnumber", "x1", "y1", "x2", "y2"])
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)
print(f"\n数据集准备就绪。总样本数: {len(data)}")

# ========= 3. 特征 & 标签 =========
X = data[["x", "y", "vx", "vy", "velocity"]]
y_pressure = data["pressure"]
y_velmag   = data["vel_mag"]

# ========= 4. 划分数据 =========
X_train, X_test, yp_train, yp_test, yv_train, yv_test = train_test_split(
    X, y_pressure, y_velmag, test_size=0.2, random_state=42
)

# ========= 5. 训练模型 (加入计时逻辑) =========
def train_lgbm(X_train, y_train, label_name):
    print(f"正在训练 {label_name} 模型...")
    start_time = time.time()  # 记录开始时间
    
    model = lgb.LGBMRegressor(
        n_estimators=1000,
        learning_rate=0.08,
        num_leaves=50,
        max_depth=10,
        n_jobs=-1,
        random_state=42,
        importance_type='gain',
        verbose=-1
    )
    model.fit(X_train, y_train)
    
    end_time = time.time()    # 记录结束时间
    print(f"--- {label_name} 训练完成，耗时: {end_time - start_time:.2f} 秒 ---")
    return model

total_train_start = time.time()

model_p = train_lgbm(X_train, yp_train, "Pressure")
model_v = train_lgbm(X_train, yv_train, "Velocity")

total_train_end = time.time()
print(f"\n>>> 所有模型总训练耗时: {total_train_end - total_train_start:.2f} 秒")

# ========= 6. 评估 (加入预测耗时统计) =========
def evaluate(model, X_test, y_test, name):
    start_pred = time.time()
    y_pred = model.predict(X_test)
    end_pred = time.time()
    
    rmse  = np.sqrt(mean_squared_error(y_test, y_pred))
    nrmse = rmse / (y_test.max() - y_test.min())
    
    print(f"\n[{name} 评估结果]")
    print(f"  预测耗时: {end_pred - start_pred:.4f} 秒 (样本数: {len(X_test)})")
    print(f"  RMSE:     {rmse:.6e}")
    print(f"  NRMSE:    {nrmse:.4%}")
    return y_pred

yp_pred = evaluate(model_p, X_test, yp_test, "Pressure (Pa)")
yv_pred = evaluate(model_v, X_test, yv_test, "Velocity Magnitude (m/s)")

# ========= 7. 可视化 =========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("LightGBM Surrogate Model — Multi-Velocity Analysis", fontsize=14)

# 7.1 压力预测散点图
ax = axes[0, 0]
ax.scatter(yp_test, yp_pred, s=1, alpha=0.3, color="steelblue")
lims = [min(yp_test.min(), yp_pred.min()), max(yp_test.max(), yp_pred.max())]
ax.plot(lims, lims, "r--", linewidth=1)
ax.set_xlabel("True Pressure (Pa)")
ax.set_ylabel("Predicted Pressure (Pa)")
ax.set_title("Pressure: Predicted vs True")

# 7.2 速度预测散点图
ax = axes[0, 1]
ax.scatter(yv_test, yv_pred, s=1, alpha=0.3, color="darkorange")
lims = [min(yv_test.min(), yv_pred.min()), max(yv_test.max(), yv_pred.max())]
ax.plot(lims, lims, "r--", linewidth=1)
ax.set_xlabel("True Velocity (m/s)")
ax.set_ylabel("Predicted Velocity (m/s)")
ax.set_title("Velocity: Predicted vs True")

# 7.3 & 7.4 云图验证 (取 v=0.05 工况)
v_plot = 0.05
subset = data[data["velocity"] == v_plot]
if not subset.empty:
    ax = axes[1, 0]
    sc1 = ax.scatter(subset["x"], subset["y"], c=subset["pressure"], cmap="jet", s=1)
    plt.colorbar(sc1, ax=ax, label="Pressure (Pa)")
    ax.set_title(f"Pressure Field (v={v_plot} m/s)")
    
    ax = axes[1, 1]
    sc2 = ax.scatter(subset["x"], subset["y"], c=subset["vel_mag"], cmap="coolwarm", s=1)
    plt.colorbar(sc2, ax=ax, label="Velocity Magnitude (m/s)")
    ax.set_title(f"Velocity Field (v={v_plot} m/s)")

plt.tight_layout()
save_path = os.path.join(DATA_DIR, "lgbm_results.png")
plt.savefig(save_path, dpi=150)
plt.show()

print(f"\n🚀 任务完成！结果图片已保存至: {save_path}")
