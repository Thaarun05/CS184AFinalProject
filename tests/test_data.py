from src.data import load_xy


def test_rna_only():
    X, y = load_xy(["mRNA"])
    assert X.shape[0] == 671
    assert all(c.startswith("mRNA__") for c in X.columns)
    assert y.value_counts().sort_index().tolist() == [353, 42, 132, 31, 113]