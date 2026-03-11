#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="${ROOT_DIR}/dp_pipeline"

if [ ! -d "${PIPELINE_DIR}" ]; then
    echo "❌ 未找到目录: ${PIPELINE_DIR}"
    exit 1
fi

# 保持原脚本不变：在子目录运行，并将数据目录映射到上层
for name in DP POSCAR POSCAR_done; do
    target="${ROOT_DIR}/${name}"
    link="${PIPELINE_DIR}/${name}"

    if [ -L "${link}" ] && [ ! -e "${link}" ]; then
        rm -f "${link}"
    fi

    if [ -e "${target}" ] && [ ! -e "${link}" ]; then
        ln -s "../${name}" "${link}"
    fi
done

source ~/.bashrc
module purge
module load vaspkit

while true
do
    echo "===== $(date) ====="
    (cd "${PIPELINE_DIR}" && python auto_calcu.py)
done
