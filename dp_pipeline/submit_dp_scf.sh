#!/bin/bash

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
DP_DIR="${BASE_DIR}/DP"

if [ ! -d "${DP_DIR}" ]; then
    echo "❌ 当前目录下未找到 DP/ 目录"
    exit 1
fi

# 支持传入材料名
if [ -z "$1" ]; then
    echo "❌ 请提供材料名，例如: bash submit_dp_scf.sh O"
    exit 1
fi

MAT="$1"
MAT_DIR="${DP_DIR}/${MAT}"

if [ ! -d "${MAT_DIR}" ]; then
    echo "❌ 材料目录不存在: ${MAT_DIR}"
    exit 1
fi

STRAINS=("undef" "0.01P" "0.01N" "0.02P" "0.02N")
submitted=0
skipped=0

for strain in "${STRAINS[@]}"; do
    SCF_DIR="${MAT_DIR}/${strain}/scf"

    [ -d "$SCF_DIR" ] || continue

    if [ -f "${SCF_DIR}/OUTCAR" ]; then
        echo "⏭️  跳过（已有 OUTCAR）：${SCF_DIR}"
        skipped=$((skipped + 1))
        continue
    fi

    if [ ! -f "${SCF_DIR}/vasp.sh" ]; then
        echo "⚠️  缺少 vasp.sh，跳过：${SCF_DIR}"
        continue
    fi

    echo "🚀 提交：${SCF_DIR}"
    (cd "${SCF_DIR}" && yhbatch vasp.sh)

    submitted=$((submitted + 1))
    sleep 0.2
done

echo ""
echo "🎉 submit_dp_scf.sh 完成："

echo "   submit_dp_scf.sh successfully submitted ${submitted} scf tasks in DP."

