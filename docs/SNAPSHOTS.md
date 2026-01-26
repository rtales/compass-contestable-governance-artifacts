# Snapshot artifacts (`data/`)

## Why `data/` is versioned
We version **processed dataset snapshots** to support fully offline reproduction and to prevent ambiguity about dataset preprocessing.

Each snapshot includes:
- `processed/` files consumed by the pipeline
- `schema.json` describing the processed format
- `manifest.json` with checksums and provenance metadata

## Updating a snapshot (policy)
- Never modify a snapshot "in place" without bumping its snapshot version.
- Update `manifest.json` checksums whenever processed files change.
- Record provenance in the manifest (raw source reference, schema version, and generator info).

## Absolute paths
Manifests must not include machine-specific absolute paths. Use a source reference (e.g., dataset name + file basename) and hashes instead.
