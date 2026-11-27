import pandas as pd

def load_xy(modalities, drop_flagged=False):
    cohort = pd.read_csv("data/processed/cohort.csv", index_col="patient_id", dtype=str)
    X = pd.concat({m: pd.read_parquet(f"data/processed/{m}_original.parquet") for m in modalities}, axis=1)
    X.columns = [f"{m}__{gene}" for m, gene in X.columns]
    assert X.index.equals(cohort.index)
    y = cohort["Label"].astype(int)
    if drop_flagged:
        keep = cohort["exclude_flag"].isna()
        X, y = X[keep], y[keep]
    return X, y