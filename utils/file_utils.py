import csv

def iter_csv_rows(path):
    with open(path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            yield row