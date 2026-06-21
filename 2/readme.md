# MLOps Data Curation Pipeline

A command-line CSV curation pipeline built with Pandas, Pandera, and scikit-learn. It validates a fixed schema, imputes missing numeric features, flags outliers, and produces leakage-safe train/test datasets with structured JSON Lines logs.

## Current status

The core pipeline is implemented in `pipeline.py` and has been exercised end to end with 5,000 generated rows. The recorded run produced 4,195 inliers, split into 3,356 training rows and 839 test rows.

Automated tests and pinned dependency metadata have not been added yet.

## Requirements

- Python 3.10 or newer
- `numpy`
- `pandas`
- `pandera`
- `scikit-learn`
- `typer`

Install the current unpinned dependencies:

```bash
python -m pip install numpy pandas pandera scikit-learn typer
```

## Usage

Run commands from this directory.

```bash
python pipeline.py generate --count 5000 --output-dir mock_data
python pipeline.py run --input-file mock_data/mock_data.csv --output-dir output
```

Use `python pipeline.py --help` or append `--help` to a subcommand for all options.

## Pipeline

```text
CSV input
  -> strict Pandera validation
  -> group-median feature imputation
  -> IsolationForest outlier flags
  -> remove outliers from model data
  -> deterministic train/test split
  -> fit scaler on training data only
  -> CSV artifacts and JSON Lines audit log
```

See [PRD.md](PRD.md) for the data and output contracts and [docs/MEMORY.md](docs/MEMORY.md) for implementation status and known risks.

## Generated files

Generated data is currently checked into `mock_data/` and `output/` as evidence of a successful manual run. Re-running commands appends to existing log files and overwrites CSV artifacts with the same names.

## Limitations

- The schema and feature names are fixed in code.
- Outlier sensitivity uses `contamination="auto"`; it is not calibrated to a business threshold.
- The CLI does not yet validate that enough inlier rows remain for splitting.
- Missing targets are accepted and written to output.
- Failures outside Pandera validation may terminate without a structured error event.
