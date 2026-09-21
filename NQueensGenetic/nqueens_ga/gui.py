"""Minimalist Tk interface for the N-Queens genetic algorithm."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import replace
from tkinter import messagebox

from .algorithm import (
    GAConfig,
    GeneticAlgorithm,
    GeneticResult,
    MutationSnapshot,
    ProgressSnapshot,
)


BACKGROUND = "#08111f"
SURFACE = "#101c2f"
SURFACE_ALT = "#16253c"
TEXT = "#e9f1ff"
MUTED = "#91a4c1"
ACCENT = "#61e7c8"
ACCENT_DARK = "#1eb79c"
DANGER = "#ff7185"
LIGHT_CELL = "#dce9ee"
DARK_CELL = "#527082"
QUEEN = "#ffca64"


class NQueensApp:
    """@brief Display genotype evolution as a board phenotype and cost chart."""

    def __init__(self, root: tk.Tk, n: int, config: GAConfig) -> None:
        """@brief Configure application state and build all interface regions."""

        self.root = root
        self.config = config
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.cost_history: list[int] = []
        self.current_genotype: tuple[int, ...] = ()
        self.latest_result: GeneticResult | None = None
        self.playback_index = 0
        self.playback_running = False
        self.playback_after_id: str | None = None
        self.highlight_columns: tuple[int, int] | None = None
        self._updating_slider = False

        root.title("N-Queens · Genetic Explorer")
        root.geometry("1320x900")
        root.minsize(1080, 760)
        root.configure(bg=BACKGROUND)
        root.protocol("WM_DELETE_WINDOW", self._close)

        self.n_var = tk.StringVar(value=str(n))
        self.population_var = tk.StringVar(value=str(config.population_size))
        self.generations_var = tk.StringVar(value=str(config.max_generations))
        self.mutation_var = tk.StringVar(value=f"{config.mutation_rate:.2f}")
        self.speed_var = tk.IntVar(value=500)
        self.status_var = tk.StringVar(value="Ready to evolve")
        self.cost_var = tk.StringVar(value="—")
        self.generation_var = tk.StringVar(value="0")
        self.fitness_var = tk.StringVar(value="—")
        self.time_var = tk.StringVar(value="0.000 s")
        self.genotype_var = tk.StringVar(value="Press Start to create the initial genotype.")
        self.step_var = tk.StringVar(value="Run the algorithm to inspect every mutation.")
        self.parent_a_var = tk.StringVar(value="—")
        self.parent_b_var = tk.StringVar(value="—")
        self.child_before_var = tk.StringVar(value="—")
        self.child_after_var = tk.StringVar(value="—")

        self._build_layout()
        self._draw_empty_board(n)
        self._draw_chart()
        self.root.after(25, self._process_messages)

    def _label(
        self,
        parent: tk.Misc,
        text: str = "",
        *,
        font: tuple[str, int, str] | tuple[str, int] = ("TkDefaultFont", 10),
        color: str = TEXT,
        background: str = SURFACE,
    ) -> tk.Label:
        """@brief Create a label matching the interface design system."""

        return tk.Label(parent, text=text, font=font, fg=color, bg=background)

    def _build_layout(self) -> None:
        """@brief Build controls, phenotype board, metrics, and convergence plot."""

        header = tk.Frame(self.root, bg=BACKGROUND, padx=28, pady=18)
        header.pack(fill="x")
        self._label(
            header,
            "N-QUEENS",
            font=("TkDefaultFont", 18, "bold"),
            background=BACKGROUND,
        ).pack(side="left")
        self._label(
            header,
            "GENETIC EXPLORER",
            font=("TkDefaultFont", 10, "bold"),
            color=ACCENT,
            background=BACKGROUND,
        ).pack(side="left", padx=(10, 0), pady=(7, 0))
        self._label(
            header,
            "Permutation genotype · OX crossover · swap mutation",
            color=MUTED,
            background=BACKGROUND,
        ).pack(side="right", pady=(7, 0))

        body = tk.Frame(self.root, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        body.grid_columnconfigure(1, weight=3)
        body.grid_columnconfigure(2, weight=2)
        body.grid_rowconfigure(0, weight=1)

        sidebar = tk.Frame(body, bg=SURFACE, padx=20, pady=20, width=235)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 16))
        sidebar.grid_propagate(False)
        self._build_controls(sidebar)

        board_panel = tk.Frame(body, bg=SURFACE, padx=16, pady=16)
        board_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 16))
        board_panel.grid_rowconfigure(1, weight=1)
        board_panel.grid_columnconfigure(0, weight=1)
        self._label(
            board_panel, "CURRENT PHENOTYPE", font=("TkDefaultFont", 11, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.board = tk.Canvas(
            board_panel, bg=SURFACE_ALT, bd=0, highlightthickness=0
        )
        self.board.grid(row=1, column=0, sticky="nsew")
        self.board.bind("<Configure>", lambda _event: self._redraw_board())

        analytics = tk.Frame(body, bg=BACKGROUND)
        analytics.grid(row=0, column=2, sticky="nsew")
        analytics.grid_columnconfigure(0, weight=1)
        analytics.grid_rowconfigure(1, weight=1)
        self._build_metrics(analytics)

        chart_panel = tk.Frame(analytics, bg=SURFACE, padx=16, pady=16)
        chart_panel.grid(row=1, column=0, sticky="nsew")
        self._label(
            chart_panel, "COST CONVERGENCE", font=("TkDefaultFont", 11, "bold")
        ).pack(anchor="w")
        self._label(
            chart_panel,
            "Diagonal attacking pairs by generation",
            color=MUTED,
            font=("TkDefaultFont", 9),
        ).pack(anchor="w", pady=(2, 10))
        self.chart = tk.Canvas(
            chart_panel, bg=SURFACE_ALT, bd=0, highlightthickness=0, height=260
        )
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda _event: self._draw_chart())

        inspector = tk.Frame(body, bg=SURFACE, padx=16, pady=14)
        inspector.grid(
            row=1, column=1, columnspan=2, sticky="nsew", padx=(0, 0), pady=(16, 0)
        )
        self._build_mutation_inspector(inspector)

        footer = tk.Frame(self.root, bg=SURFACE_ALT, padx=28, pady=12)
        footer.pack(fill="x", side="bottom", before=body)
        tk.Label(
            footer,
            textvariable=self.status_var,
            fg=ACCENT,
            bg=SURFACE_ALT,
            font=("TkDefaultFont", 9, "bold"),
        ).pack(side="left")
        tk.Label(
            footer,
            textvariable=self.genotype_var,
            fg=MUTED,
            bg=SURFACE_ALT,
            font=("TkFixedFont", 9),
            anchor="e",
        ).pack(side="right", fill="x", expand=True, padx=(24, 0))

    def _build_controls(self, parent: tk.Frame) -> None:
        """@brief Create editable genetic-algorithm hyperparameters."""

        self._label(
            parent, "EXPERIMENT", font=("TkDefaultFont", 11, "bold")
        ).pack(anchor="w", pady=(0, 16))
        fields = (
            ("Queens / board size", self.n_var),
            ("Population", self.population_var),
            ("Maximum generations", self.generations_var),
            ("Mutation rate", self.mutation_var),
        )
        for title, variable in fields:
            self._label(parent, title, color=MUTED, font=("TkDefaultFont", 9)).pack(
                anchor="w", pady=(0, 5)
            )
            entry = tk.Entry(
                parent,
                textvariable=variable,
                bg=SURFACE_ALT,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                font=("TkDefaultFont", 11),
                highlightthickness=1,
                highlightbackground="#273b57",
                highlightcolor=ACCENT,
            )
            entry.pack(fill="x", ipady=7, pady=(0, 12))

        self._label(
            parent, "Mutation playback delay (ms)", color=MUTED, font=("TkDefaultFont", 9)
        ).pack(anchor="w", pady=(0, 2))
        tk.Scale(
            parent,
            variable=self.speed_var,
            from_=50,
            to=1500,
            resolution=50,
            orient="horizontal",
            bg=SURFACE,
            fg=TEXT,
            troughcolor=SURFACE_ALT,
            activebackground=ACCENT,
            highlightthickness=0,
            bd=0,
        ).pack(fill="x", pady=(0, 18))

        self.start_button = tk.Button(
            parent,
            text="START EVOLUTION",
            command=self._start,
            bg=ACCENT,
            fg="#07151a",
            activebackground="#8af1dc",
            activeforeground="#07151a",
            relief="flat",
            font=("TkDefaultFont", 10, "bold"),
            cursor="hand2",
        )
        self.start_button.pack(fill="x", ipady=9)
        self.stop_button = tk.Button(
            parent,
            text="STOP",
            command=self._stop,
            state="disabled",
            bg=SURFACE_ALT,
            fg=MUTED,
            activebackground="#243956",
            activeforeground=TEXT,
            disabledforeground="#53647b",
            relief="flat",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.stop_button.pack(fill="x", ipady=8, pady=(8, 0))
        self._label(
            parent,
            "Rows are stored internally as 0..N-1.\nThe result is displayed as 1..N.",
            color=MUTED,
            font=("TkDefaultFont", 8),
        ).pack(anchor="w", side="bottom")

    def _build_mutation_inspector(self, parent: tk.Frame) -> None:
        """@brief Build manual navigation and full genotype-array inspection."""

        header = tk.Frame(parent, bg=SURFACE)
        header.pack(fill="x", pady=(0, 8))
        self._label(
            header, "MUTATION STEP-BY-STEP", font=("TkDefaultFont", 11, "bold")
        ).pack(side="left")
        tk.Label(
            header,
            textvariable=self.step_var,
            fg=ACCENT,
            bg=SURFACE,
            font=("TkDefaultFont", 9, "bold"),
        ).pack(side="right")

        navigator = tk.Frame(parent, bg=SURFACE)
        navigator.pack(fill="x", pady=(0, 9))
        button_specs = (
            ("|◀", self._go_first),
            ("◀", self._go_previous),
            ("▶  PLAY", self._toggle_playback),
            ("▶", self._go_next),
            ("▶|", self._go_last),
        )
        self.navigation_buttons: list[tk.Button] = []
        for label, command in button_specs:
            button = tk.Button(
                navigator,
                text=label,
                command=command,
                state="disabled",
                bg=SURFACE_ALT,
                fg=TEXT,
                disabledforeground="#53647b",
                activebackground="#243956",
                activeforeground=TEXT,
                relief="flat",
                font=("TkDefaultFont", 9, "bold"),
                padx=10,
                pady=5,
            )
            button.pack(side="left", padx=(0, 5))
            self.navigation_buttons.append(button)
        self.play_button = self.navigation_buttons[2]
        self.step_scale = tk.Scale(
            navigator,
            from_=0,
            to=1,
            orient="horizontal",
            command=self._seek_from_scale,
            state="disabled",
            showvalue=False,
            bg=SURFACE,
            troughcolor=SURFACE_ALT,
            activebackground=ACCENT,
            highlightthickness=0,
            bd=0,
        )
        self.step_scale.pack(side="left", fill="x", expand=True, padx=(8, 0))

        arrays = tk.Frame(parent, bg=SURFACE)
        arrays.pack(fill="both", expand=True)
        arrays.grid_columnconfigure(1, weight=1)
        array_rows = (
            ("Parent A", self.parent_a_var),
            ("Parent B", self.parent_b_var),
            ("Child after OX", self.child_before_var),
            ("Child after swap", self.child_after_var),
        )
        for row, (title, variable) in enumerate(array_rows):
            self._label(
                arrays, title, color=MUTED, font=("TkDefaultFont", 8, "bold")
            ).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
            entry = tk.Entry(
                arrays,
                textvariable=variable,
                state="readonly",
                readonlybackground=SURFACE_ALT,
                fg=TEXT,
                relief="flat",
                font=("TkFixedFont", 9),
            )
            entry.grid(row=row, column=1, sticky="ew", ipady=3, pady=2)

    def _build_metrics(self, parent: tk.Frame) -> None:
        """@brief Create the four real-time metric cards."""

        metrics = tk.Frame(parent, bg=BACKGROUND)
        metrics.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        for index in range(2):
            metrics.grid_columnconfigure(index, weight=1)
        cards = (
            ("DISPLAYED COST", self.cost_var),
            ("GENERATION", self.generation_var),
            ("FITNESS", self.fitness_var),
            ("EXECUTION", self.time_var),
        )
        for index, (title, variable) in enumerate(cards):
            card = tk.Frame(metrics, bg=SURFACE, padx=14, pady=12)
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=(0, 7) if index % 2 == 0 else (7, 0),
                pady=(0, 7) if index < 2 else (7, 0),
            )
            self._label(card, title, color=MUTED, font=("TkDefaultFont", 8)).pack(
                anchor="w"
            )
            tk.Label(
                card,
                textvariable=variable,
                fg=TEXT,
                bg=SURFACE,
                font=("TkDefaultFont", 16, "bold"),
            ).pack(anchor="w", pady=(3, 0))

    def _read_configuration(self) -> tuple[int, GAConfig]:
        """@brief Parse and validate interface values before starting a worker."""

        n = int(self.n_var.get())
        population = int(self.population_var.get())
        generations = int(self.generations_var.get())
        mutation = float(self.mutation_var.get())
        elite = min(max(2, population // 30), population - 1)
        config = replace(
            self.config,
            population_size=population,
            max_generations=generations,
            mutation_rate=mutation,
            elite_count=elite,
            tournament_size=min(self.config.tournament_size, population),
        )
        GeneticAlgorithm(n, config)
        return n, config

    def _start(self) -> None:
        """@brief Launch the computation without blocking the Tk event loop."""

        if self.worker and self.worker.is_alive():
            return
        try:
            n, config = self._read_configuration()
        except (ValueError, TypeError) as error:
            messagebox.showerror("Invalid parameters", str(error), parent=self.root)
            return

        self.config = config
        self._pause_playback()
        self.stop_event.clear()
        self.cost_history.clear()
        self.current_genotype = ()
        self.latest_result = None
        self.playback_index = 0
        self.highlight_columns = None
        self.step_var.set("Recording mutation history…")
        self._set_array_values()
        self.step_scale.configure(state="disabled", from_=0, to=1)
        self.step_scale.set(0)
        for button in self.navigation_buttons:
            button.configure(state="disabled")
        self.status_var.set("Creating initial population…")
        self.cost_var.set("—")
        self.generation_var.set("0")
        self.fitness_var.set("—")
        self.time_var.set("0.000 s")
        self.genotype_var.set("Evolving a valid permutation genotype…")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal", fg=TEXT)
        self._draw_empty_board(n)
        self._draw_chart()

        def run() -> None:
            try:
                solver = GeneticAlgorithm(n, config)
                result = solver.solve(
                    callback=lambda snapshot: self.messages.put(("progress", snapshot)),
                    stop_event=self.stop_event,
                    record_mutations=True,
                )
                self.messages.put(("result", result))
            except Exception as error:  # Keep worker failures visible in the UI.
                self.messages.put(("error", error))

        self.worker = threading.Thread(target=run, daemon=True)
        self.worker.start()

    def _stop(self) -> None:
        """@brief Request cooperative termination after the current generation."""

        self.stop_event.set()
        self.status_var.set("Stopping after the current generation…")

    def _process_messages(self) -> None:
        """@brief Drain worker messages while retaining all convergence points."""

        processed = 0
        while processed < 500:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                self._show_snapshot(payload)  # type: ignore[arg-type]
            elif kind == "result":
                self._finish(payload)  # type: ignore[arg-type]
            elif kind == "error":
                self._fail(payload)  # type: ignore[arg-type]
            processed += 1
        self.root.after(15 if processed else 25, self._process_messages)

    def _show_snapshot(self, snapshot: ProgressSnapshot) -> None:
        """@brief Convert a genotype snapshot into its visible board phenotype."""

        self.current_genotype = snapshot.best_genotype
        self.cost_history.append(snapshot.best_cost)
        self.cost_var.set(str(snapshot.best_cost))
        self.generation_var.set(str(snapshot.generation))
        self.fitness_var.set(f"{snapshot.fitness:.4f}")
        self.time_var.set(f"{snapshot.elapsed_seconds:.3f} s")
        self.status_var.set("Evolving · stop condition: cost = 0")
        displayed = [row + 1 for row in snapshot.best_genotype]
        compact = str(displayed)
        if len(compact) > 105:
            compact = compact[:102] + "…]"
        self.genotype_var.set(f"Genotype: {compact}")
        self._redraw_board()
        self._draw_chart()

    def _finish(self, result: GeneticResult) -> None:
        """@brief Load the recorded timeline at its initial phenotype."""

        self.latest_result = result
        self.time_var.set(f"{result.elapsed_seconds:.3f} s")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled", fg=MUTED)
        last_index = len(result.mutations) + 1
        self.step_scale.configure(state="normal", from_=0, to=last_index)
        for button in self.navigation_buttons:
            button.configure(state="normal")
        self._show_playback_step(0)
        if result.stopped_by_user:
            self.status_var.set("Stopped · mutation history is ready for inspection")
        elif result.solved:
            self.status_var.set("Solved · press PLAY or step through each recorded swap")
        else:
            self.status_var.set("Limit reached · inspect every recorded swap mutation")
        self._draw_chart()

    def _fail(self, error: BaseException) -> None:
        """@brief Restore controls and report an unexpected worker failure."""

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled", fg=MUTED)
        self.status_var.set("Execution failed")
        messagebox.showerror("Execution error", str(error), parent=self.root)

    @staticmethod
    def _display_genotype(genotype: tuple[int, ...]) -> str:
        """@brief Format a complete genotype with human-friendly row numbers."""

        return str([row + 1 for row in genotype])

    def _set_array_values(
        self,
        parent_a: tuple[int, ...] | None = None,
        parent_b: tuple[int, ...] | None = None,
        child_before: tuple[int, ...] | None = None,
        child_after: tuple[int, ...] | None = None,
    ) -> None:
        """@brief Update the four horizontally scrollable arrays of interest."""

        formatter = lambda value: self._display_genotype(value) if value else "—"
        self.parent_a_var.set(formatter(parent_a))
        self.parent_b_var.set(formatter(parent_b))
        self.child_before_var.set(formatter(child_before))
        self.child_after_var.set(formatter(child_after))

    def _show_playback_step(self, index: int) -> None:
        """@brief Render an initial, mutation, or final timeline state."""

        result = self.latest_result
        if result is None or not result.history:
            return
        last_index = len(result.mutations) + 1
        index = max(0, min(index, last_index))
        self.playback_index = index
        self._updating_slider = True
        self.step_scale.set(index)
        self._updating_slider = False
        self.highlight_columns = None

        if index == 0:
            initial = result.history[0]
            genotype = initial.best_genotype
            cost = initial.best_cost
            generation = 0
            self.step_var.set(
                f"INITIAL BOARD · cost {cost} · {len(result.mutations)} mutations recorded"
            )
            self._set_array_values(child_before=genotype, child_after=genotype)
        elif index == last_index:
            genotype = result.genotype
            cost = result.cost
            generation = result.generations
            self.step_var.set(
                f"FINAL BOARD · generation {generation} · cost {cost}"
            )
            self._set_array_values(child_before=genotype, child_after=genotype)
        else:
            mutation: MutationSnapshot = result.mutations[index - 1]
            genotype = mutation.child_after
            cost = mutation.cost_after
            generation = mutation.generation
            first, second = mutation.swapped_columns
            self.highlight_columns = (first, second)
            self.step_var.set(
                f"MUTATION {mutation.sequence}/{len(result.mutations)} · "
                f"gen {generation} · columns {first + 1} ↔ {second + 1} · "
                f"cost {mutation.cost_before} → {mutation.cost_after}"
            )
            self._set_array_values(
                mutation.parent_a,
                mutation.parent_b,
                mutation.child_before,
                mutation.child_after,
            )

        self.current_genotype = genotype
        self.cost_var.set(str(cost))
        self.generation_var.set(str(generation))
        self.fitness_var.set(f"{1 / (1 + cost):.4f}")
        self.genotype_var.set(f"Genotype: {self._display_genotype(genotype)}")
        self._redraw_board()

    def _seek_from_scale(self, value: str) -> None:
        """@brief Seek to an arbitrary recorded mutation from the timeline slider."""

        if self._updating_slider or self.latest_result is None:
            return
        self._pause_playback()
        self._show_playback_step(int(float(value)))

    def _go_first(self) -> None:
        """@brief Navigate to the initial best genotype."""

        self._pause_playback()
        self._show_playback_step(0)

    def _go_previous(self) -> None:
        """@brief Navigate exactly one mutation backward."""

        self._pause_playback()
        self._show_playback_step(self.playback_index - 1)

    def _go_next(self) -> None:
        """@brief Navigate exactly one mutation forward."""

        self._pause_playback()
        self._show_playback_step(self.playback_index + 1)

    def _go_last(self) -> None:
        """@brief Navigate directly to the final result."""

        self._pause_playback()
        if self.latest_result is not None:
            self._show_playback_step(len(self.latest_result.mutations) + 1)

    def _toggle_playback(self) -> None:
        """@brief Start or pause slow automatic mutation playback."""

        if self.latest_result is None:
            return
        if self.playback_running:
            self._pause_playback()
            return
        if self.playback_index >= len(self.latest_result.mutations) + 1:
            self._show_playback_step(0)
        self.playback_running = True
        self.play_button.configure(text="Ⅱ  PAUSE", bg=ACCENT_DARK)
        self._schedule_playback_tick()

    def _schedule_playback_tick(self) -> None:
        """@brief Schedule the next mutation using the user-selected delay."""

        if not self.playback_running:
            return
        self.playback_after_id = self.root.after(
            max(50, self.speed_var.get()), self._playback_tick
        )

    def _playback_tick(self) -> None:
        """@brief Advance automatic playback by exactly one recorded mutation."""

        self.playback_after_id = None
        if not self.playback_running or self.latest_result is None:
            return
        last_index = len(self.latest_result.mutations) + 1
        if self.playback_index >= last_index:
            self._pause_playback()
            self.status_var.set("Playback complete · final phenotype displayed")
            return
        self._show_playback_step(self.playback_index + 1)
        self._schedule_playback_tick()

    def _pause_playback(self) -> None:
        """@brief Cancel automatic playback without changing the visible step."""

        self.playback_running = False
        if self.playback_after_id is not None:
            self.root.after_cancel(self.playback_after_id)
            self.playback_after_id = None
        if hasattr(self, "play_button"):
            self.play_button.configure(text="▶  PLAY", bg=SURFACE_ALT)

    def _draw_empty_board(self, n: int) -> None:
        """@brief Prepare a deterministic placeholder genotype for a new N."""

        self.current_genotype = tuple(range(n))
        self._redraw_board(show_queens=False)

    def _redraw_board(self, show_queens: bool = True) -> None:
        """@brief Render the current permutation as an adaptive chess board."""

        self.board.delete("all")
        n = len(self.current_genotype)
        if n == 0:
            return
        width = max(self.board.winfo_width(), 120)
        height = max(self.board.winfo_height(), 120)
        size = min(width - 20, height - 20)
        cell = size / n
        origin_x = (width - size) / 2
        origin_y = (height - size) / 2

        for row in range(n):
            for column in range(n):
                x0 = origin_x + column * cell
                y0 = origin_y + row * cell
                color = LIGHT_CELL if (row + column) % 2 == 0 else DARK_CELL
                self.board.create_rectangle(
                    x0, y0, x0 + cell + 1, y0 + cell + 1, fill=color, outline=""
                )
        if show_queens:
            for column, row in enumerate(self.current_genotype):
                center_x = origin_x + (column + 0.5) * cell
                center_y = origin_y + (row + 0.5) * cell
                radius = max(1.5, cell * 0.31)
                highlighted = (
                    self.highlight_columns is not None
                    and column in self.highlight_columns
                )
                self.board.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill=QUEEN,
                    outline=DANGER if highlighted else "#805e20" if cell > 7 else "",
                    width=3 if highlighted and cell > 8 else 1,
                )
                if cell >= 24:
                    self.board.create_text(
                        center_x,
                        center_y,
                        text="♛",
                        fill="#493512",
                        font=("DejaVu Sans", max(9, int(cell * 0.46))),
                    )

    def _draw_chart(self) -> None:
        """@brief Draw a dependency-free convergence line chart."""

        self.chart.delete("all")
        width = max(self.chart.winfo_width(), 160)
        height = max(self.chart.winfo_height(), 130)
        left, top, right, bottom = 38, 16, width - 14, height - 28
        self.chart.create_line(left, top, left, bottom, fill="#40536e")
        self.chart.create_line(left, bottom, right, bottom, fill="#40536e")
        self.chart.create_text(
            left - 7, top, text="cost", fill=MUTED, anchor="e", font=("TkDefaultFont", 8)
        )
        self.chart.create_text(
            right,
            bottom + 15,
            text="generation",
            fill=MUTED,
            anchor="e",
            font=("TkDefaultFont", 8),
        )
        if not self.cost_history:
            self.chart.create_text(
                (left + right) / 2,
                (top + bottom) / 2,
                text="Waiting for data",
                fill=MUTED,
                font=("TkDefaultFont", 10),
            )
            return

        maximum = max(max(self.cost_history), 1)
        count = len(self.cost_history)
        points: list[float] = []
        for index, cost in enumerate(self.cost_history):
            x = left if count == 1 else left + index * (right - left) / (count - 1)
            y = bottom - cost * (bottom - top) / maximum
            points.extend((x, y))
        if len(points) >= 4:
            self.chart.create_line(*points, fill=ACCENT, width=2, smooth=False)
        else:
            self.chart.create_oval(
                points[0] - 3,
                points[1] - 3,
                points[0] + 3,
                points[1] + 3,
                fill=ACCENT,
                outline="",
            )
        self.chart.create_text(
            left - 7,
            bottom,
            text="0",
            fill=MUTED,
            anchor="e",
            font=("TkDefaultFont", 8),
        )
        self.chart.create_text(
            left - 7,
            top + 8,
            text=str(maximum),
            fill=MUTED,
            anchor="e",
            font=("TkDefaultFont", 8),
        )
        last_x, last_y = points[-2:]
        self.chart.create_oval(
            last_x - 3,
            last_y - 3,
            last_x + 3,
            last_y + 3,
            fill=QUEEN,
            outline="",
        )

    def _close(self) -> None:
        """@brief Stop the worker cooperatively before closing the window."""

        self._pause_playback()
        self.stop_event.set()
        self.root.destroy()


def launch(n: int, config: GAConfig) -> None:
    """@brief Create and run the Tk application event loop."""

    root = tk.Tk()
    NQueensApp(root, n, config)
    root.mainloop()
