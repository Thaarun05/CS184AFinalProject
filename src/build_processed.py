from pathlib import Path
import pandas as pd


brca_dir = Path("data/raw/MLOmics/Main_Dataset/Classification_datasets/GS-BRCA")
labels_path = Path("data/raw/MLOmics/Main_Dataset/Classification_datasets/GS-BRCA/Original/BRCA_label_num.csv")
out_dir = Path("data/processed")


# matrices: patients x features saved as parquet
matrices = {}
for name in ["mRNA", "miRNA", "Methy", "CNV"]:
    matrix = pd.read_csv(brca_dir / "Original" / f"BRCA_{name}.csv", index_col=0).T
    matrix.index = matrix.index.str.replace(".", "-", regex=False).str[:12]
    matrix.index.name = "patient_id"
    assert matrix.index.is_unique and matrix.columns.is_unique
    matrix.to_parquet(out_dir / f"{name}_original.parquet")
    matrices[name] = matrix

for name, m in matrices.items():
    assert m.index.equals(matrices["mRNA"].index)


# labels
mapping = pd.read_excel(
    "data/raw/clinical/GS-Subtype labels.xlsx",
    header=None, skiprows=1, nrows=5, names=["label", "subtype_name"],
)
class_to_name = dict(zip(mapping["label"].astype(int), mapping["subtype_name"]))

labels = pd.read_csv(labels_path)
assert len(labels) == len(matrices["mRNA"])
labels.index = matrices["mRNA"].index
labels["subtype"] = labels["Label"].astype(int).map(class_to_name)
assert labels["subtype"].notna().all()
labels.to_csv(out_dir / "labels.csv")


# cohort table
clinical = pd.read_csv("data/interim/clinical_patient.csv", dtype=str).set_index("patient_id")
receptors = pd.read_csv("data/interim/receptors.csv", dtype=str).set_index("patient_id")

cohort = (labels[["Label", "subtype"]].join(clinical, how="left").join(receptors, how="left"))

assert cohort.index.equals(labels.index)
assert len(cohort) == 671
cohort.to_csv(out_dir / "cohort.csv")

print(cohort.shape)
print("not in clinical:", int(labels.index.isin(clinical.index).__invert__().sum()))
print("not in receptors:", int(labels.index.isin(receptors.index).__invert__().sum()))
print(cohort["exclude_flag"].value_counts(dropna=False))