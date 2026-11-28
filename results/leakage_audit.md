# Leakage audit

Last updated 2026-11-28. Evidence label for every model result in this project: pilot (one cohort, no outside validation).

## Data used
- Features: MLOmics GS-BRCA **Original** matrices only (mRNA, miRNA, Methy, CNV), 671 patients, saved as patient-indexed parquet files. Top and Aligned subsets are never used.
- Labels: PAM50 from `BRCA_label_num.csv`. Targets from clinical and receptor tables are listed in `docs/target_registry.md`.

## Known limits of the data (cannot be undone)
- The Original matrices are z-score normalized across all patients upstream (per the MLOmics README). Test patients therefore influenced the scale of the features. Results are labeled pilot.
- The matrices contain no missing values at all, which suggests imputation was also done upstream (not confirmed; check the README). The imputer in the pipeline will do nothing on these matrices.
- The Top subsets are ANOVA-selected using the class labels, so any number from them would be optimistic. They are not used.
- PAM50 is defined from RNA, so RNA-to-PAM50 is close to circular. An RNA-only result is reported beside every multimodal result.

## Label alignment
- `BRCA_label_num.csv` has no patient IDs. Labels were attached by position, using the sample order of the mRNA columns (the README says all files share sample order). This is the one deliberate exception to the rule of joining by ID.
- Alignment was verified against the receptor table, which is independent of the MLOmics files: LumA and LumB are 97 to 98% ER-positive among patients with a call, Basal is 88% ER-negative, and Her2 is 71% HER2-positive (Basal 6%, LumA 12%, LumB 23%). Normal is mixed, as expected for that class.
- The four matrices list patients in the same order (checked) and have no duplicate patient IDs.

## Inputs allowed and banned, by head
| Head | Allowed inputs | Banned inputs |
|---|---|---|
| PAM50 | omics, image, mutations | ER, PR, HER2, receptor subtype, stage |
| ER, PR, HER2 | omics, image, mutations | the other receptors, PAM50 labels |
| Histology | omics, image, mutations | none beyond the label itself |
| Node, metastasis | omics, image, age | stage, pT, pN, pM |
| Recurrence | age, stage, a few omics summaries, WS1 out-of-fold outputs | treatment fields |
`load_xy` builds X from omics files only, so cohort columns cannot enter X by accident; `tests/test_data.py` checks this.

## Splits
- Unit of splitting: patient. Each row is one patient (12-character TCGA ID), so a patient cannot appear in both train and test.
- Outer: 5-fold stratified on PAM50, `shuffle=True`, seed 42; assignments saved in `results/folds.csv` and reused for every target.
- Test-fold class counts (LumA, Her2, LumB, Normal, Basal): fold 0: 71/8/27/6/23; fold 1: 71/8/27/6/22; fold 2: 71/8/26/7/22; fold 3: 70/9/26/6/23; fold 4: 70/9/26/6/23.
- Inner (tuning): 3-fold. Normal has about 25 training patients per outer fold, so a 5-fold inner split would leave about 5 per inner test fold; 3-fold leaves about 8.
- `tests/test_splits.py` checks that train and test IDs are disjoint and cover all 671 for every fold.

## What is fit on what
- Scaling, feature screening, hyperparameter tuning, calibration and abstention thresholds are fit on training rows only, inside a Pipeline within nested cross-validation.
- Stacking: the second-level model is trained on out-of-fold probabilities from the outer-training patients only, then applied to the outer-test patients.
- Temperature scaling and the abstain threshold use inner out-of-fold probabilities from the outer-training patients, never predictions on rows the model was fit on, and never the test fold.
- Early stopping (if XGBoost is used) watches an inner validation fold, never the outer test fold.
- Any model chosen to be explained (coefficient stability or SHAP) is named before looking at outer scores.
- All modalities appear in the results table; none is dropped after seeing test scores.

## Receptors and cohort flags
- HER2 call: IHC first, FISH only when IHC is not Positive or Negative. Both assays are usable for 182 patients and disagree for 15 (12 IHC Positive and FISH Negative; 3 IHC Negative and FISH Positive); the IHC call is used for them. Equivocal, indeterminate and not-evaluated results are missing, not negative.
- 25 patients are flagged (12 male, 13 neoadjuvant). No one is removed. Results are reported with and without the flagged patients.

## Checks still to run
- One label-shuffle run on the small RNA pipeline, one seed; result saved in `results/` and not used to retune.
- Fusion, calibration and abstention checked against the rules above when they are built.