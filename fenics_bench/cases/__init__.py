"""Benchmark case registry."""

from .flow import (
    ChannelFlowProblem,
    ObstacleFlowProblem,
    SingleCylinderProblem,
    TandemCylinderProblem,
)
from .heat import HeatProblem
from .poisson import PoissonProblem

CASE_REGISTRY = {
    "poisson": PoissonProblem,
    "heat": HeatProblem,
    "channel_flow": ChannelFlowProblem,
    "obstacle_flow": ObstacleFlowProblem,
    "single_cylinder": SingleCylinderProblem,
    "tandem_cylinder": TandemCylinderProblem,
}

__all__ = [
    "CASE_REGISTRY",
    "PoissonProblem",
    "HeatProblem",
    "ChannelFlowProblem",
    "ObstacleFlowProblem",
    "SingleCylinderProblem",
    "TandemCylinderProblem",
]
