"""TF-IDF and tag-overlap scoring between faculty profiles and course syllabus requirements.

Implements the multi-component expertise fit formulation:
    fit(faculty, course) = 0.60 * weighted_tag_match + 0.25 * tfidf_cosine + 0.15 * past_teaching_bonus

HC-01 (minimum proficiency) is maintained strictly as a hard feasibility filter,
evaluated independently from the continuous fit score.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

WEIGHT_TAG: float = 0.60
WEIGHT_TFIDF: float = 0.25
WEIGHT_PAST_TEACHING: float = 0.15
DEFAULT_PAST_TEACHING_CAP: int = 2


class FitResult:
    """Encapsulates the continuous fit score, explainable breakdown dict, and HC-01 feasibility."""

    def __init__(
        self,
        score: float,
        breakdown: dict[str, Any],
        is_eligible: bool,
    ) -> None:
        self.score = float(score)
        self.breakdown = breakdown
        self.is_eligible = is_eligible

    def __float__(self) -> float:
        return self.score

    def __iter__(self):
        yield self.score
        yield self.breakdown

    def __getitem__(self, item: int | str) -> Any:
        if item == 0:
            return self.score
        if item == 1:
            return self.breakdown
        if isinstance(item, str):
            return self.breakdown.get(item)
        raise IndexError(f"Index out of range: {item}")

    def __repr__(self) -> str:
        return f"FitResult(score={self.score:.4f}, eligible={self.is_eligible})"


def _normalize_tag(tag: str) -> str:
    """Normalize a domain expertise tag string for case-insensitive matching."""
    return tag.strip().lower()


def extract_faculty_skills(faculty: Any) -> dict[str, int]:
    """Extract mapping of normalized tag -> integer proficiency (1-5) from faculty object/dict."""
    skills: dict[str, int] = {}
    expertise_list = (
        faculty.get("expertise", [])
        if isinstance(faculty, dict)
        else getattr(faculty, "expertise", [])
    )
    for exp in expertise_list:
        if isinstance(exp, dict):
            tag = exp.get("tag", "")
            prof = exp.get("proficiency", 1)
        else:
            tag = getattr(exp, "tag", "")
            prof = getattr(exp, "proficiency", 1)
        if tag:
            skills[_normalize_tag(tag)] = int(prof)
    return skills


def extract_course_requirements(course: Any) -> tuple[list[str], int]:
    """Extract (required_tags, min_proficiency) from a course object or dictionary."""
    if isinstance(course, dict):
        tags = course.get("required_tags", [])
        min_prof = course.get("min_proficiency", 1)
    else:
        tags = getattr(course, "required_tags", [])
        min_prof = getattr(course, "min_proficiency", 1)
    return list(tags), int(min_prof)


def extract_course_text(course: Any) -> str:
    """Extract rich descriptive text representation of a course for TF-IDF embedding."""
    if isinstance(course, dict):
        title = course.get("title", "")
        desc = course.get("description", "")
        code = course.get("code", "")
        tags = " ".join(course.get("required_tags", []))
    else:
        title = getattr(course, "title", "")
        desc = getattr(course, "description", "")
        code = getattr(course, "code", "")
        tags = " ".join(getattr(course, "required_tags", []))
    return f"{code} {title} {desc} {tags}".strip()


def extract_faculty_text(
    faculty: Any,
    past_courses_text: str = "",
) -> str:
    """Extract rich descriptive profile text of a faculty member for TF-IDF embedding."""
    if isinstance(faculty, dict):
        name = faculty.get("name", "")
        rank = faculty.get("rank", "")
        expertise_items = faculty.get("expertise", [])
        past_from_dict = faculty.get("past_courses", [])
    else:
        name = getattr(faculty, "name", "")
        rank = getattr(faculty, "rank", "")
        expertise_items = getattr(faculty, "expertise", [])
        past_from_dict = getattr(faculty, "past_courses", [])

    tags: list[str] = []
    for exp in expertise_items:
        t = exp.get("tag", "") if isinstance(exp, dict) else getattr(exp, "tag", "")
        if t:
            tags.append(t)

    past_text = past_courses_text
    if not past_text and past_from_dict:
        if isinstance(past_from_dict, dict):
            past_text = " ".join(past_from_dict.keys())
        elif isinstance(past_from_dict, list):
            past_text = " ".join(str(p) for p in past_from_dict)

    return f"{name} {rank} {' '.join(tags)} {past_text}".strip()


def extract_times_taught(faculty: Any, course: Any) -> int:
    """Infer the count of historical terms the faculty member taught the target course."""
    cid = course.get("id", "") if isinstance(course, dict) else getattr(course, "id", "")
    code = course.get("code", "") if isinstance(course, dict) else getattr(course, "code", "")

    past = (
        faculty.get("past_courses", None)
        if isinstance(faculty, dict)
        else getattr(faculty, "past_courses", None)
    )
    if past is None:
        return 0

    if isinstance(past, dict):
        if cid in past:
            return int(past[cid])
        if code in past:
            return int(past[code])
        return 0

    if isinstance(past, (list, tuple, set)):
        matches = sum(1 for item in past if item in (cid, code))
        return matches

    return 0


def check_hc01(
    faculty: Any,
    course: Any,
) -> tuple[bool, list[str]]:
    """Evaluate Hard Constraint HC-01: Faculty proficiency >= course min_proficiency.

    Returns:
        (is_eligible, list_of_violation_reasons)
    """
    skills = extract_faculty_skills(faculty)
    required_tags, min_prof = extract_course_requirements(course)
    violations: list[str] = []

    for tag in required_tags:
        tag_norm = _normalize_tag(tag)
        current_prof = skills.get(tag_norm, 0)
        if current_prof < min_prof:
            faculty_name = (
                faculty.get("name", "Faculty")
                if isinstance(faculty, dict)
                else getattr(faculty, "name", "Faculty")
            )
            course_code = (
                course.get("code", "Course")
                if isinstance(course, dict)
                else getattr(course, "code", "Course")
            )
            violations.append(
                f"{faculty_name} proficiency {current_prof} for tag '{tag}' "
                f"is below {course_code} required min_proficiency {min_prof} (HC-01)"
            )

    return len(violations) == 0, violations


def fit(
    faculty: Any,
    course: Any,
    vectorizer: TfidfVectorizer | None = None,
    past_teaching_count: int | None = None,
    past_teaching_cap: int = DEFAULT_PAST_TEACHING_CAP,
    tag_weights: dict[str, float] | None = None,
) -> FitResult:
    """Compute normalized expertise fit score in [0.0, 1.0] and detailed breakdown.

    Formula:
        fit = 0.60 * tag_match + 0.25 * tfidf_cosine + 0.15 * past_teaching_bonus

    Args:
        faculty: Faculty domain model or dict representation.
        course: Course domain model or dict representation.
        vectorizer: Optional pre-fitted TfidfVectorizer instance. If None, fits a
                    lightweight vectorizer on the (faculty, course) text pair.
        past_teaching_count: Explicit integer times taught. If None, extracts from faculty.
        past_teaching_cap: Maximum times taught before past-teaching bonus reaches 1.0.
        tag_weights: Optional relative weighting per course required tag.

    Returns:
        FitResult containing score, breakdown dict, and HC-01 feasibility flag.
    """
    skills = extract_faculty_skills(faculty)
    required_tags, min_prof = extract_course_requirements(course)

    # 1. Component 1: Weighted tag match (weight 0.60)
    tag_details: list[dict[str, Any]] = []
    if not required_tags:
        tag_score = 1.0
    else:
        weighted_sum = 0.0
        total_weight = 0.0
        for tag in required_tags:
            tag_norm = _normalize_tag(tag)
            prof = skills.get(tag_norm, 0)
            norm_prof = prof / 5.0
            w = tag_weights.get(tag, 1.0) if tag_weights else 1.0
            weighted_sum += w * norm_prof
            total_weight += w
            tag_details.append(
                {
                    "tag": tag,
                    "proficiency": prof,
                    "min_required": min_prof,
                    "normalized_score": round(norm_prof, 4),
                    "weight": w,
                }
            )
        tag_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    tag_score = float(np.clip(tag_score, 0.0, 1.0))

    # 2. Component 2: TF-IDF cosine similarity (weight 0.25)
    f_text = extract_faculty_text(faculty)
    c_text = extract_course_text(course)

    if vectorizer is not None:
        try:
            vf = vectorizer.transform([f_text])
            vc = vectorizer.transform([c_text])
            tfidf_raw = (vf @ vc.T).toarray()[0, 0]
            tfidf_score = float(np.clip(tfidf_raw, 0.0, 1.0))
        except Exception:
            tfidf_score = 0.0
    else:
        try:
            v_pair = TfidfVectorizer(stop_words="english", token_pattern=r"(?u)\b\w+\b")
            m = v_pair.fit_transform([f_text, c_text])
            tfidf_raw = (m[0] @ m[1].T).toarray()[0, 0]
            tfidf_score = float(np.clip(tfidf_raw, 0.0, 1.0))
        except ValueError:
            # Handles empty vocabulary / stopwords only
            tfidf_score = 0.0

    # 3. Component 3: Past-teaching bonus (weight 0.15, capped)
    if past_teaching_count is not None:
        times_taught = max(0, int(past_teaching_count))
    else:
        times_taught = extract_times_taught(faculty, course)

    if past_teaching_cap > 0:
        past_bonus = min(1.0, times_taught / float(past_teaching_cap))
    else:
        past_bonus = 1.0 if times_taught > 0 else 0.0

    past_teaching_score = float(np.clip(past_bonus, 0.0, 1.0))

    # Overall weighted aggregation
    weighted_tag = WEIGHT_TAG * tag_score
    weighted_tfidf = WEIGHT_TFIDF * tfidf_score
    weighted_past = WEIGHT_PAST_TEACHING * past_teaching_score

    total_score = round(float(np.clip(weighted_tag + weighted_tfidf + weighted_past, 0.0, 1.0)), 4)

    # Evaluate HC-01 eligibility independently
    is_eligible, violations = check_hc01(faculty, course)

    breakdown = {
        "tag_score": round(tag_score, 4),
        "tfidf_score": round(tfidf_score, 4),
        "past_teaching_score": round(past_teaching_score, 4),
        "tag_weighted": round(weighted_tag, 4),
        "tfidf_weighted": round(weighted_tfidf, 4),
        "past_teaching_weighted": round(weighted_past, 4),
        "total_score": total_score,
        "hc01_eligible": is_eligible,
        "hc01_violations": violations,
        "tag_details": tag_details,
        "times_taught": times_taught,
    }

    return FitResult(score=total_score, breakdown=breakdown, is_eligible=is_eligible)


def compute_fit_matrix(
    faculties: list[Any],
    courses: list[Any],
    past_teaching_matrix: np.ndarray | None = None,
    past_teaching_cap: int = DEFAULT_PAST_TEACHING_CAP,
) -> np.ndarray:
    """Compute the full (N_faculty x M_course) expertise fit matrix in float32.

    Fits a runtime TF-IDF vectorizer across the catalog text corpus (never pickled),
    vectorizes tag matches and past-teaching bonuses, and outputs a 2D float32 ndarray.

    Args:
        faculties: List of N faculty domain models or dictionaries.
        courses: List of M course domain models or dictionaries.
        past_teaching_matrix: Optional (N, M) ndarray of past term counts.
        past_teaching_cap: Capping threshold for past-teaching bonus.

    Returns:
        np.ndarray of shape (N, M) with dtype float32, bounded in [0.0, 1.0].
    """
    n_fac = len(faculties)
    n_cou = len(courses)

    if n_fac == 0 or n_cou == 0:
        return np.zeros((n_fac, n_cou), dtype=np.float32)

    # 1. Vectorized Tag Match Matrix (N x M)
    tag_matrix = np.zeros((n_fac, n_cou), dtype=np.float32)
    faculty_skills = [extract_faculty_skills(f) for f in faculties]

    for j, c in enumerate(courses):
        req_tags, _ = extract_course_requirements(c)
        if not req_tags:
            tag_matrix[:, j] = 1.0
        else:
            norm_tags = [_normalize_tag(t) for t in req_tags]
            for i, skills in enumerate(faculty_skills):
                prof_sum = sum(skills.get(t, 0) / 5.0 for t in norm_tags)
                tag_matrix[i, j] = prof_sum / len(norm_tags)

    # 2. Vectorized TF-IDF Cosine Similarity Matrix (N x M)
    fac_texts = [extract_faculty_text(f) for f in faculties]
    cou_texts = [extract_course_text(c) for c in courses]
    full_corpus = fac_texts + cou_texts

    tfidf_matrix = np.zeros((n_fac, n_cou), dtype=np.float32)
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r"(?u)\b\w+\b",
        )
        vectorizer.fit(full_corpus)
        F = vectorizer.transform(fac_texts)  # (N, V)
        C = vectorizer.transform(cou_texts)  # (M, V)
        # Cosine similarity is direct dot product since L2-normalized
        sim_sparse = F @ C.T
        tfidf_matrix = sim_sparse.toarray().astype(np.float32)
    except ValueError:
        # Empty vocabulary or stopword-only corpus
        pass

    tfidf_matrix = np.clip(tfidf_matrix, 0.0, 1.0)

    # 3. Vectorized Past-Teaching Matrix (N x M)
    if past_teaching_matrix is not None:
        if past_teaching_cap > 0:
            past_matrix = np.clip(
                past_teaching_matrix.astype(np.float32) / float(past_teaching_cap),
                0.0,
                1.0,
            )
        else:
            past_matrix = (past_teaching_matrix > 0).astype(np.float32)
    else:
        past_matrix = np.zeros((n_fac, n_cou), dtype=np.float32)
        for i, f in enumerate(faculties):
            for j, c in enumerate(courses):
                count = extract_times_taught(f, c)
                if past_teaching_cap > 0:
                    past_matrix[i, j] = min(1.0, count / float(past_teaching_cap))
                else:
                    past_matrix[i, j] = 1.0 if count > 0 else 0.0

    # Aggregate weighted components
    fit_matrix = (
        WEIGHT_TAG * tag_matrix
        + WEIGHT_TFIDF * tfidf_matrix
        + WEIGHT_PAST_TEACHING * past_matrix
    )
    return np.clip(fit_matrix, 0.0, 1.0).astype(np.float32)


def compute_hc01_mask(
    faculties: list[Any],
    courses: list[Any],
) -> np.ndarray:
    """Compute boolean eligibility mask of shape (N_faculty, M_course) for HC-01.

    A cell (i, j) is True if and only if faculty i satisfies the minimum proficiency
    threshold on all required syllabus tags of course j.

    Returns:
        np.ndarray of shape (N, M) with dtype bool.
    """
    n_fac = len(faculties)
    n_cou = len(courses)
    mask = np.ones((n_fac, n_cou), dtype=bool)

    faculty_skills = [extract_faculty_skills(f) for f in faculties]

    for j, c in enumerate(courses):
        req_tags, min_prof = extract_course_requirements(c)
        if not req_tags:
            continue
        norm_tags = [_normalize_tag(t) for t in req_tags]
        for i, skills in enumerate(faculty_skills):
            eligible = all(skills.get(t, 0) >= min_prof for t in norm_tags)
            mask[i, j] = eligible

    return mask
