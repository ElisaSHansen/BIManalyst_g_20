# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 14:27:00 2025

@author: Ida Sofie
"""

# IFC Column Analysis Script Tutorial

This tutorial explains, step by step, how the provided **Python script** works.  
It helps you analyze **concrete column elements** from an **IFC model** using the `ifcopenshell` library.

---

## 📘 Overview

The script reads an IFC file (a Building Information Model), finds all **columns** on a specific **storey (level)**, and calculates their **axial capacity (Nrd)** based on:
- The **axial load** `Ned`
- The **material strength** of concrete (`fc`)
- The **cross-sectional area** of the column (`A`)

Then it reports whether each column satisfies the capacity check:  
👉 `Ned < Nrd` → the column is safe.

---

## ⚙️ Requirements

You need:
- **Python 3.9+**
- The following Python libraries:
  ```bash
  pip install ifcopenshell math
  ```

> 🧩 Note: `ifcopenshell` lets you read and manipulate IFC building models programmatically.

---

## 🧱 1. User Settings

At the top of the script, you can define your **project parameters**:

```python
Ned = 882.78        # kN  (design axial load)
gamma_mo = 1.45     # material safety factor
fc_default = 35.0   # N/mm² (default concrete strength)
MODEL_PATH = "25-16-D-STR.ifc"
STOREY_MATCH = "Level -1"
```

- `Ned` = applied design load  
- `gamma_mo` = safety factor (from Eurocode)  
- `fc_default` = fallback concrete strength if none is found in IFC  
- `MODEL_PATH` = the IFC model file  
- `STOREY_MATCH` = which level to filter for (e.g., *Level -1*)

---

## 🧩 2. Importing Libraries

```python
import math
import ifcopenshell
from contextlib import redirect_stdout
```

If available, it also loads the geometry engine:

```python
try:
    import ifcopenshell.geom as geom
    GEOM_OK = True
except Exception:
    GEOM_OK = False
```

> This allows geometric calculations such as bounding boxes if profile data is missing.

---

## 📏 3. Unit Conversion

IFC models can use different units (mm, m, etc.).  
The function below ensures all lengths are converted to **meters**:

```python
def length_unit_scale_to_m(model):
    """Return scale from model length unit to meters."""
    ...
```

The function looks through the model’s unit assignments (`IfcUnitAssignment`)  
and returns the correct scale (e.g., `0.001` for millimeters).

---

## 🏗️ 4. Finding Storey Information

To get the **storey** (floor level) of each element, two helper functions are used:

```python
def climb_to_storey(spatial):
    """Climb up the spatial tree to the nearest IfcBuildingStorey."""

def element_storey(element):
    """Get the IfcBuildingStorey an element is contained in."""
```

These functions navigate IFC’s hierarchical structure:
```
Project → Site → Building → Storey → Element
```

The function `is_storey_match_minus1(storey)` then checks whether the storey name matches `"Level -1"`.

---

## 🧱 5. Extracting Material Data

The following helpers get the **concrete material** assigned to each column:

```python
def _relating_material(el):
    """Return the RelatingMaterial definition on instance or type."""
```

It searches both:
- The **instance** itself (`HasAssociations`)
- The **type definition** (`IsTypedBy`)

Then it extracts names like *C30/37 Concrete* using:

```python
def _material_names_from_def(matdef):
    """Extract material names from IFC4 material definitions."""
```

If the model has no material info, the script falls back to `fc_default`.

---

## 📐 6. Geometry & Area Calculation

If the profile data is missing, the script uses bounding boxes (`bbox`) as fallback:

```python
A_SANITY_EDGE_M = 5.0  # sanity check for unrealistic geometry
```

It calculates **cross-sectional area** `A` in mm², based on profile or geometry data.

---

## 🧮 7. Structural Calculation (Capacity Check)

The script calculates the **design resistance**:

```python
Nrd = (A * fc / gamma_mo) / 1000  # converts N to kN
```

Then it compares:

```python
if Ned < Nrd:
    print("✅ OK – column passes check")
else:
    print("⚠️ FAIL – column overloaded")
```

---

## 🧾 8. Output and Reporting

The script prints for each column:
- Column name or ID  
- Storey name  
- Material name and strength  
- Cross-section area  
- Nrd result  
- Pass/fail message

Example output:
```
Column ID: #12345
Storey: Level -1
Material: C35/45
Area: 32000 mm²
Nrd: 773.5 kN
✅ OK (882.78 < 773.5)
```

---

## 🧠 9. Tips for Customization

- Change `STOREY_MATCH` to target another floor.
- Replace `fc_default` for different concrete classes.
- Add more material handling for **steel** or **composite** members.
- Use `geom.create_shape()` from `ifcopenshell.geom` to visualize geometry.

---

## 🚀 10. How to Run

Save your script (for example as `check_columns.py`) and run:

```bash
python check_columns.py
```

Make sure the `.ifc` file is in the same folder or update `MODEL_PATH`.

---

## 📚 Summary

| Step | Purpose |
|------|----------|
| 1 | Define input parameters |
| 2 | Load the IFC model |
| 3 | Convert units |
| 4 | Find storeys and elements |
| 5 | Get material data |
| 6 | Compute area |
| 7 | Calculate Nrd |
| 8 | Report results |

---

### ✅ Congratulations!
You now understand how this IFC structural capacity script works — and how to adapt it to your own building models.