import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# ========= 输入 / 输出 =========
input_csv = "band_key_results.csv"      # 你的原始 CSV
output_csv = "deformation_potential.csv"

df = pd.read_csv(input_csv)

results = []

for material, g in df.groupby("Material"):

    # 去掉 undef
    g = g[g["目录"] != "undef"]

    if len(g) < 3:
        print(f"⚠️ {material} 数据点不足，跳过")
        continue

    x = g["ln(体积)"].values.reshape(-1, 1)

    # ===== VBM =====
    y_vbm = g["VBM-core(eV)"].values
    model_vbm = LinearRegression().fit(x, y_vbm)
    y_vbm_pred = model_vbm.predict(x)

    Ev = model_vbm.coef_[0]
    R2_vbm = r2_score(y_vbm, y_vbm_pred)

    # ===== CBM =====
    y_cbm = g["CBM-core(eV)"].values
    model_cbm = LinearRegression().fit(x, y_cbm)
    y_cbm_pred = model_cbm.predict(x)

    Ec = model_cbm.coef_[0]
    R2_cbm = r2_score(y_cbm, y_cbm_pred)

    results.append([
        material,
        round(Ev, 4),
        round(Ec, 4),
        round(R2_vbm, 4),
        round(R2_cbm, 4)
    ])

# ========= 保存 =========
out_df = pd.DataFrame(
    results,
    columns=[
        "Material",
        "Ev_deformation(eV)",
        "Ec_deformation(eV)",
        "R2_VBM",
        "R2_CBM"
    ]
)

out_df.to_csv(output_csv, index=False)
print(f"\n🎉 形变势计算完成，已保存至 {output_csv}")

