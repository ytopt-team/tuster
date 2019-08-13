# Tuster: TUning clUSTER

## Install

In the same folder as `setup.py` run:
```
pip install -e .
```

## Quick start

```
$ tuster theta -q debug-cache-quad -t 30 -A datascience —n 2 'python -m ytopt.search.ambs --evaluator ray --redis-address {redis_address} --problem ytopt.benchmark.ackley.problem.Problem'
```

`{redis_address}` will be automaticaly replaced by the head redis address of the cluster.