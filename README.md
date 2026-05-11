# fenics_bench

面向 FEniCS 的统一有限元算例接口（泊松、热传导、不可压缩通道流、障碍物流、单柱与双柱绕流等）。与学位论文中「统一求解框架」的代码部分对应；**本仓库仅含程序，不含 LaTeX 论文**。

## 环境要求

- Python 3.8+（与当前 FEniCS 发行版一致即可）
- **FEniCS**（`import fenics`）
- 含 **CSG 几何** 的算例需要 **mshr**（`import mshr`）
- `pip install -r requirements.txt` 安装 `numpy` 等；FEniCS / mshr 请按[官方文档](https://fenicsproject.org/download/)在目标系统上安装

## 目录说明

| 路径 | 含义 |
|------|------|
| `fenics_bench/` | 核心：`FenicsProblem`、指标函数与各算例问题类 |
| `examples/run_case.py` | 命令行入口，按注册表启动算例 |

更细的接口说明见 `fenics_bench/README.md`（英文）。

## 使用示例

在**仓库根目录**执行（保证 `fenics_bench` 可被导入）：

```bash
python examples/run_case.py poisson --n 32
python examples/run_case.py heat --n 80 --dt 0.05 --t-end 0.5
python examples/run_case.py channel_flow --resolution 32 --steps 500 --t-end 10
python examples/run_case.py single_cylinder --resolution 80 --mu 0.0025 --steps 5000 --t-end 15
```

额外参数示例：

```bash
python examples/run_case.py poisson --param reference_terms=12
python examples/run_case.py tandem_cylinder --radius 0.08 --secondary-radius 0.04
```

## 发布到 GitHub（示例）

在已登录 GitHub 并建好空仓库后，在本目录执行：

```bash
git init
git add .
git commit -m "Initial commit: fenics_bench benchmark framework"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

若远程仓库已包含 README，可先 `git pull origin main --allow-unrelated-histories` 再合并，或 Force 仅适合个人空仓库，请谨慎使用。

## 许可

若你需对外开源，请自行在仓库根目录添加 `LICENSE` 并选择合适协议（如 MIT）。
