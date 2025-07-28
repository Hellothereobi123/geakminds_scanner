import pandas as pd
import pymysql

new_df = pd.read_csv("C:/Users/tharu/OneDrive/Documents/final_git_rep/geakminds_scanner/util/job_desc.csv")
for i in range(len(new_df)):
    new_df.iloc[i, 1] = new_df.iloc[i, 1].split(" ")[0]
print(new_df.iloc[0, 3])

new_df.to_csv("C:/Users/tharu/OneDrive/Documents/final_git_rep/geakminds_scanner/util/job_desc.csv", index=False)