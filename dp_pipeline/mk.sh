#!/bin/bash
# ==========================================
# 从 POSCAR/*.vasp 自动创建 DP 目录结构
# ==========================================

POSCAR_DIR="./POSCAR"
DP_DIR="./DP"

# 应变目录（不包含 opt）
STRAINS=("undef" "0.01P" "0.01N" "0.02P" "0.02N")
STAGES=("scf" "band")

mkdir -p "$DP_DIR"

# 接收材料名参数
if [ -z "$1" ]; then
    echo "❌ 请提供材料名称，例如: bash mk.sh O"
    exit 1
fi

base_name="$1"
vasp_file="$POSCAR_DIR/$base_name.vasp"

if [ ! -f "$vasp_file" ]; then
    echo "❌ $vasp_file 不存在"
    exit 1
fi

echo ">>> Processing $base_name"

mat_dir="$DP_DIR/$base_name"
mkdir -p "$mat_dir"

# ===== opt：只创建自己 =====
mkdir -p "$mat_dir/opt"

# ===== 其它 strain：有 scf / band =====
for strain in "${STRAINS[@]}"; do
    for stage in "${STAGES[@]}"; do
        mkdir -p "$mat_dir/$strain/$stage"
    done
done

echo ">>> mk.sh completed for $base_name"
