# fenics_bench

用 Python 包起来的几块 FEniCS 算例：泊松方程、一维热传导、压力驱动通道流、带障碍物的通道流、单圆柱绕流和串列双圆柱绕流。公共步骤（建网格 → 函数空间 → 边界条件 → 求解 → 指标计算 → 结果输出）走同一套模板方法，弱形式仍写在各个问题类里，数学式和代码之间的对应关系可以直接对照。

## 安装 FEniCS

FEniCS 无法通过 pip 安装，需按系统选择对应方式：

**Ubuntu（官方 PPA）**
```bash
curl -s https://fenicsproject.org/releases.key | sudo apt-key add -
sudo add-apt-repository "deb https://ppa.launchpadcontent.net/fenics-packages/fenics/ubuntu focal main"
sudo apt update && sudo apt install -y fenics
```

**Docker（适合 Windows/macOS）**
```bash
docker pull fenicsproject/stable
docker run -it fenicsproject/stable bash
```
容器里拉代码进去跑，或者把本地目录 mount 进去。

**WSL2 + Ubuntu（Windows）**
先装 WSL2，再在 Ubuntu 里按上面 Ubuntu 的步骤装。

装好之后验证：
```bash
python -c "import fenics; print(fenics.__version__)"
```
能打出版本号就算 OK。

带几何的算例（圆柱、障碍物）还需要 mshr，通常随 fenics 一起装进来，如果没有再单独：
```bash
sudo apt install fenics-mshr
```

本项目依赖 `numpy`，单独装：
```bash
pip install -r requirements.txt
```

## 仓库结构

```
fenics_bench/
    core/
        problem.py    FenicsProblem 基类和 BenchmarkResult
        metrics.py    误差、散度、通量等指标函数
    cases/
        poisson.py    泊松方程
        heat.py       一维热传导
        flow.py       通道流、障碍物流、圆柱绕流（共用 IPCS + Taylor–Hood）
        __init__.py   CASE_REGISTRY 算例注册表
    __init__.py
examples/
    run_case.py       命令行入口
requirements.txt
```

使用前先 `cd` 到仓库根目录（能同时看到 `fenics_bench` 和 `examples` 的那一层），这样 `run_case.py` 里的路径引用才能正常工作。

## 快速开始

```bash
python examples/run_case.py -h
```

常用选项：

| 选项 | 说明 |
|------|------|
| `--n` | 标量算例网格分段数 |
| `--resolution` | mshr 相关流动的剖分密度 |
| `--dt` `--t-end` `--steps` | 时间步长、终止时刻、总步数 |
| `--rho` `--mu` | 密度、动力黏度 |
| `--param 键=值` | 任意参数，值按 JSON 解析，可写多次 |

### 六个算例

**poisson** — 单位正方形、齐次 Dirichlet、源项常数 1，参考解用截断双重正弦级数，输出 `l2_error` 和 `h1_error`：
```bash
python examples/run_case.py poisson --n 32
```

**heat** — 区间 [0,1] 一维热传导，向后欧拉时间推进，初值 sin(πx)：
```bash
python examples/run_case.py heat --n 80 --dt 0.05 --t-end 0.5
```

**channel_flow** — 方腔压力驱动通道流，IPCS + Taylor–Hood：
```bash
python examples/run_case.py channel_flow --resolution 32 --steps 500 --t-end 10
```

**obstacle_flow** — 通道内挖障碍物，几何走 mshr，其余与 channel_flow 共用：
```bash
python examples/run_case.py obstacle_flow --resolution 32 --steps 500 --t-end 10
```

**single_cylinder** — 槽道单圆柱绕流，可调黏性系数和圆柱半径：
```bash
python examples/run_case.py single_cylinder --resolution 80 --mu 0.0025 --steps 5000 --t-end 15
```

**tandem_cylinder** — 串列双圆柱，第二根半径可单独指定：
```bash
python examples/run_case.py tandem_cylinder --radius 0.08 --secondary-radius 0.04 --resolution 80 --steps 5000 --t-end 15
```

### 跑出来什么样

成功运行后终端打印大致如下（以 poisson 为例）：

```
poisson
l2_error: 9.790000e-04
h1_error: 4.557000e-03
```

流动算例会多打散度、通量或频谱相关指标，以及 `artifacts` 里输出文件的路径。

`--output-dir` 默认为 `outputs`，会在其下建子目录写入图像或 CSV 文件。同目录反复跑会覆盖旧结果，需要备份请换输出目录或手动备份。

## 扩展方式

本项目的核心是 `fenics_bench.core.problem.FenicsProblem`，子类只需要描述数学部分，不需要改动执行流程。

新增算例的步骤：

1. 写一个新类继承 `FenicsProblem`；
2. 实现五个方法：`build_mesh`、`build_spaces`、`build_boundaries`（可不写）、`solve`、`evaluate`；
3. 在 `fenics_bench/cases/__init__.py` 的 `CASE_REGISTRY` 里加一条名字到类的映射；
4. 命令行里就能用新名字直接启动，不需要改入口脚本。

各方法里的 `self.parameters` 字典包含了从 `run_case.py` 传进来的所有命令行参数，子类自己决定用哪些键、给哪些设默认值。

## 在代码里引用

```python
from fenics_bench.cases import PoissonProblem

p = PoissonProblem(parameters={"n": 64}, output_dir="my_out")
result = p.run()
print(result.summary())
```

`BenchmarkResult` 包含三个字段：
- `fields`：FEniCS 函数对象（速度场、压力场等）
- `metrics`：字典，键如 `l2_error`、`divergence_l2`、`outlet_flux`
- `artifacts`：字典，值是 Path，指向输出的图像或数据文件

## 许可证

未附带许可证文件。如需开源请自行添加 `LICENSE` 并选择协议。