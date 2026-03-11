#!/bin/bash

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
DP_DIR="${BASE_DIR}/DP"

if [ ! -d "${DP_DIR}" ]; then
    echo "❌ 当前目录下未找到 DP/ 目录"
    exit 1
fi

if [ -z "$1" ]; then
    echo "❌ 请提供材料名，例如: bash submit_dp_band.sh O"
    exit 1
fi

MAT="$1"
MAT_DIR="${DP_DIR}/${MAT}"

if [ ! -d "${MAT_DIR}" ]; then
    echo "❌ 材料目录不存在: ${MAT_DIR}"
    exit 1
fi

echo "📂 在 DP/${MAT} 提交 band 任务（不检查 OUTCAR）..."

submitted=0

for strain in undef 0.01P 0.01N 0.02P 0.02N; do
    band_dir="${MAT_DIR}/${strain}/band"
    [ -d "$band_dir" ] || continue

    if [ ! -f "${band_dir}/vasp.sh" ]; then
        echo "⚠️  缺少 vasp.sh，跳过：${band_dir}"
        continue
    fi

    echo "🚀 提交：${band_dir}"
    (cd "${band_dir}" && yhbatch vasp.sh)

    submitted=$((submitted + 1))
    sleep 0.2
done

echo ""
echo "🎉 提交完成：submit_dp_band.sh successfully submitted ${submitted} band tasks for ${MAT}."
