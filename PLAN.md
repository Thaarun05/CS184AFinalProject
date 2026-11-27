# PLAN.md: CS 184A final, Workstream 1 + Workstream 4

Read AGENTS.md and PROJECT_CONTEXT.md first. Tutor mode: explain, review, give small snippets. Thaarun writes every script.

## Opening prompt (paste into a new Ask-mode chat, one chat per task)
"Read @AGENTS.md and @PROJECT_CONTEXT.md and @PLAN.md. We are on Phase N, task N.N. Do not write the script. Tell me what to print first and what to report back, then walk me through the first snippet line by line. I will write the code and paste it back for review."

## Timing
Status as of 2026-11-27: Phases 1 to 3 are done. The presentation is after 2026-11-30 (exact date to be confirmed). Remaining coding runs 2026-11-27 to 2026-11-29; 2026-11-30 is figures, slides and buffer. If the presentation is later than Dec 1, the extra days go to STRETCH items, never to skipping a MUST.
Tags: MUST / SHOULD / STRETCH. Cut order if behind: STRETCH, then imaging, then ablations. Never cut: the leakage audit, the RNA-only line, the masked rediscovery.

## Ground truth about the files (verified in the repo, not guessed)
- `src/load_clinical.py` loads `data/raw/clinical/clinical.tsv` into MySQL database `brca_project`, table `clinical_raw`. It uses `if_exists="replace"`, so do not re-run it while working on the collapse.
- `clinical.tsv` has repeated rows per patient. Print `DESCRIBE clinical_raw` before writing any query, and confirm `cases_submitter_id` survived the 5% column filter.
- `follow_up.tsv` is out of scope for this class-project pass.
- `data/raw/clinical/GS-Subtype labels.xlsx` (with a space) only maps class numbers to names: 0 LumA, 1 Her2, 2 LumB, 3 Normal, 4 Basal. The per-patient labels are in the MLOmics file `BRCA_label_num.csv` (column `Label`, no patient IDs). Verified counts: LumA 353, LumB 132, Basal 113, Her2 42, Normal 31 (671 total).
- `nationwidechildrens.org_clinical_patient_brca.txt` is the receptor source. It is tab-separated with a header plus two metadata rows; read it with `sep="\t"`, `dtype=str`, and `skiprows=[1, 2]`. Use `bcr_patient_barcode` as the 12-character patient key. It was downloaded from the GDC API (Clinical Supplement, BCR Biotab, file id `8162d394-8b64-4da2-9f5b-d164c54b9608`).
- MLOmics: put the download in the existing `data/raw/MLOmics/` (do not create a second folder). Its README says: rows are features and columns are patients; values are z-score normalized; **Top** means ANOVA-selected (mRNA 5000, miRNA 200, methylation 5000, CNV 5000); **Original** sizes for GS-BRCA are mRNA 18206, miRNA 345, methylation 19049, CNV 19533. Verified: the Original matrices have 671 samples each (mRNA 18,206, CNV 19,533, Methy 19,049, miRNA 345 features), no duplicate patient IDs, the same patient order in all four modalities, and zero missing values. Sample headers map to patient IDs by changing dots to hyphens and keeping the first 12 characters.
- Clinical IDs are hyphenated (for example TCGA-E2-A1IU). Print omics IDs and their lengths before slicing to 12 characters.

## Evidence rules for this project
- **Top files are ANOVA-selected, so selection used the labels. Never use them as the model input.** Model on **Original**. If Top is ever loaded, save it under a different name and label any number from it design only.
- The matrices are already z-scored across all patients. That is a small leak you cannot undo without raw counts. Record it in the audit and label every model result **pilot**.
- The matrices contain no missing values at all, which suggests imputation was also done upstream (check the README). Record this in the audit too; the imputation step in the Pipeline will do nothing on these matrices.
- Nothing is **validated** unless it is tested on an outside cohort.
- Split by 12-character patient ID, never by clinical_raw row.

## Phase 1: Patient key and clinical descriptors (Nov 22) [MUST]
Files: `src/collapse_clinical.py`, `data/interim/clinical_patient.csv`, `tests/test_clinical_patient.py`.

1.1 [done] `DESCRIBE clinical_raw`: 65 columns, `cases_submitter_id` present.
1.2 [done] 5,546 rows, 1,098 distinct patients, 0 null IDs; rows per patient range from 1 to 40.
1.3 [done] Within-patient variation: `treatments_*` varies for most patients, and `diagnoses_*` varies for up to 182 patients (several have more than one diagnosis: prior primary, metastasis, or a second cancer in another organ). `cases_*` and `demographic_*` never vary. So `diagnoses_*` and `treatments_*` are left out on purpose. Keep this summary in `docs/data_notes.md`; `data/` is local-only and not committed.
1.4 Build `clinical_patient`:
    - Select `cases_case_id`, `cases_submitter_id`, `cases_disease_type`, `cases_primary_site`, `demographic_age_at_index`, `demographic_sex_at_birth`, `demographic_vital_status`.
    - Run `drop_duplicates()` (not `MAX`, because `MAX` hides disagreements between a patient's rows).
    - Rename `cases_submitter_id` to `patient_id`.
    - Do not include any `diagnoses_` or `treatments_` column.
1.5 Save `data/interim/clinical_patient.csv` from the script. Optional: also write it to MySQL as `clinical_patient`.
Asserts and test: exactly 1,098 rows; `patient_id` is unique; `TCGA-BH-A0B2` is present; no column starts with `diagnoses_` or `treatments_`; the patient-ID set equals the set of non-null `cases_submitter_id` values in `clinical_raw`.
If the uniqueness assert fails: print the duplicated IDs with `duplicated("patient_id", keep=False)` and report them. It means a descriptive field disagrees within a patient.
Use: the patient key for ID-based alignment later, plus a few cohort descriptors. Not a source of model features.

## Phase 2: Receptor audit (Nov 22) [MUST]
Files: `src/inspect_receptor_csv.py`, `data/interim/receptors.csv`, `tests/test_receptors.py`.
Before writing any data artifact: `data/` must be in `.gitignore`.

2.1 [done] Read `data/raw/clinical/nationwidechildrens.org_clinical_patient_brca.txt` with `sep="\t"`, `dtype=str`, and `skiprows=[1, 2]`. `bcr_patient_barcode` has 1,097 unique, non-null, 12-character IDs.
2.2 [done] Derive ER and PR from explicit IHC `Positive`/`Negative` calls; all other values are missing. For HER2, retain an IHC `Positive`/`Negative` call; otherwise use a FISH `Positive`/`Negative` call; otherwise leave it missing. Record `HER2_source` as `IHC` or `FISH`. Final missing counts: ER 51, PR 54, HER2 140. HER2 sources: 728 IHC, 229 FISH. Both assays are usable for 182 patients and they disagree for 15 (12 IHC Positive / FISH Negative, 3 IHC Negative / FISH Positive); the IHC call is used for those. They are the only patients the IHC-first rule affects (FISH-first would change HER2-positive from 194 to 185). Record this in `docs/data_notes.md`.
2.3 [done] Derive `exclude_flag` without dropping rows: `male` for `gender == "MALE"` (12 patients), `neoadjuvant` for `history_neoadjuvant_treatment == "Yes"` (13 patients). The groups do not overlap; 1,072 values are missing. Save exactly `patient_id`, `ER`, `PR`, `HER2`, `HER2_source`, `exclude_flag` to `data/interim/receptors.csv`.
2.4 [done] Compare the patient-ID sets with `Index.intersection`, not row order: 1,097 IDs are shared; `TCGA-BH-A0B2` is clinical-only; no receptor ID is unmatched.
2.5 [done] Keep all rows in `receptors.csv` and `clinical_patient`. Apply `exclude_flag` only when constructing the Phase 3 modeling cohort, and report results with and without the 25 flagged patients. Receptors and flags are never model inputs.
Test: add checks that `receptors.csv` has one row per patient ID, every ID has length 12, and ER, PR, and HER2 are absent from the model feature list.
Use: this CSV is the only receptor source for this project; `follow_up.tsv` is out of scope. Receptors describe the cohort and cross-check labels. They are never model inputs.

## Phase 3: Omics and labels (Nov 23-27) [MUST] [done]
Files: `src/build_processed.py`, `src/data.py`, `tests/test_data.py`. Outputs in `data/processed/` (local only): `{mRNA,miRNA,Methy,CNV}_original.parquet`, `labels.csv`, `cohort.csv`.
3.1 [done] MLOmics GS-BRCA is in `data/raw/MLOmics/Main_Dataset/Classification_datasets/GS-BRCA/` with `Original`, `Top` and `Aligned` subfolders. Original matrices are features x samples, 671 samples each, no duplicate patient IDs, same patient order across modalities, zero missing values. Top and Aligned are not used for modeling.
3.2 [done] The xlsx only maps class numbers to names. Per-patient labels come from `BRCA_label_num.csv`. Counts: LumA 353, LumB 132, Basal 113, Her2 42, Normal 31.
3.3 [done] Labels are attached by position, using the sample order of the mRNA columns (the README says all files share sample order). This is the one deliberate exception to the ID-join rule. The alignment was verified against receptors: LumA and LumB are 97-98% ER-positive among patients with a call, Basal is 88% ER-negative, and Her2 is 71% HER2-positive (Basal 6%, LumA 12%, LumB 23%). Normal is mixed, as expected for that class.
3.4 [done] Matrices are saved as patients x features parquet files indexed by 12-character patient ID, with `labels.csv` and a unified `cohort.csv` (labels, clinical descriptors, receptors, `exclude_flag`; 671 rows). `load_xy(modalities, drop_flagged=False)` in `src/data.py` builds X from omics only and can optionally drop flagged patients.
3.5 A second expression download from GDC is not needed because Original is complete.
Test: `tests/test_data.py` checks 671 rows, only mRNA-prefixed columns for `load_xy(["mRNA"])`, and class counts 353 / 42 / 132 / 31 / 113 for labels 0 to 4.

## Phase 4: Leakage audit and splits (Nov 27) [MUST]
Files: `results/leakage_audit.md`, `src/splits.py`, `tests/test_splits.py`.
4.1 Write the audit: what is fit on what; selection, imputation and scaling live inside the Pipeline; split key is patient ID; receptors out of X; Top is ANOVA-selected; matrices are pre-z-scored.
4.2 Outer 5-fold stratified split with seeds (start with one repeat). Print the smallest class count in every outer test fold and every inner test fold. If an inner fold would hold fewer than 5 of a class, lower `n_splits` and record why.
Test: train and test IDs are disjoint and cover the full index for every fold; a toy case with a repeated ID is rejected.

## Phase 5: Per-modality models (Nov 27-28) [MUST for RNA elastic-net; SHOULD for others]
Files: `src/modality_models.py`, `results/modality_scores.csv` (macro-F1, bootstrap low and high, per-class recall, seed).
5.1 Majority baseline. Any "handful of features" baseline uses a gene list written down before any score, never genes chosen by looking at the labels.
5.2 RNA elastic-net logistic regression as a Pipeline (impute, scale, model), `solver="saga"`, explicit `max_iter`, tiny inner grid over C and l1_ratio. Time one fit first. If it is too slow, add a variance screen inside the Pipeline, fit on training rows only.
5.3 Report OOF macro-F1 with a bootstrap 95% CI, per-class recall, confusion matrix. Bootstrap by resampling the pooled outer-test predictions (do not refit the search). State the limitation: this ignores fold-to-fold variation, so intervals run slightly narrow.
5.4 One label-shuffle check: shuffle only y, one seed, the small RNA pipeline, write the score to `results/`, do not retune afterwards.
5.5 SHOULD: the same protocol for miRNA, methylation, CNV (Original). Do not drop any modality from the table after seeing scores.
5.6 SHOULD: XGBoost on RNA only. Early stopping watches an inner validation fold, never the outer test fold.
5.7 The RNA-only result is always its own line, with the sentence that PAM50 is defined from RNA, so this comparison is partly circular.
Test: on a toy train and test frame, imputed values and scaler mean match the training rows only.

## Phase 6: Fusion (Nov 28) [MUST if two or more modalities finished; otherwise design]
Files: `src/stack.py`, `results/fusion_scores.csv`.
6.1 For each outer fold, build out-of-fold probabilities from the outer-training patients only (`cross_val_predict(..., method="predict_proba")` inside that fold). Fit the stacker (a small logistic regression) on those, then predict the outer-test patients.
6.2 Report fusion, RNA-only, and the best single modality, with the single modality named before scores are seen. Keep a negative result in the CSV.
Test: stacker training IDs and outer-test IDs have an empty intersection.

## Phase 7: Calibration and abstention (Nov 29) [MUST on the RNA OOF]
Files: `src/calibrate.py`, `results/calibration.csv`, `results/risk_coverage.csv`.
7.1 Fit one temperature per outer fold on inner out-of-fold probabilities from the outer-training patients. Report ECE before and after and a reliability plot.
7.2 Choose the abstain threshold on inner out-of-fold probabilities only, never on predictions for rows the model was fit on, and never on the test fold. Report accuracy and macro-F1 at 90% and 80% coverage, with the classes still predicted (Her2 and Normal can vanish).
7.3 SHOULD: coefficient stability (selection frequency across outer folds) for the RNA elastic-net. Name this model before looking at scores. It feeds Workstream 4's attribution signal; if skipped, attribution is design.
Test: the threshold function refuses to accept test-fold probabilities.

## Background downloads (start Nov 27, while coding other phases) [MUST for Phase 9]
Report file names and sizes before using any of them.
- DepMap: CRISPR gene effect and model annotations.
- Open Targets: target-disease associations and tractability.
- ChEMBL: drug-target links.
- GDC TCGA-BRCA somatic mutations (open-access), to define a BRCA1/BRCA2-mutant group for PARP1. If this is not reachable in time, use the Basal group as the stated fallback and say so on the slide.
Any signal whose file is not on disk is labeled design and omitted from the rank sum.

## Phase 8: Imaging pilot [recommended cut for the class project: present as design]
Recommended 2026-11-27 (unless Thaarun decides otherwise): do not run this phase before the presentation; show imaging as a planned next step (design). Revisit only if every MUST is finished.
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
- Nov 22-27: Phases 1-3 done
- Nov 27: Phase 4 (audit, fold counts, split test); start Phase 5 (majority baseline, time one RNA fit); start background downloads (DepMap first)
- Nov 28: Phase 5 (RNA nested CV, shuffle check; other modalities if runtime allows); Phase 6 if two or more modalities finished
- Nov 29: Phase 7 (calibration, abstention); write the rediscovery rule file; Phase 9 ranking with what is on disk
- Nov 30: finish Phase 9; Phase 10 figures and slides; buffer
- After Nov 30: stretch items and rehearsal, until the presentation

## Three risks and the cut for each
1. Nested CV on Original RNA is too slow or unstable for the small classes: cut XGBoost and extra modalities, keep one outer 5-fold, small inner grid, RNA elastic-net, majority baseline, CI, per-class recall. Fusion and imaging become design.
2. Imaging is cut (see Phase 8). If it is revived and the GPU check fails or the slide download starts late, skip it and spend the time on Phase 9.
3. A target database or the mutation file is missing on Nov 29: do not block. Write the top-5% rule anyway, rank with what is on disk, label the rest design, and cut 9.7 and 9.8 first.
