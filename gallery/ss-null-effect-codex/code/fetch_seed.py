"""Acquire immutable seed bytes and validate only design-authorized fields.

Excluded fields are copied/hashed as bytes but never parsed as variables.
Standard library only; no outcome summaries or relationships are computed.
"""
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

URL = 'https://raw.githubusercontent.com/brycewang-stanford/Free-Research-Crew/40fac308b3c6ed5a9832e9d687519b12c9487b76/crew/bench/seeds/ss-null-effect/data.csv'
EXPECTED = 'f09fba8695df8d2cfe44abe770860772f07a562ad88c19789f6feab946048ca9'
REQUIRED = 'id treat age educ married urban region children health_limit re74 re75 unemp74 unemp75 re78'.split()
INDICATORS = 'treat married urban health_limit unemp74 unemp75'.split()
NUMERIC = [k for k in REQUIRED if k not in ('id', 'region')]

with urlopen(URL, timeout=60) as response:
    payload = response.read()
sha = hashlib.sha256(payload).hexdigest()
if sha != EXPECTED:
    raise ValueError('Seed SHA256 differs from published task metadata')
raw = Path('data/raw/seed.csv')
raw.parent.mkdir(parents=True, exist_ok=True)
raw.write_bytes(payload)
metrics = {'sha_verified': 1, 'source_bytes': len(payload), 'rows': 0,
           'duplicate_ids': 0, 'missing_ids': 0, 'missing_region': 0,
           'rows_kept': 0, 'rows_dropped': 0}
for name in REQUIRED:
    metrics['missing_' + name] = 0
for name in NUMERIC:
    metrics['nonfinite_' + name] = 0
for name in INDICATORS:
    metrics['nonbinary_' + name] = 0
ids, regions = set(), set()
# Parse only the first fourteen fields; no quoted commas occur in these fields.
# The suffix containing excluded outcomes stays opaque and is never inspected.
with raw.open(newline='', encoding='utf-8') as handle:
    header = next(csv.reader([next(handle)]))
    if header[:14] != REQUIRED:
        raise ValueError('Unexpected required-field schema or order')
    metrics['schema_columns'] = len(header)
    for line in handle:
        values = next(csv.reader([','.join(line.split(',', 14)[:14])]))
        if len(values) != len(REQUIRED):
            raise ValueError('Malformed required-field row')
        row = dict(zip(REQUIRED, values))
        metrics['rows'] += 1
        for name, value in row.items():
            metrics['missing_' + name] += int(not value.strip())
        if row['id'] in ids:
            metrics['duplicate_ids'] += 1
        ids.add(row['id'])
        if row['region'].strip():
            regions.add(row['region'])
        for name in NUMERIC:
            try:
                value = float(row[name])
            except ValueError:
                value = float('nan')
            metrics['nonfinite_' + name] += int(not math.isfinite(value))
            if name in INDICATORS:
                metrics['nonbinary_' + name] += int(value not in (0, 1))
metrics['missing_ids'] = metrics['missing_id']
metrics['unique_ids'] = len(ids)
metrics['region_categories'] = len(regions)
# Seed metadata supplies no allowed category vocabulary. Record observed labels,
# without counts or treatment/outcome comparisons, for design review.
Path('data/schema.json').write_text(json.dumps({'columns': header, 'required': REQUIRED,
    'observed_region_labels': sorted(regions),
    'region_vocabulary_source': 'Observed labels only; seed metadata supplies no vocabulary'}, indent=2) + '\n')
errors = [key for key, value in metrics.items()
          if key.startswith(('missing_', 'nonfinite_', 'nonbinary_', 'duplicate_')) and value]
if metrics['rows'] != 4000:
    errors.append('unexpected_row_count')
metrics['validation_pass'] = int(not errors)
metrics['rows_kept'] = metrics['rows'] if not errors else 0
Path('runs/fetch-seed/metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
manifest = {'datasets': [{'id': 'ss-null-effect-seed', 'origin': URL,
    'license': 'CC0-1.0 (synthetic data distributed with this repository; crew/bench/seeds/ss-null-effect/task.json)',
    'path': str(raw), 'sha256': sha,
    'retrieved_on': datetime.now(timezone.utc).date().isoformat(),
    'source_commit': '40fac308b3c6ed5a9832e9d687519b12c9487b76',
    'expected_sha256_source': 'crew/bench/seeds/ss-null-effect/task.json'}]}
Path('data/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
if errors:
    raise ValueError('Validation failed: ' + ', '.join(errors))
print('Seed acquired and required-field schema/missingness checks passed; no rows removed.')
