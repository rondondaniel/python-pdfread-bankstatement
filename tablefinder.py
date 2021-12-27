import pdfplumber
import pandas as pd
import re
import glob
import os

NAN_VALUE = float("NaN")

def credit(table_df):
    table_df_temp = table_df.dropna(subset=["Credit"])
    table_df_temp = table_df_temp.drop(["Debit"], axis=1)
    table_df_temp = table_df_temp.reset_index()
    table_df_temp.columns = ["Payment Number Suffix",
                             "Date",
                             "Description",
                             "Amount",
                             "Customer Name",]
    print("Credit data extracted")

    return table_df_temp

def debit(table_df):
    table_df_temp = table_df.dropna(subset=["Debit"])
    table_df_temp = table_df_temp.drop(["Credit"], axis=1)
    table_df_temp["TTC"] = "true"
    table_df_temp["Taxe"] = "TVA"
    table_df_temp["Taxe Percentage"] = int(20)
    table_df_temp["Currency Code"] = "EUR"
    table_df_temp = table_df_temp.reset_index()
    table_df_temp.columns = ["Entry Number",
                             "Expense Date",
                             "Expense Description",
                             "Expense Amount",
                             "Expense Account",
                             "is Inclusive Tax",
                             "Tax Name",
                             "Tax Percentage", 
                             "Currency Code",]

    print("Debit data extracted")

    return table_df_temp

def extract_table_data(table):
    table_df_temp = pd.DataFrame(table, columns=["ope",
                                                 "Date",
                                                 "Libelle",
                                                 "Debit",
                                                 "Credit",
                                                 "Check"])

     # Cleaning Data Frame
    table_df_temp = table_df_temp.drop(["ope", "Check"], axis=1)
    table_df_temp = table_df_temp.replace("", NAN_VALUE)
    table_df_temp = table_df_temp.drop([0])
    table_df_temp = table_df_temp.dropna(subset=["Date"])
    
    # Replace "," to "."
    table_df_temp["Debit"] = table_df_temp["Debit"].str.replace(",", ".")
    table_df_temp["Credit"] = table_df_temp["Credit"].str.replace(",", ".")
    
    # Replace " " to ""
    table_df_temp["Debit"] = table_df_temp["Debit"].str.replace(" ", "")
    table_df_temp["Credit"] = table_df_temp["Credit"].str.replace(" ", "")

    # Convert dTypes to "float"
    table_df_temp["Debit"] = table_df_temp["Debit"].astype(float)
    table_df_temp["Credit"] = table_df_temp["Credit"].astype(float)

    table_df_temp = table_df_temp.reset_index().drop(["index"], axis=1)
    print("Bank data extracted")

    return table_df_temp

def get_conditions():
    conditions_df = pd.read_csv("conditions.csv")

    return conditions_df

def folder_creator(pdf_file: str):
    file_name, _ = pdf_file.split(".")

    if not os.path.exists(file_name):
        os.mkdir(file_name)

    return file_name

# function doing the job
def plumber(pdf_file: str,
            year: str):
    
    print("{} analyze".format(pdf_file))

    with pdfplumber.open(pdf_file) as pdf:
        # Create Data Frame
        table_df = pd.DataFrame(columns=[
                                         "Date",
                                         "Libelle",
                                         "Debit",
                                         "Credit"
                                        ])

        conditions_df = get_conditions()

        # Read pdf file & extract table
        pages = pdf.pages

        for page_number, page in enumerate(pages):
            print("Analyzing page {}".format(page_number + 1))

            table = page.extract_table(table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "explicit_horizontal_lines":\
                             [ min(x["top"] for x in page.edges) ]
                        })

            # Cleaning table & Appending Table Data Frame
            table_df_temp = extract_table_data(table)
            table_df = table_df.append(table_df_temp).reset_index()\
                .drop(["index"], axis=1)

            # keep the index but changing the name to Entry Number

    # Modify Date format from DD.MM to YYYY-MM-DD and adding other informations
    table_df["Date"] = year + "-" + table_df["Date"].astype(str).str[3:5] \
                        + "-" + table_df["Date"].astype(str).str[0:2]

    table_df["Compte"]= NAN_VALUE

    for condition in range(0, conditions_df.shape[0]):
        index_values = (table_df[table_df["Libelle"].str\
                        .contains(conditions_df["Condition"].loc[condition])]\
                        .index.values)

        for index in index_values:
            table_df["Compte"].loc[index] = conditions_df["Compte"].loc[condition]

    # Separing Debit and Credit data
    debit_df = debit(table_df)
    credit_df = credit(table_df)

    # Create folder for results
    folder = folder_creator(pdf_file)

    # Saving results in different files
    table_df.to_excel("{}/{}".format(folder, "table.xlsx"))

    debit_df.to_excel("{}/{}".format(folder, "debit.xlsx"), index=False)

    credit_df.to_excel("{}/{}".format(folder, "credit.xlsx"), index=False)

def get_year(pdf_file: str):
    with pdfplumber.open(pdf_file) as pdf:
        first_page = pdf.pages[0]
        extracted_text = first_page.extract_text()
        
        # Regex statements 
        search_eval = re.search(
            " : *[0-9]* [a-zéèûA-Z]* ([0-9]{4})",
            extracted_text
            )

        year = search_eval.group(1)
        print("Date d'arrêté :", year)

    return year

if __name__ == "__main__":
    pdf_files = glob.glob("*.pdf")
    print(pdf_files)

    for pdf_file in pdf_files:
        #folder_creator(pdf_file)
        year = get_year(pdf_file)
        plumber(pdf_file,
                year)