# ======= USER SETTINGS (edit as needed) =======================================
Ned = 882.78           # kN (design axial load)
gamma_mo = 1.45        # material safety factor (used in Nrd formula)
fc_default = 35.0      # N/mm^2 (used if concrete strength isn't found)
MODEL_PATH = "25-16-D-STR.ifc"

# --- Choose which storey(s) to check ---
# Modes: "name_contains", "name_equals", "elevation_le", "elevation_ge", "elevation_between"
STOREY_FILTER_MODE  = "name_contains"
STOREY_FILTER_VALUE = "-1"     # for name_* modes, a string
# For elevation modes, use meters (float). Example:
# STOREY_FILTER_MODE  = "elevation_between"
# STOREY_FILTER_VALUE = ( -3.0, 0.0 )  # meters
# ------------------------------------------------------------------------------
# ==============================================================================

import math
from contextlib import redirect_stdout
import ifcopenshell

# Geometry as fallback (bbox) if profile data is missing
try:
    import ifcopenshell.geom as geom
    GEOM_OK = True
except Exception:
    GEOM_OK = False

A_SANITY_EDGE_M = 5.0   # if plan dims > 5 m → use bbox as sanity fallback
ELEV_EPS_M = 0.01       # 10 mm tolerance for elevation comparisons

# ---------- Units ----------
def length_unit_scale_to_m(model):
    """Return scale from model length unit to meters."""
    scale = 1.0
    uas = model.by_type("IfcUnitAssignment")
    if not uas:
        return scale
    for u in uas[0].Units or []:
        if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT" and u.Name == "METRE":
            pref = getattr(u, "Prefix", None)
            return {None:1.0,"MILLI":1e-3,"CENTI":1e-2,"DECI":1e-1,"KILO":1e3}.get(pref,1.0)
        if u.is_a("IfcConversionBasedUnit") and u.UnitType == "LENGTHUNIT":
            mu = u.ConversionFactor
            if mu and hasattr(mu, "ValueComponent") and hasattr(mu, "UnitComponent"):
                vc = getattr(mu.ValueComponent, "wrappedValue", mu.ValueComponent)
                si = mu.UnitComponent
                if si and si.is_a("IfcSIUnit") and si.Name == "METRE":
                    pref = getattr(si, "Prefix", None)
                    si_to_m = {None:1.0,"MILLI":1e-3,"CENTI":1e-2,"DECI":1e-1,"KILO":1e3}.get(pref,1.0)
                    try:
                        return float(vc) * float(si_to_m)
                    except Exception:
                        pass
    return scale

# ---------- Spatial ----------
def climb_to_storey(spatial):
    """Climb up the spatial tree to the nearest IfcBuildingStorey."""
    cur = spatial
    visited = set()
    while cur and cur.id() not in visited:
        visited.add(cur.id())
        if cur.is_a("IfcBuildingStorey"):
            return cur
        decomp = getattr(cur, "Decomposes", None)
        if decomp:
            rel_up = list(decomp)[0]
            cur = rel_up.RelatingObject
        else:
            return None
    return None

def element_storey(element):
    """Get the IfcBuildingStorey an element is contained in."""
    for rel in (element.ContainedInStructure or []):
        if rel.is_a("IfcRelContainedInSpatialStructure"):
            st = rel.RelatingStructure
            if not st:
                continue
            if st.is_a("IfcBuildingStorey"):
                return st
            up = climb_to_storey(st)
            if up:
                return up
    return None

# ---------- Storey filtering ----------
def storey_matches(storey, to_m):
    """Return True if the storey satisfies the selected filter."""
    mode = (STOREY_FILTER_MODE or "").lower()

    nm  = (getattr(storey, "Name", "") or "").strip()
    lnm = (getattr(storey, "LongName", "") or "").strip()
    joined = f"{nm} {lnm}".lower()

    elev_raw = getattr(storey, "Elevation", None)
    elev_m = None
    if elev_raw is not None:
        try:
            elev_m = float(elev_raw) * to_m
        except Exception:
            elev_m = None

    if mode == "name_contains":
        needle = str(STOREY_FILTER_VALUE).lower()
        return needle in joined

    if mode == "name_equals":
        needle = str(STOREY_FILTER_VALUE).lower()
        return nm.lower() == needle or lnm.lower() == needle

    if mode == "elevation_le":
        if elev_m is None: return False
        limit = float(STOREY_FILTER_VALUE)
        return elev_m <= limit + ELEV_EPS_M

    if mode == "elevation_ge":
        if elev_m is None: return False
        limit = float(STOREY_FILTER_VALUE)
        return elev_m >= limit - ELEV_EPS_M

    if mode == "elevation_between":
        if elev_m is None: return False
        low, high = STOREY_FILTER_VALUE
        low = float(low); high = float(high)
        return (elev_m >= low - ELEV_EPS_M) and (elev_m <= high + ELEV_EPS_M)

    # Default: no match
    return False

# ---------- Material helpers ----------
def _relating_material(el):
    """Return the RelatingMaterial definition on instance or type."""
    for rel in (el.HasAssociations or []):
        if rel.is_a("IfcRelAssociatesMaterial"):
            return rel.RelatingMaterial
    for t_rel in (el.IsTypedBy or []):
        t = t_rel.RelatingType
        for rel in (t.HasAssociations or []):
            if rel.is_a("IfcRelAssociatesMaterial"):
                return rel.RelatingMaterial
    return None

def _material_names_from_def(matdef):
    """Extract material names from IFC4 material definitions."""
    if not matdef: return []
    names = []
    if matdef.is_a("IfcMaterial"):
        if matdef.Name: names.append(str(matdef.Name))
    elif matdef.is_a("IfcMaterialProfileSetUsage"):
        mps = matdef.ForProfileSet
        if mps:
            for mp in (mps.MaterialProfiles or []):
                m = getattr(mp, "Material", None)
                if m and m.Name: names.append(str(m.Name))
    elif matdef.is_a("IfcMaterialProfileSet"):
        for mp in (matdef.MaterialProfiles or []):
            m = getattr(mp, "Material", None)
            if m and m.Name: names.append(str(m.Name))
    elif matdef.is_a("IfcMaterialLayerSetUsage"):
        mls = matdef.ForLayerSet
        if mls:
            for layer in (mls.MaterialLayers or []):
                m = getattr(layer, "Material", None)
                if m and m.Name: names.append(str(m.Name))
    elif matdef.is_a("IfcMaterialLayerSet"):
        for layer in (matdef.MaterialLayers or []):
            m = getattr(layer, "Material", None)
            if m and m.Name: names.append(str(m.Name))
    elif matdef.is_a("IfcMaterialConstituentSet"):
        for c in (matdef.MaterialConstituents or []):
            m = getattr(c, "Material", None)
            if m and m.Name: names.append(str(m.Name))
    # unique in order
    out, seen = [], set()
    for n in names:
        if n not in seen:
            seen.add(n); out.append(n)
    return out

def _normalize_material_class(names):
    """Roughly classify material into Concrete/Steel/Wood/... based on names."""
    text = " ".join(n.lower() for n in (names or []))
    rules = [
        ("Concrete", ["betong","concrete","c20","c25","c30","c35","c40","c45","c50"]),
        ("Steel",    ["stål","steel","s235","s275","s355","s420","s460"]),
        ("Wood",     ["tre","wood","timber","glulam","lvl","kerto","c24"]),
        ("Masonry",  ["mur","masonry","brick","block","tegl"]),
        ("Aluminium",["aluminium","aluminum","alu"]),
        ("Glass",    ["glass"]),
        ("Gypsum",   ["gips","gypsum"]),
        ("Insulation",["isolasjon","insulation","xps","eps","rockwool","mineral wool"]),
        ("Plastic",  ["plast","hdpe","pp","pvc"]),
        ("Asphalt",  ["asfalt","asphalt"]),
    ]
    for cls, keys in rules:
        if any(k in text for k in keys):
            return cls
    return "Unknown"

# ---------- fc from structured IFC properties (then fallback to name/default) ----------
def _unwrap_val(v):
    if v is None:
        return None
    w = getattr(v, "wrappedValue", None)
    if w is not None:
        return float(w)
    try:
        return float(v)
    except Exception:
        return None

def _try_fc_from_property_set_container(pset_container):
    hp = getattr(pset_container, "HasProperties", None)
    if hp:
        for p in hp:
            pname = (getattr(p, "Name", "") or "").strip().lower()
            if hasattr(p, "NominalValue") and p.NominalValue:
                if pname in ("compressivestrength", "fck", "fc", "fck_cyl", "fck_cube"):
                    return _unwrap_val(p.NominalValue)
            if hasattr(p, "ListValues") and p.ListValues:
                if pname in ("compressivestrength", "fck", "fc", "fck_cyl", "fck_cube"):
                    return _unwrap_val(p.ListValues[0])
    if pset_container.is_a("IfcMaterialMechanicalProperties"):
        cs = getattr(pset_container, "CompressiveStrength", None)
        if cs:
            return _unwrap_val(cs)
    ext_props = getattr(pset_container, "Properties", None)
    if ext_props:
        for ep in ext_props:
            pname = (getattr(ep, "Name", "") or "").strip().lower()
            val = getattr(ep, "NominalValue", None)
            if pname in ("compressivestrength", "fck", "fc", "fck_cyl", "fck_cube"):
                return _unwrap_val(val)
    return None

def _iter_material_property_sets(matdef):
    if not matdef:
        return
    for attr_name in ("HasProperties", "HasMaterialProperties", "Properties", "MaterialProperties"):
        objs = getattr(matdef, attr_name, None)
        if objs:
            for x in objs:
                yield x
    for attr_name in ("ForProfileSet", "ForLayerSet"):
        sub = getattr(matdef, attr_name, None)
        if sub:
            for nested in ("HasProperties", "HasMaterialProperties", "Properties", "MaterialProperties"):
                objs = getattr(sub, nested, None)
                if objs:
                    for x in objs:
                        yield x
            for coll_name in ("MaterialProfiles", "MaterialLayers", "MaterialConstituents"):
                coll = getattr(sub, coll_name, None)
                if coll:
                    for item in coll:
                        m = getattr(item, "Material", None)
                        if m:
                            for a in ("HasProperties", "HasMaterialProperties", "Properties", "MaterialProperties"):
                                objs = getattr(m, a, None)
                                if objs:
                                    for x in objs:
                                        yield x

def try_extract_fc_structured(matdef):
    for ps in _iter_material_property_sets(matdef):
        name = (getattr(ps, "Name", "") or "").lower()
        if "pset_materialconcrete" in name or "concrete" in name:
            fc = _try_fc_from_property_set_container(ps)
            if fc is not None:
                return fc
    for ps in _iter_material_property_sets(matdef):
        fc = _try_fc_from_property_set_container(ps)
        if fc is not None:
            return fc
    return None

import re
def extract_fc_from_name(names, mcls):
    if mcls != "Concrete" or not names:
        return None
    text = " ".join(str(n) for n in names).upper()
    m = re.search(r"\bC\s*([0-9]{2})(?:\s*/\s*[0-9]{2})?\b", text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None

def get_material_info_with_fc(el):
    md = _relating_material(el)
    names = _material_names_from_def(md)
    mcls = _normalize_material_class(names)

    fc = try_extract_fc_structured(md)
    if fc is not None:
        return names, mcls, fc, "pset"

    fc = extract_fc_from_name(names, mcls)
    if fc is not None:
        return names, mcls, fc, "name"

    return names, mcls, fc_default, "default"

# ---------- Profile / Dimensions / Area ----------
def get_material_profiledef(el):
    # Instance
    for rel in (el.HasAssociations or []):
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat = rel.RelatingMaterial
            if mat and mat.is_a("IfcMaterialProfileSetUsage"):
                mps = mat.ForProfileSet
                if mps and mps.MaterialProfiles:
                    for mp in mps.MaterialProfiles:
                        if mp.Profile: return mp.Profile
            if mat and mat.is_a("IfcMaterialProfileSet"):
                for mp in (mat.MaterialProfiles or []):
                    if mp.Profile: return mp.Profile
    # Type
    for t_rel in (el.IsTypedBy or []):
        t = t_rel.RelatingType
        for rel in (t.HasAssociations or []):
            if rel.is_a("IfcRelAssociatesMaterial"):
                mat = rel.RelatingMaterial
                if mat and mat.is_a("IfcMaterialProfileSetUsage"):
                    mps = mat.ForProfileSet
                    if mps and mps.MaterialProfiles:
                        for mp in mps.MaterialProfiles:
                            if mp.Profile: return mp.Profile
                if mat and mat.is_a("IfcMaterialProfileSet"):
                    for mp in (mat.MaterialProfiles or []):
                        if mp.Profile: return mp.Profile
    return None

def get_extruded_profiledef(el):
    def scan_rep(rep):
        if not rep: return None
        for cr in (rep.Representations or []):
            for it in (cr.Items or []):
                if it.is_a("IfcExtrudedAreaSolid") or it.is_a("IfcFixedReferenceSweptAreaSolid"):
                    sa = getattr(it, "SweptArea", None)
                    if sa and sa.is_a("IfcProfileDef"):
                        return sa
        return None
    prof = scan_rep(el.Representation)
    if prof: return prof
    for t_rel in (el.IsTypedBy or []):
        prof = scan_rep(getattr(t_rel.RelatingType, "Representation", None))
        if prof: return prof
    return None

def _f(x):
    try: return float(x)
    except: return None

def width_height_from_profile(profile, to_m):
    if not profile: return None
    if profile.is_a("IfcRectangleProfileDef") or profile.is_a("IfcRoundedRectangleProfileDef"):
        x, y = _f(profile.XDim), _f(profile.YDim)
        if x and y: return x*to_m, y*to_m
    if profile.is_a("IfcCircleProfileDef"):
        r = _f(profile.Radius)
        if r: d = 2*r*to_m; return d, d
    if profile.is_a("IfcIShapeProfileDef"):
        b, h = _f(profile.OverallWidth), _f(profile.OverallDepth)
        if b and h: return b*to_m, h*to_m
    if profile.is_a("IfcTShapeProfileDef"):
        b, h = _f(profile.FlangeWidth), _f(profile.Depth)
        if b and h: return b*to_m, h*to_m
    if profile.is_a("IfcUShapeProfileDef"):
        b, h = _f(profile.FlangeWidth), _f(profile.Depth)
        if b and h: return b*to_m, h*to_m
    if profile.is_a("IfcZShapeProfileDef"):
        b, h = _f(profile.FlangeWidth), _f(profile.Depth)
        if b and h: return b*to_m, h*to_m
    if profile.is_a("IfcEllipseProfileDef"):
        a1, a2 = _f(profile.SemiAxis1), _f(profile.SemiAxis2)
        if a1 and a2: return 2*a1*to_m, 2*a2*to_m
    return None

def area_from_profile(profile, to_m):
    if not profile: return None, False
    if profile.is_a("IfcRectangleProfileDef"):
        x, y = _f(profile.XDim), _f(profile.YDim)
        if x and y: return (x*y)*(to_m**2), True
    if profile.is_a("IfcRoundedRectangleProfileDef"):
        x, y = _f(profile.XDim), _f(profile.YDim)
        r = _f(profile.RoundingRadius) or 0.0
        if x and y:
            A = (x*y) - (4.0 - math.pi)*(r**2)
            return A*(to_m**2), True
    if profile.is_a("IfcCircleProfileDef"):
        r = _f(profile.Radius)
        if r: return math.pi*(r**2)*(to_m**2), True
    if profile.is_a("IfcEllipseProfileDef"):
        a1, a2 = _f(profile.SemiAxis1), _f(profile.SemiAxis2)
        if a1 and a2: return math.pi*a1*a2*(to_m**2), True
    if profile.is_a("IfcIShapeProfileDef"):
        b = _f(profile.OverallWidth); h = _f(profile.OverallDepth)
        tf = _f(getattr(profile, "FlangeThickness", None))
        tw = _f(getattr(profile, "WebThickness", None))
        if b and h and tf and tw:
            A = 2*b*tf + (h-2*tf)*tw
            return A*(to_m**2), True
    if profile.is_a("IfcTShapeProfileDef"):
        b = _f(profile.FlangeWidth); h = _f(profile.Depth)
        tf = _f(getattr(profile, "FlangeThickness", None))
        tw = _f(getattr(profile, "WebThickness", None))
        if b and h and tf and tw:
            A = b*tf + (h-tf)*tw
            return A*(to_m**2), True
    if profile.is_a("IfcUShapeProfileDef"):
        b = _f(profile.FlangeWidth); h = _f(profile.Depth)
        tf = _f(getattr(profile, "FlangeThickness", None))
        tw = _f(getattr(profile, "WebThickness", None))
        if b and h and tf and tw:
            A = 2*b*tf + (h-2*tf)*tw
            return A*(to_m**2), True
    if profile.is_a("IfcZShapeProfileDef"):
        b = _f(profile.FlangeWidth); h = _f(profile.Depth)
        tf = _f(getattr(profile, "FlangeThickness", None))
        tw = _f(getattr(profile, "WebThickness", None))
        if b and h and tf and tw:
            A = 2*b*tf + (h-2*tf)*tw
            return A*(to_m**2), True
    return None, False

def width_height_from_xy_bbox(el):
    if not GEOM_OK: return None
    try:
        s = geom.create_shape(geom.settings(), el)
        v = s.geometry.verts  # meters
        xs, ys = v[0::3], v[1::3]
        if not xs or not ys: return None
        return (max(xs)-min(xs)), (max(ys)-min(ys))
    except Exception:
        return None

def area_from_xy_bbox(w_m, h_m):
    if w_m is None or h_m is None: return None
    return w_m * h_m

# ---------- Capacity ----------
def capacity_kN(fc_N_per_mm2, A_m2):
    """Nrd = fc * A / gamma_mo; fc in N/mm^2, A in m^2; returns Nrd in kN."""
    if fc_N_per_mm2 is None or A_m2 is None:
        return None
    A_mm2 = A_m2 * 1e6
    Nrd_N = fc_N_per_mm2 * A_mm2 / gamma_mo
    return Nrd_N / 1000.0  # kN

# ---------- Main: generate text report ----------
def main():
    model = ifcopenshell.open(MODEL_PATH)
    to_m = length_unit_scale_to_m(model)

    ok_cnt = 0
    nok_cnt = 0
    worst = {"util": -1.0, "gid": None, "Nrd": None, "w": None, "h": None}

    with open("Capacity.control.report.txt", "w", encoding="utf-8") as f, redirect_stdout(f):
        print("CAPACITY CONTROL REPORT (IfcColumn, storey filter)")
        print(f"Filter mode: {STOREY_FILTER_MODE} | Filter value: {STOREY_FILTER_VALUE}")
        print(f"Ned = {Ned:.2f} kN | gamma_mo = {gamma_mo:.2f} | fc_default = {fc_default:.1f} N/mm²")
        print(f"Model: {MODEL_PATH}")
        print("-"*80)

        for col in model.by_type("IfcColumn"):
            st = element_storey(col)
            if not st or not storey_matches(st, to_m):
                continue

            storey_name = getattr(st, "LongName", None) or getattr(st, "Name", "<unknown storey>")

            # Material + fc (structured-first strategy)
            names, mcls, fc, fc_src = get_material_info_with_fc(col)
            name_txt = ", ".join(names[:2]) if names else "<unknown>"

            # Dimensions / area
            prof = get_material_profiledef(col)
            wh_m = width_height_from_profile(prof, to_m) if prof else None
            if not wh_m:
                prof2 = get_extruded_profiledef(col)
                wh_m = width_height_from_profile(prof2, to_m) if prof2 else None

            used_bbox = False
            if not wh_m:
                wh_m = width_height_from_xy_bbox(col)
                used_bbox = wh_m is not None

            if wh_m and (wh_m[0] > A_SANITY_EDGE_M or wh_m[1] > A_SANITY_EDGE_M):
                bb = width_height_from_xy_bbox(col)
                if bb:
                    wh_m = bb
                    used_bbox = True

            A_m2, precise = area_from_profile(prof or get_extruded_profiledef(col), to_m)
            if (A_m2 is None) and wh_m:
                A_m2 = area_from_xy_bbox(*wh_m)
                precise = False
                used_bbox = True or used_bbox

            # Results
            if wh_m:
                w_mm, h_mm = wh_m[0]*1000.0, wh_m[1]*1000.0
                w_mm, h_mm = (w_mm, h_mm) if w_mm >= h_mm else (h_mm, w_mm)
                dim_txt = f"{w_mm:.0f} × {h_mm:.0f} mm"
            else:
                dim_txt = "<unknown>"

            approx = "~" if (A_m2 is not None and (not precise or used_bbox)) else ""
            A_txt = f"{approx}{A_m2*1e6:.0f} mm²" if A_m2 is not None else "<unknown>"

            Nrd = capacity_kN(fc, A_m2) if A_m2 is not None else None
            if Nrd is not None:
                status = "OK" if Nrd >= Ned else "NOT OK"
                util = (Ned / Nrd) * 100.0 if Nrd > 0 else float("inf")
                if util > worst["util"]:
                    worst.update({"util": util, "gid": col.GlobalId, "Nrd": Nrd,
                                  "w": w_mm if wh_m else None, "h": h_mm if wh_m else None})
                if status == "OK":
                    ok_cnt += 1
                else:
                    nok_cnt += 1
            else:
                status = "UNKNOWN"
                util = float("nan")

            # Per-column block
            print(f"- GlobalId: {col.GlobalId}")
            print(f"  Storey: {storey_name}")
            print(f"  Dimensions: {dim_txt} | A = {A_txt}")
            print(f"  Material: {mcls} ({name_txt}) | fc used = {fc:.1f} N/mm² (source: {fc_src})")
            if Nrd is not None:
                print(f"  Nrd = {Nrd:.1f} kN  vs  Ned = {Ned:.1f} kN  → {status} (utilization = {util:.2f}%)")
            else:
                print(f"  Nrd = <unknown> (missing area/dimensions)")
            print("")

        # Summary
        print("-"*80)
        total = ok_cnt + nok_cnt
        print(f"TOTAL: {total} checked columns | OK: {ok_cnt} | NOT OK: {nok_cnt}")
        if worst["gid"] is not None:
            print(f"Worst utilization: {worst['util']:.2f}%  (GlobalId {worst['gid']}, Nrd={worst['Nrd']:.1f} kN, "
                  f"dim≈ {worst['w']:.0f}×{worst['h']:.0f} mm)")
        print("End of report.")

if __name__ == "__main__":
    main()
