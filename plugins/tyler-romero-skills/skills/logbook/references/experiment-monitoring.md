# Experiment monitoring

Use this workflow only when the user requests current experiment status, metrics, or health. The local logbook is historical context, not proof of live state.

## 1. Establish recorded context

Read the matching `experiments.md` row and retain:

- The exact experiment name.
- Recorded status and `Last checked` timestamp.
- Source, next check, and notes.
- Any cluster, project, dashboard, or evaluation-run identifiers explicitly recorded there.

Do not guess missing identifiers or silently rewrite an experiment name for another system.

## 2. Discover available monitoring interfaces

Use only interfaces available in the current environment:

1. **Cluster CLI**: Check whether `yolo` exists before running it. Use `yolo list` only when the relevant cluster can be determined from the logbook, current workspace, or user input. If the cluster is ambiguous, report that instead of guessing.
2. **Datadog**: Use Datadog MCP tools only when they are installed and accessible. Search using the exact experiment name and report the time window queried.
3. **Neptune**: Check that `neptune_query` is importable. Resolve the project from the logbook, `NEPTUNE_PROJECT`, current project configuration, or user input. Do not assume a project when none is known.
4. **Other systems**: Use Grafana or another monitoring interface only when an appropriate tool or authenticated connector is available.

The absence of a tool is not a failure. Continue with the available sources and explicitly list what could not be checked.

## 3. Query Neptune when configured

Adapt the metric names to the recorded experiment rather than assuming every run exposes the same attributes:

```python
import neptune_query.runs as nq_runs
from neptune_query.filters import Filter

df = nq_runs.fetch_metrics(
    project="<resolved-project>",
    runs=Filter.name("<exact-experiment-name>"),
    attributes=[
        "train.lm_loss",
        "train.consumed_flops",
        "train.frac_completed",
    ],
    tail_limit=50,
).reset_index()
```

Query an evaluation run only when its exact name is recorded or confirmed. Do not assume that appending `-eval` always produces the correct run name.

## 4. Report and reconcile freshness

Structure the result as:

- **Recorded status**: status, source, and recorded `Last checked` timestamp.
- **Live status**: observations from each source and the timestamp or time window checked.
- **Not checked**: unavailable tools, missing identifiers, or inaccessible sources.
- **Assessment**: whether live evidence agrees with, supersedes, or cannot verify the recorded status.

Never describe the experiment as healthy, failed, complete, or still running unless the available evidence supports that conclusion. When updating the logbook is in scope, update `Status`, `Last checked`, `Source`, `Next check`, and `Notes` with the newly verified evidence while preserving the exact experiment name and original `Started` date.
