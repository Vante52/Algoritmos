#!/usr/bin/env python3
"""Command-line entry point for the N-Queens genetic algorithm."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import replace
from pathlib import Path

from nqueens_ga import GAConfig, GeneticAlgorithm, GeneticResult


def build_parser() -> argparse.ArgumentParser:
    """@brief Define the public command-line interface and its defaults."""

    parser = argparse.ArgumentParser(
        description="Solve scalable N-Queens with a permutation genetic algorithm."
    )
    parser.add_argument("n", type=int, nargs="?", default=8, help="number of queens")
    parser.add_argument(
        "--no-gui", action="store_true", help="run in the terminal without the interface"
    )
    parser.add_argument("--population", type=int, default=240, help="population size")
    parser.add_argument("--generations", type=int, default=5000, help="generation limit")
    parser.add_argument("--mutation", type=float, default=0.35, help="swap mutation rate")
    parser.add_argument("--crossover", type=float, default=0.95, help="OX crossover rate")
    parser.add_argument("--elite", type=int, default=8, help="elite individuals retained")
    parser.add_argument("--tournament", type=int, default=5, help="tournament size")
    parser.add_argument("--seed", type=int, default=None, help="reproducible random seed")
    parser.add_argument(
        "--history-csv", type=Path, help="write generation metrics to a CSV file"
    )
    parser.add_argument(
        "--benchmark",
        type=int,
        nargs="+",
        metavar="N",
        help="run terminal experiments for one or more board sizes",
    )
    return parser


def print_result(n: int, result: GeneticResult) -> None:
    """@brief Print final genotype, cost, fitness, and timing metrics."""

    print(f"N = {n}")
    print(f"Genotype (rows 1..N): {list(result.one_based_genotype)}")
    print(f"Final cost (diagonal attacking pairs): {result.cost}")
    print(f"Final fitness: {1 / (1 + result.cost):.6f}")
    print(f"Generations: {result.generations}")
    print(f"Execution time: {result.elapsed_seconds:.6f} seconds")
    print(f"Stop condition reached: {'yes' if result.solved else 'no'}")


def export_history(path: Path, result: GeneticResult) -> None:
    """@brief Persist convergence data for external analysis or plotting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["generation", "best_cost", "average_cost", "fitness", "elapsed_seconds"]
        )
        for snapshot in result.history:
            writer.writerow(
                [
                    snapshot.generation,
                    snapshot.best_cost,
                    f"{snapshot.average_cost:.6f}",
                    f"{snapshot.fitness:.8f}",
                    f"{snapshot.elapsed_seconds:.8f}",
                ]
            )


def solve_terminal(n: int, config: GAConfig) -> GeneticResult:
    """@brief Execute one non-interactive experiment."""

    result = GeneticAlgorithm(n, config).solve()
    print_result(n, result)
    return result


def main(argv: list[str] | None = None) -> int:
    """@brief Parse parameters and select GUI, terminal, or benchmark mode."""

    args = build_parser().parse_args(argv)
    config = GAConfig(
        population_size=args.population,
        max_generations=args.generations,
        crossover_rate=args.crossover,
        mutation_rate=args.mutation,
        elite_count=args.elite,
        tournament_size=args.tournament,
        seed=args.seed,
    )

    try:
        if args.benchmark:
            for index, n in enumerate(args.benchmark):
                if index:
                    print()
                # Offset fixed seeds so each benchmark is reproducible but independent.
                run_config = replace(
                    config, seed=None if config.seed is None else config.seed + index
                )
                solve_terminal(n, run_config)
            return 0

        display_available = bool(os.environ.get("DISPLAY") or sys.platform in ("win32", "darwin"))
        if args.no_gui or not display_available:
            result = solve_terminal(args.n, config)
            if args.history_csv:
                export_history(args.history_csv, result)
                print(f"Convergence history: {args.history_csv}")
            return 0 if result.solved else 1

        from nqueens_ga.gui import launch

        launch(args.n, config)
        return 0
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
