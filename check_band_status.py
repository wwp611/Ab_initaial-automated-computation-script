#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

STRAINS = ["undef", "0.01P", "0.01N", "0.02P", "0.02N"]
REACHED_KEY = "Elapsed time"

BASE_DIR = Path(__file__).resolve().parent
DP_DIR = BASE_DIR / "DP"


def check_mat(mat):

    unfinished = []

    for sd in STRAINS:

        path = DP_DIR / mat / sd / "band"
        outcar = path / "OUTCAR"

        if not outcar.exists():
            unfinished.append((sd, "没有 OUTCAR"))
            continue

        with open(outcar, "r", errors="ignore") as f:
            content = f.read()

        if REACHED_KEY not in content:
            unfinished.append((sd, "OUTCAR存在但没有 Elapsed time"))

    # 如果有未完成才打印
    if unfinished:
        print(f"\n🔧 材料: {mat}")
        print("未完成 strain：")

        for sd, reason in unfinished:
            print(f"  ❌ {sd} : {reason}")


def main():

    mats = [d for d in os.listdir(DP_DIR) if os.path.isdir(DP_DIR / d)]

    for m in mats:
        check_mat(m)


if __name__ == "__main__":
    main()