# DP Deformation Potential Pipeline

一个用于 VASP 形变势（Deformation Potential, DP）批量计算的自动化流程。

核心功能：
- 按材料自动执行 `opt → scf(多应变) → band(多应变)` 的提交与状态判断。
- 自动准备输入文件（INCAR/KPOINTS/POTCAR/POSCAR）。
- 提取能带关键能量，生成 `band_key_results.csv`。
- 线性拟合得到形变势 `deformation_potential.csv`。
- 提供 SCF 状态检查脚本 `check_scf_status.py`。

## 目录结构
运行前请保证根目录下有以下结构（脚本会自动创建缺失目录）：

```
./
├─ auto.sh
├─ POSCAR/             # 输入结构文件，*.vasp
├─ POSCAR_done/        # 完成后移动到此目录
├─ DP/                 # 计算目录（每个材料一个子目录）
└─ dp_pipeline/        # 脚本与提交逻辑
```

在 `DP/<material>/` 下的结构示例：

```
DP/<material>/
├─ opt/
├─ undef/
│  ├─ scf/
│  └─ band/
├─ 0.01P/
│  ├─ scf/
│  └─ band/
├─ 0.01N/
│  ├─ scf/
│  └─ band/
├─ 0.02P/
│  ├─ scf/
│  └─ band/
└─ 0.02N/
   ├─ scf/
   └─ band/
```

## 依赖环境
- VASP 与集群提交命令 `yhbatch`
- vaspkit（用于 KPOINTS/POTCAR/PRIMCELL/KPATH 等生成）
- Python 3
- Python 库：`numpy`、`pandas`、`scikit-learn`

`auto.sh` 会执行：
- `source ~/.bashrc`
- `module purge`
- `module load vaspkit`

请根据集群环境自行调整模块加载逻辑。

## 快速开始
1. 准备输入结构文件：
   - 放到 `POSCAR/` 下，命名为 `材料名.vasp`。

2. 启动自动流程：

```bash
bash auto.sh
```

脚本会持续循环：
- 从 `POSCAR/` 取前 `N_BATCH` 个材料。
- 依次提交 opt / scf / band。
- 完成后将 `*.vasp` 移动至 `POSCAR_done/`。

## 手动执行（可选）
如果不使用 `auto.sh`，可手动执行：

```bash
# 初始化目录
bash dp_pipeline/mk.sh <material>

# opt
python dp_pipeline/prepare_dp_opt_inputs.py <material>
bash dp_pipeline/submit_dp_opt.sh <material>

# scf
python dp_pipeline/prepare_dp_scf_inputs.py <material>
bash dp_pipeline/submit_dp_scf.sh <material>

# band
python dp_pipeline/prepare_dp_band_inputs.py <material>
bash dp_pipeline/submit_dp_band.sh <material>
```

## 结果提取与形变势计算
在计算完成后执行：

```bash
# 提取能带关键数据
python dp_pipeline/DP.py

# 计算形变势
python dp_pipeline/calc_deformation_potential.py
```

输出文件：
- `band_key_results.csv`：包含各应变下的 `ln(体积)`、`VBM/CBM` 等。
- `deformation_potential.csv`：Ev/Ec 形变势及 R2。

## 可配置项
- `dp_pipeline/auto_calcu.py`
  - `N_BATCH`：每轮提交的材料数。
  - `STRAINS`：应变列表。
  - `REACHED_KEY`：判断完成的 OUTCAR 关键字。

- `dp_pipeline/prepare_dp_opt_inputs.py` / `prepare_dp_scf_inputs.py` / `prepare_dp_band_inputs.py`
  - INCAR 参数与 vaspkit 输入可按需要修改。

## 运行机制说明
- 每个阶段提交后创建锁文件：`opt.lock` / `scf.lock` / `band.lock`。
- 若 OUTCAR 完成且检测到锁文件，会自动删除锁。
- 重新运行脚本会自动跳过已完成或正在运行的任务。

## 常见问题
- `vaspkit` 未加载：请确认模块加载或 PATH 配置。
- `POTCAR` 未生成：检查 `vaspkit 103` 是否可用。
- `KPOINTS` 未生成：检查 `vaspkit 102/303` 是否执行成功。
- `OUTCAR` 不完整：确保 VASP 正常结束并包含 `Elapsed time`。
- 确认所使用的vasp.sh集群脚本，自行在`prepare_dp_opt_inputs.py`里进行修改

## 许可
该项目未包含明确许可协议，如需公开或复用请先确认授权。
