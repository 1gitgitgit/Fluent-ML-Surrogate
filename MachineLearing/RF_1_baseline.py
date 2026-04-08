#使用随机森林训练预测速度和压力场
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor

# ========= 1. 配置 =========
DATA_DIR = r"D:\VScode\project\2026\demo1\2026-4-5\project_data\data"
# 修改后的完整列表
VELOCITY_LIST = [0.01, 0.02, 0.05, 0.06, 0.08, 0.1, 0.2, 0.3, 0.5]

# ========= 2. 读取多工况数据 =========
dfs = []
for v in VELOCITY_LIST:
    file_path = f"{DATA_DIR}\\full_field_v{v}.csv"
    
    # 读取原始数据
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
    
    # 数据清洗与统计
    original_count = len(df)
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    dropped_count = original_count - len(df)
    drop_rate = dropped_count / original_count
    
    # 打印监测信息
    print(f"工况 v={v}: 清洗掉 {dropped_count} 个异常点 (占比: {drop_rate:.2%})")
    
    # 核心判断：如果大于 5%，发出醒目警告
    if drop_rate > 0.05:
        print(f"--- ❗ 警告: v={v} 工况剔除比例过高 ({drop_rate:.2%})，请检查 CFD 原始数据质量！ ---")

    # 后续特征处理
    df["x"] = df["x1"]
    df["y"] = df["y1"]
    df["velocity"] = v
    df = df.drop(columns=["cellnumber", "x1", "y1", "x2", "y2"])
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)
print("-" * 30)
print(f"数据合并完成。总样本数: {len(data)}")

# ========= 3. 特征 & 标签 =========
X = data[["x", "y", "vx", "vy", "velocity"]]
y_pressure = data["pressure"]
y_velmag   = data["vel_mag"]

# ========= 4. 划分数据 =========
X_train, X_test, yp_train, yp_test, yv_train, yv_test = train_test_split(
    X, y_pressure, y_velmag, test_size=0.2, random_state=42
)

# ========= 5. 训练模型 =========
def train_rf(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model

print("训练压力模型...")
model_p = train_rf(X_train, yp_train)
print("训练速度模型...")
model_v = train_rf(X_train, yv_train)

# ========= 6. 评估 =========
def evaluate(model, X_test, y_test, name):
    y_pred = model.predict(X_test)
    rmse  = np.sqrt(mean_squared_error(y_test, y_pred))
    nrmse = rmse / (y_test.max() - y_test.min())
    print(f"\n[{name}]")
    print(f"  RMSE:  {rmse:.6e}")
    print(f"  NRMSE: {nrmse:.4%}")
    return y_pred

yp_pred = evaluate(model_p, X_test, yp_test, "Pressure (Pa)")
yv_pred = evaluate(model_v, X_test, yv_test, "Velocity Magnitude (m/s)")

# ========= 7. 可视化 =========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Random Forest Surrogate Model — Multi-Velocity Results", fontsize=14)

# 7.1 压力：预测 vs 真实
ax = axes[0, 0]
ax.scatter(yp_test, yp_pred, s=1, alpha=0.3, color="steelblue")
lims = [min(yp_test.min(), yp_pred.min()), max(yp_test.max(), yp_pred.max())]
ax.plot(lims, lims, "r--", linewidth=1)
ax.set_xlabel("True Pressure (Pa)")
ax.set_ylabel("Predicted Pressure (Pa)")
ax.set_title("Pressure: Predicted vs True")

# 7.2 速度：预测 vs 真实
ax = axes[0, 1]
ax.scatter(yv_test, yv_pred, s=1, alpha=0.3, color="darkorange")
lims = [min(yv_test.min(), yv_pred.min()), max(yv_test.max(), yv_pred.max())]
ax.plot(lims, lims, "r--", linewidth=1)
ax.set_xlabel("True Velocity Magnitude (m/s)")
ax.set_ylabel("Predicted Velocity Magnitude (m/s)")
ax.set_title("Velocity: Predicted vs True")

# 7.3 单工况流场压力分布（取v=0.05工况）
v_plot = 0.05
subset = data[data["velocity"] == v_plot]
ax = axes[1, 0]
sc = ax.scatter(subset["x"], subset["y"], c=subset["pressure"],
                cmap="jet", s=1)
plt.colorbar(sc, ax=ax, label="Pressure (Pa)")
ax.set_title(f"Pressure Field (v={v_plot} m/s)")
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")

# 7.4 单工况流场速度分布
ax = axes[1, 1]
sc = ax.scatter(subset["x"], subset["y"], c=subset["vel_mag"],
                cmap="coolwarm", s=1)
plt.colorbar(sc, ax=ax, label="Velocity Magnitude (m/s)")
ax.set_title(f"Velocity Field (v={v_plot} m/s)")
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")

plt.tight_layout()
plt.savefig(f"{DATA_DIR}\\rf_results.png", dpi=150)
plt.show()
print(f"\n图片已保存至: {DATA_DIR}\\rf_results.png")