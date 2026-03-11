#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DP Band 数据提取脚本
实施步骤：
1. 遍历 DP/<material>/ 下各应变目录 undef、0.01P、0.01N、0.02P、0.02N。
2. 在 undef/band 下，如果没有 BAND_GAP 文件，执行 vaspkit 211 生成。
3. 读取 BAND_GAP 提取 VBM/CBM Band Index 和 k-point Index。
4. 从 band/OUTCAR 提取体积 (取第一条 volume of cell)。
5. 从 band/OUTCAR 提取所有 1s 核心能量，选最小值作为 core_energy。
6. 使用 VBM/CBM k-point & Band Index，从 OUTCAR 提取能量。
7. 输出 CSV：目录, ln(体积), VBM-core, CBM-core, VBM, CBM, core_energy
"""

import os
import subprocess
import math
import csv

BASE_DIR = os.getcwd()
DP_DIR = os.path.join(BASE_DIR, "DP")
strain_dirs = ["undef", "0.01P", "0.01N", "0.02P", "0.02N"]
output_file = "band_key_results.csv"

if not os.path.isdir(DP_DIR):
    print("❌ 当前目录下未找到 DP/ 目录")
    exit(1)

print(f"📂 在 DP 目录下工作: {DP_DIR}")

def get_first_volume(outcar_file):
    """取 OUTCAR 中第一条 'volume of cell' 的数值"""
    with open(outcar_file) as f:
        for line in f:
            if "volume of cell" in line:
                for p in line.split()[::-1]:  # 倒序找最后一个浮点数
                    try:
                        v = float(p)
                        return v
                    except:
                        continue
    return None

def get_min_1s_core(outcar_file):
    """取 OUTCAR 中所有 1s 核心能量的最小值"""
    min_energy = None
    in_core_block = False

    with open(outcar_file) as f:
        for line in f:
            # 进入 core state 区块
            if "the core state eigenenergies are" in line:
                in_core_block = True
                continue

            if in_core_block:
                # 空行 → core block 结束
                if line.strip() == "":
                    break

                parts = line.split()
                for i, p in enumerate(parts):
                    if p.lower() == "1s":
                        try:
                            e = float(parts[i + 1])
                            if min_energy is None or e < min_energy:
                                min_energy = e
                        except:
                            pass

    return min_energy

def parse_band_gap(band_gap_file):
    """解析 BAND_GAP 文件，返回 VBM/CBM Band Index 与 k-point Index"""
    vbm_band = cbm_band = vbm_kpt = cbm_kpt = None
    with open(band_gap_file) as f:
        for line in f:
            if "Band Indexes of VBM & CBM" in line:
                parts = line.strip().split()
                vbm_band, cbm_band = int(parts[-2]), int(parts[-1])
            if "Kpt Indexes of VBM & CBM" in line:
                parts = line.strip().split()
                vbm_kpt, cbm_kpt = int(parts[-2]), int(parts[-1])
    return vbm_band, cbm_band, vbm_kpt, cbm_kpt

def get_band_energy(outcar_file, kpt_index, band_index):
    """提取指定 k-point 和 band index 的能量"""
    import re

    with open(outcar_file, 'r') as f:
        lines = f.readlines()

    kpt_pattern = re.compile(rf"^\s*k-point\s+{kpt_index}\s*:")

    for i, line in enumerate(lines):
        if kpt_pattern.match(line):
            # band 数据从下一行表头后开始
            for band_line in lines[i+2:]:
                if band_line.strip() == "" or band_line.lower().startswith("k-point"):
                    break
                parts = band_line.split()
                if len(parts) < 2:
                    continue
                try:
                    b_no = int(parts[0])
                    energy = float(parts[1])
                    if b_no == band_index:
                        return energy
                except:
                    continue
    return None

# 写入 CSV 文件表头
with open(output_file, "w", newline="") as fcsv:
    writer = csv.writer(fcsv)
    writer.writerow(["Material","目录", "ln(体积)", "VBM-core(eV)", "CBM-core(eV)", "VBM(eV)", "CBM(eV)", "core_energy(eV)"])

processed = 0

for mat in sorted(os.listdir(DP_DIR)):
    mat_dir = os.path.join(DP_DIR, mat)
    if not os.path.isdir(mat_dir):
        continue

    print(f"\n🔧 处理材料: {mat}")
    processed += 1

    undef_band_dir = os.path.join(mat_dir, "undef", "band")
    os.makedirs(undef_band_dir, exist_ok=True)
    band_gap_file = os.path.join(undef_band_dir, "BAND_GAP")

    # 如果 BAND_GAP 不存在，运行 vaspkit 211
    if not os.path.exists(band_gap_file):
        print(f"  ⚙️ undef/band 下未找到 BAND_GAP，执行 vaspkit 211 生成...")
        try:
            subprocess.run("vaspkit << EOF\n211\nEOF", shell=True, cwd=undef_band_dir, check=True)
        except subprocess.CalledProcessError:
            print("  ❌ vaspkit 执行失败，跳过材料")
            continue
        if not os.path.exists(band_gap_file):
            print("  ❌ 未生成 BAND_GAP，跳过材料")
            continue

    vbm_band, cbm_band, vbm_kpt, cbm_kpt = parse_band_gap(band_gap_file)
    if None in [vbm_band, cbm_band, vbm_kpt, cbm_kpt]:
        print("  ❌ BAND_GAP 文件信息不完整，跳过")
        continue

    for sd in strain_dirs:
        band_dir = os.path.join(mat_dir, sd, "band")
        outcar_file = os.path.join(band_dir, "OUTCAR")
        if not os.path.exists(outcar_file):
            print(f"  ⚠️ {sd}/band/OUTCAR 不存在，跳过")
            continue

        # 体积
        vol = get_first_volume(outcar_file)
        ln_vol = round(math.log(vol), 4) if vol else "NaN"

        # 核心能量
        core_energy = get_min_1s_core(outcar_file)
        if core_energy is None:
            core_energy = "NaN"

        # VBM / CBM 能量
        vbm_energy = get_band_energy(outcar_file, vbm_kpt, vbm_band)
        cbm_energy = get_band_energy(outcar_file, cbm_kpt, cbm_band)

        vbm_core_diff = round(vbm_energy - core_energy, 4) if vbm_energy not in [None,"NaN"] else "NaN"
        cbm_core_diff = round(cbm_energy - core_energy, 4) if cbm_energy not in [None,"NaN"] else "NaN"

        # 写入 CSV
        with open(output_file, "a", newline="") as fcsv:
            writer = csv.writer(fcsv)
            writer.writerow([mat, sd, ln_vol, vbm_core_diff, cbm_core_diff, vbm_energy, cbm_energy, core_energy])

        print(f"  ✅ {sd}/band 已提取")

print(f"\n🎉 共处理 {processed} 个材料，结果已保存至 {output_file}")

