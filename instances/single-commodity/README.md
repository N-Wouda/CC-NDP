# Single-commodity instances

The 60 instances in this directory are generated from the 72 `r04` and `r07` instances in the `test/` directory.
Those instances each have ten commodities, which we aggregate here to instances just a single commodity.
We skip the `r04-9-*` instances because those cannot be made feasible with the simple modification scheme we propose in the next paragraph.

The aggregation process is as follows.
We introduce two new nodes $s$ and $t$.
We introduce new edges $(s, 1)$ and $(|N|, t)$.
These edges are unconstrained in capacity, and cost zero to construct.
Finally, we aggregate commodities: we create a single commodity with origin $s$ and destination $t$, and sum the original commodity demands (in each scenario) to create the new commodity demand.
We then remove all other commodities.
