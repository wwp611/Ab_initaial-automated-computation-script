#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
prepare_dp_scf_inputs.py

Prepare SCF inputs for a single material based on opt/CONTCAR.

Usage:
    python prepare_dp_scf_inputs.py <material>

Directory layout:
    DP/<material>/opt/CONTCAR -> DP/<material>/<strain>/scf/
"""

import os
import shutil
import sys
import numpy as np

BASE_DIR = os.getcwd()
DP_DIR = os.path.join(BASE_DIR, "DP")

# ================= 检查参数 =================
if len(sys.argv) < 2:
    print("Usage: python prepare_dp_scf_inputs.py <material>")
    sys.exit(1)

mat = sys.argv[1]
mat_dir = os.path.join(DP_DIR, mat)

if not os.path.isdir(mat_dir):
    print(f"❌ DP/{mat} 不存在")
    sys.exit(1)

opt_dir = os.path.join(mat_dir, "opt")
contcar = os.path.join(opt_dir, "CONTCAR")
if not os.path.isfile(contcar):
    print(f"❌ {mat}/opt/CONTCAR 不存在，先完成 opt")
    sys.exit(1)

print(f"📂 在 DP/{mat} 下生成 SCF 输入文件")

# ================= 应变设置 =================
strain_map = {
    "undef": 0.0,
    "0.01P": 0.01,
    "0.01N": -0.01,
    "0.02P": 0.02,
    "0.02N": -0.02,
}

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
"""

# ================= 读取 opt/CONTCAR =================
with open(contcar) as f:
    lines = [l.rstrip() for l in f.readlines()]

scale = float(lines[1])
lattice = np.array([[float(x) for x in lines[i].split()] for i in range(2, 5)])
rest = lines[5:]

# ================= 读取 KPOINTS =================
with open(os.path.join(opt_dir, "KPOINTS")) as f:
    kp = [l.rstrip() for l in f.readlines()]

kmesh = list(map(int, kp[3].split()))
kp[3] = "  " + "  ".join(str(2 * k - 1) for k in kmesh)

# ================= 为每个应变生成 SCF 文件 =================
for name, eps in strain_map.items():
    scf_dir = os.path.join(mat_dir, name, "scf")
    os.makedirs(scf_dir, exist_ok=True)

    # --- POSCAR ---
    F = np.diag([1 + eps, 1 + eps, 1 + eps])
    new_lattice = lattice @ F

    with open(os.path.join(scf_dir, "POSCAR"), "w") as f:
        f.write(f"{mat}  strain {eps:+.3f} (from opt/CONTCAR)\n")
        f.write(f"   {scale}\n")
        for row in new_lattice:
            f.write("  " + "  ".join(f"{x:20.12f}" for x in row) + "\n")
        for l in rest:
            f.write(l + "\n")

    # --- 复制 POTCAR, INCAR, KPOINTS, vasp.sh ---
    shutil.copy(os.path.join(opt_dir, "POTCAR"), scf_dir)
    shutil.copy(os.path.join(opt_dir, "vasp.sh"), scf_dir)

    with open(os.path.join(scf_dir, "INCAR"), "w") as f:
        f.write(INCAR_CONTENT)

    with open(os.path.join(scf_dir, "KPOINTS"), "w") as f:
        f.write("\n".join(kp) + "\n")

    print(f"  ✅ {name}/scf 完成（strain {eps:+.3f}）")

print(f"\n✅ prepare_dp_scf_inputs.py successfully prepared SCF inputs for {mat}")
