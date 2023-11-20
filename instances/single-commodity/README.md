# Single-commodity instances

The instances in this directory are generated from the `r04` and `r07` instances in the `test/` directory.
Those instances each have ten commodities, which we aggregate here to instances just a single commodity.

The aggregation process is as follows.
We introduce two new nodes $s$ and $t$.
We introduce new edges $(s, 1)$ and $(|N|, t)$.
These edges are unconstrained in capacity, and cost zero to construct.
Finally, we aggregate commodities: we create a single commodity with origin $s$ and destination $t$, and sum the original commodity demands (in each scenario) to create the new commodity demand.
We then remove all other commodities.
