import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password=os.environ["MYSQL_PWD"],
    host="localhost",
    database="brca_project",
)
engine = create_engine(url)


desc = pd.read_sql("DESCRIBE clinical_raw", engine)
# print(desc.to_string())
# print("cases_submitter_id" in set(desc["Field"]))

counts = pd.read_sql(
    """
    SELECT COUNT(*) AS n_rows,
           COUNT(DISTINCT cases_submitter_id) AS n_patients,
           SUM(cases_submitter_id IS NULL) AS n_null_id
    FROM clinical_raw
    """,
    engine,
)
# print(counts.to_string())


hist = pd.read_sql(
    """
    SELECT n_rows, COUNT(*) AS n_patients
    FROM (
        SELECT cases_submitter_id, COUNT(*) AS n_rows
        FROM clinical_raw
        GROUP BY cases_submitter_id
    ) AS per_patient
    GROUP BY n_rows
    ORDER BY n_rows
    """,
    engine,
)
# print(hist.to_string())


df = pd.read_sql("SELECT * FROM clinical_raw", engine)
n_varying_patients = df.groupby("cases_submitter_id").nunique().gt(1).sum()
# print(n_varying_patients[n_varying_patients.gt(0)].sort_values(ascending=False).to_string())


# diagnosis_cols = [col for col in df.columns if col.startswith("diagnoses_")]

# diagnosis_conflict_ids = (
#     df.groupby("cases_submitter_id")[diagnosis_cols].nunique().gt(1).any(axis=1)
# )

# sample_ids = diagnosis_conflict_ids[diagnosis_conflict_ids].index[:3]

# print(
#     df.loc[
#         df["cases_submitter_id"].isin(sample_ids),
#         ["cases_submitter_id", *diagnosis_cols],
#     ].drop_duplicates().to_string(index=False)
# )



# primary_diagnoses = (
#     df.loc[
#         df["diagnoses_diagnosis_is_primary_disease"].eq("true"),
#         ["cases_submitter_id", "diagnoses_diagnosis_id"],
#     ]
#     .drop_duplicates()
# )

# print(
#     primary_diagnoses.groupby("cases_submitter_id")
#     .size()
#     .value_counts()
#     .sort_index()
#     .to_string()
# )


# all_patient_ids = pd.Index(df["cases_submitter_id"].unique())

# no_primary_ids = all_patient_ids.difference(
#     primary_diagnoses["cases_submitter_id"].unique()
# )

# print(
#     df.loc[
#         df["cases_submitter_id"].isin(no_primary_ids),
#         ["cases_submitter_id", *diagnosis_cols],
#     ]
#     .drop_duplicates()
#     .to_string(index=False)
# )


# treatment_cols = [
#     col for col in df.columns
#     if col.startswith("treatments_")
# ]

# print(
#     df.loc[
#         df["cases_submitter_id"].isin(no_primary_ids),
#         ["cases_submitter_id", *treatment_cols],
#     ]
#     .drop_duplicates()
#     .to_string(index=False)
# )


patient_cols = [
    "cases_case_id",
    "cases_submitter_id",
    "cases_disease_type",
    "cases_primary_site",
    "demographic_age_at_index",
    "demographic_sex_at_birth",
    "demographic_vital_status"
]

clinical_patient = (
    df[patient_cols]
    .drop_duplicates()
    .rename(columns={"cases_submitter_id": "patient_id"})
)

clinical_patient.to_csv("data/interim/clinical_patient.csv", index=False)

print(clinical_patient.shape)

# print(clinical_patient)

# duplicate_rows = clinical_patient[
#     clinical_patient.duplicated("patient_id", keep=False)
# ]

# if not duplicate_rows.empty:
#     print(duplicate_rows.to_string(index=False))
#     raise AssertionError("A descriptive field differs within at least one patient.")


# raw_patient_ids = set(df["cases_submitter_id"].dropna())

# assert len(clinical_patient) == 1098
# assert clinical_patient["patient_id"].is_unique
# assert "TCGA-BH-A0B2" in set(clinical_patient["patient_id"])
# assert not any(
#     col.startswith(("diagnoses_", "treatments_"))
#     for col in clinical_patient.columns
# )
# assert set(clinical_patient["patient_id"]) == raw_patient_ids