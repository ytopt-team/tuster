# Tuster: TUning clUSTER


## Quick start

```
$ tuster theta -q debug-cache-quad -t 30 -A datascience —n 2 ‘python -m ytopt.search.ambs --evaluator ray --redis-address {redis_address} --problem ytopt.benchmark.ackley.problem.Problem'
```