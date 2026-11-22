import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


raw = "data/raw/clinical/clinical.tsv"
df = pd.read_csv(raw, sep="\t", dtype=str, na_values=["'--"])  
# print(df.shape) 
share = df.notna().mean() # show share of non-null values for each column
# print(share)
# dropped = share[(share > 0) & (share <= 0.05)]
# print(dropped.sort_values(ascending=False))
df = df.loc[:, share > 0.05] # select all rows and columns with more than 5% non-null values
df.columns = df.columns.str.replace(".", "_", regex=False) # replace for ex.) cases.submitter_id -> cases_submitter_id, regex=False 
# print(df.shape)
# print(list(df.columns))

url = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password=os.environ["MYSQL_PWD"],
    host="localhost",
    database="brca_project",
)

engine = create_engine(url)

df.to_sql("clinical_raw", engine, if_exists="replace", index=False) # write table replacing old one without pandas row number column



