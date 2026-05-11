"""Backward-Euler heat-equation benchmark."""

from __future__ import annotations

from typing import Any, Dict, Mapping

from fenics_bench.core.metrics import l2_error
from fenics_bench.core.problem import FenicsProblem


class HeatProblem(FenicsProblem):
    name = "heat"

    def build_mesh(self) -> Any:
        from fenics import IntervalMesh

        n = int(self.parameters.get("n", 80))
        return IntervalMesh(n, 0.0, 1.0)

    def build_spaces(self) -> Dict[str, Any]:
        from fenics import FunctionSpace

        return {"scalar": FunctionSpace(self.mesh, "P", 1)}

    def build_boundaries(self) -> Dict[str, Any]:
        from fenics import Constant, DirichletBC

        V = self.spaces["scalar"]
        return {"dirichlet": DirichletBC(V, Constant(0.0), "on_boundary")}

    def solve(self) -> Dict[str, Any]:
        from fenics import (
            Constant,
            Expression,
            Function,
            TestFunction,
            TrialFunction,
            dot,
            dx,
            grad,
            interpolate,
            solve,
        )

        V = self.spaces["scalar"]
        alpha = float(self.parameters.get("alpha", 1.0))
        dt = float(self.parameters.get("dt", 0.05))
        t_end = float(self.parameters.get("t_end", 0.5))

        u = TrialFunction(V)
        v = TestFunction(V)
        u_prev = interpolate(Expression("sin(pi*x[0])", degree=3), V)
        uh = Function(V)
        f = Constant(0.0)

        a = u * v * dx + dt * alpha * dot(grad(u), grad(v)) * dx
        L = (u_prev + dt * f) * v * dx

        t = 0.0
        while t < t_end - 1.0e-12:
            solve(a == L, uh, self.boundaries["dirichlet"])
            u_prev.assign(uh)
            t += dt

        return {"u": uh, "time": t}

    def evaluate(self, solution: Mapping[str, Any]) -> Dict[str, float]:
        from fenics import Expression, interpolate

        V = self.spaces["scalar"]
        t = float(solution["time"])
        reference = interpolate(
            Expression("exp(-pi*pi*t)*sin(pi*x[0])", degree=4, t=t),
            V,
        )
        return {"l2_error": l2_error(solution["u"], reference)}
