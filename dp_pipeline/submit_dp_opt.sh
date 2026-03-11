#!/bin/bash

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
DP_DIR="${BASE_DIR}/DP"

if [ ! -d "${DP_DIR}" ]; then
    echo "❌ 当前目录下未找到 DP/ 目录"
    exit 1
fi

if [ -z "$1" ]; then
    echo "❌ 请提供材料名，例如: bash submit_dp_opt.sh O"
    exit 1
fi

MAT="$1"
MAT_DIR="${DP_DIR}/${MAT}"
OPT_DIR="${MAT_DIR}/opt"

if [ ! -d "${OPT_DIR}" ]; then
    echo "❌ 材料 opt 目录不存在: ${OPT_DIR}"
    exit 1
fi

if [ ! -f "${OPT_DIR}/vasp.sh" ]; then
    echo "⚠️  缺少 vasp.sh，跳过：${OPT_DIR}"
    exit 1
fi

echo "🚀 提交：${OPT_DIR}"
(cd "${OPT_DIR}" && yhbatch vasp.sh)

echo ""
echo "🎉 submit_dp_opt.sh successfully submitted opt task for ${MAT}."
