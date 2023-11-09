from dataclasses import dataclass
from pathlib import Path


@dataclass
class Arc:
    from_node: int
    to_node: int
    var_cost: float  # currently unused
    capacity: float
    fixed_cost: float


@dataclass
class Commodity:
    from_node: int
    to_node: int
    demands: list[float]  # one per scenario


@dataclass
class ProblemData:
    num_nodes: int
    arcs: list[Arc]
    commodities: list[Commodity]
    probabilities: list[float]  # scenario probabilities

    @property
    def num_arcs(self) -> int:
        return len(self.arcs)

    @property
    def num_commodities(self) -> int:
        return len(self.commodities)

    @property
    def num_scenarios(self) -> int:
        return len(self.probabilities)

    def arc_indices_from(self, node: int) -> list[int]:
        """
        Implements N_i(+) from the paper, for a given node i.
        """
        return [
            idx for idx, arc in enumerate(self.arcs) if arc.from_node == node
        ]

    def arc_indices_to(self, node: int) -> list[int]:
        """
        Implements N_i(-) from the paper, for a given node i.
        """
        return [
            idx for idx, arc in enumerate(self.arcs) if arc.to_node == node
        ]

    def origins(self) -> list[int]:
        """
        TODO
        """
        origins = {c.from_node for c in self.commodities}
        return sorted(origins)

    def destinations(self) -> list[int]:
        """
        TODO
        """
        destinations = {c.to_node for c in self.commodities}
        return sorted(destinations)

    @classmethod
    def from_file(cls, where: str | Path) -> "ProblemData":
        """
        Parses an instance file.
        """
        where = Path(where)

        with open(where) as fh:
            lines = (line.strip() for line in fh.readlines())

        # First line specifies number of nodes, arcs, commodities, scenarios.
        num_nodes, num_arcs, num_comm, num_scen = map(int, next(lines).split())

        # Next num_arcs lines specify arc data.
        arcs: list[Arc] = []
        for _ in range(num_arcs):
            attributes = [float(v) for v in next(lines).split()]
            arcs.append(
                Arc(
                    from_node=int(attributes[0]),
                    to_node=int(attributes[1]),
                    var_cost=attributes[2],
                    capacity=attributes[3],
                    fixed_cost=attributes[4],
                )
            )

        # Next num_comm lines specify commodity data.
        commodities: list[Commodity] = []
        for _ in range(num_comm):
            from_node, to_node, *_ = map(float, next(lines).split())
            commodities.append(Commodity(int(from_node), int(to_node), []))

        # Next num_scen lines specify the scenarios.
        probabilities = []
        for _ in range(num_scen):
            prob, *demands = map(float, next(lines).split())
            probabilities.append(prob)

            for commodity, demand in zip(commodities, demands):
                commodity.demands.append(demand)

        return cls(num_nodes, arcs, commodities, probabilities)

    def to_file(self, where: str | Path):
        """
        Writes an instance file.
        """
        where = Path(where)

        with open(where, "w") as fh:
            stats = [
                self.num_nodes,
                self.num_arcs,
                self.num_commodities,
                self.num_scenarios,
            ]
            fh.write(" ".join(map(str, stats)) + "\n")

            for arc in self.arcs:
                attributes = [
                    arc.from_node,
                    arc.to_node,
                    arc.var_cost,
                    arc.capacity,
                    arc.fixed_cost,
                ]
                fh.write(" ".join(map(str, attributes)) + "\n")

            for commodity in self.commodities:
                attributes = [commodity.from_node, commodity.to_node]
                fh.write(" ".join(map(str, attributes)) + "\n")

            for scen in range(self.num_scenarios):
                demands = [c.demands[scen] for c in self.commodities]
                prob = self.probabilities[scen]
                fh.write(" ".join(map(str, [prob, *demands])) + "\n")

    def __str__(self) -> str:
        lines = [
            "ProblemData",
            f"      # nodes: {self.num_nodes}",
            f"       # arcs: {self.num_arcs}",
            f"# commodities: {self.num_commodities}",
            f"  # scenarios: {self.num_scenarios}",
        ]

        return "\n".join(lines)
