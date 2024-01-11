# Results

This directory contains all raw results that are analysed further and presented in various forms in the paper.
The JSON files in subdirectories can be read using the `Result` class from `src.classes`, as follows:
```python
from src.classes import Result

res = Result.from_file("path to json")
```
Such a `Result` object will contain all decisions, run-time information, and the development of the upper and lower bounds during the search.

The subdirectories are as follows:
- `everything`: the results in this subdirectory were generated using all enhancements active, that is, using the VI's and the metric cuts;
- `no-metric`: the results in this subdirectory were generated using VI's, but not the metric cuts;
- `no-metric-no-vis`: the results in this subdirecotry were generated without the VI's and metric cuts. These results correspond to the pure, simple Benders' routine without any enhancements.
- `single-commodity`: the results in this directory are for the single-commodity instances in `instances/single-commodity`.
`
