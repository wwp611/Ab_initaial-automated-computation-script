#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

STRAINS = ["undef", "0.01P", "0.01N", "0.02P", "0.02N"]
REACHED_KEY = "Elapsed time"

BASE_DIR = Path(__file__).resolve().parent
DP_DIR = BASE_DIR / "DP"


def check_mat(mat):
    print(f"\n🔍 检查材料: {mat}")

    all_done = True

    for sd in STRAINS:

        path = DP_DIR / mat / sd / "scf"
        outcar = path / "OUTCAR"

        if not outcar.exists():
            print(f"❌ {sd} : 没有 OUTCAR")
            all_done = False
            continue

        with open(outcar, "r", errors="ignore") as f:
            content = f.read()

        if REACHED_KEY in content:
            print(f"✅ {sd} : 完成")
        else:
            print(f"⚠️  {sd} : OUTCAR存在但没有 Elapsed time")
            all_done = False

    if all_done:
        print("\n🎉 所有 SCF 已完成")
    else:
        print("\n🚨 SCF 未全部完成")


def main():

    mats = [d for d in os.listdir(DP_DIR) if os.path.isdir(DP_DIR / d)]

    for m in mats:
        check_mat(m)


if __name__ == "__main__":
    main()