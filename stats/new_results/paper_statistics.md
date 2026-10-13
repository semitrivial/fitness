# Simulation results (generated from the updated exports)

Fitness means winners / (winners + losers), among organisms with exactly
one outcome flag. Foods are ever-eaten exposures and can overlap; these
are descriptive associations, not causal effects. Organisms share a run,
so organism-level binomial intervals would be misleading.

Runs: 3,123; extinct: 393.
Organisms: 752,311,817; winner-only: 577,576,571; loser-only: 171,501,993; both: 6,217; unresolved: 3,227,036.

## Fitness by food (pooled organism counts)

| Food | Winners | Losers | Fitness | Runs with exposure |
|---|---:|---:|---:|---:|
| Normal | 24,957,280 | 7,572,212 | 0.767220 | 3,003 |
| StrlFutDescs | 1,222,987 | 1,337,362 | 0.477664 | 2,830 |
| StrlAllDescs | 125 | 2,564,553 | 0.000049 | 2,845 |
| StrlFutDescsBonus | 1,220,135 | 1,338,680 | 0.476836 | 2,821 |
| StrlAllDescsBonus | 137 | 2,564,675 | 0.000053 | 2,853 |
| FrtlBonus | 2,101,611 | 454,259 | 0.822268 | 2,809 |
| Insanity | 1,716,655 | 845,967 | 0.669882 | 2,778 |
| Shortsighted | 1,957,547 | 601,541 | 0.764939 | 2,799 |

## Fitness by number of children

| Children | Winners | Losers | Fitness |
|---:|---:|---:|---:|
| 0 | 0 | 108,233,010 | 0.000000 |
| 1 | 148,004,675 | 45,741,321 | 0.763911 |
| 2 | 188,414,209 | 12,715,892 | 0.936778 |
| 3 | 134,167,016 | 3,270,658 | 0.976203 |
| 4 | 68,187,983 | 1,020,505 | 0.985255 |
| 5 | 26,988,451 | 354,819 | 0.987024 |
| 6 | 8,729,533 | 118,757 | 0.986579 |
| 7 | 2,378,513 | 34,842 | 0.985563 |
| 8 | 559,543 | 9,348 | 0.983568 |
| 9 | 117,599 | 2,167 | 0.981906 |
| 10 | 22,922 | 539 | 0.977026 |
| 11 | 4,574 | 104 | 0.977768 |
| 12 | 1,067 | 23 | 0.978899 |
| 13 | 318 | 7 | 0.978462 |
| 14 | 117 | 1 | 0.991525 |
| 15 | 35 | 0 | 1.000000 |
| 16 | 13 | 0 | 1.000000 |
| 17 | 2 | 0 | 1.000000 |
| 18 | 1 | 0 | 1.000000 |

## Run-level context

Run-level denominators and food-specific counts are in food_by_run.csv.
Pooled proportions weight runs by the number of organisms exposed; they
are not averages over independent simulations. Extinct runs and unresolved
organisms are retained in the audit but excluded from the fitness denominator.
Food timing, offspring, age and winner timing are preserved in the Parquet
parts for later sensitivity analyses. Differences in food or children
fitness cannot by themselves establish an effect of exposure or crowding.
