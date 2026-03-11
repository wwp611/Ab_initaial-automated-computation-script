#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
prepare_dp_band_inputs.py

Prepare BAND inputs for a single material based on SCF results.

Usage:
    python prepare_dp_band_inputs.py <material>

Directory layout:
    DP/<material>/<strain>/scf/POSCAR -> DP/<material>/<strain>/band/
"""

import os
import shutil
import subprocess
import sys

# ================= 检查参数 =================
if len(sys.argv) < 2:
    print("Usage: python prepare_dp_band_inputs.py <material>")
    sys.exit(1)

mat = sys.argv[1]
BASE_DIR = os.getcwd()
DP_DIR = os.path.join(BASE_DIR, "DP")
mat_dir = os.path.join(DP_DIR, mat)

if not os.path.isdir(mat_dir):
    print(f"❌ DP/{mat} 不存在")
    sys.exit(1)

opt_dir = os.path.join(mat_dir, "opt")
if not os.path.isdir(opt_dir):
    print(f"❌ DP/{mat}/opt 不存在")
    sys.exit(1)

print(f"📂 在 DP/{mat} 下生成 BAND 输入文件")

# ================= 应变设置 =================
strain_dirs = ["undef", "0.01P", "0.01N", "0.02P", "0.02N"]

# ================= INCAR =================
INCAR_CONTENT = """Global Parameters
ISTART = 0
ISPIN  = 1
LREAL  = .FALSE.
ENCUT  = 520
LWAVE  = .FALSE.
LCHARG = .TRUE.
ADDGRID= .TRUE.
LASPH  = .TRUE.
PREC   = Accurate

Static Calculation
ISMEAR = 0
SIGMA  = 0.05
LORBIT = 11
NELM   = 120
EDIFF  = 1E-08

ICORELEVEL = 1
ICHARG = 11
"""

processed = 0

# ================= 1️⃣ 准备 undef/band =================
undef_scf_poscar = os.path.join(mat_dir, "undef", "scf", "POSCAR")
undef_band_dir = os.path.join(mat_dir, "undef", "band")
os.makedirs(undef_band_dir, exist_ok=True)

if not os.path.exists(undef_scf_poscar):
    print("❌ undef/scf/POSCAR 不存在，无法生成 band")
    sys.exit(1)

# POSCAR
shutil.copy(undef_scf_poscar, os.path.join(undef_band_dir, "POSCAR"))
print("📄 已复制 POSCAR → undef/band")

# vaspkit 303 -> KPOINTS
kpoints = os.path.join(undef_band_dir, "KPOINTS")
kpath = os.path.join(undef_band_dir, "KPATH.in")

if not os.path.exists(kpoints):
    if not os.path.exists(kpath):
        print("⚙️ 在 undef/band 中执行 vaspkit 303")
        try:
            subprocess.run(
                "vaspkit << EOF\n303\nEOF",
                shell=True,
                cwd=undef_band_dir,
                check=True
            )
        except subprocess.CalledProcessError:
            print("❌ vaspkit 303 执行失败")
            sys.exit(1)

    if os.path.exists(kpath):
        shutil.copy(kpath, kpoints)
        print("✅ KPATH.in → KPOINTS")
    else:
        print("❌ 未生成 KPATH.in，退出")
        sys.exit(1)

# ================= 2️⃣ 为所有 strain 生成 band 目录 =================
for sd in strain_dirs:
    scf_poscar = os.path.join(mat_dir, sd, "scf", "POSCAR")
    band_dir = os.path.join(mat_dir, sd, "band")

    if not os.path.exists(scf_poscar):
        print(f"⚠️ {sd}/scf/POSCAR 不存在，跳过")
        continue

    os.makedirs(band_dir, exist_ok=True)

    # POSCAR
    shutil.copy(scf_poscar, os.path.join(band_dir, "POSCAR"))

    # CHGCAR（来自对应 scf）
    scf_chgcar = os.path.join(mat_dir, sd, "scf", "CHGCAR")
    band_chgcar = os.path.join(band_dir, "CHGCAR")
    if os.path.exists(scf_chgcar):
        shutil.copy(scf_chgcar, band_chgcar)
    else:
        print(f"⚠️ {sd}/scf/CHGCAR 不存在，band 将从头算电荷")

    # POTCAR & vasp.sh
    shutil.copy(os.path.join(opt_dir, "POTCAR"), band_dir)
    shutil.copy(os.path.join(opt_dir, "vasp.sh"), band_dir)

    # INCAR
    with open(os.path.join(band_dir, "INCAR"), "w") as f:
        f.write(INCAR_CONTENT)

    # KPOINTS（统一来自 undef/band）
    dst_kpoints = os.path.join(band_dir, "KPOINTS")
    if os.path.abspath(kpoints) != os.path.abspath(dst_kpoints):
        shutil.copy(kpoints, dst_kpoints)

    print(f"✅ {sd}/band 已生成")
    processed += 1

# ================= 总结 =================
if processed == 0:
    print("\n❌ 没有处理任何材料，请确认目录结构")
else:
    print(f"\n✅ prepare_dp_band_inputs.py successfully prepared BAND inputs for {mat}")
