"""Core abstractions used by all benchmark cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union


@dataclass
class BenchmarkResult:
    """Container for numerical fields, metrics and generated files."""

    name: str
    fields: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    artifacts: Dict[str, Path] = field(default_factory=dict)

    def summary(self) -> Dict[str, float]:
        return dict(self.metrics)


class FenicsProblem:
    """Template method for a FEniCS finite-element benchmark.

    Subclasses only describe the mathematical problem: mesh, function spaces,
    boundary conditions, variational forms and diagnostics. The execution order
    remains fixed, which makes different PDE cases comparable.
    """

    name = "fenics_problem"

    def __init__(
        self,
        parameters: Optional[Mapping[str, Any]] = None,
        output_dir: Union[str, Path] = "outputs",
    ) -> None:
        self.parameters: Dict[str, Any] = dict(parameters or {})
        self.output_dir = Path(output_dir)
        self.mesh: Any = None
        self.spaces: Dict[str, Any] = {}
        self.boundaries: Dict[str, Any] = {}
        self.solution: Dict[str, Any] = {}

    def setup(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mesh = self.build_mesh()
        self.spaces = self.build_spaces()
        self.boundaries = self.build_boundaries()

    def run(self) -> BenchmarkResult:
        self.setup()
        self.solution = self.solve()
        metrics = self.evaluate(self.solution)
        artifacts = self.postprocess(self.solution)
        return BenchmarkResult(
            name=self.name,
            fields=self.solution,
            metrics=metrics,
            artifacts=artifacts,
        )

    def build_mesh(self) -> Any:
        raise NotImplementedError

    def build_spaces(self) -> Dict[str, Any]:
        raise NotImplementedError

    def build_boundaries(self) -> Dict[str, Any]:
        return {}

    def solve(self) -> Dict[str, Any]:
        raise NotImplementedError

    def evaluate(self, solution: Mapping[str, Any]) -> Dict[str, float]:
        return {}

    def postprocess(self, solution: Mapping[str, Any]) -> Dict[str, Path]:
        return {}
