"""Core building blocks for the FEniCS benchmark interface."""

from .metrics import divergence_l2, h1_error, l2_error, outlet_flux
from .problem import BenchmarkResult, FenicsProblem

__all__ = [
    "BenchmarkResult",
    "FenicsProblem",
    "l2_error",
    "h1_error",
    "divergence_l2",
    "outlet_flux",
]
