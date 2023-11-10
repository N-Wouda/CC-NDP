# Instances

These instances are all based on the R instances of Rahmaniani (2017; 2023).
In particular, they use the topologies of the well-known R instances, but replace the commodity demands by a fixed set of scenarios.
Each instance is named `r<group>-<fixed>-<correlation>-<# scenarios>.ndp`, where:

- `group` indicates the group of the `R` instances, e.g. `r01` to `r30`.
  This repository contains instances from groups `04` through `10`.
- `fixed` indicates the importance of the fixed (design) costs w.r.t. the variable (flow) costs.
  We use the groups `3`, `6`, and `9`, where the fixed design costs are maximal (since we care about design costs, not variable costs).
- `correlation` indicates the correlation between various demand realisations.
  We use `0` and `0.2`, which imply no correlation (`0`) and weakly correlated demands (`0.2`).
- `# scenarios`, the number of different demand scenarios.
  We use values of `16`, `32`, `64`, `128`, `256`, and `512` scenarios.
  The values up to and including `64` are taken directly from Rahmaniani (2023), the higher values are taken from the 1000 scenario instances there: our `128` uses the first 128 scenarios, our `256` the scenarios [128, 384), and our `512` the scenarios [384, 896).

Each instance file consists of whitespace-separated values, in the following format.
The first line specifies (in order): the number of nodes, arcs, commodities, and scenarios.
The next `num_arcs` lines specify (in order) for each arc: the origin node, the destination node, the variable cost (unused), the arc capacity, and the fixed cost.
The next `num_commodities` lines specify (in order) for each commodity: the origin node, the destination node.
The next `num_scenarios` lines specify (in order) for each scenario: the probability, the demands of each commodity.

## References

Rahmaniani, Ragheb, Teodor Gabriel Crainic, Michel Gendreau, and Walter Rei. 
“An Asynchronous Parallel Benders Decomposition Method for Stochastic Network Design Problems.”
_Computers & Operations Research_ 162 (2024): 106459. https://doi.org/10.1016/j.cor.2023.106459.

Rahmaniani, Ragheb, Teodor Gabriel Crainic, Michel Gendreau, and Walter Rei. 
“Accelerating the Benders Decomposition Method: Application to Stochastic Network Design Problems.”
_SIAM Journal on Optimization_ 28, no. 1 (2018): 875–903. https://doi.org/10.1137/17M1128204.
