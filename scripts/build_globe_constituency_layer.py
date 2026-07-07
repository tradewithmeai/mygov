#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the simplified UK constituency layer used by the /globe-map asset.

Reads the full-resolution promap boundary file
(static/promap/data/constituencies-uk-2024-bgc.geojson, ONS BGC generalised
20m, EPSG:4326) and emits two much smaller files for the 3D globe:

  static/data/geo/constituencies-uk-2024-globe.geojson  (~730 KiB)
      All 650 constituencies, ring-simplified and coordinate-quantised, with
      properties reduced to {code, name, centroidLat, centroidLong}. Drawn on
      the globe as line segments. Sub-polygons (islets) smaller than
      --min-part-area are dropped, always keeping each constituency's largest
      part, so archipelago seats survive.

  static/data/geo/uk-outline-globe.geojson  (~11 KiB)
      The dissolved UK landmass outline (union of all constituencies),
      aggressively simplified and buffered outward ~3 km so clicks just off
      the coast still count. Used client-side for "did the user click the
      UK?" hit-testing only — never drawn.

This is a one-off generator: outputs are checked into the repo (like the other
generated data under static/data/). Re-run only if the source boundaries or
tolerances change.

Dependency: shapely >= 2.0  (pip install shapely)

Usage:
  python scripts/build_globe_constituency_layer.py [--out-dir static/data/geo]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    from shapely.geometry import MultiPolygon, mapping, shape
    from shapely.ops import unary_union
    from shapely.validation import make_valid
except ImportError:  # pragma: no cover
    sys.exit("shapely is required: pip install shapely")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(
    REPO_ROOT, "static", "promap", "data", "constituencies-uk-2024-bgc.geojson"
)


def _polygonal(geom):
    """Reduce make_valid()/simplify() output to its polygonal parts only."""
    if geom is None:
        return None
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        if polys:
            return unary_union(polys)
    return None


def _filter_parts(geom, min_area):
    """Drop sub-polygons below min_area (sq degrees), keeping the largest."""
    parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    biggest = max(parts, key=lambda p: p.area)
    kept = [p for p in parts if p.area >= min_area or p is biggest]
    return MultiPolygon(kept) if len(kept) > 1 else kept[0]


def _round_coords(obj, precision):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(float(v), precision) for v in obj]
        return [_round_coords(item, precision) for item in obj]
    return obj


def _clean_geometry(geom_dict):
    """Drop degenerate rings (< 4 points) that can survive simplification."""

    def ring_ok(ring):
        return len(ring) >= 4

    gtype = geom_dict["type"]
    if gtype == "Polygon":
        rings = [r for r in geom_dict["coordinates"] if ring_ok(r)]
        if not rings:
            return None
        return {"type": "Polygon", "coordinates": rings}
    if gtype == "MultiPolygon":
        polys = []
        for poly in geom_dict["coordinates"]:
            rings = [r for r in poly if ring_ok(r)]
            if rings:
                polys.append(rings)
        if not polys:
            return None
        if len(polys) == 1:
            return {"type": "Polygon", "coordinates": polys[0]}
        return {"type": "MultiPolygon", "coordinates": polys}
    return geom_dict


def _emit(geom, tolerance, precision, preserve_topology=True):
    simplified = _polygonal(geom.simplify(tolerance, preserve_topology=preserve_topology))
    if simplified is None or simplified.is_empty:
        return None
    geom_dict = mapping(simplified)
    return _clean_geometry(
        {
            "type": geom_dict["type"],
            "coordinates": _round_coords(geom_dict["coordinates"], precision),
        }
    )


def build(out_dir, tolerance, precision, min_part_area, outline_buffer):
    with open(SOURCE, "r", encoding="utf-8") as fh:
        source = json.load(fh)

    features_out = []
    shapes = []
    for feat in source["features"]:
        props = feat.get("properties") or {}
        geom = shape(feat["geometry"])
        if not geom.is_valid:
            geom = _polygonal(make_valid(geom))
        if geom is None:
            continue
        shapes.append(geom)
        geom_dict = _emit(_filter_parts(geom, min_part_area), tolerance, precision)
        if geom_dict is None:
            continue
        features_out.append(
            {
                "type": "Feature",
                "properties": {
                    "code": props.get("PCON24CD") or props.get("code"),
                    "name": props.get("PCON24NM") or props.get("name"),
                    "centroidLat": props.get("centroidLat") or props.get("LAT"),
                    "centroidLong": props.get("centroidLong") or props.get("LONG"),
                },
                "geometry": geom_dict,
            }
        )

    constituencies = {
        "type": "FeatureCollection",
        "meta": {
            "source": "constituencies-uk-2024-bgc.geojson (ONS BGC, EPSG:4326)",
            "generator": "scripts/build_globe_constituency_layer.py",
            "tolerance": tolerance,
            "precision": precision,
            "minPartArea": min_part_area,
            "featureCount": len(features_out),
            "attribution": (
                "Office for National Statistics Open Geography Portal; contains "
                "Ordnance Survey and ONS intellectual property."
            ),
        },
        "features": features_out,
    }

    # Hit-test outline: dissolve, drop islets, coarse non-topological simplify
    # (the raw union resists topology-preserving simplification), then buffer
    # outward so near-coast clicks still register. Never rendered.
    union = _filter_parts(unary_union(shapes), 0.01)
    union = _polygonal(make_valid(union.simplify(0.05, preserve_topology=False)))
    union = _polygonal(make_valid(union.buffer(outline_buffer)))
    outline_dict = _emit(union, 0.01, 2)
    outline = {
        "type": "FeatureCollection",
        "meta": {
            "source": "dissolved union of constituencies-uk-2024-bgc.geojson",
            "generator": "scripts/build_globe_constituency_layer.py",
            "simplify": 0.05,
            "buffer": outline_buffer,
            "precision": 2,
            "note": "click hit-testing only; never drawn",
        },
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "United Kingdom"},
                "geometry": outline_dict,
            }
        ],
    }

    os.makedirs(out_dir, exist_ok=True)
    for name, payload in (
        ("constituencies-uk-2024-globe.geojson", constituencies),
        ("uk-outline-globe.geojson", outline),
    ):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, separators=(",", ":"), ensure_ascii=False)
        print(f"{name}: {os.path.getsize(path) / 1024:.0f} KiB")
    print(f"features: {len(features_out)}")


def main():
    parser = argparse.ArgumentParser(
        description="Build the simplified constituency layer for /globe-map."
    )
    parser.add_argument("--out-dir", default=os.path.join(REPO_ROOT, "static", "data", "geo"))
    parser.add_argument("--tolerance", type=float, default=0.01)
    parser.add_argument("--precision", type=int, default=3)
    parser.add_argument("--min-part-area", type=float, default=0.0005)
    parser.add_argument("--outline-buffer", type=float, default=0.03)
    args = parser.parse_args()
    build(args.out_dir, args.tolerance, args.precision, args.min_part_area, args.outline_buffer)


if __name__ == "__main__":
    main()
