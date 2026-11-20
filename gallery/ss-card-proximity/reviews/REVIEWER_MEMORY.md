# Reviewer memory: ss-card-proximity

## question-r1 (2026-11-20, verdict revise)

Suspicions:
- The robustness layer (H2-H5) is fixed on Table 3 Panel A col 5 (no family background), while the headline basic spec is Panel B col 6. Watch for the paper describing the Panel A results as stressing "Card's IV estimate" (F1).
- Scout missed Cinelli & Hazlett (Biometrika 2025, iv.sensemakr): AR [0.025, 0.285] plus exclusion/confounding sensitivity (RV 0.67%) on exactly the Panel A col 5 spec. Also arXiv 2508.12474 (weak-IV-robust guide, Card example). The novelty sentence must change (F2).
- With one instrument, AR at 0 is the reduced-form t-test, and the AR-based CHR breakdown is the RF lower confidence bound (~0.007). Wald-based CHR is not weak-IV robust (F3).
- H5's "design-stage run from the first stage alone" is a pre-gate pilot and cannot produce an MDE without the outcome; the published SEs give MDE ~0.15 (F4).

Asked for: H2-H5 moved to Panel A col 6 (or col 6 primary) or narrowed wording; Cinelli-Hazlett fetched, recorded and compared; H4 interval type fixed (AR-based primary); MDE from published SEs, no pre-gate run; one primary IV-vs-OLS rule; H1 columns and seed-claim mapping explicit.

Check next time:
- plan.json H1-H5 text and contribution; sources.json has a cinelli/hazlett record; no runs/ dir entries before the design gate.
- At the design gate: does H4's code invert AR per gamma0? Is the Panel B 3-endogenous model stated as uncovered by H2-H4?
- At the results gate: SE formula used for the H1 comparison matches the pre-specified one (conventional); OLS SE .003 vs .004 knife-edge (Kling).

## question-r2 (2026-11-20, verdict pass)

F1-F6 all resolved in plan.json and sources (Steiner et al. spot-checked against arXiv 2511.16029: matches). New minors: F7 (question still says "the IV conclusion" though H2-H5 never touch Panel B col 6; contribution calls Panel A col 6 "Card's preferred"), F8 (H5 non-rejection read via MDE; should be the robust CI of the IV-OLS difference, ~[-0.04, 0.17] from published numbers).

Check next time:
- Design: F7/F8 wording carried into design and paper. H4 code inverts AR per gamma0 with robust SE of the reduced form; breakdown should equal RF lower bound (~0.010 col 6) to rounding, else a bug.
- Design: controls lists match notes sec. 5 item 6 (reg662-reg669 vs CH's reg661-reg668: same span, different omitted region); sample = non-missing lwage76, unweighted; conventional SE for H1, robust for H2-H5.
- Results: OLS SE four decimals (Kling .003 vs Card .004); H1 secondary target AR [0.025, 0.285] reproduced homoskedastically on col 5.
- Paper: no "Card's preferred" for Panel A col 6; no "average return".

## literature-r1 (2026-11-20, verdict revise)

Spot-checked against fetched sources (all held): Card WP 4483 Tables 2/3/5 page images, abstract "25-60%", p.13 "50-60 percent", 5525/3694 inconsistencies; Kling WP 7989 Table 1 + sample note; Bi et al. Table 1; Kang et al. sec. 7 (AR [0.0384, 0.2612], F 16.72); BBMT Table 3; Cinelli-Hazlett Table 2; Delbianco Table 2; Sloczynski Table 3; Carr-Kitagawa 5.1; Lee 104.7/3.43; MOP 23.11; Londschien AR [0.083, 0.352].

Suspicions / asked for:
- L1 (major): plan reads IV as "weighted average of returns for compliers" but BBMT RESET rejects rich covariates on Card (p=0.000); Tuebbicke 2023 (EmpEcon 65, 10.1007/s00181-023-02441-7) finds 2SLS 50-100% above propensity-score IV on these data; Angrist-Imbens never fetched. Asked: qualify wording (monotonicity + rich covariates; not guaranteed here), add Kling "conditional on X" claim.
- L2 (minor): chapter tables unseen; Kling labels T2-c2 / T3-c5B and pp. 201-221 vs WP numbering; Card 2001 (NBER WP 7769, Table II row 4) confirms 0.073 (0.004), 0.132 (0.049), 0.097 (0.048) for "Card 1995b". card1995chapter method not a protocol value.
- L3 (minor): c-validity-tests leans on Kitagawa abstract; Carr-Kitagawa test binarises educ>=16; c-bbmt-card is Panel A col 5; c-ivmodel-card "homoskedastic" wording.
- L4 (minor): exclusion literature on these data incomplete (Luo et al. arXiv 2206.08228; Tan 2006; Kedagni 2021; Jiang et al. 2022).

Check next time:
- plan.json contribution/H5 wording; claims for Kling conditional-on-X and BBMT caveat; refs for tuebbicke/card2001/angrist-imbens with records.
- Paper: no unqualified "weighted average of returns for compliers"; targets labelled as WP 4483 columns.
- Carry earlier checks (H4 AR inversion = RF lower bound; OLS SE .003/.004; conventional SE for H1).

## design-r1 (2026-11-20, verdict revise)

Held under attack: N/sample rule, control lists vs read1.sas, conventional (n-k) vs HC1, AR quadratic + grid, CHR breakdown = RF lower bound (my earlier check is now built in as an identity), D = -rho g, SY 16.38 / MOP 23.11, pinned versions exist on PyPI, read1.lst quarantined (fetch_data leaves it in the zip; prepare_data has no nearc4-outcome stat).

Suspicions / asked for:
- F1 (major): Panel A treats exp76 = age76 - ed76 - 6 as exogenous; Card WP p.13 (PDF p.15) says experience is endogenous if education is. RF conditioning on exp76 is a collider path. Asked: state the assumption, add a threat mapped to A6 vs B6, word H3-H5 as about the Panel A coefficient; optional subvector AR on B6.
- F2 (major): H5 interval from CF HC1 SE of rho is valid only at rho=0 (generated regressor, extra SD ~0.26|rho|) and is Wald under F~15. Asked: AR set minus OLS, or stacked-influence SE of the difference.
- F3 (major): KWW administered in 1966 (ages 14-24), correlated with schooling (Card PDF p.7) -> not pre-schooling; IQ from school records for a subset (PDF p.17). Asked: KWW on 14-15/14-17 in 1966, amend reading, IQ missingness by nearc4.
- F4-F7 minor: H3 survival should require bounded set with lower bound > 0; BASE_A is 15 cols not 16, BASE_B 13 not 14 (CODEBOOK says 13 base vars, true 14); r-cluster reading one-directional; A3 and B1/B3/B5 left out of H1 count without reason.

Check next time:
- design.identifying_assumption and threats mention exogenous experience; H3/H4 claim texts say "Panel A column 6 coefficient".
- h5-cf interval method changed; no 'treating g as fixed' as justification.
- r-balance age restriction fixed before any run; no r-balance run before the gate.
- Code review: k counts and df in ivlib; AR V matrix uses e_i u_i cross term; grid check uses same n/(n-k); CHR grid start at 0; survival flag sign.

## literature-r2 (2026-11-20, verdict pass)

Checked against sources (held): Tuebbicke Table 3 + p. 2990 (EconStor PDF); Card 2000 WP 7769 ref list p. 40 (pp. 201-222); AI TP 127 abstract (no monotonicity/covariate/complier wording); Jiang et al. Table 3; Luo et al. Table 2; GKM19 Table 3 (k-m_W=1, 5%) and pp. 489-490 homoskedasticity; GKM24 abstract; Londschien-Buehlmann p. 4; ASS projection + Lee non-extension; Sun 2018 project()/Table 2; ivmodels API.

Rulings: L1 open but downgraded to minor (contribution fixed; H5 last sentence and design.estimand still unconditional "weighted average of returns for compliers"). L2-L4 resolved.
New: L5 (minor) monotonicity doubted on these data (Tuebbicke reporting Sloczynski: reordered instrument 0.570 -> 0.289) but contribution only flags rich covariates; Tuebbicke is binary "some college", n=2988; AI cited for conditions its abstract lacks. L6 (minor) c-principal-strata: Jiang text says tau10 significant but triply robust CI (-0.01, 0.23); Luo case (iv) CI (0.00, 1.88); Luo case (i) never-taker effect significant.

Check next time (design-r2 / paper):
- H5 and design.estimand carry the contribution's qualifier; contribution mentions monotonicity doubt.
- Paper: no unqualified complier-weighted reading; c-principal-strata narrowed before cited; Tuebbicke described as binary-treatment evidence.
- Carry earlier checks (AR inversion = RF lower bound; OLS SE .003/.004; conventional SE for H1; exogenous-experience caveat on Panel A).

## design-r2 (2026-11-20, verdict pass)

F1-F7 all resolved (checked in plan.json). Held under attack: GKM19 valid for m_W = 2 with largest root (Thm 3 / Cor 4, fetched PDF pure.uva.nl); ivmodels 0.10.0 statistic x dfn = kappa_p with dfd 2980; hyp1f1 stable to kappa_1 = 1e8; stacked-IF algebra; CHR identity; k counts; age76 - 10 = age in 1966.

New minors: F8 (H3(a) survival label still 'the IV return to schooling'); F9 (H1 secondary list in hypotheses lacks A3, B1, B3, B5; CODEBOOK '13 variables'); F10 (ivmodels uses exact eq. 2.12 quantile, not GKM19's rounded-up Table 3 interpolation: 3.305 vs 3.4 at kappa_1 9.8; kappa 2981 in test vs 2980 in inverse); F11 (projection coverage check homoskedastic only).

Kill argument kept: Panel A robust results concern a pseudo-parameter; H3(b) projection pre-announced to include 0. Do NOT accept a later switch of the H3(b) primary to a robust chi2(1) or GKMC version after results: that would be a results-driven change.

Check next time (code review):
- ivlib: AR V uses e_i u_i cross term; HC1 n/(n-k) with k = 30/16; CHR breakdown = lambda - 1.96 se; H3(b) A = (1,-b0,-g1,-g2) kron I3 assertion; BFGS starts include LIML; probes at +-1000.
- h3b: kappa_1 written to metrics; GKM19 cv both ways (F10); which kappa scaling.
- check-synthetic heteroskedastic coverage (F11); runs only synthetic data; no analysis run before the gate.
- Results/paper: h3a flag wording (F8); 9/22 denominators; Panel A never 'Card's preferred'; carried checks (OLS SE .003/.004 four decimals, conventional SE for H1).

## design-r3 (2026-11-20, verdict pass)

F8-F11 resolved (plan.json, CODEBOOK lines 87-93). Checked: Scout's 37-row GKM19 Table 3 (k-m_W=1, 5%) matches the PDF text layer row for row; my own eq. (2.12) quantile at all 36 finite rows satisfies table - 0.1 - 1e-3 < q <= table + 1e-6, but tight at kappa_1 7.0 (3.0005 vs 2.999) and 29.7 (3.7004 vs 3.699); q(1000) = 3.8376. Appendix B p. 522: rounding up applies to Tables 3-7 (notes sec. 4b wrongly says unstated). ivmodels inverse 'gkm' uses dfd 2980, chi2 set as outer bound, one root per side between chi2 boundary and LIML (assumes connected set). No analysis run; Designer scratch reads no data.

New minors: F12 (3T) interpolation departs from eq. 2.13 below 0.5 (should go from (0,0)) and steps to 3.841 above 1000 (fn. 4 F; proof of Thm 5 p. 518 wants continuity); notes rounding sentence wrong. F13 H4 'robust 95% set for the return to schooling', H5 '2SLS and OLS returns are equal' are Panel A quantities. F14 H3(b) grid [-1,1]: no rule to locate a bound between grid edge and probe; 'accepted probe = unbounded' misclassifies disconnected bounded sets. Published-number sketch: chi2(3) set roughly [-0.02, 0.8] before minimisation.

Check next time (code review):
- ivlib (3T) interpolation at kappa_1 < 0.5 and > 1000 (F12); test_ivlib tolerance at kappa_1 7.0/29.7 not loosened after a failure without a logged deviation.
- h3b bound search beyond [-1,1] (F14); ivmodels gkm inverse vs own (3Q) set when set disconnected.
- Carried: AR V e_i u_i cross term; HC1 n/(n-k) with k 30/16; CHR = lambda - 1.96 se; A = (1,-b0,-g1,-g2) kron I3; BFGS starts incl. LIML; heteroskedastic coverage designs S and WN with threshold 0.921; runs only synthetic data before the gate.
- Results/paper: h3a flags 'Panel A coefficient'; H4/H5 wording (F13); 9/22 denominators; no 'Card's preferred' for A6; OLS SE four decimals (.003/.004); conventional SE for H1.

## code-r1 (2026-11-20, verdict pass)

Read every file in code/ (ivlib, h1_b6/a6/a5, h2h3_weakiv, h3b_subvector, h4_chr, h5_cf, r_age1419, r_balance, r_cluster, verdict, fig_chr, test_ivlib, fetch_data, prepare_data, requirements). Code hashes equal the check-synthetic run record. No real-data run exists.

Held under attack: k / n-k for all 14 specs; conventional and HC1 (synthetic hand-formula match); AR V cross term e_i u_i; AR quadric coefficients; CHR delta* = lambda - 1.96 se (V unchanged by the gamma0 shift); Wald CHR via beta_z = 1/pi; IF psi_IV with Xhat and D = -rho g (omitted-variable identity); HAR = a'pis, V = sum a_j a_l S_jl, gradient incl. symmetric dV; LIML kappa = 1 + min eig(P, M); GKMC quadric via Schur complement; (3T) table = notes sec. 4b (36 rows), (0,0) anchor, fn. 4 tail; verdict 9/22 targets and values = design.method. My own synthetic check: BFGS profile = 61-start Nelder-Mead + grids at 17 b0 on synthetic_card.csv (to 1e-8); profile asymptote ~18.8 there (> 7.815, so bounded); ivmodels boundaries real (0j).

Open (all minor): F1 no real-data minimisation check in h3b (anti-conservative direction if BFGS fails); F2 NOTES items 2 and 10 are design departures not in design.deviations; F3 --code must include h1_a6.py for h1-a5 and ivlib.py for verdict; F4 inner bounds of non-convex sets only as strings, fig_chr labels interior ends at grid points.

Check next time (results):
- run.json of h1-a5 lists code/h1_a6.py; verdict lists code/ivlib.py (F3). design.deviations has a D3 for F2.
- h3b metrics: b6_rob_m_at_0 vs 7.815 margin; if within ~5% of 7.815, ask for an independent minimiser value (F1). b6_ar_*_npieces = 1 for every set, else F4 bites (paper needs numeric piece bounds).
- ivmodels *_outer differences recorded; (3Q) vs ivmodels gkm passed (ivmodels root search uses max_value 1e3 x boundary gap in the unbounded case).
- check_sas_listing.py does not exist yet: it needs its own code round before it runs, and only after e-claims.
- Carried: H3(a) flags say 'Panel A coefficient'; H4/H5 wording (F13 of design-r3); OLS SE four decimals (.003/.004); conventional SE for H1; no switch of the H3(b) primary after results.
