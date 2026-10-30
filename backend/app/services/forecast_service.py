"""Service bridging demand forecasts with assignment planning inputs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.errors import ServiceUnavailableError
from app.repositories import get_forecast_repository, get_section_repository
from app.repositories.base import Repository
from app.schemas.forecast import ForecastRecord, ForecastRunResponse
from app.schemas.section import Section
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.forecast")

REPO_ROOT: Path = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR: Path = REPO_ROOT / "ml" / "artifacts"
HISTORY_FILE: Path = REPO_ROOT / "data" / "seed" / "enrollment_history.json"

UPCOMING_TERMS = [
    {"term": "Fall 2026", "season": "Fall", "year": 2026, "term_index": 10},
    {"term": "Spring 2027", "season": "Spring", "year": 2027, "term_index": 11},
    {"term": "Summer 2027", "season": "Summer", "year": 2027, "term_index": 12},
]


class ForecastService:
    """Service managing ML demand forecasts and section updating."""

    def __init__(
        self,
        forecast_repo: Repository[dict[str, Any]] | None = None,
        section_repo: Repository[Section] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.forecast_repo = forecast_repo or get_forecast_repository()
        self.section_repo = section_repo or get_section_repository()
        self.audit_service = audit_service or AuditService()

    async def get_forecasts(self, term: str | None = None) -> list[ForecastRecord]:
        """Fetch stored forecasts, optionally filtered by academic term."""
        records = await self.forecast_repo.get_all()
        if not records:
            # Fall back to precomputed file if forecasts.json not yet seeded
            precomputed_file = ARTIFACTS_DIR / "precomputed_forecasts.json"
            if precomputed_file.exists():
                try:
                    records = json.loads(precomputed_file.read_text(encoding="utf-8"))
                except Exception as exc:
                    logger.warning(f"Could not read precomputed forecasts: {exc}")

        if term:
            records = [
                r for r in records if r.get("term", "").lower() == term.lower()
            ]

        return [
            ForecastRecord(
                course_id=r["course_id"],
                course_code=r.get("course_code", r["course_id"]),
                term=r["term"],
                season=r.get("season", "Fall"),
                year=int(r.get("year", 2026)),
                p10=int(r["p10"]),
                p50=int(r["p50"]),
                p90=int(r["p90"]),
                n_sections=int(r["n_sections"]),
                p90_risk_sections=int(r["p90_risk_sections"]),
            )
            for r in records
        ]

    async def run_forecast(
        self,
        term: str | None = None,
        actor_id: str | None = None,
    ) -> ForecastRunResponse:
        """Generate forecasts using trained models or precomputed fallback.

        Never trains models. If model artifacts are missing in 'model' mode,
        raises ServiceUnavailableError (503).
        """
        mode = settings.FORECAST_MODE.lower()

        if mode == "precomputed":
            new_forecasts = self._run_precomputed(term)
        else:
            new_forecasts = self._run_model(term)

        # Merge with existing records in forecasts.json
        existing = await self.forecast_repo.get_all()
        forecast_dict: dict[tuple[str, str], dict[str, Any]] = {
            (r["course_id"], r["term"].lower()): r for r in existing if "course_id" in r and "term" in r
        }

        for nf in new_forecasts:
            forecast_dict[(nf["course_id"], nf["term"].lower())] = nf

        merged_list = list(forecast_dict.values())
        await self.forecast_repo.bulk_replace(merged_list)

        # Update Section records in sections.json
        sections = await self.section_repo.get_all()
        updated_count = 0
        forecast_lookup = {
            (nf["course_id"], nf["term"].lower()): nf for nf in new_forecasts
        }

        for sec in sections:
            key = (sec.course_id, sec.term.lower())
            if key in forecast_lookup:
                fc = forecast_lookup[key]
                sec.size_p10 = fc["p10"]
                sec.size_p50 = fc["p50"]
                sec.size_p90 = fc["p90"]
                updated_count += 1

        if sections:
            await self.section_repo.bulk_replace(sections)

        if actor_id:
            await self.audit_service.log_event(
                actor_id=actor_id,
                action="FORECAST_RUN",
                entity="forecast",
                payload={
                    "mode": mode,
                    "term": term or "all_upcoming",
                    "forecasts_generated": len(new_forecasts),
                    "sections_updated": updated_count,
                },
            )

        return ForecastRunResponse(
            status="ok",
            term=term or "all_upcoming",
            courses_forecasted=len(new_forecasts),
            forecast_mode=mode,
            message=(
                f"Generated {len(new_forecasts)} course forecasts and updated "
                f"{updated_count} section quantiles in {mode} mode."
            ),
        )

    def _run_precomputed(self, term: str | None) -> list[dict[str, Any]]:
        """Load forecasts from precomputed JSON artifact without importing LightGBM."""
        path = ARTIFACTS_DIR / "precomputed_forecasts.json"
        if not path.exists():
            raise ServiceUnavailableError(
                "ML artifacts missing: precomputed_forecasts.json not found. "
                "Run 'make train' to generate forecasts before using this endpoint."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        if term:
            data = [r for r in data if r.get("term", "").lower() == term.lower()]
        return data

    def _run_model(self, term: str | None) -> list[dict[str, Any]]:
        """Load text model artifacts and run inference. Raises 503 if artifacts missing."""
        required_artifacts = [
            "forecast_p10.txt",
            "forecast_p50.txt",
            "forecast_p90.txt",
            "feature_config.json",
        ]
        missing = [f for f in required_artifacts if not (ARTIFACTS_DIR / f).exists()]
        if missing:
            raise ServiceUnavailableError(
                f"ML artifacts missing: {missing}. "
                "Run 'make train' to generate forecasts before using this endpoint."
            )

        if not HISTORY_FILE.exists():
            raise ServiceUnavailableError(
                f"Training history missing: {HISTORY_FILE.name} not found."
            )

        # Lazy import: LightGBM is only loaded when in model mode
        try:
            from ml.forecast.model import SECTION_CAP_DEFAULT, build_feature_df
            from ml.forecast.predict import load_models, predict, predict_sections
        except Exception as exc:
            raise ServiceUnavailableError(
                f"Failed to load ML prediction routines: {exc}. "
                "Run 'make train' before running inference."
            ) from exc

        models = load_models()
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

        courses_seen: dict[str, dict[str, Any]] = {}
        for rec in history:
            cid = rec["course_id"]
            if cid not in courses_seen:
                courses_seen[cid] = rec

        terms_to_run = UPCOMING_TERMS
        if term:
            matching = [
                ut for ut in UPCOMING_TERMS if ut["term"].lower() == term.lower()
            ]
            if matching:
                terms_to_run = matching
            else:
                # Custom term: derive season and year
                season = "Fall"
                for s in ["Spring", "Summer", "Fall"]:
                    if s.lower() in term.lower():
                        season = s
                        break
                year = 2026
                import re

                m = re.search(r"\d{4}", term)
                if m:
                    year = int(m.group())
                terms_to_run = [
                    {"term": term, "season": season, "year": year, "term_index": 10}
                ]

        results: list[dict[str, Any]] = []
        for t_info in terms_to_run:
            target_records = [
                {
                    **courses_seen[cid],
                    "term_index": t_info["term_index"],
                    "season": t_info["season"],
                }
                for cid in courses_seen
            ]

            X_df, _ = build_feature_df(history, target_records)
            X = X_df.values.astype("float32")
            preds = predict(models, X)
            sections_data = predict_sections(preds, section_cap=SECTION_CAP_DEFAULT)

            for i, cid in enumerate(courses_seen):
                results.append(
                    {
                        "course_id": cid,
                        "course_code": courses_seen[cid]["course_code"],
                        "term": t_info["term"],
                        "season": t_info["season"],
                        "year": t_info["year"],
                        "p10": sections_data["p10"][i],
                        "p50": sections_data["p50"][i],
                        "p90": sections_data["p90"][i],
                        "n_sections": sections_data["n_sections"][i],
                        "p90_risk_sections": sections_data["p90_risk_sections"][i],
                    }
                )

        return results
