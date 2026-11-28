import numpy as np
from sklearn.model_selection import StratifiedKFold
import pandas as pd

def outer_folds(y, n_splits=5, seed=42):
    # y is PAM50 label with patient_id as index from load_xy
    assert y.index.is_unique
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed) # stratified --> same class proportions
    return [(y.index[train], y.index[test]) for train, test in skf.split(np.zeros(len(y)), y)] # build list of tuples of train ids and test ids for each fold


def fold_table(y, n_splits=5, seed=42):
    parts = []
    for fold, (_, test_ids) in enumerate(outer_folds(y, n_splits, seed)):
        parts.append(pd.DataFrame({"patient_id": test_ids, "fold": fold}))
    table = pd.concat(parts, ignore_index=True) # table of (patient, test fold)
    assert table["patient_id"].is_unique and len(table) == len(y)
    return table.set_index("patient_id").loc[y.index].reset_index()


if __name__ == "__main__":
    from src.data import load_xy

    _, y = load_xy(["miRNA"])
    for i, (train_ids, test_ids) in enumerate(outer_folds(y)):
        print(i, y.loc[test_ids].value_counts().sort_index().to_dict()) # class counts per fold


    fold_table(y).to_csv("results/folds.csv", index=False)
