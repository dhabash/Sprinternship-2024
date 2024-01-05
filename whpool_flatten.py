import os
import csv

base_folder = "/Users/dhabash/Documents/GitHub/Sprinternship-2024/whpool_month_of_2021-04"
output_csv_path = "/Users/dhabash/Documents/GitHub/Sprinternship-2024/output_flatten_3.csv"

HEADER = ["ID", "Date", "Reporter", "Title"]

with open(output_csv_path, 'w', newline='') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=HEADER, extrasaction='ignore')
    csv_writer.writeheader()

    for file_name in os.listdir(base_folder):
        file_path = os.path.join(base_folder, file_name)

        if os.path.isfile(file_path):  # Check if it's a file
            # Read the contents of the file
            with open(file_path, 'r', encoding="ISO-8859-1") as input_file:
                file_lines = input_file.readlines()

            # Initialize variables to store field values
            id_value = None
            date_value = None
            reporter_value = None
            title_value = None

            # Iterate through the lines and extract field values
            for line in file_lines:
                line = line.strip()  # Remove leading/trailing whitespace

                if line.startswith("ID:"):
                    id_value = line.split(":", 1)[1].strip()
                elif line.startswith("Date:"):
                    date_value = line.split(":", 1)[1].strip()
                elif line.startswith("Reporter:"):
                    reporter_value = line.split(":", 1)[1].strip()
                elif line.startswith("Title:"):
                    title_value = line.split(":", 1)[1].strip()

            # Check if all fields have been extracted
            if id_value is not None and date_value is not None and reporter_value is not None and title_value is not None:
                row_data = {
                    'ID': id_value,
                    'Date': date_value,
                    'Reporter': reporter_value,
                    'Title': title_value
                }

                # Write the row to the CSV file
                csv_writer.writerow(row_data)
