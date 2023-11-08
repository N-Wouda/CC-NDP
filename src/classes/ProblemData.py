from dataclasses import dataclass
from pathlib import Path


@dataclass
class Arc:
    from_node: int
    to_node: int
    var_cost: float
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
            idx
            for idx, arc in enumerate(self.arcs)
            if arc.from_node == node
        ]

    def arc_indices_to(self, node: int) -> list[int]:
        """
        Implements N_i(-) from the paper, for a given node i.
        """
        return [
            idx
            for idx, arc in enumerate(self.arcs)
            if arc.to_node == node
        ]

    @classmethod
    def from_file(cls, where: str | Path) -> "ProblemData":
        """
        Parses an instance file.
        """
        # TODO update with actual scenarios
        where = Path(where)

        with open(where) as fh:
            lines = (line.strip() for line in fh.readlines())

        # First line specifies number of nodes, arcs, commodities.
        num_nodes, num_arcs, num_commodities = map(int, next(lines).split())
    
        # Next num_arcs lines specify arc data.
        arcs: list[Arc] = []
        for _ in range(num_arcs):
            attributes = map(float, next(lines).split())
            arcs.append(Arc(
                from_node=int(attributes[0]),
                to_node=int(attributes[1]),
                var_cost=attributes[2],
                capacity=attributes[3],
                fixed_cost=attributes[4],
            ))

        # Next num_commodities lines specify commodity data.
        commodities: list[Commodity] = []
        for _ in range(num_commodities):
            from_node, to_node, demand = map(float, next(lines).split())
            commodities.append(Commodity(
                int(from_node), 
                int(to_node),
                [demand]
            ))

        return cls(
            num_nodes,
            arcs,
            commodities,
            [1.]
        )
