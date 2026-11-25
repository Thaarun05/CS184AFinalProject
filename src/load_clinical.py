import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


clinical_raw = "data/raw/clinical/clinical.tsv"
clinical_df = pd.read_csv(clinical_raw, sep="\t", dtype=str, na_values=["'--"])  
# print(clinical_df.shape) 
share = clinical_df.notna().mean() # show share of non-null values for each column
# print(share)
# dropped = share[(share > 0) & (share <= 0.05)]
# print(dropped.sort_values(ascending=False))
clinical_df = clinical_df.loc[:, share > 0.05] # select all rows and columns with more than 5% non-null values
clinical_df.columns = clinical_df.columns.str.replace(".", "_", regex=False) # replace for ex.) cases.submitter_id -> cases_submitter_id, regex=False 
# print(clinical_df.shape)
# print(list(clinical_df.columns))

url = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password=os.environ["MYSQL_PWD"],
    host="localhost",
    database="brca_project",
)

engine = create_engine(url)

clinical_df.to_sql("clinical_raw", engine, if_exists="replace", index=False) # write table replacing old one without pandas row number column


# labels = "data/raw/GS-Subtype-Labels.xlsx"



