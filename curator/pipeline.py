"""Enterprise MLOps Data Curation Pipeline.

=======================================

A production-style command-line pipeline for tabular machine learning workflows.

Features
--------
- Strict schema validation with Pandera
- Group-wise median imputation
- Multivariate outlier detection using Isolation Forest
- Leakage-free train/test split and feature scaling
- Structured JSON Lines logging
- Synthetic data generation for testing

Examples
--------
Generate mock data:

    python pipeline.py generate \\
        --count 10000 \\
        --output-dir ./mock_data

Run the pipeline:

    python pipeline.py run \\
        --input-file mock_data/mock_data.csv \\
        --output-dir ./output

Outputs
-------
The pipeline produces:

- curated_full.csv
- X_train.csv
- X_test.csv
- y_train.csv
- y_test.csv
- pipeline.log.jsonl
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pandera.pandas as pa
import typer
from pandera.typing import Series
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Centralized Reproducibility Engine
RANDOM_STATE = 42

app = typer.Typer(
    help="Enterprise MLOps Data Curation Pipeline",
    no_args_is_help=True,
    add_completion=False,
)

# =========================================================================
# Structured JSON Lines Logger (Splunk / Datadog compatible)
# =========================================================================


class JsonLinesLogger:
    """Append-only structured logger. Every call writes one JSON line."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _emit(self, level: str, event: str, **kwargs: Any) -> None:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "trace_id": uuid.uuid4().hex,
            "logger": "DataCurationPipeline",
        }
        payload.update(kwargs)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, default=str) + "\n")

    def info(self, event: str, **kwargs: Any) -> None:
        self._emit("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._emit("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._emit("ERROR", event, **kwargs)

    def exception(self, event: str, exc: Exception) -> None:
        """Log exceptions with distinct error type extraction."""
        self._emit(
            "ERROR",
            event,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


# =========================================================================
# Pandera Structural Schema (data contract enforced at runtime)
# =========================================================================


class InputSchema(pa.DataFrameModel):
    """Structural contract every ingested DataFrame must satisfy."""

    amount: Series[float] = pa.Field(nullable=True, ge=0.0)
    tenure: Series[float] = pa.Field(nullable=True, ge=0.0)
    score: Series[float] = pa.Field(nullable=True, ge=-1_000_000.0, le=1_000_000.0)
    group: Series[str] = pa.Field(nullable=False, isin=["alpha", "beta", "gamma"])
    target: Series[float] = pa.Field(nullable=True)

    class Config:
        coerce = True
        strict = True


# =========================================================================
# Imputation — Localised group-based median
# =========================================================================


def group_median_impute(
    df: pd.DataFrame,
    group_col: str,
    value_cols: list[str],
    logger: JsonLinesLogger,
) -> pd.DataFrame:
    """Fill missing continuous values with the median of their group.

    Falls back to the global column median when a whole group is null.
    """
    result = df.copy()
    for col in value_cols:
        n_null = int(result[col].isna().sum())
        if n_null == 0:
            continue
        group_medians = result.groupby(group_col)[col].transform("median")
        global_median = result[col].median()
        result[col] = result[col].fillna(group_medians).fillna(global_median)
        logger.info(
            "imputation_complete",
            column=col,
            nulls_imputed=n_null,
            strategy="group_median",
            group_column=group_col,
        )
    return result


# =========================================================================
# Outlier Detection — Unsupervised multivariate (IsolationForest)
# =========================================================================


def isolate_outliers(
    df: pd.DataFrame,
    feature_cols: list[str],
    logger: JsonLinesLogger,
) -> pd.DataFrame:
    """Flag multivariate outliers via IsolationForest. Returns df with 'outlier' column."""
    model = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=RANDOM_STATE,
    )
    clean = df[feature_cols].dropna()
    preds = model.fit_predict(clean)
    outlier_mask = pd.Series(False, index=df.index)
    outlier_mask.loc[clean.index] = preds == -1
    n = int(outlier_mask.sum())
    logger.info(
        "outlier_detection_complete",
        outliers_found=n,
        total_rows=len(df),
    )
    result = df.copy()
    result["outlier"] = outlier_mask.astype(int)
    return result


# =========================================================================
# Leakage-Free Split & Scale — StandardScaler fit on train slice only
# =========================================================================


def split_and_scale(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    test_size: float,
    logger: JsonLinesLogger,
) -> dict[str, pd.DataFrame]:
    """Split then scale. Scaler parameters are learned *exclusively* from X_train."""
    X = df[feature_cols]
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_STATE
    )
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=feature_cols,
        index=X_train.index,
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=feature_cols,
        index=X_test.index,
    )
    logger.info(
        "split_and_scale_complete",
        train_rows=len(X_train_scaled),
        test_rows=len(X_test_scaled),
        test_ratio=test_size,
        scaler_mean=scaler.mean_.tolist(),
        scaler_scale=scaler.scale_.tolist(),
    )
    return {
        "X_train": X_train_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train.to_frame(name=target_col),
        "y_test": y_test.to_frame(name=target_col),
    }


# =========================================================================
# CLI Commands
# =========================================================================


@app.command()
def run(
    input_file: Path = typer.Option(
        ..., "--input-file", "-i", help="Path to input CSV", exists=True, readable=True
    ),
    output_dir: Path = typer.Option(
        Path("output"), "--output-dir", "-o", help="Artifact output directory"
    ),
    test_size: float = typer.Option(
        0.2, "--test-size", min=0.05, max=0.5, help="Test split ratio"
    ),
) -> None:
    """Run the full curation pipeline on a provided dataset."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log = JsonLinesLogger(output_dir / "pipeline.log.jsonl")
    log.info("pipeline_started", input_file=str(input_file))
    df = pd.read_csv(input_file)
    log.info("data_loaded", rows=len(df), columns=list(df.columns))

    # -- 1. Validate ----------------------------------------------------------
    schema = InputSchema.to_schema()
    try:
        df = schema.validate(df)
    except pa.errors.SchemaError as exc:
        log.exception("validation_failed", exc)
        typer.secho(
            "❌ Validation failed: Input CSV does not match the required schema.",
            fg=typer.colors.RED,
        )
        typer.echo(f"\nReason:\n{exc}")
        raise typer.Exit(code=1)
    log.info("validation_passed", rows=len(df))

    # -- 2. Impute ------------------------------------------------------------
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ("target", "outlier")]
    df = group_median_impute(df, "group", numeric_cols, log)

    # -- 3. Detect outliers ---------------------------------------------------
    df = isolate_outliers(df, numeric_cols, log)

    # -- 4. Split & scale (leakage-free: scale learns from train only) --------
    inliers = df[df["outlier"] == 0].copy()
    result = split_and_scale(inliers, numeric_cols, "target", test_size, log)

    # -- 5. Persist artifacts -------------------------------------------------
    for name, frame in result.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        log.info("artifact_written", artifact=str(path), rows=len(frame))
    df.to_csv(output_dir / "curated_full.csv", index=False)
    log.info("pipeline_complete", output_dir=str(output_dir))

    # -- 6. Generate markdown report (Indented correctly inside run) ----------
    report = f"""
# Pipeline Execution Report
## Dataset
- Rows processed: {len(df)}
- Features: {numeric_cols}
## Outliers
- Outliers detected: {int(df["outlier"].sum())}
## Train/Test Split
- Train rows: {len(result["X_train"])}
- Test rows: {len(result["X_test"])}
## Artifacts
- X_train.csv
- X_test.csv
- y_train.csv
- y_test.csv
- curated_full.csv
Status: SUCCESS
"""
    save_report(report, output_dir / "reports")


@app.command()
def generate(
    count: int = typer.Option(
        ..., "--count", "-n", min=1, help="Number of mock rows to generate"
    ),
    output_dir: Path = typer.Option(
        Path("mock_data"), "--output-dir", help="Output directory for mock data"
    ),
) -> None:
    """Generate synthetic tabular data for pipeline testing."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log = JsonLinesLogger(output_dir / "generator.log.jsonl")
    rng = np.random.default_rng(RANDOM_STATE)
    groups = ["alpha", "beta", "gamma"]
    df = pd.DataFrame(
        {
            "amount": np.round(np.abs(rng.normal(500, 200, count)), 2),
            "tenure": np.round(np.abs(rng.exponential(12, count)), 1),
            "score": np.round(rng.uniform(-10, 100, count), 3),
            "group": rng.choice(groups, count),
            "target": np.round(rng.normal(1000, 250, count), 2),
        }
    )
    # Inject ~5 % missing values
    for col in ("amount", "tenure", "score"):
        idx = rng.choice(df.index, size=int(count * 0.05), replace=False)
        df.loc[idx, col] = None
    # Inject ~2 % extreme outliers in 'amount'
    outlier_idx = rng.choice(df.index, size=int(count * 0.02), replace=False)
    df.loc[outlier_idx, "amount"] = rng.uniform(5_000, 10_000, len(outlier_idx))
    path = output_dir / "mock_data.csv"
    df.to_csv(path, index=False)
    log.info("mock_data_generated", rows=count, artifact=str(path))


def save_report(report: str, reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    latest = reports_dir / "latest.md"
    if latest.exists():
        choice = typer.prompt(
            "\nReport exists.\n"
            "1 = Overwrite latest.md\n"
            "2 = Create timestamped file\n"
            "3 = Cancel\n"
            "Choice",
            type=int,
        )
        if choice == 1:
            target = latest
        elif choice == 2:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = reports_dir / f"run_{timestamp}.md"
        else:
            typer.echo("Cancelled.")
            raise typer.Exit()
    else:
        target = latest
    target.write_text(report, encoding="utf-8")
    typer.secho(
        f"✓ Report saved: {target}",
        fg=typer.colors.GREEN,
    )


# =========================================================================
# Entry Point
# =========================================================================
if __name__ == "__main__":
    app()
