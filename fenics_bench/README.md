# fenics_bench

`fenics_bench` is a lightweight reusable interface for the FEniCS benchmark
cases in this thesis. It separates a numerical experiment into mesh generation,
function-space construction, boundary management, variational solving,
evaluation and postprocessing.

## Design Goals

- Keep weak forms close to their mathematical expressions.
- Reuse the same execution pipeline across scalar and flow problems.
- Report metrics with consistent names, such as `l2_error`, `h1_error`,
  `divergence_l2`, `outlet_flux` and `probe_frequency`.
- Make it possible to add a new case by subclassing `FenicsProblem`.

## Example

```bash
python examples/run_case.py poisson --n 32
python examples/run_case.py heat --n 80 --dt 0.05 --t-end 0.5
python examples/run_case.py channel_flow --resolution 32 --steps 500 --t-end 10
python examples/run_case.py single_cylinder --resolution 80 --mu 0.0025 --steps 5000 --t-end 15
```

All commands must be run in an environment that provides the legacy FEniCS
Python package. Cases with CSG geometry also require `mshr`.

Additional parameters can be passed without changing the runner:

```bash
python examples/run_case.py poisson --param reference_terms=12
python examples/run_case.py tandem_cylinder --radius 0.08 --secondary-radius 0.04
```

## Extension Pattern

To add a new benchmark, create a subclass of `FenicsProblem` and implement:

1. `build_mesh`
2. `build_spaces`
3. `build_boundaries`
4. `solve`
5. `evaluate`
6. `postprocess`

The current prototype implements the engineering abstraction behind Poisson,
heat-conduction, pressure-driven channel-flow, obstacle-flow, single-cylinder
and tandem-cylinder benchmarks. Scalar cases use exact or truncated-reference
solutions for error norms. Flow cases share IPCS time stepping, Taylor-Hood
velocity-pressure spaces, boundary markers, divergence/flux diagnostics, and
optional probe-frequency extraction.
