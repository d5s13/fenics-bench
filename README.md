# fenics_bench

用 Python 包起来的几块 FEniCS 算例：泊松、一维热传导、压力驱动通道流、带障碍物的通道、单圆柱和串列双圆柱绕流。公共部分（建网格、函数空间、边界、求解、算误差或通量、写文件）走同一套模板方法，弱形式仍写在各个问题类里，改方程时对着数学式改代码即可。

算例名在命令行里用英文键：`poisson`、`heat`、`channel_flow`、`obstacle_flow`、`single_cylinder`、`tandem_cylinder`。

## 依赖

- Python 3 能 `import fenics`（本文代码按旧版 `fenics` 包写的，不是 dolfinx）。
- 凡是用 `mshr` 做几何的算例要能 `import mshr`。
- `pip install -r requirements.txt` 装 `numpy`；其余随 FEniCS 环境走。

Linux 上装 FEniCS 按官方文档即可。Windows 本机直接装 legacy FEniCS 比较麻烦，常见做法是在 WSL2 里装 Ubuntu 再装 FEniCS，或直接用带 FEniCS 的 Docker 镜像。

装好后建议先跑：

```
python -c "import fenics, numpy"
python -c "import mshr"
```

第二行若打算跑圆柱、障碍物再测。

## 仓库里有什么

```
fenics_bench/          包：core（基类、指标）、cases（各算例）
examples/run_case.py   命令行入口
requirements.txt
```

使用或调试时请在**本仓库根目录**打开终端（能看到 `fenics_bench` 和 `examples` 两个文件夹的那一层），这样 `run_case.py` 里往 `sys.path` 塞的根路径才对。

## 命令行用法

```
python examples/run_case.py <算例名> [选项...]
python examples/run_case.py -h
```

常用选项（名字和 `run_case.py` 里 argparse 一致，缺省值以源码为准）：

| 选项 | 作用 |
|------|------|
| `--output-dir` | 输出目录，默认 `outputs` |
| `--n` | 标量网格分段数；有的流动里也会当分辨率用 |
| `--resolution` | mshr 相关流动的剖分参数 |
| `--nx` `--ny` | 矩形结构化网格两个方向的单元数 |
| `--dt` `--t-end` `--steps` | 时间步长、结束时刻、步数；只给 `dt` 和 `t-end` 时会反推步数 |
| `--rho` `--mu` | 密度、动力黏度 |
| `--pressure-in` `--pressure-out` | 压力驱动通道进出口压力 |
| `--inlet-velocity` | 速度入口大小 |
| `--radius` `--secondary-radius` | 主圆柱半径、双柱算例里第二根柱半径 |
| `--param 键=值` | 额外参数；值按 JSON 解析，可重复写多次 |

例如泊松里把参考级数项数改成 12：

```
python examples/run_case.py poisson --n 32 --param reference_terms=12
```

## 各算例一句话

**poisson**  
单位正方形、四周齐次 Dirichlet，源项默认常数 1；参考解是截断的双重正弦级数，可调 `reference_terms`。终端里会打 `l2_error`、`h1_error`。

```
python examples/run_case.py poisson --n 32
```

**heat**  
区间 [0,1] 上一维热方程，向后欧拉，初值 sin(πx)，两端温度 0。可调 `n`、`dt`、`t-end`，扩散系数默认 1，键名 `alpha`，要用 `--param alpha=0.5` 这种形式改。

```
python examples/run_case.py heat --n 80 --dt 0.05 --t-end 0.5
```

**channel_flow**  
方腔里的压力驱动通道流，IPCS 分裂、Taylor–Hood 元。默认算一段时间再看场和诊断量。

```
python examples/run_case.py channel_flow --resolution 32 --steps 500 --t-end 10
```

**obstacle_flow**  
通道里抠掉障碍物，几何走 mshr，其余和通道流同一套求解思路。

```
python examples/run_case.py obstacle_flow --resolution 32 --steps 500 --t-end 10
```

**single_cylinder**、**tandem_cylinder**  
槽道里一根或两根圆柱，入口定速度、出口定压力那一类边界在 `fenics_bench/cases/flow.py` 里写好了；监测点坐标、圆心、半径等都在 `parameters` 里读，命令行能直接给的已经挂成选项，其余用 `--param` 跟源码里的键名对齐即可。分辨率和步数一大就算得久，先从小一点的 `resolution`、`steps` 试起。

```
python examples/run_case.py single_cylinder --resolution 80 --mu 0.0025 --steps 5000 --t-end 15
python examples/run_case.py tandem_cylinder --radius 0.08 --secondary-radius 0.04 --resolution 80 --steps 5000 --t-end 15
```

## 跑完之后

标准输出里会有算例名、数值指标（浮点科学计数）、以及 `artifacts` 字典里每个输出文件的路径。具体写出哪些图、csv 看各算例的 `postprocess` 实现。`--output-dir` 下会建子目录；同一目录反复跑可能覆盖旧文件，需要留档就自己换输出路径。

## 当库用

```python
from fenics_bench.cases import PoissonProblem

p = PoissonProblem(parameters={"n": 32}, output_dir="my_out")
r = p.run()
print(r.metrics)
print(r.artifacts)
```

加新算例：子类化 `fenics_bench.core.problem.FenicsProblem`，把 `build_mesh`、`build_spaces`、`solve`、`evaluate` 等按需要实现，最后在 `fenics_bench/cases/__init__.py` 的 `CASE_REGISTRY` 里挂一个字符串名字。

## 许可证

仓库根目录默认没有 LICENSE 文件；要对外发布的话自己选一个协议放上即可。
