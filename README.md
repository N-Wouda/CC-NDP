# CC-NDP

Chance-constrained multicommodity capacitated fixed-charge network design problems.
The solver implementation can be found in `src/`, the instances in `instances/`, and the paper results in `results/` (with an analysis in the notebooks under `notebooks/`).

## Entrypoints

This repository defines a few command-line scripts that may be used to generate and solve experimental instances.
The following scripts are available:
- `solve`, to solve a single instance to optimality.
  Its use and arguments are detailed further below.
- `make_multi`, to generate the multi-commodity instances under `instances/`.
  See the README in `instances/` for details, or read this script's implementation.
- `make_single`, to generate the single-commodity instances under `instances/single-commodity/`.
  See the README in `instances/single-commodity/` for details, or read this script's implementation.

Each of these scripts is available via `poetry` as
```
poetry run <script>
```

## Solving experiments

> **Note:**
> To solve many instances in parallel (e.g., on a computer cluster), make sure to turn off Gurobi's output by setting `OutputFlag 0` in the `gurobi.env` file.
> Also turn off logging by setting the root logging level to `WARNING` in `logging.toml`.

TODO
