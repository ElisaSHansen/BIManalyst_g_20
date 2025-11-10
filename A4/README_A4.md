# -*- coding: utf-8 -*-
"""
Created on Mon Nov 10 13:39:37 2025

@author: Ida Sofie, Elisa Steen-Hansen
"""

Først må user settings defineres. Dette tilpasses til den modellen og tilfellet du skal sjekke med tilhørende eurokoder. Skriv inn hvilke etasje du vil sjekke, f.eks. Level 1, Level 2 eller Level -1. Skriv inn lasten som du ønsker å påføre søylene. 

```python
Ned = 882.78         # kN  (design axial load)
gamma_mo = 1.45      # material safety factor (used in Nrd formula)
fc_default = 35.0    # N/mm^2 (used if concrete strength isn't found)
MODEL_PATH = "25-16-D-STR.ifc" # checked model
STOREY_MATCH = "Level -1"  # match storey Name/LongName containing this text (e.g., "Level -1")
```

Merk her at: IFC har støtte for å lagre materialfasthet som egenskaper i Pset_MaterialConcrete eller IfcMaterialMechanicalProperties, men i praksis må man ofte lese verdien fra materialnavnet fordi mange eksportører ikke fyller ut disse feltene. Setter derfor en Fc_default slik at dersom det ikke finnes i modellen så bruker den fastheten du har satt inn som default.


Disse biblotekene må importeres for at koden skal kunne kjøres

```python
import math
from contextlib import redirect_stdout
import ifcopenshell

# Geometry as fallback (bbox) if profile data is missing
try:
    import ifcopenshell.geom as geom
    GEOM_OK = True
except Exception:
    GEOM_OK = False
```

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

MaterialDef
   ↓  (find all psets)
_iter_material_property_sets
   ↓
try_extract_fc_structured
     ├─ Prefer Pset_MaterialConcrete
     └─ Else any pset/mech/extended
   ↓
if None → extract_fc_from_name
   ↓
if None → fc_default

