# PROJECT_CONTEXT.md

Read this first in every new chat. It holds the decisions made so far. Update the "Progress log" at the end of each session.

## Who and what
Thaarun, UCI CSE '28, bioinformatics minor. CS 184A (AI in Bio) final project. Presentation is about 10 days from 2026-11-19. He will keep working on this research after the course and wants it to be publication-level (AACR, EACR, ML4H) and eventually a full-stack web app.

**He wants to write the code himself and understand every line.** See AGENTS.md for how to behave.

## Long-term vision (context only)
At a checkup: take a patient's multi-omics and imaging, decide whether it is breast cancer and what kind, whether it spread, whether it may develop later, then find targets, propose molecules, simulate response, and write a cited report. Everything is research use only.

## Scope of the 10-day class project
Two workstreams, nothing else:

**Workstream 1: subtype diagnosis (thin version).** Predict the 5 PAM50 subtypes from multi-omics, with calibrated probabilities and an option to abstain.
- Labels: 0 LumA, 1 Her2, 2 LumB, 3 Normal, 4 Basal (from GS-Subtype_labels.xlsx; the old notebook comment was wrong).
- Notebook class counts 353, 42, 132, 31, 113 (assumed in class-index order; confirm with value_counts).
- Models: elastic-net logistic regression and XGBoost per modality, then stacked late fusion. No neural network in the first pass.
- Evaluation: nested repeated stratified CV, macro-F1 with bootstrap CIs, per-class recall, calibration (temperature scaling), risk-coverage curve.
- Imaging pilot: TCGA-BRCA H&E slide features from a frozen pretrained model on a slide subset; compare omics only, image only, fused on the same patients.
- Always report an RNA-only result beside multi-omics (subtype is defined from RNA, so RNA-to-subtype is close to circular).

**Workstream 4: target ranking.** Rank genes per subtype by six signals combined by rank aggregation: stable model attribution, DepMap dependency, driver evidence, tumor-vs-subtype expression, druggability, normal-tissue safety.
- Test: masked rediscovery. Hide the known drug links for PARP1 (BRCA1/2-mutant tumors; mutations from GDC, basal-like as fallback), CDK4/6 (luminal) and ERBB2 (Her2 group). Success threshold written before the run: top 5% of genes.
- ERBB2 in the Her2 group is close to circular; treat it as a sanity check. PARP1 and CDK4/6 are the informative cases.
- Baselines: differential expression alone, DepMap alone, Open Targets with drug evidence removed.
- Ablate each signal. Report negative results.
- Optional: a pre-written list of known breast targets, hiding each in turn.

**Cut (later work):** spread/recurrence, future risk, new molecule design, simulation, report generation, web app. Radiology (MRI, mammography) is later.

## Data
| Source | Use | Note |
|---|---|---|
| MLOmics GS-BRCA (HF `AIBIC/MLOmics`) | Diagnosis baseline | 671 TCGA patients; mRNA, methylation, CNV 5,000 features each in "Top" files, miRNA 366. "Top" files may be label-selected. File names/orientation/IDs not yet confirmed. |
| GDC TCGA-BRCA clinical TSVs | Receptors, stage, M status | 1,098 patients. clinical.tsv has 5,546 rows (patients repeat). Missing marker is `'--`. family_history (empty) and exposure (1 patient) are useless. |
| nationwidechildrens.org clinical patient table | Receptor descriptors | `nationwidechildrens.org_clinical_patient_brca.txt`; 1,097 patients; baseline IHC receptor calls plus HER2 FISH fallback |
| GS-Subtype_labels.xlsx | Class mapping | |
| GDC slides | Imaging pilot | 1,062 diagnostic-slide cases; subset only; needs a GPU |
| DepMap, ChEMBL, Open Targets | Workstream 4 | not yet downloaded |
| METABRIC (cBioPortal), HTAN, AURORA (TCIA) | Later / outside check | AURORA: 55 patients, images + clinical CC BY 4.0, molecular on dbGaP/GEO |

Wide omics matrices stay in pandas (MySQL InnoDB allows at most 1,017 columns per table). MySQL holds only clinical, receptor and label tables.

## Environment
- Repo: github.com/Thaarun05/CS184AFinalProject, macOS, `.venv`, MySQL in DBeaver, database `brca_project`.
- Password only via the `MYSQL_PWD` environment variable, never in code.
- Compute: Google Cloud $300 credit (upgrade to paid for GPU, budget alert at $50), AWS about $117 credit, Databricks Free Edition (CPU only), about 600 GB local disk. Slides: run extraction on a cloud GPU, delete slides after saving features.
- Venues: AACR late-breaking due 2027-01-06 (eligibility unchecked); EACR 2027 abstracts due 2027-03-02; ML4H 2026 deadline passed, watch the 2027 call.

## Rules that hold everywhere
1. Never fit anything (scaling, imputation, feature selection, tuning) on rows later used for testing; use sklearn Pipeline inside nested CV.
2. Never feed ER/PR/HER2 into the subtype model.
3. Outside cohorts are test-only.
4. Join on patient IDs (12-character TCGA ID), never row order; assert alignment.
5. Raw data is read-only; every cleaned file comes from a script.
6. Record seeds; numbers in slides come from files in `results/`.
7. Label results validated / pilot / design.

## Progress log
- 2026-11-21: `src/load_clinical.py` tidies clinical.tsv: reads with `na_values=["'--"]`, keeps columns more than 5% filled (202 to 65; dropped ones were negligible), renames dots to underscores. Next: add the `to_sql` load into `brca_project.clinical_raw`, find which columns cause repeated rows (groupby/nunique), then collapse to one row per patient in SQL.
- 2026-11-24: Phase 1 complete. `clinical_patient.csv` has 1,098 unique 12-character patient IDs and only stable descriptive fields; diagnosis and treatment fields are intentionally excluded.
- 2026-11-25: Phase 2 receptor audit complete. `receptors.csv` has 1,097 unique IDs; ER/PR use explicit IHC calls, HER2 uses IHC with FISH fallback, and all rows are retained with 25 documented flags for later sensitivity analysis.

## Next steps
1. Add `tests/test_receptors.py`: one row per patient ID, all IDs length 12, and receptor fields excluded from the future model-feature list.
2. Start Phase 3: inspect MLOmics GS-BRCA filenames, orientations, and ID formats; inspect the subtype-label workbook before loading either into a model.
3. Align Original omics matrices and labels by 12-character patient ID, then complete the leakage audit and nested-CV baseline.

## Longer docs (private Claude Docs, for reference only)
- Proposal (class template): https://claude.ai/artifact/MrBBmWLuxyGP9e721pGWk6
- Full-vision roadmap: https://claude.ai/artifact/LqAyAwf3RBxkrhmWu1Wuhv
- Workstream 1 build guide: https://claude.ai/artifact/24m1mzMJf2oUcry481N6AT
- 2026-11-21: MySQL connection works; `clinical_raw` loaded into brca_project. Next: PLAN.md Phase 1.
