#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
prepare_dp_opt_inputs.py

Prepare DP opt inputs for a single material.

Usage:
    python prepare_dp_opt_inputs.py <material>

Directory layout:
    POSCAR/<material>.vasp -> DP/<material>/opt/
"""

import os
import subprocess
import shutil
import sys

# ================= 配置 =================
POSCAR_DIR = "POSCAR"
DP_DIR = "DP"

INCAR_CONTENT = """Global Parameters
ISTART =  0
ISPIN  =  1
LREAL  = .FALSE.
ENCUT  =  520
PREC   =  Accurate
LWAVE  = .F.
LCHARG = .F.
ADDGRID= .TRUE.

Electronic Relaxation
ISMEAR =  0
SIGMA  =  0.05
NELM   =  90
NELMIN =  6
EDIFF  =  1E-07
NCORE  =  4

Ionic Relaxation
NSW    =  200
IBRION =  2
ISIF   =  3
EDIFFG = -1E-02
"""

VASP_SH_CONTENT = """#!/bin/bash
#SBATCH -N 1
#SBATCH -n 56
#SBATCH -p cp6

module add vasp
EXE=vasp # choose one vasp version to run. e.g. vasp / vasp_ncl / vasp_gam / vasp_neb ...

yhrun vasp
"""

# ================= 主程序 =================

def main():
    if len(sys.argv) < 2:
        print("Usage: python prepare_dp_opt_inputs.py <material>")
        sys.exit(1)

    mat = sys.argv[1]
    src_vasp = os.path.join(POSCAR_DIR, f"{mat}.vasp")
    mat_dir = os.path.join(DP_DIR, mat)

    if not os.path.isfile(src_vasp):
        print(f"❌ POSCAR/{mat}.vasp 不存在")
        sys.exit(1)

    if not os.path.isdir(mat_dir):
        print(f"⚠️ DP/{mat} 不存在，跳过")
        sys.exit(1)

    print(f"\n>>> Processing {mat}")

    # ================= opt 目录 =================
    opt_dir = os.path.join(mat_dir, "opt")
    os.makedirs(opt_dir, exist_ok=True)

    # 保留原始 vasp
    keep_vasp = os.path.join(opt_dir, f"{mat}.vasp")
    shutil.copy(src_vasp, keep_vasp)

    # 给 vaspkit 用的 POSCAR
    poscar_path = os.path.join(opt_dir, "POSCAR")
    shutil.copy(src_vasp, poscar_path)

    # ================= vaspkit 602 → primitive =================
    subprocess.run(
        'printf "602\n" | vaspkit',
        shell=True,
        cwd=opt_dir,
        check=True
    )

    primcell = os.path.join(opt_dir, "PRIMCELL.vasp")

    if not os.path.isfile(primcell):
        raise RuntimeError(f"PRIMCELL.vasp 未生成：{mat}（vaspkit 602 未正确执行）")

    # 用 PRIMCELL 覆盖 POSCAR
    os.remove(poscar_path)
    os.rename(primcell, poscar_path)
    print("  ✔ POSCAR = primitive (vaspkit 602)")

    # ================= 写 INCAR =================
    with open(os.path.join(opt_dir, "INCAR"), "w") as f:
        f.write(INCAR_CONTENT)
    print("  ✔ INCAR")

    # ================= vaspkit 102 → KPOINTS =================
    subprocess.run(
        'printf "102\n2\n0.03\n" | vaspkit',
        shell=True,
        cwd=opt_dir,
        check=True
    )

    if not os.path.isfile(os.path.join(opt_dir, "KPOINTS")):
        raise RuntimeError(f"KPOINTS 未生成：{mat}")

    print("  ✔ KPOINTS (0.03)")

    # ================= vaspkit → POTCAR =================
    subprocess.run(
        'printf "103\n" | vaspkit',
        shell=True,
        cwd=opt_dir,
        check=True
    )

    if not os.path.isfile(os.path.join(opt_dir, "POTCAR")):
        raise RuntimeError(f"POTCAR 未生成：{mat}")

    print("  ✔ POTCAR")

    # ================= 写 vasp.sh =================
    vasp_sh_path = os.path.join(opt_dir, "vasp.sh")
    with open(vasp_sh_path, "w") as f:
        f.write(VASP_SH_CONTENT)

    print("  ✔ vasp.sh")
    print(f"\n✅ prepare_dp_opt_inputs.py successfully prepared opt inputs for {mat}")


if __name__ == "__main__":
    main()
