#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

REACHED_KEY = "Elapsed time"

BASE_DIR = Path(__file__).resolve().parent
DP_DIR = BASE_DIR / "DP"


def check_mat(mat):

    path = DP_DIR / mat / "opt"
    outcar = path / "OUTCAR"

    # 没有 OUTCAR
    if not outcar.exists():
        print(f"\n🔧 材料: {mat}")
        print("  ❌ OPT : 没有 OUTCAR")
        return

    # 检查是否正常结束
    with open(outcar, "r", errors="ignore") as f:
        content = f.read()

    if REACHED_KEY not in content:
        print(f"\n🔧 材料: {mat}")
        print("  ❌ OPT : OUTCAR存在但没有 Elapsed time")


def main():

    if not DP_DIR.exists():
        print("❌ 没有找到 DP 目录")
        return

    mats = sorted(d for d in os.listdir(DP_DIR) if os.path.isdir(DP_DIR / d))

    for m in mats:
        check_mat(m)


if __name__ == "__main__":
    main()