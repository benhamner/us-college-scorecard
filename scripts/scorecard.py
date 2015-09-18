import csv

# Process data dictionary
sqlite_types = {
    "integer": "INTEGER",
    "string":  "TEXT",
    "float":   "REAL"
}
name_col=4
type_col=5
value_col=7
label_col=8
previous_col = None
columns = {}
for (i, row) in enumerate(csv.reader(open("working/raw/CollegeScorecard_Raw_Data/CollegeScorecardDataDictionary-09-12-2015.csv"))):
#    print("Row %d, %s, %s, %s" % (i+1, row[name_col], row[value_col], row[label_col]))
    if i==0:
        assert row[name_col]=="VARIABLE NAME"
        assert row[type_col]=="API data type"
        assert row[value_col]=="VALUE"
        assert row[label_col]=="LABEL"
        continue
    if row[name_col].strip() != "":
        previous_col = row[name_col]
        if row[type_col]=="integer" and row[value_col].strip() != "":
            assert row[label_col].strip() != ""
            columns[row[name_col]] = {"type": sqlite_types[row[type_col]],
                                      "key": {row[value_col]: row[label_col]}}
        elif row[type_col] in sqlite_types:
            assert row[value_col].strip() == ""
            columns[row[name_col]] = {"type": sqlite_types[row[type_col]]}
        else:
            raise Exception("Unexpected type: %s" % row[type_col])
    else:
        assert row[value_col] != ""
        assert row[label_col] != ""
        columns[previous_col]["key"][row[value_col]] = row[label_col]
print(len(columns))
columns["Year"] = {"type": sqlite_types["integer"]}

# Correcting errors in dictionary/data combination
for col in ["CIP01CERT1", "CIP01CERT2", "CIP01ASSOC"]:
    if "0" not in columns[col]["key"]:
        columns[col]["key"]["0"] = "Program not offered"
    if "1" not in columns[col]["key"]:
        columns[col]["key"]["1"] = "Program offered"
    if "2" not in columns[col]["key"]:
        columns[col]["key"]["2"] = "Program offered through an exclusively distance-education program"
if "68" not in columns["st_fips"]["key"]:
    columns["st_fips"]["key"]["68"] = "Unknown"
if "0" not in columns["CCUGPROF"]["key"]:
    columns["CCUGPROF"]["key"]["0"] = "Unknown"

# Process data files
years = range(1996, 2014)
filename_from_year = lambda year: "working/raw/CollegeScorecard_Raw_Data/MERGED%d_PP.csv" % year

r = csv.reader(open(filename_from_year(years[0])))
rows = list(r)
header_raw = rows[0]

f = open("output/Scorecard.csv", "w")

w = csv.writer(f)

if header_raw[0]=="\ufeffUNITID":
    print("removing unicode from header")
    header = ["UNITID"] + header_raw[1:] + ["Year"]
else:
    header = header_raw + ["Year"]

for missing in set(header).difference(set(columns.keys())):
    print("Adding column %s as string type" % missing)
    columns[missing] = {"type": sqlite_types["string"]}

in_dictionary_not_header = set(columns.keys()).difference(set(header))
if in_dictionary_not_header:
    raise Exception("Not handling case where items in dictionary aren't in header: %s" % in_dictionary_not_header)

w.writerow(header)

def transform(x, col_name, columns):
    if x=="NULL":
        return ""
    if "key" in columns[col_name]:
        try:
            return columns[col_name]["key"][x]
        except:
            print("Key %s not found in column %s" %(x, col_name))
    return x

for year in years:
    rows = list(csv.reader(open(filename_from_year(year))))
    if header_raw != rows[0]:
        raise Exception("Different headers")
    for row in rows[1:]:
        row = row + [str(year)]
        row = [transform(row[i], col, columns) for (i, col) in enumerate(header)]
        w.writerow(row)
f.close()

sqlite_imports = ["    %s %s," % (col, columns[col]["type"]) for col in header]
sqlite_imports[-1] = sqlite_imports[-1][:-1] + ");"
sqlite_imports = ([".separator \",\"", "", "CREATE TABLE Scorecard ("] + 
                  sqlite_imports +
                  ["", ".import working/ScorecardNoHeader.csv Scorecard"])
f = open("working/sqliteImport.sql", "w")
f.write("\n".join(sqlite_imports))
f.close()
