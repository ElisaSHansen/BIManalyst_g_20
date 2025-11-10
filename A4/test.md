# Tutorial: IFC Column Analysis Script

This tutorial explains, step by step, how the provided Python script (A3) works.
The tutorial dives deeper into how you can extract material strength properties.
It helps you analyze concrete column elements from an IFC model using the `ifcopenshell` library.

---

## Overview

The script reads an IFC file (a Building Information Model), finds all columns on a specific storey (level), and calculates their axial capacity (Nrd) based on:
- The axial load: `Ned`
- The material strength of concrete: `fc`
- The cross-sectional area of the column: `A`

Then it reports whether each column passes the capacity check:  
if `Ned < Nrd`,  the column is safe.

---

## Requirements for the code to run

- Python
- ifcopenshell

---

## 1. User Settings

Først må user settings defineres. Dette tilpasses til den modellen og tilfellet du skal sjekke med tilhørende eurokoder. Skriv inn hvilke etasje du vil sjekke, f.eks. Level 1, Level 2 eller Level -1. Skriv inn lasten som du ønsker å påføre søylene. 

```python
Ned = 882.78        # kN  (design axial load)
gamma_mo = 1.45     # material safety factor from eurocode
fc_default = 35.0   # N/mm² (default concrete strength)
MODEL_PATH = "25-16-D-STR.ifc" # checked IFC model
STOREY_MATCH = "Level -1" # checked storey
```

Merk her at: IFC har støtte for å lagre materialfasthet som egenskaper i Pset_MaterialConcrete eller IfcMaterialMechanicalProperties, men i praksis må man ofte lese verdien fra materialnavnet fordi mange eksportører ikke fyller ut disse feltene. Setter derfor en Fc_default slik at dersom det ikke finnes i modellen så bruker den fastheten du har satt inn som default.

---

## 2. Import Libraries

```python
import math
import ifcopenshell
from contextlib import redirect_stdout
```

If available, it loads the geometry engine:

```python
try:
    import ifcopenshell.geom as geom
    GEOM_OK = True
except Exception:
    GEOM_OK = False
```
This allows geometric calculations such as bounding boxes if profile data is missing.

--- 

## 3. Unit conversion

IFC models can use different units (mm, m).  
length_unit_scale_to_m ensures all lengths are converted to meters:

```python
def length_unit_scale_to_m(model):
```

The function looks through the model’s unit assignments using `IfcUnitAssignment` 
and returns the correct scale in meters.

---

## 4. Finding Storey Information

To get the storey of each element, two helper functions are used:

```python
def climb_to_storey(spatial):
    """Climb up the spatial tree to the nearest IfcBuildingStorey."""

def element_storey(element):
    """Get the IfcBuildingStorey an element is contained in."""
```

The functions navigate IFC’s structure: Project --> Site --> Building --> Storey --> Element

The function `is_storey_match(storey)` then checks whether the storey name matches `"Level x"` that you defined in the  user settings.

---

## 5. Extract Material Data
The following helpers get the concrete material assigned to each column:

```python
def _relating_material(el):
    """Return the RelatingMaterial definition on instance or type."""
```

It searches:
- The instance itself (`HasAssociations`)
- The type definition (`IsTypedBy`)

Then it extracts names like C30/37 Concrete using:

```python
def _material_names_from_def(matdef):
    """Extract material names from IFC4 material definitions."""
```

If the model has no material info, the script falls back to `fc_default` that you defined in the user settings.

Vi oppdaget at materialfasthet ofte mangler i materialegenskapene, så vi bygget en strategi i tre nivåer som søker etter materialfasthet.
Her prøver koden å finne fc ut i ifra IFC properties, navn eller hvis begge metodene ikke fungerer, så bruker den default verdien som en skrev i user settings øverst i koden.

```python
    # 1) Try structured IFC properties first
    fc = try_extract_fc_structured(md)
    if fc is not None:
        return names, mcls, fc, "pset"

    # 2) Fallback to parsing name (Concrete)
    fc = extract_fc_from_name(names, mcls)
    if fc is not None:
        return names, mcls, fc, "name"

    # 3) Final fallback to default
    return names, mcls, fc_default, "default"
```

---


## 6. Geometry and cross-section calculations
Find the width and height for each section, for example for rectangles:

```python
def width_height_from_profile(profile, to_m):
    """Return (w_m, h_m) from common IfcProfileDef types, scaled to meters."""
    if not profile: return None
    # Rectangle / rounded rectangle
    if profile.is_a("IfcRectangleProfileDef") or profile.is_a("IfcRoundedRectangleProfileDef"):
        x, y = _f(profile.XDim), _f(profile.YDim)
        if x and y: return x*to_m, y*to_m
```

Find the area for each profile, for example for rectangles:

```python
def area_from_profile(profile, to_m):
    """Return (area_m2, precise_bool) computed from profile parameters."""
    if not profile: return None, False

    # Rectangle
    if profile.is_a("IfcRectangleProfileDef"):
        x, y = _f(profile.XDim), _f(profile.YDim)
        if x and y: return (x*y)*(to_m**2), True
```

If the profile data for columns is missing, the script uses bounding boxes as fallback to calculate the area:

```python
def area_from_xy_bbox(w_m, h_m):
    """Approximate area from bbox (m^2)."""
    if w_m is None or h_m is None: return None
    return w_m * h_m
```

In case the geometry date for columns is wrong or has odd scales (over 5 meters), geometric shape dimensions is used instead:

```python
A_SANITY_EDGE_M = 5.0  # sanity check for unrealistic geometry
```

It calculates cross-sectional area in mm², based on profile or geometry data.

---

## 7. Axial capacity check

The script calculates the axial capacity by the formulas in the eurocode:

```python
Nrd = (A * fc / gamma_mo) / 1000  # converts N to kN
```

Then it checks if the capacity is bigger than the design load:

```python
if Ned < Nrd:
    print("OK")
else:
    print("NOT OK")
```

---

## 8. Output and Reporting

The script prints for each column:
- Column name or globalID  
- Building storey name  
- Material name and compressive strength  
- Cross-section area  
- Nrd for each column in storey
- OK/not OK message

Output example:
```
- GlobalId: 2KJNIOw1nAJheMLIWB4kE8
  Storey: Level -1
  Dimensions: 700 × 200 mm | A = 140000 mm²
  Material: Concrete (Concrete) | fc used = 35.0 N/mm² (source: default)
  Nrd = 3379.3 kN  vs  Ned = 882.8 kN  → OK (utilization = 26.12%)
```

---

## 9. How to Run

Save your script and run

Make sure the `.ifc` file is in the same folder as your python file or update `MODEL_PATH`.

---

## Summary


---
