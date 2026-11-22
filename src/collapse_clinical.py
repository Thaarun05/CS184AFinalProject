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
print(desc.to_string())
print("cases_submitter_id" in set(desc["Field"]))

counts = pd.read_sql(
    """
    SELECT COUNT(*) AS n_rows,
           COUNT(DISTINCT cases_submitter_id) AS n_patients,
           SUM(cases_submitter_id IS NULL) AS n_null_id
    FROM clinical_raw
    """,
    engine,
)
print(counts.to_string())

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
print(hist.to_string())