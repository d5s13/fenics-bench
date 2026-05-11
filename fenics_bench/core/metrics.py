"""Shared diagnostics for scalar and incompressible-flow cases."""

from __future__ import annotations

from typing import Any


def l2_error(numerical: Any, reference: Any) -> float:
    from fenics import errornorm

    return float(errornorm(reference, numerical, norm_type="L2"))


def h1_error(numerical: Any, reference: Any) -> float:
    from fenics import errornorm

    return float(errornorm(reference, numerical, norm_type="H1"))


def divergence_l2(velocity: Any) -> float:
    from fenics import assemble, div, dx

    return float(assemble(div(velocity) * div(velocity) * dx) ** 0.5)


def outlet_flux(velocity: Any, normal: Any, boundary_measure: Any, marker: int) -> float:
    from fenics import assemble, dot

    return float(assemble(dot(velocity, normal) * boundary_measure(marker)))
