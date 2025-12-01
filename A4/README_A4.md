# Tutorial: IFC Column analysis script
[![Watch the video](https://img.youtube.com/vi/lFscrQuUNMY/maxresdefault.jpg)](https://www.youtube.com/watch?v=lFscrQuUNMY)
This tutorial explains, step by step, how the provided Python script (A3) works.
It dives deeper into how you can extract material strength properties, and what to do if it does not exist in the model
This script helps you analyze concrete column elements from an IFC model using the `ifcopenshell` library.

---

## Overview

The script reads an IFC file (a Building Information Model), finds all columns on a specific storey (level), and calculates their axial capacity (Nrd) based on:
- The axial load: `Ned`
- The material strength of concrete: `fc`
- The cross-section area of the column: `A`

Then it reports whether each column passes the capacity check:  
if Ned < Nrd,  the column is safe.
 
---

## Requirements for the code to run

- Python
- ifcopenshell

---

## 1. User Settings

First, you have to define the user settings. The values are adjusted to the structural situation and eurocode that applies to the user. Specify which story you want to check e.g. *Level 1* or others, and specify the design load that you want to apply to the columns. Insert the path to the model you want to check.

```python
Ned = 882.78        # kN  (design axial load)
gamma_mo = 1.45     # material safety factor from eurocode
fc_default = 35.0   # N/mm² (default concrete strength)
MODEL_PATH = "25-16-D-STR.ifc" # checked IFC model
STOREY_MATCH = "Level -1" # checked storey
```

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
If geometric calulations does not work, the script will still run, but it uses limited fallback methods.

--- 

## 3. Unit conversion

IFC models may use different units e.g mm or+ m.  
length_unit_scale_to_m ensures all lengths are converted to meters:

```python
def length_unit_scale_to_m(model):
```

The function looks through the model’s unit assignments using `IfcUnitAssignment` 
and returns the correct scale in meters.

---

## 4. Finding Storey Information

To get the storey of each element, two functions are used:

```python
def climb_to_storey(spatial):
    """Climb up the spatial tree to the nearest IfcBuildingStorey."""

def element_storey(element):
    """Get the IfcBuildingStorey an element is contained in."""
```

The first functions navigate IFC’s structure: Project --> Site --> Building --> Storey --> Element and climbs upwards until it finds the correct story.

The second function finds which spatial element and calls for the first function.

The function `is_storey_match(storey)` then checks whether the storey name matches "Level x" that you defined in the  user settings. And allows you to analyze any storey by changing `STORY_MATCH`.

---

## 5. Extract Material Data
To calculate capacity, you must determine the material strengths for each column.
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

Note: IFC supports storing material strength as properties in Pset_MaterialConcrete or IfcMaterialMechanicalProperties. However, in practice this information is often missing, and the material strength must be read from the material name instead or from a default value the user defines. The fc_default value is therefore defined so that if no strength is found in the model, the script will use the default value you specify.


Therefore, the script uses a three-level strategy to find fc:

```python
    # 1) Try structured IFC properties first
    fc = try_extract_fc_structured(md)
    if fc is not None:
        return names, mcls, fc, "pset"

    # 2) Fallback to name (Concrete)
    fc = extract_fc_from_name(names, mcls)
    if fc is not None:
        return names, mcls, fc, "name"

    # 3) Fallback to default value fc_default
    return names, mcls, fc_default, "default"
```
Here, the code tries to find fc from `IfcProperties` or name. If both methods fail, it uses the default value. This guarantees that the script always has an compressive strength to calculate the axial capacity with.

---


## 6. Geometry and cross-section calculations
To calculate the axial capacity, the script must determine each columns width, height and cross-section area.

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
    print("Maybe insufficient")
```

---

## 8. Output and Reporting

The script prints a rapport with the following information for each column:
- Column name or globalID  
- Building storey name  
- Material name and compressive strength  
- Cross-section area  
- Nrd for each column in storey
- OK/Maybe insufficient message

Output example from report:
```
- GlobalId: 2KJNIOw1nAJheMLIWB4kE8
  Storey: Level -1
  Dimensions: 700 × 200 mm | A = 140000 mm²
  Material: Concrete (Concrete) | fc used = 35.0 N/mm² (source: default)
  Nrd = 3379.3 kN  vs  Ned = 882.8 kN  → OK (utilization = 26.12%)

TOTAL: 83 checked columns | OK: 83 | Maybe insufficient: 0
Worst utilization: 57.14%  (GlobalId 1gBbes5lD1DQsWtn$7fdd6, Nrd=1544.8 kN, dim≈ 320×200 mm)
End of report.

```

---

## 9. How to Run

Save your script and run

Make sure the `.ifc` file is in the same folder as your python file or update `MODEL_PATH`.


---

## Summary
Title: IFC Column axial capacity analysis
Category: Structures
Description: The scripts extracts Columns geometry (to find cross-section area), Info about the material, Concrete strength and then calculates the Axial capacity for all columns in the user defined level. It also handles missing material property sets.

---
