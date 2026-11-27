from pathlib import Path
import pandas as pd

brca_dir = Path("data/raw/MLOmics/Main_Dataset/Classification_datasets/GS-BRCA")

# for subset_name in ["Original", "Top", "Aligned"]:
#     subset_dir = brca_dir / subset_name
#     print(f"\n{subset_name}")

#     for file_path in sorted(subset_dir.glob("*csv")):
#         size_mb = file_path.stat().st_size / 1024**2
#         print(f"{file_path.name}: {size_mb:.1f} MB")

mrna_path = brca_dir / "Original" / "BRCA_mRNA.csv"

# mrna_preview = pd.read_csv(
#     mrna_path,
#     nrows=5,
# )

# candidate_ids = mrna_preview.columns[1:6]

# print("preview shape:", mrna_preview.shape)
# print("first six column names:", mrna_preview.columns[:6].tolist())
# print("first five values in column 1:", mrna_preview.iloc[:, 0].tolist())

# print(
#     pd.DataFrame(
#         {
#             "candidate_id": candidate_ids,
#             "id_length": candidate_ids.str.len(),
#         }
#     ).to_string(index=False)
# )


mrna = pd.read_csv(
    mrna_path,
    index_col=0,
)

raw_sample_ids = pd.Index(mrna.columns)

patient_ids = (
    raw_sample_ids
    .str.replace(".", "-", regex=False)
    .str[:12]
)

# print("mRNA shape, features x samples:", mrna.shape)

# print(
#     pd.DataFrame(
#         {
#             "raw_sample_id": raw_sample_ids[:5],
#             "patient_id": patient_ids[:5],
#             "raw_length": raw_sample_ids[:5].str.len(),
#             "patient_length": patient_ids[:5].str.len(),
#         }
#     ).to_string(index=False)
# )

# print("n_duplicate_patient_ids:", patient_ids.duplicated().sum())



# for modality in ["CNV", "Methy", "miRNA"]:
#     matrix_path = brca_dir / "Original" / f"BRCA_{modality}.csv"

#     matrix = pd.read_csv(
#         matrix_path,
#         index_col=0,
#     )

#     raw_ids = pd.Index(matrix.columns)
#     mapped_ids = (
#         raw_ids
#         .str.replace(".", "-", regex=False)
#         .str[:12]
#     )

#     print(f"\n{modality}")
#     print("shape, rows x samples:", matrix.shape)
#     print("first five row labels:", matrix.index[:5].tolist())
#     print(
#         pd.DataFrame(
#             {
#                 "raw_sample_id": raw_ids[:5],
#                 "patient_id": mapped_ids[:5],
#                 "raw_length": raw_ids[:5].str.len(),
#                 "patient_length": mapped_ids[:5].str.len(),
#             }
#         ).to_string(index=False)
#     )
#     print("n_duplicate_patient_ids:", mapped_ids.duplicated().sum())

#     del matrix


# for modality in ["CNV", "Methy", "mRNA", "miRNA"]:
#     top_path = brca_dir / "Top" / f"BRCA_{modality}_top.csv"

#     top_matrix = pd.read_csv(
#         top_path,
#         index_col=0,
#     )

#     raw_ids = pd.Index(top_matrix.columns)
#     mapped_ids = (
#         raw_ids
#         .str.replace(".", "-", regex=False)
#         .str[:12]
#     )

#     print(f"\nTop {modality}")
#     print("shape, rows x samples:", top_matrix.shape)
#     print("first five row labels:", top_matrix.index[:5].tolist())
#     print(
#         pd.DataFrame(
#             {
#                 "raw_sample_id": raw_ids[:5],
#                 "patient_id": mapped_ids[:5],
#                 "raw_length": raw_ids[:5].str.len(),
#                 "patient_length": mapped_ids[:5].str.len(),
#             }
#         ).to_string(index=False)
#     )
#     print("n_duplicate_patient_ids:", mapped_ids.duplicated().sum())

#     del top_matrix


# ids = {}
# for name in ["mRNA", "miRNA", "Methy", "CNV"]:
#     path = brca_dir / "Original" / f"BRCA_{name}.csv"
#     cols = pd.read_csv(path, nrows=0).columns[1:]
#     ids[name] = [c.replace(".", "-")[:12] for c in cols]
#     suffixes = {c.split(".")[-1] for c in cols}
#     print(name, len(cols), cols[0], len(set(ids[name])), suffixes)

# print(all(ids[k] == ids["mRNA"] for k in ids))



mapping = pd.read_excel(
    "data/raw/clinical/GS-Subtype Labels.xlsx",
    header=None,
    skiprows=1,
    nrows=5,
    names=["label", "subtype_name"]
)
class_to_name = dict(zip(mapping["label"].astype(int), mapping["subtype_name"]))
print(class_to_name)


labels = pd.read_csv("data/raw/MLOmics/Main_Dataset/Classification_datasets/GS-BRCA/Original/BRCA_label_num.csv")
assert len(labels) == len(patient_ids)
labels.index = patient_ids
labels.index.name = "patient_id"

labels["subtype"] = labels["Label"].astype(int).map(class_to_name)
assert labels["subtype"].notna().all()
print(labels["subtype"].value_counts())


# receptors = pd.read_csv("data/interim/receptors.csv", dtype=str).set_index("patient_id")
# check = labels.join(receptors[["ER", "HER2"]])
# print(pd.crosstab(check["subtype"], check["ER"].fillna("missing")))
# print(pd.crosstab(check["subtype"], check["HER2"].fillna("missing")))


matrices = {}
for name in ["mRNA", "miRNA", "Methy", "CNV"]:
    matrix = pd.read_csv(brca_dir / "Original" / f"BRCA_{name}.csv", index_col=0).T
    matrix.index = matrix.index.str.replace(".", "-", regex=False).str[:12]
    assert matrix.index.equals(labels.index)
    assert matrix.columns.is_unique
    print(name, matrix.shape, int(matrix.isna().sum().sum()))
    matrices[name] = matrix