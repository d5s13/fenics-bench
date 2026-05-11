"""Reusable IPCS-based incompressible-flow benchmarks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from fenics_bench.core.metrics import divergence_l2, outlet_flux
from fenics_bench.core.problem import FenicsProblem


Point2D = Tuple[float, float]


@dataclass
class FlowParameters:
    rho: float = 1.0
    mu: float = 1.0
    t_end: float = 10.0
    steps: int = 500
    pressure_in: float = 8.0
    pressure_out: float = 0.0
    inlet_velocity: float = 1.0

    @property
    def dt(self) -> float:
        return self.t_end / self.steps


class IPCSFlowProblem(FenicsProblem):
    """Base class for incompressible-flow benchmarks.

    The class owns the complete mesh/space/boundary/solve/evaluate lifecycle.
    Subclasses only customize geometry and the pressure-driven or velocity-
    driven boundary setup.
    """

    name = "ipcs_flow"

    INLET = 1
    OUTLET = 2
    WALL = 3
    SOLID = 4

    def flow_parameters(self) -> FlowParameters:
        t_end = float(self.parameters.get("t_end", 10.0))
        if "dt" in self.parameters and "steps" not in self.parameters:
            steps = max(1, round(t_end / float(self.parameters["dt"])))
        else:
            steps = max(1, int(self.parameters.get("steps", 500)))
        return FlowParameters(
            rho=float(self.parameters.get("rho", 1.0)),
            mu=float(self.parameters.get("mu", 1.0)),
            t_end=t_end,
            steps=steps,
            pressure_in=float(self.parameters.get("pressure_in", 8.0)),
            pressure_out=float(self.parameters.get("pressure_out", 0.0)),
            inlet_velocity=float(self.parameters.get("inlet_velocity", 1.0)),
        )

    def length(self) -> float:
        return float(self.parameters.get("length", 1.0))

    def height(self) -> float:
        return float(self.parameters.get("height", 1.0))

    def resolution(self) -> int:
        return int(self.parameters.get("resolution", self.parameters.get("n", 32)))

    def velocity_degree(self) -> int:
        return int(self.parameters.get("velocity_degree", 2))

    def pressure_degree(self) -> int:
        return int(self.parameters.get("pressure_degree", 1))

    def uses_velocity_inlet(self) -> bool:
        return False

    def uses_pressure_inlet(self) -> bool:
        return True

    def obstacle_specs(self) -> Sequence[Mapping[str, Any]]:
        return ()

    def cylinder_specs(self) -> Sequence[Mapping[str, Any]]:
        return ()

    def has_solid_boundaries(self) -> bool:
        return bool(self.obstacle_specs() or self.cylinder_specs())

    def probe_point(self) -> Optional[Point2D]:
        return None

    def build_mesh(self) -> Any:
        if self.has_solid_boundaries():
            return self._build_csg_mesh()
        return self._build_rectangle_mesh()

    def _build_rectangle_mesh(self) -> Any:
        from fenics import Point, RectangleMesh

        nx = int(self.parameters.get("nx", max(1, round(self.length() * self.resolution()))))
        ny = int(self.parameters.get("ny", max(1, round(self.height() * self.resolution()))))
        return RectangleMesh(Point(0.0, 0.0), Point(self.length(), self.height()), nx, ny)

    def _build_csg_mesh(self) -> Any:
        from fenics import Point
        from mshr import Circle, Rectangle, generate_mesh

        domain = Rectangle(Point(0.0, 0.0), Point(self.length(), self.height()))
        for obstacle in self.obstacle_specs():
            if obstacle.get("type", "circle") == "circle":
                cx, cy = obstacle["center"]
                radius = float(obstacle["radius"])
                segments = int(obstacle.get("segments", 64))
                domain = domain - Circle(Point(float(cx), float(cy)), radius, segments)
            elif obstacle.get("type") == "rectangle":
                x0, y0 = obstacle["lower_left"]
                x1, y1 = obstacle["upper_right"]
                domain = domain - Rectangle(Point(float(x0), float(y0)), Point(float(x1), float(y1)))
            else:
                raise ValueError(f"Unsupported obstacle type: {obstacle.get('type')}")

        for cylinder in self.cylinder_specs():
            cx, cy = cylinder["center"]
            radius = float(cylinder["radius"])
            segments = int(cylinder.get("segments", 96))
            domain = domain - Circle(Point(float(cx), float(cy)), radius, segments)

        return generate_mesh(domain, self.resolution())

    def build_spaces(self) -> Dict[str, Any]:
        from fenics import FunctionSpace, VectorFunctionSpace

        return {
            "velocity": VectorFunctionSpace(self.mesh, "P", self.velocity_degree()),
            "pressure": FunctionSpace(self.mesh, "P", self.pressure_degree()),
        }

    def build_boundaries(self) -> Dict[str, Any]:
        from fenics import Constant, DirichletBC, FacetNormal, Measure, MeshFunction, SubDomain, near

        outer = self
        tol = float(self.parameters.get("boundary_tolerance", 1.0e-8))

        class Inlet(SubDomain):
            def inside(self, x: Any, on_boundary: bool) -> bool:
                return on_boundary and near(x[0], 0.0, tol)

        class Outlet(SubDomain):
            def inside(self, x: Any, on_boundary: bool) -> bool:
                return on_boundary and near(x[0], outer.length(), tol)

        class Wall(SubDomain):
            def inside(self, x: Any, on_boundary: bool) -> bool:
                return on_boundary and (
                    near(x[1], 0.0, tol) or near(x[1], outer.height(), tol)
                )

        class Solid(SubDomain):
            def inside(self, x: Any, on_boundary: bool) -> bool:
                return on_boundary and outer._is_solid_boundary(x, tol)

        markers = MeshFunction("size_t", self.mesh, self.mesh.topology().dim() - 1)
        markers.set_all(0)
        Wall().mark(markers, self.WALL)
        Inlet().mark(markers, self.INLET)
        Outlet().mark(markers, self.OUTLET)
        if self.has_solid_boundaries():
            Solid().mark(markers, self.SOLID)

        V = self.spaces["velocity"]
        Q = self.spaces["pressure"]
        zero_velocity = Constant((0.0, 0.0))
        bcu = [DirichletBC(V, zero_velocity, markers, self.WALL)]
        if self.has_solid_boundaries():
            bcu.append(DirichletBC(V, zero_velocity, markers, self.SOLID))
        if self.uses_velocity_inlet():
            inflow = Constant((self.flow_parameters().inlet_velocity, 0.0))
            bcu.append(DirichletBC(V, inflow, markers, self.INLET))

        bcp = [DirichletBC(Q, Constant(self.flow_parameters().pressure_out), markers, self.OUTLET)]
        if self.uses_pressure_inlet():
            bcp.append(DirichletBC(Q, Constant(self.flow_parameters().pressure_in), markers, self.INLET))

        return {
            "markers": markers,
            "ds": Measure("ds", domain=self.mesh, subdomain_data=markers),
            "normal": FacetNormal(self.mesh),
            "velocity": bcu,
            "pressure": bcp,
            "ids": {
                "inlet": self.INLET,
                "outlet": self.OUTLET,
                "wall": self.WALL,
                "solid": self.SOLID,
            },
        }

    def _is_solid_boundary(self, x: Any, tol: float) -> bool:
        for obstacle in self.obstacle_specs():
            if obstacle.get("type", "circle") == "circle":
                if self._near_circle(x, obstacle["center"], float(obstacle["radius"]), tol):
                    return True
            elif obstacle.get("type") == "rectangle":
                if self._near_rectangle(x, obstacle["lower_left"], obstacle["upper_right"], tol):
                    return True
        for cylinder in self.cylinder_specs():
            if self._near_circle(x, cylinder["center"], float(cylinder["radius"]), tol):
                return True
        return False

    @staticmethod
    def _near_circle(x: Any, center: Sequence[float], radius: float, tol: float) -> bool:
        dx = float(x[0]) - float(center[0])
        dy = float(x[1]) - float(center[1])
        return abs((dx * dx + dy * dy) ** 0.5 - radius) <= max(5.0e-3, 20.0 * tol)

    @staticmethod
    def _near_rectangle(
        x: Any,
        lower_left: Sequence[float],
        upper_right: Sequence[float],
        tol: float,
    ) -> bool:
        x0, y0 = map(float, lower_left)
        x1, y1 = map(float, upper_right)
        px, py = float(x[0]), float(x[1])
        on_vertical = (abs(px - x0) <= tol or abs(px - x1) <= tol) and y0 - tol <= py <= y1 + tol
        on_horizontal = (abs(py - y0) <= tol or abs(py - y1) <= tol) and x0 - tol <= px <= x1 + tol
        return on_vertical or on_horizontal

    def solve(self) -> Dict[str, Any]:
        from fenics import (
            Constant,
            Function,
            TestFunction,
            TrialFunction,
            div,
            dot,
            dx,
            grad,
            inner,
            lhs,
            nabla_grad,
            rhs,
            solve,
            sym,
        )

        params = self.flow_parameters()
        V = self.spaces["velocity"]
        Q = self.spaces["pressure"]
        u = TrialFunction(V)
        v = TestFunction(V)
        pressure = TrialFunction(Q)
        q = TestFunction(Q)
        u_n = Function(V)
        u_ = Function(V)
        p_n = Function(Q)
        p_ = Function(Q)

        k = Constant(params.dt)
        rho = Constant(params.rho)
        mu = Constant(params.mu)
        normal = self.boundaries["normal"]
        ds = self.boundaries["ds"]
        force = Constant((0.0, 0.0))

        U = 0.5 * (u_n + u)
        F1 = (
            rho * dot((u - u_n) / k, v) * dx
            + rho * dot(dot(u_n, nabla_grad(u_n)), v) * dx
            + inner(2.0 * mu * sym(nabla_grad(U)), sym(nabla_grad(v))) * dx
            - p_n * div(v) * dx
            + dot(p_n * normal, v) * ds
            - dot(mu * nabla_grad(U) * normal, v) * ds
            - dot(force, v) * dx
        )
        a1, L1 = lhs(F1), rhs(F1)

        a2 = dot(grad(pressure), grad(q)) * dx
        L2 = dot(grad(p_n), grad(q)) * dx - (rho / k) * div(u_) * q * dx

        a3 = dot(u, v) * dx
        L3 = dot(u_, v) * dx - (k / rho) * dot(grad(p_ - p_n), v) * dx

        probe = self.probe_point()
        probe_times: List[float] = []
        probe_values: List[float] = []

        for step in range(params.steps):
            solve(a1 == L1, u_, self.boundaries["velocity"])
            solve(a2 == L2, p_, self.boundaries["pressure"])
            solve(a3 == L3, u_)
            u_n.assign(u_)
            p_n.assign(p_)
            if probe is not None:
                self._record_probe(u_, probe, (step + 1) * params.dt, probe_times, probe_values)

        return {
            "velocity": u_,
            "pressure": p_,
            "time": params.t_end,
            "probe_times": probe_times,
            "probe_values": probe_values,
        }

    def _record_probe(
        self,
        velocity: Any,
        probe: Point2D,
        time_value: float,
        times: List[float],
        values: List[float],
    ) -> None:
        from fenics import Point

        try:
            sample = velocity(Point(float(probe[0]), float(probe[1])))
        except RuntimeError:
            return
        times.append(float(time_value))
        values.append(float(sample[1]))

    def evaluate(self, solution: Mapping[str, Any]) -> Dict[str, float]:
        metrics: Dict[str, float] = {
            "divergence_l2": divergence_l2(solution["velocity"]),
            "outlet_flux": outlet_flux(
                solution["velocity"],
                self.boundaries["normal"],
                self.boundaries["ds"],
                self.OUTLET,
            ),
            "velocity_linf": float(solution["velocity"].vector().norm("linf")),
        }
        frequency = self._dominant_frequency(
            solution.get("probe_times", ()),
            solution.get("probe_values", ()),
        )
        if frequency is not None:
            metrics["probe_frequency"] = frequency
        return metrics

    @staticmethod
    def _dominant_frequency(times: Iterable[float], values: Iterable[float]) -> Optional[float]:
        time_list = list(times)
        value_list = list(values)
        if len(time_list) < 4 or len(time_list) != len(value_list):
            return None
        try:
            import numpy as np
        except ImportError:
            return None

        dt = time_list[1] - time_list[0]
        signal = np.asarray(value_list, dtype=float)
        signal = signal - signal.mean()
        spectrum = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(signal.size, d=dt)
        if spectrum.size <= 1:
            return None
        peak = int(np.argmax(spectrum[1:]) + 1)
        return float(freqs[peak])

    def postprocess(self, solution: Mapping[str, Any]) -> Dict[str, Path]:
        artifacts: Dict[str, Path] = {}
        try:
            from fenics import File
        except ImportError:
            return artifacts

        velocity_path = self.output_dir / f"{self.name}_velocity.pvd"
        pressure_path = self.output_dir / f"{self.name}_pressure.pvd"
        File(str(velocity_path)) << solution["velocity"]
        File(str(pressure_path)) << solution["pressure"]
        artifacts["velocity"] = velocity_path
        artifacts["pressure"] = pressure_path

        if solution.get("probe_times"):
            probe_path = self.output_dir / f"{self.name}_probe.csv"
            with probe_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["time", "uy"])
                writer.writerows(zip(solution["probe_times"], solution["probe_values"]))
            artifacts["probe"] = probe_path
        return artifacts


class ChannelFlowProblem(IPCSFlowProblem):
    name = "channel_flow"


class ObstacleFlowProblem(IPCSFlowProblem):
    name = "obstacle_flow"

    def obstacle_specs(self) -> Sequence[Mapping[str, Any]]:
        return self.parameters.get(
            "obstacles",
            (
                {"type": "circle", "center": (0.32, 0.50), "radius": 0.08},
                {"type": "circle", "center": (0.58, 0.28), "radius": 0.06},
                {"type": "rectangle", "lower_left": (0.70, 0.58), "upper_right": (0.82, 0.72)},
            ),
        )


class SingleCylinderProblem(IPCSFlowProblem):
    name = "single_cylinder"

    def length(self) -> float:
        return float(self.parameters.get("length", 5.0))

    def height(self) -> float:
        return float(self.parameters.get("height", 1.0))

    def resolution(self) -> int:
        return int(self.parameters.get("resolution", self.parameters.get("n", 80)))

    def uses_velocity_inlet(self) -> bool:
        return True

    def uses_pressure_inlet(self) -> bool:
        return False

    def flow_parameters(self) -> FlowParameters:
        params = super().flow_parameters()
        if "mu" not in self.parameters:
            params.mu = 0.0025
        if "t_end" not in self.parameters:
            params.t_end = 15.0
        if "steps" not in self.parameters:
            if "dt" in self.parameters:
                params.steps = max(1, round(params.t_end / float(self.parameters["dt"])))
            else:
                params.steps = 5000
        return params

    def cylinder_specs(self) -> Sequence[Mapping[str, Any]]:
        return (
            {
                "center": self.parameters.get("center", (1.0, 0.5)),
                "radius": float(self.parameters.get("radius", 0.08)),
                "segments": int(self.parameters.get("segments", 128)),
            },
        )

    def probe_point(self) -> Optional[Point2D]:
        point = self.parameters.get("probe", (2.4, 0.5))
        return (float(point[0]), float(point[1]))

    def reynolds_number(self) -> float:
        radius = float(self.parameters.get("radius", 0.08))
        velocity = float(self.parameters.get("inlet_velocity", 1.0))
        params = self.flow_parameters()
        return params.rho * velocity * (2.0 * radius) / params.mu

    def evaluate(self, solution: Mapping[str, Any]) -> Dict[str, float]:
        metrics = super().evaluate(solution)
        metrics["reynolds"] = self.reynolds_number()
        return metrics


class TandemCylinderProblem(SingleCylinderProblem):
    name = "tandem_cylinder"

    def cylinder_specs(self) -> Sequence[Mapping[str, Any]]:
        return (
            {
                "center": self.parameters.get("center", (1.0, 0.5)),
                "radius": float(self.parameters.get("radius", 0.08)),
                "segments": int(self.parameters.get("segments", 128)),
            },
            {
                "center": self.parameters.get("secondary_center", (1.85, 0.46)),
                "radius": float(self.parameters.get("secondary_radius", 0.04)),
                "segments": int(self.parameters.get("secondary_segments", 96)),
            },
        )

    def probe_point(self) -> Optional[Point2D]:
        point = self.parameters.get("probe", (2.6, 0.5))
        return (float(point[0]), float(point[1]))

    def secondary_reynolds_number(self) -> float:
        radius = float(self.parameters.get("secondary_radius", 0.04))
        velocity = float(self.parameters.get("inlet_velocity", 1.0))
        params = self.flow_parameters()
        return params.rho * velocity * (2.0 * radius) / params.mu

    def evaluate(self, solution: Mapping[str, Any]) -> Dict[str, float]:
        metrics = super().evaluate(solution)
        metrics["secondary_reynolds"] = self.secondary_reynolds_number()
        return metrics
