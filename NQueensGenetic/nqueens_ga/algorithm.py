"""Core genetic algorithm for the scalable N-Queens problem."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from statistics import fmean
from threading import Event
from time import perf_counter
from typing import Callable, Sequence


Genotype = tuple[int, ...]
ProgressCallback = Callable[["ProgressSnapshot"], None]


@dataclass(frozen=True, slots=True)
class Individual:
    """@brief A candidate solution represented by a permutation genotype."""

    genotype: Genotype
    cost: int

    @property
    def fitness(self) -> float:
        """@brief Return a maximization fitness derived from the diagonal cost."""

        return 1.0 / (1.0 + self.cost)


@dataclass(frozen=True, slots=True)
class ProgressSnapshot:
    """@brief Immutable phenotype snapshot used by the UI and convergence plot."""

    generation: int
    best_genotype: Genotype
    best_cost: int
    average_cost: float
    fitness: float
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class MutationSnapshot:
    """@brief Trace one applied swap mutation and its arrays of interest."""

    sequence: int
    generation: int
    parent_a: Genotype
    parent_b: Genotype
    child_before: Genotype
    child_after: Genotype
    swapped_columns: tuple[int, int]
    cost_before: int
    cost_after: int


@dataclass(frozen=True, slots=True)
class GeneticResult:
    """@brief Complete outcome of one genetic-algorithm execution."""

    genotype: Genotype
    cost: int
    generations: int
    elapsed_seconds: float
    history: tuple[ProgressSnapshot, ...]
    mutations: tuple[MutationSnapshot, ...] = ()
    stopped_by_user: bool = False

    @property
    def solved(self) -> bool:
        """@brief Indicate whether the phenotype has no diagonal attacks."""

        return self.cost == 0

    @property
    def one_based_genotype(self) -> tuple[int, ...]:
        """@brief Expose row numbers in the human-friendly range 1..N."""

        return tuple(row + 1 for row in self.genotype)


@dataclass(slots=True)
class GAConfig:
    """@brief Tunable parameters kept together to simplify experimentation."""

    population_size: int = 240
    max_generations: int = 5_000
    crossover_rate: float = 0.95
    mutation_rate: float = 0.35
    elite_count: int = 8
    tournament_size: int = 5
    stagnation_limit: int = 120
    immigrant_fraction: float = 0.12
    seed: int | None = None

    def validate(self) -> None:
        """@brief Validate parameter ranges before allocating a population."""

        if self.population_size < 4:
            raise ValueError("population_size must be at least 4")
        if self.max_generations < 1:
            raise ValueError("max_generations must be positive")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise ValueError("crossover_rate must be between 0 and 1")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be between 0 and 1")
        if not 1 <= self.elite_count < self.population_size:
            raise ValueError("elite_count must be in [1, population_size)")
        if not 2 <= self.tournament_size <= self.population_size:
            raise ValueError("tournament_size must be in [2, population_size]")
        if self.stagnation_limit < 1:
            raise ValueError("stagnation_limit must be positive")
        if not 0.0 <= self.immigrant_fraction < 1.0:
            raise ValueError("immigrant_fraction must be in [0, 1)")


class GeneticAlgorithm:
    """@brief Solve N-Queens through selection, OX crossover, and swap mutation.

    The genotype is a row permutation whose index identifies a column.  The
    corresponding phenotype is an N x N board with exactly one queen in every
    row and column, so the fitness only needs to penalize diagonal attacks.
    """

    def __init__(self, n: int, config: GAConfig | None = None) -> None:
        """@brief Build a solver for an N x N phenotype.

        @param n Number of queens and board dimension.
        @param config Genetic algorithm hyperparameters.
        """

        if n < 1:
            raise ValueError("N must be positive")
        if n in (2, 3):
            raise ValueError("N-Queens has no solution for N=2 or N=3")
        self.n = n
        self.config = config or GAConfig()
        self.config.validate()
        self.random = Random(self.config.seed)

    @staticmethod
    def diagonal_attacks(genotype: Sequence[int]) -> int:
        """@brief Count every attacking diagonal pair in O(N) time.

        @param genotype Row permutation indexed by column.
        @return Number of pairs sharing either diagonal.
        """

        n = len(genotype)
        descending = [0] * (2 * n - 1)
        ascending = [0] * (2 * n - 1)
        offset = n - 1
        for column, row in enumerate(genotype):
            descending[row - column + offset] += 1
            ascending[row + column] += 1
        return sum(count * (count - 1) // 2 for count in descending + ascending)

    @staticmethod
    def conflicted_queens(genotype: Sequence[int]) -> int:
        """@brief Count queens involved in at least one diagonal attack."""

        attacked: set[int] = set()
        for first in range(len(genotype)):
            for second in range(first + 1, len(genotype)):
                if abs(genotype[first] - genotype[second]) == second - first:
                    attacked.add(first)
                    attacked.add(second)
        return len(attacked)

    def _individual(self, genotype: Sequence[int]) -> Individual:
        """@brief Evaluate a genotype and create its fitness-bearing individual."""

        frozen = tuple(genotype)
        return Individual(frozen, self.diagonal_attacks(frozen))

    def initial_population(self) -> list[Individual]:
        """@brief Stage 1: define a diverse initial population of permutations."""

        base = list(range(self.n))
        population: list[Individual] = []
        seen: set[Genotype] = set()
        attempts = 0
        max_unique_attempts = self.config.population_size * 10
        while len(population) < self.config.population_size:
            candidate = base.copy()
            self.random.shuffle(candidate)
            genotype = tuple(candidate)
            attempts += 1
            if genotype in seen and attempts < max_unique_attempts:
                continue
            seen.add(genotype)
            population.append(self._individual(genotype))
        return population

    def _select_parent(self, population: Sequence[Individual]) -> Individual:
        """@brief Select a parent by comparing fitness in a tournament."""

        contenders = self.random.sample(
            population, min(self.config.tournament_size, len(population))
        )
        return max(contenders, key=lambda individual: individual.fitness)

    def _order_crossover(
        self, first: Genotype, second: Genotype
    ) -> tuple[Genotype, Genotype]:
        """@brief Apply Order Crossover (OX) while preserving valid permutations."""

        if self.n < 2 or self.random.random() > self.config.crossover_rate:
            return first, second
        left, right = sorted(self.random.sample(range(self.n), 2))
        right += 1

        def build_child(donor: Genotype, filler: Genotype) -> Genotype:
            child = [-1] * self.n
            child[left:right] = donor[left:right]
            used = set(child[left:right])
            available = [gene for gene in filler[right:] + filler[:right] if gene not in used]
            positions = list(range(right, self.n)) + list(range(0, left))
            for position, gene in zip(positions, available):
                child[position] = gene
            return tuple(child)

        return build_child(first, second), build_child(second, first)

    def _mutate_swap(
        self, genotype: Genotype, mutation_rate: float
    ) -> tuple[Genotype, tuple[int, int] | None]:
        """@brief Mutate a genotype through the required two-position swap.

        One endpoint is sampled from a currently attacked diagonal when possible.
        The second endpoint stays random, so this remains a mutation operator while
        spending changes on genes that can actually improve the phenotype.
        """

        if self.n < 2 or self.random.random() >= mutation_rate:
            return genotype, None
        descending: dict[int, int] = {}
        ascending: dict[int, int] = {}
        for column, row in enumerate(genotype):
            descending[row - column] = descending.get(row - column, 0) + 1
            ascending[row + column] = ascending.get(row + column, 0) + 1
        conflicted = [
            column
            for column, row in enumerate(genotype)
            if descending[row - column] > 1 or ascending[row + column] > 1
        ]
        first = self.random.choice(conflicted) if conflicted else self.random.randrange(self.n)
        second = self.random.randrange(self.n - 1)
        if second >= first:
            second += 1
        genes = list(genotype)
        genes[first], genes[second] = genes[second], genes[first]
        return tuple(genes), (first, second)

    def _snapshot(
        self,
        generation: int,
        population: Sequence[Individual],
        started_at: float,
    ) -> ProgressSnapshot:
        """@brief Capture the best phenotype and aggregate fitness information."""

        best = min(population, key=lambda individual: individual.cost)
        return ProgressSnapshot(
            generation=generation,
            best_genotype=best.genotype,
            best_cost=best.cost,
            average_cost=fmean(individual.cost for individual in population),
            fitness=best.fitness,
            elapsed_seconds=perf_counter() - started_at,
        )

    def _new_population(
        self,
        population: Sequence[Individual],
        stagnation: int,
        generation: int,
        mutation_history: list[MutationSnapshot] | None,
    ) -> list[Individual]:
        """@brief Stage 3: select, cross, mutate, and replace the population."""

        ranked = sorted(population, key=lambda individual: individual.cost)
        next_population = ranked[: self.config.elite_count]

        # Increase mutation gradually when fitness has stopped improving.
        pressure = 1.0 + min(stagnation / self.config.stagnation_limit, 2.0)
        mutation_rate = min(0.95, self.config.mutation_rate * pressure)

        while len(next_population) < self.config.population_size:
            first_parent = self._select_parent(population)
            second_parent = self._select_parent(population)
            first_child, second_child = self._order_crossover(
                first_parent.genotype, second_parent.genotype
            )
            for child in (first_child, second_child):
                mutated, swapped_columns = self._mutate_swap(child, mutation_rate)
                if mutation_history is not None and swapped_columns is not None:
                    mutation_history.append(
                        MutationSnapshot(
                            sequence=len(mutation_history) + 1,
                            generation=generation,
                            parent_a=first_parent.genotype,
                            parent_b=second_parent.genotype,
                            child_before=child,
                            child_after=mutated,
                            swapped_columns=swapped_columns,
                            cost_before=self.diagonal_attacks(child),
                            cost_after=self.diagonal_attacks(mutated),
                        )
                    )
                next_population.append(self._individual(mutated))
                if len(next_population) == self.config.population_size:
                    break

        # Random immigrants recover diversity after a long fitness plateau.
        if stagnation and stagnation % self.config.stagnation_limit == 0:
            immigrant_count = max(
                1, int(self.config.population_size * self.config.immigrant_fraction)
            )
            base = list(range(self.n))
            immigrants: list[Individual] = []
            for _ in range(immigrant_count):
                self.random.shuffle(base)
                immigrants.append(self._individual(base))
            next_population[-immigrant_count:] = immigrants
        return next_population

    def solve(
        self,
        callback: ProgressCallback | None = None,
        stop_event: Event | None = None,
        record_mutations: bool = False,
    ) -> GeneticResult:
        """@brief Stage 2: iteratively generate populations until cost reaches zero.

        @param callback Optional observer invoked after every generation.
        @param stop_event Optional cooperative cancellation signal for the GUI.
        @param record_mutations Store every applied swap for step-by-step playback.
        @return Best individual, timing metrics, and convergence history.
        """

        started_at = perf_counter()
        population = self.initial_population()
        history: list[ProgressSnapshot] = []
        mutation_history: list[MutationSnapshot] | None = [] if record_mutations else None
        best_cost = min(individual.cost for individual in population)
        stagnation = 0
        generation = 0
        stopped = False

        snapshot = self._snapshot(generation, population, started_at)
        history.append(snapshot)
        if callback:
            callback(snapshot)

        while snapshot.best_cost != 0 and generation < self.config.max_generations:
            if stop_event is not None and stop_event.is_set():
                stopped = True
                break

            population = self._new_population(
                population, stagnation, generation + 1, mutation_history
            )
            generation += 1
            snapshot = self._snapshot(generation, population, started_at)
            history.append(snapshot)
            if callback:
                callback(snapshot)

            if snapshot.best_cost < best_cost:
                best_cost = snapshot.best_cost
                stagnation = 0
            else:
                stagnation += 1

        best = min(population, key=lambda individual: individual.cost)
        elapsed = perf_counter() - started_at
        return GeneticResult(
            genotype=best.genotype,
            cost=best.cost,
            generations=generation,
            elapsed_seconds=elapsed,
            history=tuple(history),
            mutations=tuple(mutation_history or ()),
            stopped_by_user=stopped,
        )
