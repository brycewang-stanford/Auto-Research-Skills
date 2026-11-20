# Scout notes: q-novelty (Senate incumbency RD replication)

Verified on 2026-11-20. Full texts were downloaded with curl into the session scratchpad and read with pdftotext -layout; the data file was not downloaded.

## 1. Published estimate (primary target)

Source: Calonico, Cattaneo, Farrell and Titiunik (2017), "rdrobust: Software for regression-discontinuity designs", Stata Journal 17(2): 372-404 (`calonico2017rdrobust`). Full text: https://ageconsearch.umn.edu/record/340181/files/Calonico.pdf (sha256 c41e81d2b3763ea5e2ac060747f7c6a22cf6ae3f7fd27d44dfece82e2fe63c8a). Metadata also confirmed on the IDEAS/RePEc page. The DOI is not printed in the PDF or on IDEAS, and the publisher page blocked fetching, so no DOI is recorded.

Location: Section 7 "Illustration of new methods", subsection 7.2 "Default results and backward compatibility", p. 392, output of `rdrobust vote margin`:

- Data: rdrobust_senate.dta, N = 1,297 with a non-missing outcome (595 left, 702 right of the cutoff, of 1,390 rows). Outcome `vote` (Democratic vote share in the election six years later, i.e. t+2). Running variable `margin` (Democratic margin of victory at t). Cutoff 0.
- Specification: sharp RD, local polynomial, order p = 1 (estimation), q = 2 (bias), triangular kernel, bandwidth selector mserd (MSE-optimal, common bandwidth), VCE method NN (nearest-neighbour, default 3 matches), robust bias-corrected inference.
- Bandwidths: h = 17.708 on both sides, b = 27.984, rho = 0.633. Effective N 359 (left) and 322 (right).
- Conventional estimate: 7.416, SE 1.4604, z 5.0782, p < 0.001, CI [4.55378, 10.2783].
- Robust bias-corrected CI: [4.09441, 10.9255] (z 4.3095). The article prints no bias-corrected point estimate; the robust row shows "-". The text on p. 396 calls 7.416 "the MSE-optimal point estimate (without covariates)".
- Software: the article describes the "2016 version" of rdrobust and reports timings in Stata 14.2 (Table 1 note). No exact package version number is printed.

Other locations in the same article (all from the fetched text):
- p. 393 (section 7.2): manual bandwidths h = 16.79369, b = 27.43745 (the 2014 bandwidths) give conventional 7.4253, SE 1.4954, CI [4.49446, 10.3561], robust CI [4.06975, 10.9833]. These match the earlier rdrobust (CCT 2014) numbers.
- p. 396 (section 7.4): covariate-adjusted conventional estimate 6.860 with fixed bandwidths; 6.851 with re-selected bandwidth (h = 17.987).
- p. 398 (section 7.4): state-clustered NN variance gives robust CI [4.091, 11.046] (50 clusters).
- p. 397 (section 7.4, covariate balance): robust p-values for predetermined covariates: class -0.021 (p = 0.897), termshouse -0.173 (p = 0.561), termssenate -0.192 (p = 0.901), population -318,455 (p = 0.634).

The data source and the 1,390 rows are described on p. 390. The four covariates in the seed data (class, termshouse, termssenate, population) and the state and year identifiers are listed there. The file does NOT contain the other covariates used in CFT 2015 (see section 3).

## 2. Data source and prior use

Cattaneo, Frandsen and Titiunik (2015), "Randomization Inference in the Regression Discontinuity Design: An Application to Party Advantages in the U.S. Senate", Journal of Causal Inference 3(1): 1-24, DOI 10.1515/jci-2013-0010 (`cattaneo2015randomization`). Full text was taken from a third-party mirror (https://nbviewer.org/github/Mixtape-Sessions/Regression-Discontinuity/raw/main/Readings/CattaneoFrandsenTitiunik2015-JCI.pdf, sha256 d69cc5000b5e314eee480b172985a5a0c372c7f5b54cc8059f1232942a733aa4). The title, authors and DOI printed in the fetched text match the publisher record.

What it shows (Section 5, Table 3, p. 15):
- Sample: 1,390 Senate elections, 1914-2010. Running variable demmv (Democratic margin at t). Outcome Democratic vote share at t+2 (Design I). The Design II placebo outcome (other seat, t+1) is in the paper's data but not in the seed file.
- Conventional estimates: 4th-order parametric fit 9.41, CI [6.16, 12.65]; local-linear with rdrobust 2014 bandwidth 16.79: 7.43, CI [4.49, 10.36], robust CI [4.07, 10.98].
- Randomization-based estimate in window [-0.75, 0.75] (22 treated, 15 control): 9.32, CI [4.60, 14.78], p = 0.0004.
- Window selection (Section 5.1, Table 2): balance tests on eight predetermined covariates, alpha = 0.15; the minimum p-value is 0.2682 in [-0.75, 0.75] and 0.0842 in [-0.875, 0.875].
- Density test (footnote 13): McCrary test p = 0.39, with no evidence of sorting; a binomial test on the 38 window observations gives p = 0.2559. The footnote does not say which sample the McCrary test uses.
- Placebo outcome (Design II, t+1, the other seat): null in all specifications (conventional 0.35, CI [-2.69, 3.39]).

Cattaneo, Titiunik and Vazquez-Bare (2016), "Inference in Regression Discontinuity Designs under Local Randomization", Stata Journal 16(2): 331-367 (`cattaneo2016rdlocrand`). Full text: https://ageconsearch.umn.edu/record/340127/files/Cattaneo.pdf (sha256 957f0118bfcf2559d5ced1ef31d254609086abfbd523a252ff3d38cb1f18e498). Section 7 (p. 351) describes the same 1,390-election file and the eight predetermined covariates, and says the authors "can replicate their empirical findings". The rdlocrand package implements the window and randomization tools. It is a software source, not a prior replication of the rdrobust estimate.

## 3. Prior replications and falsification checks in the literature

- Replication of the published rdrobust estimate: CCFT (2017) Section 7 reproduces the same data's default output, and the 2014 bandwidths reproduce the CCT 2014 numbers. CFT (2015) Table 3 reports the same local-linear point (7.43) with bandwidth 16.79. No separate independent replication was found. These are the same authors' software and data, so they are not independent confirmation.
- Falsification checks used in this line of work:
  1. Density (manipulation) test of the running variable: McCrary test in CFT (2015), p = 0.39. CCFT (2017) cites rddensity (Cattaneo, Jansson and Ma 2017) but does not run it on this data.
  2. Balance on predetermined covariates: CFT (2015) with eight covariates in randomization windows; CCFT (2017) with four covariates and robust bias-corrected p-values.
  3. Placebo outcome: CFT (2015) Design II (the other seat, t+1), null throughout.
  4. Window and bandwidth sensitivity: CFT (2015) Table 4 and CCFT (2017) 7.2 (2014 vs 2016 bandwidths).
- Critique of RD validity in close elections: Caughey and Sekhon (2011), "Elections and the Regression Discontinuity Design: Lessons from Close U.S. House Races, 1942-2008", Political Analysis 19(4): 385-408, DOI 10.1093/pan/mpr032 (`caughey2011elections`). Full text read (https://www.jsekhon.com/papers/CaugheySekhonRD.pdf, sha256 5bc1e3e242b363f6331e285bef6d154e508cf9529484b2fa6dd32c6f897b0851). Finds that bare winners and losers differ on pretreatment covariates in U.S. House races and that imbalance grows in the closest races. The paper covers the House, not the Senate.
- Eggers, Fowler, Hainmueller, Hall and Snyder (2015), "On the Validity of the Regression Discontinuity Design for Estimating Electoral Effects: New Evidence from Over 40,000 Close Races", AJPS 59(1): 259-274, DOI 10.1111/ajps.12127 (`eggers2015validity`). Only the abstract was checked, through a fetched summary of the LSE repository record (https://researchonline.lse.ac.uk/id/eprint/59620/). The authors argue the House anomaly does not appear in other settings and that RD assumptions are likely to hold in many electoral settings. They do not analyse the Senate in the abstract. The Harvard PDF returned Access Denied and the LSE repository has no PDF.

## 4. Implications for the design

1. Target of H1. The article prints one point estimate for the default specification: 7.416 (conventional). The robust bias-corrected CI is centred on a bias-corrected estimate that is not printed. The design gate needs to say whether the point target is 7.416 and whether the CI target is [4.094, 10.926] (the robust CI, as printed).
2. Bandwidth matters at the third decimal. The 2014 bandwidths give 7.425 and an upper robust limit of 10.983; the 2016 default gives 7.416 and 10.926. A tolerance set only from rounding will fail on bandwidth choice alone. The tolerance should be set at the design gate, with the software version pinned.
3. Software version. The article says "2016 version" and does not give a package version. The replication should record the rdrobust release it actually runs, and note that the article's numbers may differ from a later release.
4. Covariates. The seed file has only four covariates (class, termshouse, termssenate, population). CFT (2015) uses eight, and the Design II placebo outcome is not in the seed file. The falsification plan must be built from the four covariates and the running variable, or it will differ from the published balance test.
5. Density test. CFT (2015) reports McCrary p = 0.39 but does not say on which sample. Pre-specify the density test (rddensity or McCrary) and its sample before any outcome analysis.
6. Local estimand. The published estimate uses bandwidth about 17.7 points; the randomization result uses a window of about 0.75 points (22 + 15 observations) and gives 9.32. The two are different local estimands. The paper should not present them as one.
7. Caveat from Caughey and Sekhon: covariate imbalance in close elections is documented for the House, not the Senate. The Senate balance tests above are the relevant check, and the replication should report them whatever they show.

## 5. Novelty verdict

ALREADY ANSWERED (replication of a published estimate).

- The headline estimate is published with its specification and default output (CCFT 2017, Section 7.2), and the same data is analysed in CFT (2015). Rerunning the same software on the same file can reproduce the numbers but produces no new empirical finding.
- The falsification checks the question proposes (McCrary density test, predetermined-covariate balance) were already run on this data in CFT (2015) and CCFT (2017). The question's H2 is therefore a re-test of published results, not a new one.
- What is new in the workspace is the logged, pre-specified, rerunnable procedure. That is a process contribution, not a scientific one.

Closest prior work: Calonico, Cattaneo, Farrell and Titiunik (2017), Section 7 (same data, same default output, same balance checks); Cattaneo, Frandsen and Titiunik (2015), Section 5 (same data, density test and window-based balance tests).

## 6. Counts

- Verified sources with a record in sources/sources.json: 5 (calonico2017rdrobust, cattaneo2015randomization, cattaneo2016rdlocrand, caughey2011elections, eggers2015validity). Four are fetched full texts; Eggers et al. is fetched abstract only.

## 7. Unverified (not added to refs.bib)

- McCrary (2008), "Manipulation of the running variable in the regression discontinuity design: a density test", Journal of Econometrics 142(2): 698-714. Only a search summary and an EconBiz record were seen, not the paper. The DOI 10.1016/j.jeconom.2007.05.005 redirects to Elsevier linkinghub, which returned only "Redirecting".
- Calonico, Cattaneo and Titiunik (2014), Econometrica (robust bias-corrected inference) and rdrobust 2014. Cited in CCFT 2017 and CFT 2015; not fetched.
- Cattaneo, Jansson and Ma (2017/2018), rddensity. Cited in CCFT 2017 and CFT 2015; not fetched.
- Butler and Butler (2006), "Splitting the difference? Causal inference and theories of split-party delegations", Political Analysis 14. Cited in CFT 2015 as the prior Senate balancing study; not fetched.
- DOI of CCFT 2017 (search summary gave 10.1177/1536867X1701700208; the Sage page returned 403). Not recorded.
- DOI of CTV 2016 (search summary gave 10.1177/1536867X1601600205, not confirmed on a fetched page). Not recorded.
- Eggers et al. (2015): full text and any Senate-specific result. Only the abstract, via a fetched summary, was checked.
- The exact rdrobust package version used in CCFT 2017 Section 7.2.
