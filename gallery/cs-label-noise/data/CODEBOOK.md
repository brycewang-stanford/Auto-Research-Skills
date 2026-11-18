# Codebook: label-noise study datasets

Data RA, 2026-11-18. Four tabular classification datasets, retrieved through scikit-learn
1.9.1 by `code/fetch_data.py` (run `fetch-data`) and prepared by `code/prepare_data.py`
(run `prepare-data`). Provenance and hashes are in `data/manifest.json`; every count below
is a metric of run `prepare-data` (`runs/prepare-data/metrics.json`).

## Common layout

- `data/raw/<name>.csv`: the loader's output, written as features followed by a final
  `target` column, one row per instance. `data/derived/<name>.csv` holds the same rows and
  columns, read back with categorical columns as strings (whitespace stripped) and checked;
  for all four datasets the derived file is byte-identical to the raw one.
- **Nothing is dropped, capped, imputed, encoded or scaled here.** The stratified
  5,000-row cap is drawn per seed by the experiment code; missing-value handling and
  encoding are design decisions. `rows_dropped = 0` for every dataset.
- `data/derived/schema.json` lists, per dataset, the numeric and categorical columns, the
  class labels, and the columns that contain missing values.
- Missing values are empty fields in the CSV (pandas reads them as NaN).
- Both `data/raw/` and `data/derived/` are git-ignored; the runs rebuild them, and the
  hashes in the manifest and run records check them.
- The metrics are label-only or feature-only facts. No model was trained and no
  relationship between features and labels was computed.

## Summary

| Dataset | Pin | Rows | Features (num / cat) | Classes | Majority class (share) | Missing cells (rows) |
|---|---|---:|---|---:|---|---|
| breast_cancer | bundled with scikit-learn 1.9.1 | 569 | 30 (30 / 0) | 2 | 1 = benign (0.6274) | 0 |
| credit-g | OpenML data_id 31, version 1 | 1,000 | 20 (7 / 13) | 2 | good (0.7000) | 0 |
| adult | OpenML data_id 1590, version 2 | 48,842 | 14 (6 / 8) | 2 | <=50K (0.7607) | 6,465 (3,620) |
| covtype | sklearn `fetch_covtype` archive, sha256 614360d0… | 581,012 | 54 (54 / 0; 44 are 0/1) | 7 | 2 = Lodgepole Pine (0.4876) | 0 |

The majority shares above are for the full datasets. The study's `m` is the majority
share of each seed's test split, after the per-seed stratified cap, so it will be close to
but not exactly these values.

Every row count, feature count, class count and missing-value count matches the source's
documentation (`matches_source.*` metrics are all true). The only discrepancy found is the
duplicate count for adult, described below.

## breast_cancer

- **Source.** `sklearn.datasets.load_breast_cancer(as_frame=True)`: Breast Cancer
  Wisconsin (Diagnostic), UCI ML Repository dataset 17, bundled in the scikit-learn wheel as
  `sklearn/datasets/data/breast_cancer.csv` (sha256 `fed3eb72…72ed`). No download.
- **Version.** The copy bundled with scikit-learn 1.9.1.
- **License.** CC BY 4.0, as stated on the UCI page; scikit-learn redistributes it inside
  its BSD-3-Clause package.
- **Target.** `target`: diagnosis of the imaged breast mass, scikit-learn coding
  0 = malignant, 1 = benign.
- **Features.** 30 numeric, real-valued: the mean, standard error ("error") and worst
  (mean of the three largest) value of ten nucleus measurements computed from a digitized
  fine-needle-aspirate image: radius, texture, perimeter, area, smoothness, compactness,
  concavity, concave points, symmetry, fractal dimension. No categorical features.
- **Class balance.** 357 benign (0.6274), 212 malignant (0.3726).
- **Missing values.** None. Duplicate rows: 0.
- **Against the source.** scikit-learn's DESCR and the UCI page: 569 instances, 30
  numeric attributes, 212 malignant / 357 benign. All match.
- **Note.** This is the 569 × 30 Diagnostic data, not the 699 × 9 original Wisconsin data
  that Le Baher et al. and Breiman (2001) used (see `sources/notes.md`).

## credit-g

- **Source.** `fetch_openml(data_id=31)`: OpenML dataset 31 "credit-g", the Statlog
  (German Credit Data) set from UCI (dataset 144), creator Hans Hofmann. ARFF file
  `https://openml.org/data/v1/download/31/credit-g.arff`.
- **Version.** OpenML version 1 (status active, uploaded 2014-04-06). OpenML also lists
  later uploads under the same name (versions 2-5, data_ids 44096, 45058, 46378, 46918);
  version 1 is the original upload and the one in the OpenML-CC18 benchmark suite
  (study 99), so it is the canonical choice. The script asserts data_id 31, version 1, file_id 31 and OpenML's
  published md5 `9a475053fed0c26ee95cd4525e50074c`, which it checks on the downloaded ARFF
  itself. sha256 of the ARFF: `768be84e…42f5`.
- **License.** OpenML licence field "Public"; UCI page: CC BY 4.0.
- **Target.** `target` = OpenML's default target `class`: credit risk, `good` or `bad`.
- **Features.** 7 numeric (integers): `duration` (months), `credit_amount` (Deutsche
  Mark), `installment_commitment` (instalment as % of disposable income, coded 1–4),
  `residence_since` (years, coded 1–4), `age` (years), `existing_credits` (count at this
  bank), `num_dependents` (count). 13 categorical, with observed levels in parentheses:
  `checking_status` (4), `credit_history` (5), `purpose` (10), `savings_status` (5),
  `employment` (5), `personal_status` (4), `other_parties` (3), `property_magnitude` (4),
  `other_payment_plans` (3), `housing` (3), `job` (4), `own_telephone` (2),
  `foreign_worker` (2). OpenML gives the UCI codes (A11, A40, …) readable labels.
- **Class balance.** 700 good (0.7000), 300 bad (0.3000).
- **Missing values.** None. Duplicate rows: 0.
- **Against the source.** UCI `german.doc`: 1000 instances, 20 attributes (7 numerical,
  13 categorical). OpenML qualities: 700 / 300, no missing values. All match. The UCI
  codebook lists 11 purpose codes and 5 personal-status codes; one of each does not occur
  in the data (10 and 4 observed), which is a property of the data, not of the retrieval.
- **Note.** The UCI documentation pairs this dataset with a cost matrix (misclassifying a
  bad risk as good costs 5, the reverse 1). The study uses accuracy, so the cost matrix is
  not used; the paper should say so if it mentions credit-g's usual evaluation.

## adult

- **Source.** `fetch_openml(data_id=1590)`: OpenML dataset 1590 "adult", from the UCI
  Adult (Census Income) data, dataset 2. ARFF file
  `https://openml.org/data/v1/download/1595261/adult.arff`.
- **Version and why.** OpenML **version 2 (data_id 1590)**, status active, uploaded
  2015-06-09. Pinned md5 `bb6510925e5d4b23d136715febb2cdf5`, checked on the ARFF; sha256
  of the ARFF `77aa1703…26b0`. Version 2 rather than version 1 (data_id 179) because:
  1. version 1 stores `age`, `capitalgain`, `capitalloss` and `hoursperweek` as
     discretized nominal bins (2 numeric, 13 nominal columns), whereas version 2 keeps the
     six UCI continuous attributes numeric, as in the original data;
  2. version 2 is the one in the OpenML-CC18 benchmark suite (study 99);
  3. later uploads (version 3, data_id 43898, 2022; version 4, data_id 45068, 2023) are
     re-uploads by other users; version 3, for example, drops 52 duplicate rows, so it is
     not the reference data;
  4. versions 1 and 2 have the same 48,842 rows, labels and missing values, so the choice
     changes only feature types.
- **License.** OpenML licence field "Public"; UCI page: CC BY 4.0.
- **Target.** `target` = OpenML's default target `class`: annual income `>50K` or
  `<=50K` (US dollars, 1994 Census). OpenML version 2 has already removed the trailing
  period that the UCI test file puts on its labels (`>50K.`), so there are exactly two
  labels.
- **Features.** 6 numeric (integers): `age` (years), `fnlwgt` (Census final sampling
  weight; it is a weight, not a person attribute, and is kept as a feature here because
  the source ships it as one), `education-num` (education level, coded 1–16),
  `capital-gain` and `capital-loss` (dollars), `hours-per-week`. 8 categorical, with
  observed levels: `workclass` (8), `education` (16), `marital-status` (7),
  `occupation` (14), `relationship` (6), `race` (5), `sex` (2), `native-country` (41).
- **Class balance.** 37,155 `<=50K` (0.7607), 11,687 `>50K` (0.2393).
- **Missing values.** 6,465 cells in 3,620 rows (7.4%), only in categorical columns:
  `workclass` 2,799, `occupation` 2,809, `native-country` 857 (UCI's `?`).
- **Duplicate rows.** 52 rows repeat an earlier row exactly (features and label).
- **Against the source.** UCI `adult.names`: 48,842 instances (32,561 train + 16,281
  test, combined here), P(>50K) = 23.93%; 45,222 instances without unknowns, i.e. 3,620
  with them. OpenML qualities: 37,155 / 11,687, 6,465 missing values in 3,620 instances,
  6 numeric + 8 nominal features. All match.
  **Discrepancy:** `adult.names` reports 6 "duplicate or conflicting instances"; the
  combined data have 52 exact duplicate rows. OpenML's version 3 of adult (data_id 43898)
  independently reports "52 duplicate values found and dropped" for the same combined
  data, which corroborates the count. The UCI figure most likely uses a different
  definition or file; it was not investigated further
  (counting conflicting labels would mean relating features to labels, which this stage
  does not do). The design should say whether duplicates are kept; this stage keeps them.

## covtype

- **Source.** `sklearn.datasets.fetch_covtype(as_frame=True)`: the UCI Covertype data
  (dataset 31; Blackard, Dean & Anderson, US Forest Service, Roosevelt National Forest,
  Colorado). scikit-learn downloads `covtype.data.gz` from its figshare mirror
  `https://ndownloader.figshare.com/files/5976039` and checks the archive's sha256
  `614360d0257557dd1792834a85a1cdebfadc3c4f30b011d56afee7ffb5b15771`, pinned in
  scikit-learn 1.9.1, before converting it to its cache (the archive itself is then
  deleted by scikit-learn).
- **Version.** The archive with the sha256 above; there is one version of the UCI data.
- **License.** CC BY 4.0, as stated on the UCI page.
- **Target.** `target` = `Cover_Type`, forest cover type as integer codes 1–7:
  1 Spruce/Fir, 2 Lodgepole Pine, 3 Ponderosa Pine, 4 Cottonwood/Willow, 5 Aspen,
  6 Douglas-fir, 7 Krummholz.
- **Features.** 54 numeric, all integers (scikit-learn returns them as float64; the fetch
  script checks they are integral and writes them as integers):
  - 10 quantitative: `Elevation` (m), `Aspect` (degrees azimuth), `Slope` (degrees),
    `Horizontal_Distance_To_Hydrology` (m), `Vertical_Distance_To_Hydrology` (m),
    `Horizontal_Distance_To_Roadways` (m), `Hillshade_9am`, `Hillshade_Noon`,
    `Hillshade_3pm` (index 0–255), `Horizontal_Distance_To_Fire_Points` (m);
  - 4 binary `Wilderness_Area_0`–`_3` and 40 binary `Soil_Type_0`–`_39`: one-hot
    encodings of two categorical variables. scikit-learn numbers them from 0; the UCI
    documentation numbers them from 1.
- **Class balance.** 2: 283,301 (0.4876); 1: 211,840 (0.3646); 3: 35,754 (0.0615);
  7: 20,510 (0.0353); 6: 17,367 (0.0299); 5: 9,493 (0.0163); 4: 2,747 (0.0047).
- **Missing values.** None. Duplicate rows: 0.
- **Against the source.** UCI `covtype.info`: 581,012 instances, 54 columns (10
  quantitative, 4 binary wilderness, 40 binary soil), and the class distribution in its
  section 10. All match.
- **Note for the design.** Class 4 has 0.47% of rows; in a stratified 5,000-row sample it
  will have about 24 rows, so about 5 per 20% test split. With 7 classes, "replace by a
  different class chosen uniformly at random" spreads each flipped label over 6 classes.

## Reproducibility

`fetch-data` was run twice, the second time after deleting `data/raw/` (including the
scikit-learn cache) so that every file was downloaded again. breast_cancer, credit-g and
adult were byte-identical across the two runs; covtype changed only because the script
was edited between runs to write integers instead of floats. A clean rerun
(`crew.py rerun`) re-downloads and compares the four CSV sha256 values, which are recorded
as metrics of `fetch-data`.
