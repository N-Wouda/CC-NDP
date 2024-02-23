# CC-NDP

This repository contains models and various decomposition formulations to solve chance-constrained multicommodity capacitated fixed-charge network design problems.
The software implementation can be found in `src/`, the instances in `instances/`, and the paper results in `results/` (with an analysis of these results in the notebook under `notebooks/`).

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

> [!NOTE]
> To solve many instances in parallel (e.g., on a computer cluster), make sure to turn off Gurobi's output by setting `OutputFlag 0` in the `gurobi.env` file.
> Also turn off logging by setting the root logging level to `WARNING` in `logging.toml`.

Suppose we want to solve the `r04-7-16` instance using FlowMIS and $\alpha = 0.1$, and write the result to the `out.json` file.
In the project root, one could then run the following command:
```
poetry run solve instances/r04-7-16.ndp out.json 0.1 decomp FlowMIS
```
The other formulations may be specified in the place of FlowMIS as BB, MIS, and SNC.
One may optionally specify the `--with_combinatorial_cut` and `--without_metric_cuts` at the end of the command, to tell the decomposition to also use (or not use) those particular cuts.
The default is to use metric cut strengthening, but not to use combinatorial cuts.
Additionally, all decompositions can make use of a `--without_master_scenario` flag, which turns on or off the scenario creation technique (default on).  

Finally, a deterministic equivalent solver is available and may be used as follows (here, with a time limit of 120 seconds):
```
poetry run solve instances/r04-7-16.ndp out.json 0.1 deq --time_limit 120
```
The deterministic equivalent solver is useful for verifying correct outputs, but typically does not scale as well as the decomposition method.
