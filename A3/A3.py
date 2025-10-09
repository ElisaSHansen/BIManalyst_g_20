import ifcopenshell as ifc
from collections import defaultdict, Counter

# Import geometry module (requires IfcOpenShell with OCC support)
try:
    import ifcopenshell.geom as geom
except Exception as e:
    print("ifcopenshell.geom is not available (OCC geometry kernel required).", e)
    raise SystemExit(1)

# Open the IFC model
model = ifc.open("25-16-D-STR.ifc")
settings = geom.settings()

def get_bbox_height_m(col):
    """Calculate column height from its bounding box."""
    try:
        shape = geom.create_shape(settings, col)
        verts = shape.geometry.verts  # flat list [x, y, z, x, y, z, ...] in meters
        zs = verts[2::3]
        return (max(zs) - min(zs)) if zs else None
    except Exception:
        return None

def get_material(name):
    """Detect material from the name string."""
    n = (name or "").lower()
    if "concrete" in n:
        return "Concrete"
    elif "wood" in n:
        return "Wood"
    return None

# Collect height data per material and dimension
data = defaultdict(lambda: defaultdict(list))

for col in model.by_type("IfcColumn"):
    name = getattr(col, "Name", "") or ""
    material = get_material(name)
    if not material:
        continue  # skip other materials
    dim = name.split(":")[-1].strip() if ":" in name else "UNKNOWN"
    height = get_bbox_height_m(col)
    if height is not None:
        data[material][dim].append(round(height, 3))

# --- Print results ---
print("Bounding-box based column height summary (meters):\n")

for material, dims in data.items():
    print(f"{material} columns:")
    for dim, heights in sorted(dims.items()):
        counts = Counter(heights) 
        summary = ", ".join(f"{h} m (x{n})" for h, n in sorted(counts.items()))
        print(f"  {dim}: {len(heights)} columns, heights = [{summary}]")
    print()


# --- geometry (bounding box) ---
try:
    import ifcopenshell.geom as geom
except Exception as e:
    print("ifcopenshell.geom is not available (OCC geometry kernel required).", e)
    raise SystemExit(1)

model = ifc.open("25-16-D-STR.ifc")

# Make sure we use world coordinates (so z=0 is global)
settings = geom.settings()
try:
    settings.set(settings.USE_WORLD_COORDS, True)
except Exception:
    # Some versions already use world coordinates by default
    pass

TOL = 0.002  # tolerance in meters (~2 mm)

def get_bbox_minmax_z(col):
    """Return (min_z, max_z) of the column geometry in meters."""
    try:
        shape = geom.create_shape(settings, col)
        verts = shape.geometry.verts  # flat list [x, y, z, x, y, z, ...]
        zs = verts[2::3]
        if not zs:
            return None
        return min(zs), max(zs)
    except Exception:
        return None

def get_bbox_height_m(col):
    mm = get_bbox_minmax_z(col)
    if not mm:
        return None
    zmin, zmax = mm
    return zmax - zmin

def material_from_name(name):
    """Detect material type based on the column name."""
    n = (name or "").lower()
    if "concrete" in n:
        return "Concrete"
    if "wood" in n:
        return "Wood"
    return None

# --- collect only columns whose base is at Z=0 (within tolerance) ---
data = defaultdict(lambda: defaultdict(list))  # material -> dimension -> [heights]

for col in model.by_type("IfcColumn"):
    name = getattr(col, "Name", "") or ""
    mat = material_from_name(name)
    if not mat:
        continue  # only include Concrete or Wood

    # extract dimensions from name
    dim = name.split(":")[-1].strip() if ":" in name else "UNKNOWN"

    mm = get_bbox_minmax_z(col)
    if not mm:
        continue
    zmin, zmax = mm

    # keep only columns whose base is at z=0 (± tolerance)
    if -TOL <= zmin <= TOL:
        h = zmax - zmin
        data[mat][dim].append(round(h, 3))

# --- print summary ---
print("Columns with base at Z=0 (assumed first storey), grouped by material & dimension:\n")
for mat, dims in data.items():
    print(f"{mat} columns:")
    for dim, heights in sorted(dims.items()):
        counts = Counter(heights)
        summary = ", ".join(f"{h} m (x{n})" for h, n in sorted(counts.items()))
        print(f"  {dim}: {len(heights)} columns, heights = [{summary}]")
    print()

import re

fc=355
gamma_m0 = 1.5

def rect_area_from_dim(dim_text: str) -> float:
    """Return area in m² from text like '200x200 mm' or '0.2x0.2 m'."""
    m = re.search(r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?', dim_text.lower())
    if not m:
        return None
    b, h, unit = m.groups()
    b = float(b); h = float(h)
    unit = unit or "mm"
    if unit == "mm": b *= 1e-3; h *= 1e-3
    elif unit == "cm": b *= 1e-2; h *= 1e-2
    return b * h  # m²

print("Axial capacities for all dimensions (Z=0 columns):\n")
i = 1
for mat, dims in data.items():
    print(f"{mat} columns:")
    for dim in sorted(dims.keys()):
        A = rect_area_from_dim(dim)
        if A:
            # Convert area to mm² for capacity calc
            A_mm2 = A * 1e6
            Nrd = (fc * A_mm2 / gamma_m0) / 1000  # kN
            print(f"  A{i}: {dim} -> A = {A_mm2:.0f} mm², Nrd = {round(Nrd,1)} kN")
            i += 1
    print()