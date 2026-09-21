"""Genetic algorithm and user interface for the scalable N-Queens problem."""

from .algorithm import (
    GAConfig,
    GeneticAlgorithm,
    GeneticResult,
    MutationSnapshot,
    ProgressSnapshot,
)

__all__ = [
    "GAConfig",
    "GeneticAlgorithm",
    "GeneticResult",
    "MutationSnapshot",
    "ProgressSnapshot",
]
