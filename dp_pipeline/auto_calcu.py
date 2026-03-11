#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DP workflow controller (material-level scheduler)

One material = opt → all scf strains → all band strains
Submit N_BATCH materials at a time from POSCAR/ folder
Move completed materials to POSCAR_done/
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# ================= 用户配置 =================
STRAINS = ["undef", "0.01P", "0.01N", "0.02P", "0.02N"]
REACHED_KEY = "Elapsed time"

# dp_pipeline/auto_calcu.py 当前目录
BASE_DIR = Path(__file__).resolve().parent.parent  # project/
DP_DIR = BASE_DIR / "DP"
POSCAR_DIR = BASE_DIR / "POSCAR"
POSCAR_DONE_DIR = BASE_DIR / "POSCAR_done"
SUBMIT_DIR = Path(__file__).resolve().parent  # dp_pipeline/
POSCAR_DONE_DIR.mkdir(exist_ok=True)
os.makedirs(POSCAR_DONE_DIR, exist_ok=True)

# 一次提交的材料数量
N_BATCH = 2  # ← 在这里修改 n

# ================= 工具函数 =================
def run(cmd, cwd=None):
    print(f"▶ {cmd} (cwd={cwd})")
    p = subprocess.run(cmd, shell=True, cwd=cwd,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True)
    print(p.stdout)
    return p.stdout.lower()

def stage_done(path):
    outcar = os.path.join(path, "OUTCAR")
    if not os.path.exists(outcar):
        return False
    with open(outcar, "r", errors="ignore") as f:
        return REACHED_KEY in f.read()

# --- 在判断完成的同时，如果有锁文件就将其删除 ---
def opt_done(mat):
    is_done = stage_done(os.path.join(DP_DIR, mat, "opt"))
    lock_file = os.path.join(DP_DIR, mat, "opt.lock")
    if is_done and os.path.exists(lock_file):
        os.remove(lock_file)
    return is_done

def scf_done(mat):
    is_done = all(stage_done(os.path.join(DP_DIR, mat, sd, "scf")) for sd in STRAINS)
    lock_file = os.path.join(DP_DIR, mat, "scf.lock")
    if is_done and os.path.exists(lock_file):
        os.remove(lock_file)
    return is_done

def band_done(mat):
    is_done = all(stage_done(os.path.join(DP_DIR, mat, sd, "band")) for sd in STRAINS)
    lock_file = os.path.join(DP_DIR, mat, "band.lock")
    if is_done and os.path.exists(lock_file):
        os.remove(lock_file)
    return is_done

# --- 在判断运行时，优先检查锁文件是否存在 ---
def opt_running(mat):
    if os.path.exists(os.path.join(DP_DIR, mat, "opt.lock")):
        return True
    outcar = os.path.join(DP_DIR, mat, "opt", "OUTCAR")
    return os.path.exists(outcar) and not stage_done(os.path.join(DP_DIR, mat, "opt"))

def scf_running(mat):
    if os.path.exists(os.path.join(DP_DIR, mat, "scf.lock")):
        return True
    for sd in STRAINS:
        path = os.path.join(DP_DIR, mat, sd, "scf")
        outcar = os.path.join(path, "OUTCAR")
        if os.path.exists(outcar) and not stage_done(path):
            return True
    return False

def band_running(mat):
    if os.path.exists(os.path.join(DP_DIR, mat, "band.lock")):
        return True
    for sd in STRAINS:
        path = os.path.join(DP_DIR, mat, sd, "band")
        outcar = os.path.join(path, "OUTCAR")
        if os.path.exists(outcar) and not stage_done(path):
            return True
    return False

# ================= 主流程 =================
def main():

    if not os.path.isdir(DP_DIR) or not os.path.isdir(POSCAR_DIR):
        print("❌ 缺少 DP/ 或 POSCAR/ 目录")
        sys.exit(1)

    while True:
        # 当前 POSCAR/ 下剩余材料
        poscar_files = sorted(f for f in os.listdir(POSCAR_DIR) if f.endswith(".vasp"))
        if not poscar_files:
            print("📂 POSCAR/ 文件夹为空，全部材料计算完成！")
            break

        # 取前 N_BATCH 个材料
        materials = [f[:-5] for f in poscar_files[:N_BATCH]]
        print(f"\n📌 本轮提交材料: {materials}")

        for mat in materials:
            print(f"\n🔧 材料: {mat}")
            mat_dir = DP_DIR / mat
            mat_dir.mkdir(parents=True, exist_ok=True) 

            # 初始化
            if not os.path.isdir(mat_dir):
                print("  ▶ 初始化目录 (mk.sh)")
                run(f"bash {SUBMIT_DIR}/mk.sh {mat}")

            # OPT
            if not opt_done(mat):
                if opt_running(mat):
                    print("  ⏳ OPT 正在排队或运行")
                    continue
                print("  ▶ 提交 OPT")
                run(f"python {SUBMIT_DIR}/prepare_dp_opt_inputs.py {mat}", cwd=BASE_DIR)
                run(f"bash {SUBMIT_DIR}/submit_dp_opt.sh {mat}", cwd=SUBMIT_DIR)
                # --- 提交任务后立刻创建锁文件 ---
                (mat_dir / "opt.lock").touch()
                continue

            # SCF
            if not scf_done(mat):
                if scf_running(mat):
                    print("  ⏳ SCF 正在排队或运行")
                    continue
                print("  ▶ 提交 SCF（所有应变）")
                run(f"python {SUBMIT_DIR}/prepare_dp_scf_inputs.py {mat}", cwd=BASE_DIR)
                run(f"bash {SUBMIT_DIR}/submit_dp_scf.sh {mat}", cwd=SUBMIT_DIR)
                # --- 提交任务后立刻创建锁文件 ---
                (mat_dir / "scf.lock").touch()
                continue

            # BAND
            if not band_done(mat):
                if band_running(mat):
                    print("  ⏳ BAND 正在排队或运行")
                    continue
                print("  ▶ 提交 BAND（所有应变）")
                run(f"python {SUBMIT_DIR}/prepare_dp_band_inputs.py {mat}", cwd=BASE_DIR)
                run(f"bash {SUBMIT_DIR}/submit_dp_band.sh {mat}", cwd=SUBMIT_DIR)
                # --- 提交任务后立刻创建锁文件 ---
                (mat_dir / "band.lock").touch()
                continue

            # BAND 完成
            print("  ✅ BAND 已完成")

            # 移动 POSCAR 文件到 POSCAR_done/
            src = os.path.join(POSCAR_DIR, f"{mat}.vasp")
            dst = os.path.join(POSCAR_DONE_DIR, f"{mat}.vasp")
            if os.path.exists(src):
                shutil.move(src, dst)
                print(f"  ✅ {mat}.vasp 已移动到 POSCAR_done/")

        # 本轮结束后可选择自动等待一段时间再继续
        print("\n⏳ 本轮提交完成，等待下一轮...")
        time.sleep(5)  # 可根据需要修改间隔时间

if __name__ == "__main__":
    main()