from numpy.lib.function_base import extract
import pdfplumber
import pandas as pd
import re

NAN_VALUE = float("NaN")

def debit(table_df):
    table_df_temp = table_df.dropna(subset=["Credit"])
    table_df_temp = table_df_temp.drop(["Debit"], axis=1)
    table_df_temp = table_df_temp.reset_index().drop(["index"], axis=1)

    return table_df_temp

def credit(table_df):
    table_df_temp = table_df.dropna(subset=["Debit"])
    table_df_temp = table_df_temp.drop(["Credit"], axis=1)
    table_df_temp = table_df_temp.reset_index().drop(["index"], axis=1)

    return table_df_temp

def extract_table_data(table):
    table_df_temp = pd.DataFrame(table, columns=["ope", "Date", "Libelle", "Debit",
        "Credit","Check"])

     # Cleaning Data Frame
    table_df_temp = table_df_temp.drop(["ope", "Check"], axis=1)
    table_df_temp = table_df_temp.drop([0,1,2,3,4])
    table_df_temp = table_df_temp.replace("", NAN_VALUE)
    table_df_temp = table_df_temp.dropna(subset=["Date"])
    table_df_temp = table_df_temp.reset_index().drop(["index"], axis=1)

    return table_df_temp

def plumber(pdf_file: str):
    with pdfplumber.open(pdf_file) as pdf:
        # Create Data Frame
        table_df = pd.DataFrame(columns=["Date", "Libelle", "Debit", "Credit"])

        # Read pdf file
        pages = pdf.pages

        for page_number, page in enumerate(pages):
            print("Analyzing page {}".format(page_number + 1))

            table = page.extract_table(table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        #"explicit_vertical_lines": curves_to_edges(page.curves),
                        "explicit_horizontal_lines": [ min(x["top"] for x in page.edges) ]
                        })

            # Cleaning table
            table_df_temp = extract_table_data(table)

            # Appending Table Data Frame
            table_df = table_df.append(table_df_temp).reset_index().drop(["index"], axis=1)

    print(table_df)

    # get table_df and only use column Date
    # get value and extract the month and day
    # add year at the begining of the sentence
    # invert month and day to obtain year-month-day

    """
    # Separing Debit and Credit data
    debit_df = debit(table_df)
    credit_df = credit(table_df)

    # Saving results en differents files
    table_df.to_excel("table.xlsx")
    debit_df.to_csv("debit.csv", index=False)
    credit_df.to_csv("credit.csv", index=False)
    """

def get_year(pdf_file: str):
    with pdfplumber.open(pdf_file) as pdf:
        first_page = pdf.pages[0]
        extracted_text = first_page.extract_text()
        
        search_eval = re.search("Date d'arrêté", extracted_text)

        start_extraction = search_eval.end() + 3
        end_extraction = search_eval.end() + 16
        start_year_straction = end_extraction - 4

        print("Date d'arrêté : ", extracted_text[start_extraction:end_extraction])

    return extracted_text[start_year_straction:end_extraction]

if __name__ == "__main__":
    pdf_file = "Releve.pdf"
    year = get_year(pdf_file)
    print(year)
    plumber(pdf_file)
