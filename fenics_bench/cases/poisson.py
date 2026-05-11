"""Poisson benchmark with homogeneous Dirichlet boundaries."""

from __future__ import annotations

import math
from typing import Any, Dict, Mapping, Optional

from fenics_bench.core.metrics import h1_error, l2_error
from fenics_bench.core.problem import FenicsProblem


class PoissonProblem(FenicsProblem):
    name = "poisson"

    def build_mesh(self) -> Any:
        from fenics import UnitSquareMesh

        n = int(self.parameters.get("n", 32))
        return UnitSquareMesh(n, n)

    def build_spaces(self) -> Dict[str, Any]:
        from fenics import FunctionSpace

        return {"scalar": FunctionSpace(self.mesh, "P", 1)}

    def build_boundaries(self) -> Dict[str, Any]:
        from fenics import Constant, DirichletBC

        V = self.spaces["scalar"]
        return {
            "dirichlet": DirichletBC(V, Constant(0.0), "on_boundary"),
        }

    def solve(self) -> Dict[str, Any]:
        from fenics import Constant, Expression, Function, TestFunction, TrialFunction, dot, dx, grad, solve

        V = self.spaces["scalar"]
        u = TrialFunction(V)
        v = TestFunction(V)
        uh = Function(V)
        if "source_expression" in self.parameters:
            f = Expression(
                str(self.parameters["source_expression"]),
                degree=int(self.parameters.get("source_degree", 4)),
            )
        else:
            f = Constant(float(self.parameters.get("source", 1.0)))
        a = dot(grad(u), grad(v)) * dx
        L = f * v * dx
        solve(a == L, uh, self.boundaries["dirichlet"])
        return {"u": uh}

    def evaluate(self, solution: Mapping[str, Any]) -> Dict[str, float]:
        from fenics import Expression, interpolate

        V = self.spaces["scalar"]
        reference_expr = self.reference_expression()
        if reference_expr is None:
            return {}
        reference = interpolate(reference_expr, V)
        return {
            "l2_error": l2_error(solution["u"], reference),
            "h1_error": h1_error(solution["u"], reference),
        }

    def reference_expression(self) -> Optional[Any]:
        """Return a reference solution consistent with the configured source."""

        from fenics import Expression

        if "reference_expression" in self.parameters:
            return Expression(
                str(self.parameters["reference_expression"]),
                degree=int(self.parameters.get("reference_degree", 5)),
            )

        source = float(self.parameters.get("source", 1.0))
        if "source_expression" in self.parameters or abs(source - 1.0) > 1.0e-14:
            return None

        terms = int(self.parameters.get("reference_terms", 10))
        pieces = []
        for i in range(terms):
            m = 2 * i + 1
            for j in range(terms):
                n = 2 * j + 1
                coeff = 16.0 / (math.pi**4 * m * n * (m * m + n * n))
                pieces.append(
                    f"{coeff:.17g}*sin({m}*pi*x[0])*sin({n}*pi*x[1])"
                )
        return Expression(
            " + ".join(pieces),
            degree=int(self.parameters.get("reference_degree", 8)),
            pi=math.pi,
        )
