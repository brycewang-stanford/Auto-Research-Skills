"""Write plan.json design and tasks for ss-lalonde-observational ONLY (Designer)."""
import json
from pathlib import Path

ws = Path("/Users/brycewang/Auto-Research-Skills/gallery/ss-lalonde-observational")
plan = json.loads((ws / "plan.json").read_text())
assert plan["question"].startswith("For the 185 NSW-treated men"), "wrong workspace"
tim = json.loads((ws / "runs/timing-synthetic/timing.json").read_text())
b = tim["block_seconds"]
pr = tim["projected_run_seconds"]
mult = tim["se_per_unit_outcome_sd"]

ADOPTED = ("gallery/ss-null-effect/plan.json design.method (design gate approved 2026-11-18T13:00:13Z, "
           "before this workspace was created at 16:28:21Z) and its code at commit 716b6c3: "
           "code/aipw_lib.py sha256 86435b8f...b541, code/main_aipw.py sha256 230b7b08...7bf4, "
           "code/diag_overlap.py sha256 235d2ecb...acf5")

summary = (
    "The estimand is the ATT of the NSW program on 1978 earnings (1982 dollars) for all 185 NSW-treated men of the "
    "Dehejia-Wahba subsample, identified against the 15,992 CPS-1 men by unconfoundedness given ten pre-program "
    "covariates (age, educ, black, hisp, married, nodegree, re74, re75, u74, u75) plus overlap (every treated man has "
    "a positive probability of being a CPS man at his X); no treated man is ever dropped. "
    "It is estimated by the cross-fitted AIPW ATT estimator adopted from ss-null-effect (L2-logistic propensity on "
    "B(X), gradient-boosted control outcome model on T(X), 5 folds x 5 repetitions, seeds 20261118 + s, "
    "influence-function standard errors, normal 95% interval), with every adaptation listed in method.deviations "
    "(chiefly: bases rebuilt for these ten covariates, the lower propensity clip removed because 1.1% of units are "
    "treated, and a control-only trimming rule for rob-trim), and overlap and balance are checked on covariates only "
    "before the gate (rules B1, O1, O2). "
    "H3 applies the same estimator to re75 without conditioning on re75 or u75 (fail if its 95% CI excludes 0, which "
    "takes precedence; pass only if the CI lies within [-900, 900]; otherwise inconclusive; H1 is worded as an effect "
    "only on a pass), rob-trim and rob-learners are the only robustness runs, H2 (estimate minus $1,794 with "
    "SE sqrt(SE^2 + 633^2), descriptive) is computed only after the results gate, and a Reviewer code review precedes "
    "every analysis run."
)

method = {
    "adopted_from": ADOPTED + ". Everything in that design.method that is not listed in method.deviations is "
                    "carried over unchanged: the AIPW ATT score, the propensity and outcome learners and their "
                    "hyperparameters, cross-fitting with mean aggregation, the variance rule, influence-function "
                    "SEs, the relative effect, rule B1 and its one-step escalation, rules O1 and O2, and the "
                    "outcome-validity rule for earnings.",
    "estimand": "ATT = E[re78(1) - re78(0) | treat = 1] over all 185 NSW-treated men (DW RE74 subsample), "
                "1982 dollars. Sample: 185 treated (data/raw/nswre74_treated.txt) and 15,992 CPS-1 men "
                "(data/raw/cps_controls.txt), n = 16,177, no restriction. Overlap trimming (rob-trim only) removes "
                "CPS men only, so every run targets the same estimand.",
    "identifying_assumption": "Untreated 1978 earnings are independent of being an NSW participant rather than a "
                              "CPS man, given X = (age, educ, black, hisp, married, nodegree, re74, re75, u74, u75), "
                              "and P(treat = 1 | X) < 1 for every treated man's X. What would contradict it: "
                              "treated and comparable CPS men differing in an earnings outcome that the program "
                              "cannot have affected, given the covariates available at that time; H3 is that "
                              "check (re75 given X without re75 and u75). Its limit is stated in advance: a "
                              "transitory pre-program dip in 1975 makes the placebo nonzero even if the "
                              "assumption holds given re75, so a failure is not proof that the main estimate is "
                              "biased, and a pass is only 'did not reject'. Overlap is checked on covariates "
                              "only (method.overlap_and_balance).",
    "treatment": "treat (1 = NSW treated, 0 = CPS-1), set by source file; column of data/derived/analysis_noRE78.csv.",
    "outcome": "re78, 1978 earnings in 1982 dollars (CPS: SSA administrative earnings, top-coded; NSW: survey "
               "earnings). Read only by analysis runs after the design gate, from field 10 of the raw files, "
               "using method.join_rule.",
    "join_rule": "data/derived/analysis_noRE78.csv carries the row key (src, row = 1-based line number in the raw "
                 "file). An analysis run that needs re78 parses data/raw/nswre74_treated.txt and "
                 "data/raw/cps_controls.txt, takes field 10 by (src, row), checks that fields 1-9 of each raw line "
                 "equal treat and the eight raw covariates of the derived row exactly (u74, u75 rebuilt and "
                 "compared), and stops if any row differs or is unmatched. Both raw files and the derived file are "
                 "listed as --input of the run.",
    "covariate_bases": {
        "B(X), for logistic and linear models": "age, age^2, educ, educ^2, black, hisp, married, nodegree, "
            "re74, re74^2, re75, re75^2, u74, u75: 14 terms, standardized within each training fold. "
            "Construction rule of the adopted design: continuous covariates linear and squared, binary covariates "
            "linear, no interactions (method.deviations DEV-2).",
        "T(X), for tree learners": "the ten covariates, unscaled: 10 columns (DEV-3).",
        "B+(X), escalation basis used only if rule B1 fails": "B(X) plus all pairwise products of the ten "
            "covariates, dropping any product that is constant or identical to a column already present (in "
            "these files re74 x u74, re75 x u75 and black x hisp are identically zero): "
            f"{tim['n_terms_B_plus']} terms (DEV-4).",
        "B(X-), T(X-), for the H3 placebo": "the same rules on X- = X without re75 and u75: B(X-) has "
            f"{tim['n_terms_B_minus']} terms (age, age^2, educ, educ^2, black, hisp, married, nodegree, re74, "
            "re74^2, u74), T(X-) 8 columns. If B1 escalated the primary basis to B+(X), the placebo uses B+(X) "
            "restricted to products of X- covariates. No basis choice is made from placebo-set statistics."
    },
    "primary_estimator": "Cross-fitted AIPW for the ATT, unchanged from the adopted design. Per repetition s: "
        "theta_s = sum_i [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i)] / sum_i D_i, w_i = m_i / (1 - m_i), "
        "m_i and g0_i out-of-fold. psi_s,i = [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i) - D_i theta_s] / "
        "pi_hat, pi_hat = mean(D) = 185 / 16,177; SE_s = sqrt(mean(psi_s^2) / n).",
    "propensity_learner": "Unchanged: sklearn StandardScaler + LogisticRegressionCV on B(X), L2, Cs = 10 values "
        "log-spaced on [1e-4, 1e4], inner StratifiedKFold(5, shuffle, random_state = seed of the repetition), "
        "scoring neg_log_loss, solver lbfgs, max_iter 10000. (scikit-learn 1.9.1 emits FutureWarnings about "
        "l1_ratios and legacy attributes; any argument added to silence them must leave the fit unchanged.)",
    "outcome_learner": "Unchanged: sklearn HistGradientBoostingRegressor on T(X), loss squared_error, "
        "learning_rate 0.05, max_iter 300, max_leaf_nodes 15, min_samples_leaf 20, l2_regularization 1.0, "
        "early_stopping False, random_state = seed of the repetition, fitted on the CPS men of the training folds "
        "only.",
    "cross_fitting": "Unchanged: K = 5 StratifiedKFold on treat (shuffle), S = 5 repetitions with random_state "
        "20261118 + s, s = 0..4. Stratification puts 37 treated men in every test fold and 148 in every training "
        "fold (about 118 in each inner-CV training split). theta = mean_s theta_s; Var = mean_s [SE_s^2 + "
        "(theta_s - theta)^2]; psi_bar = mean_s psi_s (DEV-7).",
    "propensity_clipping": "m_i is clipped above at 0.99 before weights are formed (largest control weight 99); "
        "there is no lower clip (DEV-5). A unit is 'clipped' if its raw out-of-fold m exceeds 0.99 in any "
        "repetition; clipped units and unit-repetition pairs are counted and reported by diag-overlap and by every "
        "analysis run. Clipping is a numerical safeguard, not a sample restriction.",
    "overlap_and_balance": "Pre-gate data-prep run diag-overlap reads data/derived/analysis_noRE78.csv only "
        "(treat and the ten covariates; it refuses to run if an re78 column exists) and uses the primary "
        "propensity fits (all S x K; m_bar_i = mean over repetitions of the unclipped out-of-fold m). Nothing is "
        "computed under X- before the gate. Reported: (a) normalized differences (x1 - x0) / sqrt(s1^2 + s0^2) "
        "for the ten covariates, |nd| > 0.25 flagged, no action; (b) ATT-weighted SMDs for every term of B(X), "
        "w = m / (1 - m) with the clipped m of each repetition, averaged over repetitions; (c) the propensity "
        "histogram by treat (log scale on m allowed); (d) share of treated with m_bar > 0.9, clipped units, Kish "
        "effective sample size of the weighted controls, the largest control weight, and the number of CPS men "
        "rob-trim removes. Rules, fixed now and unchanged from the adopted design except O2's clip definition: "
        "B1 every weighted |SMD| < 0.10, else B+(X) replaces B(X) once (run diag-overlap-ext) and is final; "
        "O1 at most 5% of treated have m_bar > 0.9; O2 at most 1% of all units are clipped. If O1 or O2 fails, "
        "the primary estimate stays the full-sample ATT and the rob-trim estimate is reported next to it in the "
        "abstract. The Designer records the B1/O1/O2 outcome, the final basis and the trimmed-control count in "
        "design.diagnostics with a logged plan.json hash before the design gate is requested.",
    "control_only_trimming": "rob-trim drops the CPS men whose m_bar lies outside [min, max] of m_bar over the "
        "185 treated men (m_bar from the primary full-sample propensity fits, unclipped); no treated man is "
        "dropped. The full estimator is re-run on the kept units (folds re-drawn with the same seeds, nuisances "
        "re-fitted); the kept set is treated as fixed for the SE. The count is fixed outcome-blind by "
        "diag-overlap (DEV-6).",
    "standard_errors": "Influence-function (heteroskedasticity-robust) SEs at the person level, mean-aggregated "
        "over repetitions as above, normal reference distribution; 95% CI = theta +/- 1.959964 SE. No clustering: "
        "treatment varies by person and the files carry no site or cluster identifier. Nuisance estimation error "
        "is treated as negligible (orthogonal score, cross-fitting).",
    "h1_test": "H1 holds iff primary-ci-low > 0 (95% CI of main-aipw entirely above zero). p = 2 (1 - Phi(|theta| "
        "/ SE)) is reported. A CI that includes zero is never reported as 'no effect'. Wording depends on H3: "
        "'effect' only if H3 = pass; otherwise 'statistical contrast between the groups'.",
    "h3_placebo": "Run placebo-re75: the primary estimator with outcome re75 (1982 dollars) and conditioning set "
        "X- = (age, educ, black, hisp, married, nodegree, re74, u74), bases B(X-) and T(X-), propensity re-fitted "
        "on B(X-), same folds, repetitions, seeds, clipping and SE rule; all 16,177 units. 95% CI = theta_p +/- "
        "1.959964 SE_p. Rule, in this order: FAIL if the CI excludes 0 (takes precedence); otherwise PASS if "
        "-900 <= ci_low and ci_high <= 900; otherwise INCONCLUSIVE. The bound 900 is fixed (half the benchmark, "
        "set at the question gate). A pass is worded only as 'the placebo did not reject', never as evidence that "
        "the assumption holds. If FAIL or INCONCLUSIVE, H1 is reported as a statistical contrast between groups. "
        "The run also reports, descriptively, its clipped-unit count, Kish ESS and weighted SMDs on B(X-); no rule "
        "or basis change depends on them. re75 is top-coded for CPS men (3,007 at the maximum) and not for NSW "
        "men; this is stated with the result.",
    "h2_descriptive": "Run h2-benchmark, after the results gate is approved: reads runs/main-aipw/metrics.json; "
        "diff = theta - 1,794; se_comb = sqrt(SE^2 + 633^2), where 633 is the SE published with the benchmark "
        "(DW 1999 Table 3, the value named in design_constraints; the robust 670.82 is not used); reports diff, "
        "se_comb and diff +/- 1.959964 se_comb. The two estimates share the 185 treated men, so their covariance "
        "is positive and se_comb overstates the uncertainty (stated with the number). Descriptive only: no test "
        "language, no ranking or choice of estimators. No file written before the results gate contains a "
        "comparison of any estimate with the benchmark.",
    "relative_effect": "Unchanged: r = theta / (mu1 - theta), mu1 = mean(re78 | treat = 1), delta-method 95% CI "
        "from psi_r = [mu1 psi_theta - theta psi_mu] / (mu1 - theta)^2, psi_mu = D (Y - mu1) / pi_hat; mu1 - "
        "theta is reported as the estimated counterfactual mean.",
    "outcome_validity": "Unchanged rule for earnings: re78 (and re75 in the placebo) admissible if finite and >= 0, "
        "with the adopted sentinel rule (a value in {999, 9999, 99999, 999999, 9999999} above every other "
        "admissible value is inadmissible). Inadmissible or missing values: complete cases, counted by arm and "
        "reported by the run; values are never recoded, winsorized or imputed, and the CPS top-code is left as "
        "it is. re75 has 0 missing and 0 negative values (data/prepare_metrics.json); re78 is not examined "
        "before the gate (DEV-10).",
    "deviations": [
        "DEV-1 Covariates. Adopted: eleven covariates of the synthetic file (age, educ, married, urban, region, "
        "children, health_limit, re74, re75, unemp74, unemp75). Here: the ten covariates these files provide or "
        "imply (age, educ, black, hisp, married, nodegree, re74, re75, u74, u75), with u74 = 1[re74 = 0] and u75 = "
        "1[re75 = 0], the same definition as the adopted unemp74/unemp75. Reason: the variables in the data; no "
        "covariate available in the files is left out, and none is added.",
        "DEV-2 Logistic basis B(X). The adopted construction rule (continuous covariates linear and squared, "
        "binaries linear, no interactions, standardized within training folds) applied to these covariates gives "
        "14 terms; region dummies disappear because there is no region variable. Reason: the rule is carried "
        "over, only the variable list changes. It is not the published propensity specification for this sample "
        "(which adds age^3 and educ x re74 after a balance search); adopting a rule rather than a specification "
        "avoids choosing terms. nodegree equals 1[educ < 12] in these files; it is kept because it is a listed "
        "covariate and is not a linear combination of educ and educ^2.",
        "DEV-3 Tree basis T(X): the ten covariates unscaled (10 columns; adopted: 14 with region one-hot). "
        "Reason: same rule (all covariates, numeric, unscaled), new variable list.",
        f"DEV-4 Escalation basis B+(X): B(X) plus all pairwise products of the ten covariates ({tim['n_terms_B_plus']} "
        "terms), dropping products that are constant or duplicate a column (re74 x u74, re75 x u75, black x hisp "
        "are identically zero here). Adopted: pairwise products of its ten non-region covariates plus region x "
        "{re74, re75}. Reason: same rule restated for these variables; a constant column carries no information "
        "and only slows the solver.",
        "DEV-5 Propensity clipping. Adopted: clip to [0.01, 0.99]. Here: upper clip 0.99 only. Reason: 185 of "
        "16,177 units (1.14%) are treated, so the average propensity is 0.0114 and a floor of 0.01 would bind for "
        "a large share of CPS men, raising each one's weight m / (1 - m) to at least 0.0101; that reweights the "
        "comparison group rather than guarding against numerical failure. In the ATT score m enters only as m / "
        "(1 - m) for controls, which is bounded as m -> 0, so no floor is needed numerically. The upper clip, which "
        "caps a control's weight at 99, is the numerical safeguard and is kept. O2 counts units clipped above.",
        "DEV-6 Trimming. Adopted: rob-trim keeps units with m_bar in [0.1, 0.9], which drops treated units and "
        "changes the estimand. Here: rob-trim drops only CPS men with m_bar outside the range of m_bar among the "
        "185 treated (method.control_only_trimming); the primary estimate is untrimmed, as adopted. Reason: "
        "design_constraints forbid dropping treated men; for the ATT, a CPS man whose propensity lies outside the "
        "treated range has no treated man at a comparable propensity, so removing him leaves the estimand "
        "unchanged and tests only dependence on extrapolation by the outcome model.",
        "DEV-7 Folds, repetitions, seeds: no change (K = 5 stratified on treat, S = 5, seeds 20261118 + s, inner "
        "5-fold CV with the same seeds). Listed so that 'unchanged' is a checked statement: with 185 treated, "
        "stratification gives 37 treated per test fold and 148 per training fold, enough for a 14-term L2 logit; "
        "increasing S or K would be a choice made for this sample, and the between-repetition variance term "
        "already reports split noise.",
        "DEV-8 Units: 1982 dollars as in the files (adopted: nominal units of a synthetic file).",
        "DEV-9 Components dropped because they answer hypotheses this question does not have or add estimators "
        "or assumptions outside the approved H1-H3: H1b (TOST against margin M) and data-prep run margin; the "
        "five-outcome secondary family with Romano-Wolf and max-t; select-re75 (its specification becomes H3's, "
        "now with a decision rule, as the approved question requires); rob-covsets; rob-diff74; rob-estimators "
        "(OLS, IPW); rob-ipow; sens-imbens. Reason: keeping the plan to the approved hypotheses limits the "
        "number of reported forks; none of them was dropped for what it might show on this sample.",
        "DEV-10 Pre-gate outcome counts (missing-counts, range-counts) are not run, because RE78 is set aside "
        "before the gate (design_constraints). main-aipw counts missing and inadmissible re78 values by arm and "
        "applies the adopted complete-case rule; nothing else depends on the counts.",
        "DEV-11 Disagreement rule restricted to the robustness runs kept: rob-trim, rob-learners (a), rob-learners "
        "(b) (adopted rule otherwise unchanged; see threats).",
        "DEV-12 The re75 placebo outcome carries the same outcome-validity rule as re78; the placebo's propensity "
        "is re-fitted on B(X-) (as in the adopted select-re75)."
    ],
}

data = ("Source: data/raw/nswre74_treated.txt (185 rows) and data/raw/cps_controls.txt (15,992 rows) from "
        "https://users.nber.org/~rdehejia/data/ (dehejiadata), fetched by data-prep run fetch-data and recorded in "
        "data/manifest.json; the experimental control file is never fetched. Working file: "
        "data/derived/analysis_noRE78.csv (data-prep run prepare-data): src, row, treat, age, educ, black, hisp, "
        "married, nodegree, re74, re75, u74 = 1[re74 = 0], u75 = 1[re75 = 0]; no re78. Unit: man; n = 16,177 "
        "(185 treated, 15,992 CPS-1); no sample restriction, no missing covariate. Outcome re78 (1982 dollars) is "
        "joined by the first analysis run after the gate (method.join_rule). Covariate facts relevant to overlap, "
        "from the codebook: CPS re74 and re75 are top-coded (3,052 and 3,007 men at the maximum); one treated man's "
        "re74 (35,040) exceeds every CPS value; no man is both black and hispanic; nodegree = 1[educ < 12].")

analysis_plan = [
    "fetch-data, prepare-data (data-prep, data-ra, before the gate): fetch the two files, write the RE78-free "
    "working file and codebook. Purpose: data without the outcome.",
    "timing-synthetic (data-prep, designer, done before the gate): runtime of every planned run on the real "
    "covariates and treatment with a synthetic N(0,1) outcome; the placebo-set propensity is timed with a "
    "permuted (synthetic) treatment so nothing is fitted under X- with the real treatment. Purpose: fit the "
    "30-minute budget (design.runtime).",
    "diag-overlap (data-prep, econometrician, before the gate): method.overlap_and_balance on the full covariate "
    "set only; rules B1, O1, O2; clipped-unit count; Kish ESS; largest control weight; number of CPS men rob-trim "
    "removes; propensity histogram. diag-overlap-ext only if B1 fails. Purpose: fix the basis, the trimming count "
    "and the reporting branch before any outcome is read.",
    "code-review (Reviewer, review target 'code', before ANY analysis run): the Reviewer reads every analysis "
    "script (code/aipw_lib.py, main_aipw.py, placebo_re75.py, rob_trim.py, rob_learners.py, h2_benchmark.py) "
    "against design.method and checks: the estimator matches the adopted code except for the listed deviations; "
    "re78 is read only through method.join_rule; placebo_re75.py never reads re78 and never conditions on re75 or "
    "u75; no script except h2_benchmark.py contains the benchmark; seeds, folds and clip are as fixed. No analysis "
    "run starts while the latest code review has an open critical or major finding; a script changed after review "
    "is re-reviewed.",
    "main-aipw (analysis): primary ATT on re78. Metrics: effect, se, ci_low, ci_high (95%), p, n, n_treated, "
    "n_control, clipped units, missing and inadmissible re78 counts by arm, treated mean, counterfactual mean, "
    "relative effect and its CI, per-repetition thetas and SEs, O1/O2 shares, Kish ESS, largest control weight. "
    "Purpose: H1; required claims primary-effect, primary-ci-low, primary-ci-high.",
    "placebo-re75 (analysis): method.h3_placebo; metrics effect, se, ci_low, ci_high, verdict (pass / fail / "
    "inconclusive, also coded 1 / -1 / 0), clipped units, Kish ESS. Purpose: H3, and the wording of H1.",
    "rob-trim (analysis): method.control_only_trimming; effect, se, CI, n_control kept and dropped, H1 decision. "
    "Purpose: dependence on CPS men outside the treated propensity range (same estimand).",
    "rob-learners (analysis): primary score with (a) parametric nuisances, LogisticRegressionCV on B(X) and OLS of "
    "re78 on B(X) among CPS men; (b) random forests, RandomForestClassifier and RandomForestRegressor, 500 trees, "
    "min_samples_leaf 5, max_features 'sqrt', on T(X); same folds, repetitions, seeds and clip (adopted settings). "
    "Purpose: dependence on the learner.",
    "claims (econometrician, then results gate): result claims from main-aipw, placebo-re75, rob-trim, "
    "rob-learners with the ids in design.claim_ids; the H3 verdict and the H1 wording rule applied as fixed.",
    "h2-benchmark (analysis, econometrician, only after the results gate is approved): method.h2_descriptive. "
    "Purpose: H2, descriptive.",
    "figures (figures-ra): propensity histogram by group (covariates only); forest plot of main-aipw, rob-trim, "
    "rob-learners (a), (b) and the placebo with zero marked; the benchmark appears in a figure only after the "
    "results gate."
]

threats = [
    "Selection on unobservables, in particular the pre-program earnings dip: if treated men's low 1975 earnings "
    "were transitory while comparable CPS men's were permanent, conditioning on re75 compares unlike men. Addressed "
    "only by H3 (placebo-re75), which the dip can make fail even if the assumption holds given re75; its result "
    "decides the wording of H1 and is reported whatever it is. There is no sensitivity analysis (DEV-9); the paper "
    "states that the assumption is untested beyond H3.",
    "Outcome measurement differs: CPS earnings are SSA administrative records top-coded at the Social Security "
    "maximum, NSW earnings are survey reports. Cannot be fixed with these files; stated as a limitation. The same "
    "difference affects re75 in the placebo.",
    "Comparison men come from national samples and different local labour markets, and the CPS file is "
    "pre-screened on income and labour-force status. Stated as limitations; no run addresses them.",
    "Dependence on the Dehejia-Wahba subsample: the estimand is defined for these 185 men; no claim is made "
    "about NSW men in general.",
    "Limited overlap and extreme weights with 1.1% treated: a few CPS men can carry much of the control weight, "
    "and one treated man's re74 lies above every CPS value (top-coding). Addressed by diag-overlap (B1, O1, O2, "
    "Kish ESS, largest weight, all before the gate), the clipped-unit count, rob-trim (control-only) and "
    "rob-learners.",
    "Misspecified nuisance models: addressed by double robustness, rule B1 with one fixed escalation, and "
    "rob-learners (parametric and random forest).",
    "Small treated sample (185): the normal approximation to the influence-function SE may under-cover; the "
    "per-repetition estimates and SEs are reported so split noise is visible. Not otherwise corrected.",
    "Literature-aware adaptation: every adaptation of the adopted estimator is a choice made by people who know "
    "the published results on this sample. Addressed only by listing each one in method.deviations with a reason "
    "that does not rest on those results, by logging the plan.json hash before the gate, and by disclosure in the "
    "paper.",
    "Specification search after outcomes are opened: estimator, bases, learners, seeds, folds, clip, trimming "
    "rule, placebo specification and every decision rule are fixed here; every run is reported; analysis code is "
    "reviewed before it runs.",
    "An H3 that cannot pass: if the placebo's SE exceeds 459, a pass is impossible and H3 can only fail or be "
    "inconclusive (design.runtime gives the outcome-free precision multiplier). Either way H1 is then reported "
    "as a contrast; the paper states this, and the bound 900 is not changed.",
    "Benchmark sampling error: H2 uses a combined SE (overstated, since the treated men are shared) and is "
    "descriptive; closeness is never used to choose or rank estimators.",
    "Rule for disagreement, fixed now: if the H1 decision (95% CI entirely above zero or not) differs between "
    "main-aipw and rob-trim, rob-learners (a) or rob-learners (b), the abstract says the conclusion is not robust "
    "to that check. The primary estimate is never replaced."
]

against = {
    "H1": "Counts against H1: the 95% CI of main-aipw includes zero or lies below it. If H3 is not 'pass', H1's "
          "result is reported as a statistical contrast whatever it is.",
    "H2": "Descriptive; nothing counts for or against it, and it is computed only after the results gate.",
    "H3": "Fails if the placebo 95% CI excludes zero (precedence); passes only if the CI includes zero and lies "
          "within [-900, 900]; otherwise inconclusive."
}

claim_ids = {
    "required_by_seed": "primary-effect, primary-ci-low, primary-ci-high (95% CI, 1982 dollars; run main-aipw, "
                        "metrics effect, ci_low, ci_high)",
    "primary": "primary-se, primary-p, primary-n, primary-n-treated, primary-n-control, primary-n-clipped, "
               "primary-treated-mean, primary-cf-mean, primary-rel-effect, primary-rel-ci-low, primary-rel-ci-high, "
               "primary-re78-invalid-treated, primary-re78-invalid-control, overlap-treated-above-09, "
               "overlap-kish-ess, overlap-max-control-weight (all run main-aipw)",
    "placebo": "placebo-effect, placebo-se, placebo-ci-low, placebo-ci-high, placebo-verdict (1 pass, 0 "
               "inconclusive, -1 fail), placebo-n-clipped (run placebo-re75)",
    "robustness": "trim-effect, trim-ci-low, trim-ci-high, trim-n-control-kept, trim-n-control-dropped (run "
                  "rob-trim); learner-linear-effect, learner-linear-ci-low, learner-linear-ci-high, learner-rf-effect, "
                  "learner-rf-ci-low, learner-rf-ci-high (run rob-learners)",
    "h2_after_results_gate": "h2-diff, h2-se-combined, h2-ci-low, h2-ci-high (run h2-benchmark)"
}

worst = tim["projected_total_minutes_if_Bplus"]
runtime = (
    f"Measured by data-prep run timing-synthetic on the real covariates and treatment (n = {tim['n']}, "
    f"{tim['n_treated']} treated) with a synthetic N(0,1) outcome (Apple M3, 8 cores; runs/timing-synthetic/"
    f"timing.json): one propensity cross-fit on B(X) (5 x 5 LogisticRegressionCV) {b['A_propensity_crossfit']:.1f} s; "
    f"on B(X-) with a synthetic treatment {b['Aminus_propensity_crossfit_synthetic_treat']:.1f} s; on B+(X) "
    f"{b['Aplus_propensity_crossfit']:.1f} s; one outcome cross-fit (gradient boosting on T(X)) "
    f"{b['G_outcome_crossfit']:.1f} s; linear outcome {b['linear_outcome_crossfit']:.1f} s; random-forest propensity "
    f"{b['rf_propensity_crossfit']:.1f} s and outcome {b['rf_outcome_crossfit']:.1f} s. Projected per run (3 s "
    f"start-up each): " + ", ".join(f"{k} {v:.0f} s" for k, v in pr.items()) +
    f" (rob-trim at full-sample cost, an upper bound). Total {tim['projected_total_minutes']:.1f} minutes; "
    f"{worst:.1f} minutes if B1 fails and B+(X) is used throughout; budget 30 minutes (about 6x headroom), so "
    f"nothing is cut or resized for time. Precision multiplier (same run, outcome-free): the primary estimator's "
    f"SE for a unit-variance noise outcome with the real full-set propensity is {mult:.3f} (includes the cost of "
    f"ATT weighting, no gain from covariate adjustment). Implication for H3, stated before any placebo statistic "
    f"exists: a pass needs the whole 95% CI inside [-900, 900], i.e. SE_p < 459 even at a zero estimate, which "
    f"under this multiplier needs a residual SD of re75 given X- below about {459 / mult:,.0f} dollars; that SD is "
    f"not computed before the gate (it is a placebo-set statistic), so H3 may be unable to pass and end "
    f"'inconclusive' even with a zero placebo estimate."
)

plan["design"] = {
    "summary": summary,
    "method": method,
    "data": data,
    "analysis_plan": analysis_plan,
    "threats": threats,
    "against_each_hypothesis": against,
    "claim_ids": claim_ids,
    "runtime": runtime,
    "diagnostics": {"status": "pending: diag-overlap has not run; B1/O1/O2, final basis and trimmed-control "
                              "count are recorded here before the design gate is requested"},
}

plan["tasks"] = [t for t in plan["tasks"] if t["id"] == "q-novelty"] + [
    {"id": "d-data", "title": "Run fetch-data and prepare-data: raw files, RE78-free working file "
     "data/derived/analysis_noRE78.csv, manifest and codebook", "owner": "data-ra", "status": "done"},
    {"id": "d-design", "title": "Write plan.json design and tasks; runtime check timing-synthetic (data-prep, "
     "synthetic outcome)", "owner": "designer", "status": "done"},
    {"id": "d-diag", "title": "Run diag-overlap (data-prep, full covariate set only, before the gate), and "
     "diag-overlap-ext if B1 fails; report B1/O1/O2, clipped units, Kish ESS, largest weight, rob-trim count",
     "owner": "econometrician", "status": "todo"},
    {"id": "d-diag-record", "title": "Record the diag-overlap outcome in design.diagnostics and log the plan.json "
     "hash before the gate request", "owner": "designer", "status": "todo"},
    {"id": "r-design", "title": "Review the design (target design) before the gate", "owner": "reviewer",
     "status": "todo"},
    {"id": "a-code", "title": "Write analysis scripts aipw_lib.py, main_aipw.py, placebo_re75.py, rob_trim.py, "
     "rob_learners.py, h2_benchmark.py per design.method (no run)", "owner": "econometrician", "status": "todo"},
    {"id": "r-code", "title": "Code review (target code) of every analysis script before any analysis run",
     "owner": "reviewer", "status": "todo"},
    {"id": "a-main", "title": "Run main-aipw: primary ATT on re78 (H1)", "owner": "econometrician",
     "status": "todo"},
    {"id": "a-placebo", "title": "Run placebo-re75: H3 placebo, outcome re75 given X without re75 and u75",
     "owner": "econometrician", "status": "todo"},
    {"id": "a-trim", "title": "Run rob-trim: control-only treated-range trimming", "owner": "econometrician",
     "status": "todo"},
    {"id": "a-learners", "title": "Run rob-learners: parametric and random-forest nuisances",
     "owner": "econometrician", "status": "todo"},
    {"id": "a-claims", "title": "Write result claims with the ids in design.claim_ids, including primary-effect, "
     "primary-ci-low, primary-ci-high", "owner": "econometrician", "status": "todo"},
    {"id": "a-h2", "title": "After the results gate only: run h2-benchmark (H2, descriptive) and add its claims",
     "owner": "econometrician", "status": "todo"},
    {"id": "f-figures", "title": "Propensity histogram; forest plot of primary, robustness and placebo (benchmark "
     "only after the results gate)", "owner": "figures-ra", "status": "todo"},
]

(ws / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
print("written", ws / "plan.json")
