<!-- Written by Anthropic Claude Opus 5.5 (via Hermes Agent). -->
# Proposed statistics for fit.tex (not yet in the paper)

Sources: stats/new_results/organisms.parquet.parts (752,311,817 organisms, 3,123 runs),
runs.csv, food_by_run.csv. Scratch scripts: stats/exploration/fit_explore.py, stats/exploration/fit_runs.py,
stats/exploration/fit_timing.py,
stats/exploration/fit_cluster.py, stats/exploration/fit_bonus.py (sections H, I). Fitness = winners / (winners + losers).

## A. Corrections / facts the current text should reflect
1. Run count is now 3,123 (paper: 2,488). 393 went extinct and 2,730 survived all 100,000 turns.
2. The latest extinction happened at turn 262. The paper says "if the species survived more
   than 200 turns, it never went extinct", which is false for this data (mean extinction turn 128).
3. StrlAllDescs(+Bonus) fitness is not exactly 0 in the pooled data (125 and 137 winners).
   Every one of those winners is in an extinct run: sim.py marks every organism a winner
   when the last organism dies. The 6,217 "both winner and loser" organisms are the same
   artifact. Recommendation: report food fitness on surviving runs only. There, both
   StrlAllDescs foods are exactly 0.
4. Unresolved organisms: 3,227,036 (0.43%). Every resolved organism was resolved within
   209 turns of birth (median: losers 80 turns, winners 106 turns; 99th percentile about 160),
   so discarding organisms from the last few hundred turns of a 100,000-turn run adds very
   little truncation bias. That justifies the paper's "discarded" sentence.

## B. Food table with run-clustered uncertainty (surviving runs, 2,730)
Run-clustered bootstrap 95% CI (2,000 resamples of whole runs):

  Normal             0.76722 [0.76706, 0.76737]
  StrlFutDescs       0.47764 [0.47703, 0.47824]
  StrlAllDescs       0      (exact)
  StrlFutDescsBonus  0.47682 [0.47617, 0.47743]
  StrlAllDescsBonus  0      (exact)
  FrtlBonus          0.82226 [0.82179, 0.82271]
  Insanity           0.66988 [0.66929, 0.67046]
  Shortsighted       0.76493 [0.76440, 0.76544]

Paired within-run differences (each run is its own control):
  Frtl - Normal:          +0.0551 [+0.0546, +0.0556]; Frtl higher in 100% of runs
  Normal - Insanity:      +0.0973 [+0.0967, +0.0979]; Normal higher in 100% of runs
  Normal - Shortsighted:  +0.0023 [+0.0017, +0.0028]; Normal higher in only 55.7% of runs
  StrlFut - StrlFutBonus: +0.0008 [-0.0000, +0.0017]; 51.8% of runs (not distinguishable)

Suggested narrative: the Shortsighted footnote is now quantified. The penalty is real at
the run level but tiny (about 0.2 percentage points), and a single run cannot reliably
show it. The StrlFutDescs vs Bonus gap is NOT statistically established, so the
"surprising finding" bullet should be softened to "indistinguishable".

## C. Timing matters: when the food is eaten (53 sampled runs, parent-child join)
  StrlFutDescs eaten before first child:  fitness 0.0001 (n=12,947)
  StrlFutDescs eaten after first child:   fitness 0.844  (n=25,674)
  StrlFutDescsBonus before/after:         0.0001 / 0.846
  Insanity before/after:                  0.832 / 0.889
  Shortsighted before/after:              0.876 / 0.909
  FrtlBonus before/after:                 0.902 / 0.926
  (Organisms with no children: 0 in every group.)

Suggested narrative: this is a strong illustration of the methodology. The fitness of an
action is context-dependent, as the paper already hints: "sterilize future offspring" is
fatal before reproduction and nearly harmless after it. The ~0.48 headline number is a mix
of two very different populations.

CORRECTED by section H (304-run sample): the before-first-child share is identical
(43.8% for both foods), so the gap is not explained by composition. See H.

## H. StrlFutDescs vs StrlFutDescsBonus deep dive (304 surviving runs, 567k eaters of one only)
  Plain: fitness 0.4795, 0.99 fertile kids (born before eating), 0.99 sterile kids after eating
  Bonus: fitness 0.4780, 0.99 fertile kids, 1.41 sterile kids (+42%)
  Eating age and P(no children before eating) are identical for the two foods.
  Fitness by number of fertile kids (Plain / Bonus): 0: .002/.002; 1: .760/.757;
    2: .934/.932; 3: .976/.972
  Standardized to the same fertile-kid mix: 0.4795 vs 0.4779 (gap 0.16 pp)
  P(at least one pre-eating child is a winner) is about equal to fitness (0.852 / 0.849).
  So an eater wins only through its fertile children.
  Holding fertile kids = 2 fixed, fitness by number of sterile kids:
    1: .941, 2: .935, 3: .931, 4: .920 (0 sterile kids: .929, which is confounded)
Narrative: the paper's crowding story is supported in direction. The bonus produces ~40%
more sterile offspring, and at a fixed number of fertile children, each extra sterile child
is associated with a lower chance that a fertile child wins. The size is tiny, though
(~0.2-0.4 pp), and the run-level paired gap is borderline (CI just touches 0).

## I. Clustering on birth-time blocks (run x 5,000-turn blocks, 54,600 clusters)
Design effects are about 1.0-1.2. So clustering by run or by time block hardly widens the
intervals: organisms from the same run/time are close to independent for these proportions.
Fitness is flat across time blocks (e.g. Normal 0.767-0.769), except in:
  first block (0-5k turns): slightly lower (Normal 0.764): start-up transient
  last block (95k-100k): lower (Normal 0.752): end-of-run truncation. Late-born organisms
    get resolved only if they lose quickly, so losers are over-represented there.
Suggestion: a sensitivity table that drops the first and last 5,000 turns (the ranking is
unchanged). Paired within-block gaps: Normal-Shortsighted +0.0022 [+0.0017, +0.0028];
Plain-Bonus +0.0008 [-0.0001, +0.0017].

## D. Confounding by survival: who gets to eat
  No food at all:           0.7788
  All resolved organisms:   0.7710
  Ate Normal food:          0.7672
  Among parents only (>=1 child): baseline 0.9013, Normal 0.8985, Shortsighted 0.8992,
    Insanity 0.8753, Frtl 0.9174, StrlFut 0.5594, StrlFutBonus 0.5318
  Ate only this one special food: StrlFut 0.4819, Frtl 0.8309, Insanity 0.6736, Shortsighted 0.7707

Suggested caveat: "Normal" is not a neutral control. Normal eaters score slightly below
organisms that ate nothing. Fitness scores therefore compare food types with each other
(as the paper says: relative, not absolute), and they include which organisms tend to eat
at all. Food co-occurrence is rare enough that the exclusive-eater numbers match the
headline table to within about 0.01.

## E. Dose response (number of times eaten)
  StrlFutDescs 1x: 0.478, 2x: 0.348
  Insanity     1x: 0.670, 2x: 0.613
  Shortsighted 1x: 0.765, 2x: 0.731
  FrtlBonus    1x: 0.822, 2x: 0.821
Multiple meals are rare (thousands of organisms, not millions) and they overlap with living
longer. Treat this as a possible footnote only.

## F. Children-count curve
The new data show the rise and then a mild decline more clearly than before: the peak is at
5 children (0.9870), falling to 0.9770 at 10 children. The n=14..18 points (n <= 118) should
get CIs or be merged; at 15+ children the data are 100% winners from only 51 organisms.

## G. Age at death
All resolved organisms died at age >= 76 (the old-age hazard starts after 75, and no one
starved earlier). Within each age band the ranking Normal > Shortsighted >> Insanity holds.
At age 76: all 0.760, Shortsighted 0.752, Insanity 0.657. At age 90: 0.809 / 0.804 / 0.709.
So the Shortsighted and Insanity penalties are not explained by lifespan.
