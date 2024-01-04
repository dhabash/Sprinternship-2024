import os
import csv

base_folder = "/Users/dhabash/Documents/GitHub/Sprinternship-2024/whpool_month_of_2021-04"
output_csv_path = "/Users/dhabash/Documents/GitHub/Sprinternship-2024/output123.csv"

HEADER = ["File Name", "Content"]

with open(output_csv_path, 'w', newline='') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=HEADER, extrasaction='ignore')
    csv_writer.writeheader()

    for folder_name, subfolders, file_names in os.walk(base_folder):
        for file_name in file_names:
            file_path = os.path.join(folder_name, file_name)

            # Read the contents of the file
            with open(file_path, 'r', encoding="ISO-8859-1") as input_file:
                file_contents = input_file.read()

            # Create a dictionary with file name and contents
            row_data = {'File Name': file_name, 'Content': file_contents}

            # Write the row to the CSV file
            csv_writer.writerow(row_data)






"""Open the output CSV for writing
with open(output_path / 'whpool.csv', 'w') as csv_file:
            csv_writer = DictWriter(csv_file, fieldnames=HEADER, extrasaction='ignore', escapechar='\\')
            # Add the headers
            csv_writer.writeheader()


root.dictionary = "/Users/dhabash/Documents/GitHub/Sprinternship-2024/whpool_month_of_2021-0o4"

all_data = []

def parse_email(folder,filename)
    with open(os.path.join(folder,filename), 'r', encoding = 'utf-8') as file
    soup = BeautifulSoup (fi)


#pd.read_html(body-517.html) """

