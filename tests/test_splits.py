from src.data import load_xy
from src.splits import outer_folds

def test_folds_disjoint_and_complete():
    _, y = load_xy(["miRNA"])
    for train_ids, test_ids in outer_folds(y):
        assert set(train_ids).isdisjoint(test_ids)
        assert set(train_ids) | set(test_ids) == set(y.index)