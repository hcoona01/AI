from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.schemas.common import RuleType
from app.schemas.constraint import (
    ConstraintBatchUpdateRequest,
    ConstraintRule,
    ValidationRequest,
    ValidationResponse,
)
from app.services.constraint_engine import ConstraintEngine

router = APIRouter(prefix="/constraints", tags=["Constraints"])

# Global or dependency-injected engine instance
engine = ConstraintEngine()


def get_constraint_engine() -> ConstraintEngine:
    return engine


def require_admin_role(
    x_user_role: Annotated[
        str | None, Header(description="Current user role for RBAC")
    ] = None,
) -> str:
    """RBAC guard enforcing admin authorization for modifying system constraints."""
    # In development mode, if header is explicitly 'faculty', forbid modification
    if x_user_role and x_user_role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin role required to update constraint rules",
        )
    return x_user_role or "admin"


@router.get("", response_model=list[ConstraintRule])
async def list_constraints(
    service: Annotated[ConstraintEngine, Depends(get_constraint_engine)],
) -> list[ConstraintRule]:
    """Retrieve the catalog of all hard and soft constraint rules."""
    return service.get_rules()


@router.put("", response_model=list[ConstraintRule])
async def update_constraints(
    request: ConstraintBatchUpdateRequest,
    service: Annotated[ConstraintEngine, Depends(get_constraint_engine)],
    _: Annotated[str, Depends(require_admin_role)],
) -> list[ConstraintRule]:
    """Admin-only: Update constraint parameters, weights, and enabled/disabled states."""
    return service.update_rules(request.rules)


@router.post("/validate", response_model=ValidationResponse)
async def validate_assignments(
    request: ValidationRequest,
    service: Annotated[ConstraintEngine, Depends(get_constraint_engine)],
) -> ValidationResponse:
    """Validate a set of course assignments against a scenario using active constraint rules."""
    violations = service.validate(
        assignments=request.assignments,
        scenario=request.scenario,
        rule_overrides=request.rule_overrides,
    )

    # Count hard vs soft violations based on rule catalog type
    rule_lookup = {r.rule_id: r.type for r in service.get_rules()}
    if request.rule_overrides:
        for override in request.rule_overrides:
            rule_lookup[override.rule_id] = override.type

    hard_count = sum(
        1
        for v in violations
        if rule_lookup.get(v.rule_id) == RuleType.HARD or v.rule_id.startswith("HC")
    )
    soft_count = sum(
        1
        for v in violations
        if rule_lookup.get(v.rule_id) == RuleType.SOFT or v.rule_id.startswith("SC")
    )

    return ValidationResponse(
        is_valid=(hard_count == 0),
        hard_violation_count=hard_count,
        soft_violation_count=soft_count,
        violations=violations,
    )
