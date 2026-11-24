# PLAN.md: CS 184A final, Workstream 1 + Workstream 4

Read AGENTS.md and PROJECT_CONTEXT.md first. Tutor mode: explain, review, give small snippets. Thaarun writes every script.

## Opening prompt (paste into a new Ask-mode chat, one chat per task)
"Read @AGENTS.md and @PROJECT_CONTEXT.md and @PLAN.md. We are on Phase N, task N.N. Do not write the script. Tell me what to print first and what to report back, then walk me through the first snippet line by line. I will write the code and paste it back for review."

## Timing
Today is 2026-11-21. The presentation is after 2026-11-30 (exact date to be confirmed). Coding runs 2026-11-22 to 2026-11-29; 2026-11-30 is figures, slides and buffer. If the presentation is later than Dec 1, the extra days go to STRETCH items, never to skipping a MUST.
Tags: MUST / SHOULD / STRETCH. Cut order if behind: STRETCH, then imaging, then ablations. Never cut: the leakage audit, the RNA-only line, the masked rediscovery.

## Ground truth about the files (verified in the repo, not guessed)
- `src/load_clinical.py` loads `data/raw/clinical/clinical.tsv` into MySQL database `brca_project`, table `clinical_raw`. It uses `if_exists="replace"`, so do not re-run it while working on the collapse.
- `clinical.tsv` has repeated rows per patient. Print `DESCRIBE clinical_raw` before writing any query, and confirm `cases_submitter_id` survived the 5% column filter.
- `follow_up.tsv` is a long table. ESR1, PGR and ERBB2 are values under `molecular_tests.gene_symbol`, with the call in `molecular_tests.test_result` and the assay in `molecular_tests.laboratory_test` (IHC and FISH both appear for ERBB2). Do not apply the 5% column drop to this file until you print fill rates for those three columns.
- Subtype labels file on disk is `data/raw/clinical/GS-Subtype labels.xlsx` (with a space). Print its sheet names and columns before reading it. The class order 0 LumA, 1 Her2, 2 LumB, 3 Normal, 4 Basal and the counts 353, 42, 132, 31, 113 stay hypotheses until you print `value_counts()`.
- `brca_clinical_labels.csv` goes in `data/raw/clinical/`. It has 1,097 patient rows plus a header and columns patient_id, sex, ER, PR, HER2, HER2_source, clinical_subtype, histology_group, stage, pT, pN, pM, age, menopause, neoadjuvant, vital_status, last_contact_days, death_days, exclude_flag.
- MLOmics: put the download in the existing `data/raw/MLOmics/` (do not create a second folder). Its README says: rows are features and columns are patients; values are z-score normalized; **Top** means ANOVA-selected (mRNA 5000, miRNA 200, methylation 5000, CNV 5000); **Original** sizes for GS-BRCA are mRNA 18206, miRNA 345, methylation 19049, CNV 19533. File names and ID spelling are unknown until you run `ls` and print them.
- Clinical IDs are hyphenated (for example TCGA-E2-A1IU). Print omics IDs and their lengths before slicing to 12 characters.

## Evidence rules for this project
- **Top files are ANOVA-selected, so selection used the labels. Never use them as the model input.** Model on **Original**. If Top is ever loaded, save it under a different name and label any number from it design only.
- The matrices are already z-scored across all patients. That is a small leak you cannot undo without raw counts. Record it in the audit and label every model result **pilot**.
- Nothing is **validated** unless it is tested on an outside cohort.
- Split by 12-character patient ID, never by clinical_raw row.

## Phase 1: Patient key and clinical descriptors (Nov 22) [MUST]
Files: `src/collapse_clinical.py`, `data/interim/clinical_patient.csv`, `tests/test_clinical_patient.py`.

1.1 [done] `DESCRIBE clinical_raw`: 65 columns, `cases_submitter_id` present.
1.2 [done] 5,546 rows, 1,098 distinct patients, 0 null IDs; rows per patient range from 1 to 40.
1.3 [done] Within-patient variation: `treatments_*` varies for most patients, and `diagnoses_*` varies for up to 182 patients (several have more than one diagnosis: prior primary, metastasis, or a second cancer in another organ). `cases_*` and `demographic_*` never vary. So `diagnoses_*` and `treatments_*` are left out on purpose. Keep this summary in `docs/clinical_data_notes.md`; `data/` is local-only and not committed.
1.4 Build `clinical_patient`:
    - Select `cases_case_id`, `cases_submitter_id`, `cases_disease_type`, `cases_primary_site`, `demographic_age_at_index`, `demographic_sex_at_birth`, `demographic_vital_status`.
    - Run `drop_duplicates()` (not `MAX`, because `MAX` hides disagreements between a patient's rows).
    - Rename `cases_submitter_id` to `patient_id`.
    - Do not include any `diagnoses_` or `treatments_` column.
1.5 Save `data/interim/clinical_patient.csv` from the script. Optional: also write it to MySQL as `clinical_patient`.
Asserts and test: exactly 1,098 rows; `patient_id` is unique; `TCGA-BH-A0B2` is present; no column starts with `diagnoses_` or `treatments_`; the patient-ID set equals the set of non-null `cases_submitter_id` values in `clinical_raw`.
If the uniqueness assert fails: print the duplicated IDs with `duplicated("patient_id", keep=False)` and report them. It means a descriptive field disagrees within a patient.
Use: the patient key for ID-based alignment later, plus a few cohort descriptors. Not a source of model features.

## Phase 2: Receptor CSV audit (Nov 22) [MUST]
Files: `src/inspect_receptor_csv.py`, `data/interim/receptors.csv`, `tests/test_receptors.py`.
Before writing any data artifact: `data/` must be in `.gitignore`.

2.1 Read `data/raw/clinical/brca_clinical_labels.csv` with `dtype=str`. Print the columns, row count, number of unique `patient_id` values, null patient-ID count, and the first five IDs with their string lengths. Expected: 1,097 rows, 1,097 unique, all of length 12.
2.2 Print `value_counts(dropna=False)` for `ER`, `PR`, `HER2`, `HER2_source` and `exclude_flag`. Report the output. Expected: `exclude_flag` has 1,072 empty, 13 `neoadjuvant`, 12 `male`; ER, PR and HER2 are missing for about 51, 54 and 140 patients.
2.3 Assert `patient_id` is unique. Save exactly `patient_id`, `ER`, `PR`, `HER2`, `HER2_source`, `exclude_flag` to `data/interim/receptors.csv`. Keep missing values as missing. Do not drop any row.
2.4 Compare the `patient_id` set in the receptor CSV with `clinical_patient` using `Index.intersection`, not row order. Report the overlap and the IDs that appear in only one source. Expected: 1,097 shared, and exactly one patient only in `clinical_patient`.
2.5 Decide the `exclude_flag` rule only after 2.2 is printed. Default: keep all rows in `receptors.csv` and `clinical_patient`, apply the flag when building the modeling cohort in Phase 3, and report results with and without the flagged patients. Write the decision in `PROJECT_CONTEXT.md`.
Test: `receptors.csv` has one row per patient ID; every ID has length 12; ER, PR and HER2 are absent from the model feature list.
Use: this CSV is the only receptor source for this project; `follow_up.tsv` is out of scope. Receptors describe the cohort and cross-check labels. They are never model inputs.

## Phase 3: Omics and labels (Nov 23) [MUST]
Files: `src/align_omics.py`, `tests/test_alignment.py`, aligned matrices in `data/processed/` (names chosen after you see the IDs).
3.1 Download MLOmics GS-BRCA into `data/raw/MLOmics/`. Report `ls`, then for each file: shape, whether rows are features, the first 5 IDs and their lengths, and whether Original and Top both exist. Report all of it before writing any loader.
3.2 Print the xlsx sheet names and columns, then `value_counts()` of the labels. Confirm or correct the class mapping and counts.
3.3 Transpose to patients x features. Map IDs to 12-character patient IDs, assert no duplicates, and compute overlap with `clinical_patient` using `Index.intersection`. Expect up to 671; do not drop patients silently.
3.4 Build aligned Original matrices (one per modality) with the label vector on the same index; assert the indexes are equal.
3.5 Pulling a second expression download from GDC is cut unless Original turns out to be missing.
Test: all matrix indexes equal the label index; every ID has length 12; no duplicates.

## Phase 4: Leakage audit and splits (Nov 24) [MUST]
Files: `results/leakage_audit.md`, `src/splits.py`, `tests/test_splits.py`.
4.1 Write the audit: what is fit on what; selection, imputation and scaling live inside the Pipeline; split key is patient ID; receptors out of X; Top is ANOVA-selected; matrices are pre-z-scored.
4.2 Outer 5-fold stratified split with seeds (start with one repeat). Print the smallest class count in every outer test fold and every inner test fold. If an inner fold would hold fewer than 5 of a class, lower `n_splits` and record why.
Test: train and test IDs are disjoint and cover the full index for every fold; a toy case with a repeated ID is rejected.

## Phase 5: Per-modality models (Nov 24-26) [MUST for RNA elastic-net; SHOULD for others]
Files: `src/modality_models.py`, `results/modality_scores.csv` (macro-F1, bootstrap low and high, per-class recall, seed).
5.1 Majority baseline. Any "handful of features" baseline uses a gene list written down before any score, never genes chosen by looking at the labels.
5.2 RNA elastic-net logistic regression as a Pipeline (impute, scale, model), `solver="saga"`, explicit `max_iter`, tiny inner grid over C and l1_ratio. Time one fit first. If it is too slow, add a variance screen inside the Pipeline, fit on training rows only.
5.3 Report OOF macro-F1 with a bootstrap 95% CI, per-class recall, confusion matrix. Bootstrap by resampling the pooled outer-test predictions (do not refit the search). State the limitation: this ignores fold-to-fold variation, so intervals run slightly narrow.
5.4 One label-shuffle check: shuffle only y, one seed, the small RNA pipeline, write the score to `results/`, do not retune afterwards.
5.5 SHOULD: the same protocol for miRNA, methylation, CNV (Original). Do not drop any modality from the table after seeing scores.
5.6 SHOULD: XGBoost on RNA only. Early stopping watches an inner validation fold, never the outer test fold.
5.7 The RNA-only result is always its own line, with the sentence that PAM50 is defined from RNA, so this comparison is partly circular.
Test: on a toy train and test frame, imputed values and scaler mean match the training rows only.

## Phase 6: Fusion (Nov 26) [MUST if two or more modalities finished; otherwise design]
Files: `src/stack.py`, `results/fusion_scores.csv`.
6.1 For each outer fold, build out-of-fold probabilities from the outer-training patients only (`cross_val_predict(..., method="predict_proba")` inside that fold). Fit the stacker (a small logistic regression) on those, then predict the outer-test patients.
6.2 Report fusion, RNA-only, and the best single modality, with the single modality named before scores are seen. Keep a negative result in the CSV.
Test: stacker training IDs and outer-test IDs have an empty intersection.

## Phase 7: Calibration and abstention (Nov 27) [MUST on the RNA OOF]
Files: `src/calibrate.py`, `results/calibration.csv`, `results/risk_coverage.csv`.
7.1 Fit one temperature per outer fold on inner out-of-fold probabilities from the outer-training patients. Report ECE before and after and a reliability plot.
7.2 Choose the abstain threshold on inner out-of-fold probabilities only, never on predictions for rows the model was fit on, and never on the test fold. Report accuracy and macro-F1 at 90% and 80% coverage, with the classes still predicted (Her2 and Normal can vanish).
7.3 SHOULD: coefficient stability (selection frequency across outer folds) for the RNA elastic-net. Name this model before looking at scores. It feeds Workstream 4's attribution signal; if skipped, attribution is design.
Test: the threshold function refuses to accept test-fold probabilities.

## Background downloads (start Nov 23-24, while coding other phases) [MUST for Phase 9]
Report file names and sizes before using any of them.
- DepMap: CRISPR gene effect and model annotations.
- Open Targets: target-disease associations and tractability.
- ChEMBL: drug-target links.
- GDC TCGA-BRCA somatic mutations (open-access), to define a BRCA1/BRCA2-mutant group for PARP1. If this is not reachable in time, use the Basal group as the stated fallback and say so on the slide.
Any signal whose file is not on disk is labeled design and omitted from the rank sum.

## Phase 8: Imaging pilot (Nov 28-29) [SHOULD; first to cut]
8.1 Gate: launch a GPU instance, set the $50 budget alert, confirm `nvidia-smi`. If it fails, download no slides and mark imaging design.
8.2 Check the pretrained pathology model's license and whether it was trained on TCGA-BRCA labels before choosing it. Record the choice.
8.3 Pick a slide subset (150-300 patients in the omics index), download only those slides, extract frozen-model features, average per patient, save features, delete slides.
8.4 Compare omics only, image only, fused, on the intersection of patients only, same protocol. Label **pilot**.
Test: every image-feature ID is in the omics index; all three comparisons use the same ID set.

## Phase 9: Workstream 4, target ranking (Nov 29-30) [MUST]
9.1 Before any ranking code, write `results/rediscovery_rule.md`: a held-out known target ranks in the top 5% of the gene universe; PARP1 and CDK4/CDK6 are the informative cases; ERBB2 in the Her2 group is a sanity check (close to circular); no weight changes after seeing ranks.
9.2 Define the gene universe from the printed RNA index, and the subtype groups from the confirmed class names.
9.3 Compute the signals you have files for: stable attribution (from 7.3), DepMap dependency in breast lines, driver evidence, tumor-vs-subtype expression (t-test; FDR only if statsmodels imports, otherwise report raw p-values and say so), druggability, normal-tissue safety.
9.4 Equal-weight rank aggregation (mean of ranks of the signals computed). No tuning against the known answers.
9.5 Masked rediscovery: remove drug-link fields for PARP1, CDK4, CDK6 and ERBB2 and any feature derived from them before ranking, not after a disappointing rank. Report the rank of each.
9.6 If expression contrast is the only signal available, say plainly that the result is the differential-expression baseline, not the six-signal method.
9.7 SHOULD: baselines (differential expression alone, DepMap alone, Open Targets with drug evidence removed) and one-signal-at-a-time ablation.
9.8 STRETCH: hide each target on a pre-written list of known breast targets in turn.
Test: a toy table where a drug-link column would put the held-out gene first, and the masked ranker ignores that column.

## Phase 10: Figures and slides (build as you go; finish Nov 30) [MUST]
10.1 `src/make_figures.py` reads CSVs in `results/` only and raises if one is missing. No number is typed from memory.
10.2 Slides: problem, data, leakage controls, results with CIs, negative results, calibration and abstention, target ranking, validated vs pilot vs design, next steps.
10.3 Update the proposal (student ID and UCI email are still placeholders), the README run steps, and the Progress log in PROJECT_CONTEXT.md.
Slide claims: RNA elastic-net is pilot; any Top-file number is not a result; imaging is pilot or design; ranking is pilot for computed signals and design for the rest; nothing is validated.

## STRETCH (only after every MUST is done)
- External check of the RNA model on METABRIC (cBioPortal), test only, never tuned on. Needs gene-name overlap and platform handling. This would be the only **validated** claim.
- Extra repeats of the outer CV, XGBoost on other modalities.

## Day plan
- Nov 22: Phase 1, start Phase 2
- Nov 23: finish Phase 2, Phase 3; start background downloads
- Nov 24: Phase 4, start Phase 5
- Nov 25: Phase 5
- Nov 26: finish Phase 5, Phase 6
- Nov 27: Phase 7
- Nov 28: GPU gate, Phase 8
- Nov 29: Phase 8 finish, Phase 9 rule and ranking
- Nov 30: Phase 9 finish, Phase 10, buffer
- After Nov 30: stretch items and rehearsal, until the presentation

## Three risks and the cut for each
1. Nested CV on Original RNA is too slow or unstable for the small classes: cut XGBoost and extra modalities, keep one outer 5-fold, small inner grid, RNA elastic-net, majority baseline, CI, per-class recall. Fusion and imaging become design.
2. GPU check fails or slide download starts late: skip Phase 8 at the gate and spend the time on Phase 9.
3. A target database or the mutation file is missing on Nov 29: do not block. Write the top-5% rule anyway, rank with what is on disk, label the rest design, and cut 9.7 and 9.8 first.
