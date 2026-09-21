"""Regression tests for the N-Queens genetic algorithm."""

import unittest

from nqueens_ga.algorithm import GAConfig, GeneticAlgorithm


class GeneticAlgorithmTests(unittest.TestCase):
    """@brief Verify representation, operators, stop condition, and scalability."""

    def test_known_costs(self) -> None:
        """@brief Count diagonal pairs, not merely conflicted queens."""

        self.assertEqual(GeneticAlgorithm.diagonal_attacks((0, 1, 2, 3)), 6)
        self.assertEqual(GeneticAlgorithm.diagonal_attacks((1, 3, 0, 2)), 0)

    def test_initial_population_contains_permutations(self) -> None:
        """@brief Ensure every genotype places one queen per row and column."""

        solver = GeneticAlgorithm(
            8, GAConfig(population_size=30, elite_count=2, seed=9)
        )
        for individual in solver.initial_population():
            self.assertEqual(sorted(individual.genotype), list(range(8)))

    def test_order_crossover_preserves_permutations(self) -> None:
        """@brief Ensure OX never duplicates or loses a row gene."""

        solver = GeneticAlgorithm(
            8,
            GAConfig(
                population_size=20,
                elite_count=2,
                crossover_rate=1.0,
                seed=4,
            ),
        )
        first, second = solver._order_crossover(
            tuple(range(8)), tuple(reversed(range(8)))
        )
        self.assertEqual(sorted(first), list(range(8)))
        self.assertEqual(sorted(second), list(range(8)))

    def test_base_case_reaches_zero_cost(self) -> None:
        """@brief Solve the mandatory N=8 base case reproducibly."""

        result = GeneticAlgorithm(
            8,
            GAConfig(
                population_size=120,
                max_generations=1000,
                elite_count=4,
                seed=42,
            ),
        ).solve()
        self.assertTrue(result.solved)
        self.assertEqual(result.cost, 0)
        self.assertEqual(sorted(result.genotype), list(range(8)))

    def test_convergence_history_is_monotonic(self) -> None:
        """@brief Confirm elitist replacement never loses the best fitness."""

        result = GeneticAlgorithm(
            20,
            GAConfig(
                population_size=100,
                max_generations=500,
                elite_count=4,
                seed=7,
            ),
        ).solve()
        costs = [snapshot.best_cost for snapshot in result.history]
        self.assertTrue(all(after <= before for before, after in zip(costs, costs[1:])))

    def test_mutation_history_replays_exact_swaps(self) -> None:
        """@brief Ensure every recorded UI step is a truthful swap mutation."""

        result = GeneticAlgorithm(
            8,
            GAConfig(
                population_size=40,
                max_generations=20,
                mutation_rate=1.0,
                elite_count=2,
                seed=11,
            ),
        ).solve(record_mutations=True)
        self.assertTrue(result.mutations)
        for mutation in result.mutations:
            first, second = mutation.swapped_columns
            expected = list(mutation.child_before)
            expected[first], expected[second] = expected[second], expected[first]
            self.assertEqual(tuple(expected), mutation.child_after)
            self.assertEqual(
                mutation.cost_after,
                GeneticAlgorithm.diagonal_attacks(mutation.child_after),
            )

    def test_impossible_board_is_rejected(self) -> None:
        """@brief Reject N values for which the stop condition cannot exist."""

        with self.assertRaises(ValueError):
            GeneticAlgorithm(3)


if __name__ == "__main__":
    unittest.main()
