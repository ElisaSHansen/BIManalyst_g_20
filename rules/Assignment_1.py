import ifcopenshell as ifc
from collections import Counter

import os

model=ifc.open("25-16-D-STR.ifc")

# Lists up attributes for all columns in ifc file
columns = model.by_type('IfcColumn')

# Making a list of info for all columns
columns_info = [col.get_info() for col in columns]

# Prints the whole list
print(columns_info)

# Lists up names for all columns in ifc file
names = [col.Name for col in columns]
print(names)

# Concrete columns
# Print out concrete columns name
concrete_columns = [col for col in columns if col.Name and "Concrete" in col.Name]
print("\nNavn på alle Concrete-søyler:")
for col in concrete_columns:
    print("-", col.Name)

# Number of Concrete-columns
print("\nNumber of Concrete-columns:", len(concrete_columns))

# Get dimensions from the name (last part after colon ":")
dimensions = [col.Name.split(":")[-1].strip() for col in concrete_columns]

# Count how many of each dimension
dimension_counts = Counter(dimensions)

# Print result
print("Number of concrete columns per dimension:\n")
for dimension, count in dimension_counts.items():
    print(f"{dimension}: {count}")

# Wood columns
# Number of wood-columns
wood_columns = [col for col in columns if col.Name and "Wood" in col.Name]
print("\nNumber of wood-columns:", len(wood_columns))

# Get dimensions from the name (last part after colon ":")
dimensions = [col.Name.split(":")[-1].strip() for col in wood_columns]

# Count how many of each dimension
dimension_counts = Counter(dimensions)

# Print result
print("Number of wood columns per dimension:\n")
for dimension, count in dimension_counts.items():
    print(f"{dimension}: {count}")


