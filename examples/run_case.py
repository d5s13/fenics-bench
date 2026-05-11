"""Run a registered benchmark case from the command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fenics_bench.cases import CASE_REGISTRY


def parse_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_param(raw: str) -> Tuple[str, Any]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("parameters must use KEY=VALUE syntax")
    key, value = raw.split("=", 1)
    if not key:
        raise argparse.ArgumentTypeError("parameter key must not be empty")
    return key, parse_value(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a FEniCS benchmark case.")
    parser.add_argument("case", choices=sorted(CASE_REGISTRY))
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--n", type=int, help="mesh resolution for scalar cases")
    parser.add_argument("--resolution", type=int, help="mshr/flow mesh resolution")
    parser.add_argument("--nx", type=int, help="structured mesh cells in x direction")
    parser.add_argument("--ny", type=int, help="structured mesh cells in y direction")
    parser.add_argument("--dt", type=float, help="time-step size")
    parser.add_argument("--t-end", type=float, dest="t_end", help="final simulation time")
    parser.add_argument("--steps", type=int, help="number of time steps")
    parser.add_argument("--rho", type=float, help="fluid density")
    parser.add_argument("--mu", type=float, help="dynamic viscosity")
    parser.add_argument("--pressure-in", type=float, dest="pressure_in", help="inlet pressure")
    parser.add_argument("--pressure-out", type=float, dest="pressure_out", help="outlet pressure")
    parser.add_argument("--inlet-velocity", type=float, dest="inlet_velocity", help="velocity inlet value")
    parser.add_argument("--radius", type=float, help="primary cylinder radius")
    parser.add_argument("--secondary-radius", type=float, dest="secondary_radius", help="secondary cylinder radius")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        type=parse_param,
        metavar="KEY=VALUE",
        help="additional JSON-parsed parameter, for example --param reference_terms=12",
    )
    args = parser.parse_args()

    parameters: Dict[str, Any] = {}
    for key in (
        "n",
        "resolution",
        "nx",
        "ny",
        "dt",
        "t_end",
        "steps",
        "rho",
        "mu",
        "pressure_in",
        "pressure_out",
        "inlet_velocity",
        "radius",
        "secondary_radius",
    ):
        value = getattr(args, key)
        if value is not None:
            parameters[key] = value
    for key, value in args.param:
        parameters[key] = value

    problem = CASE_REGISTRY[args.case](parameters=parameters, output_dir=args.output_dir)
    try:
        result = problem.run()
    except ModuleNotFoundError as exc:
        if exc.name in {"fenics", "mshr"}:
            parser.exit(
                2,
                f"Missing dependency '{exc.name}'. Run this command inside a FEniCS/mshr environment.\n",
            )
        raise
    print(result.name)
    for key, value in result.summary().items():
        print(f"{key}: {value:.6e}")
    for key, path in result.artifacts.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
