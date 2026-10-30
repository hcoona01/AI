"""Unit tests with hand-computed examples for faculty expertise fit scoring."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in [str(REPO_ROOT), str(REPO_ROOT / "backend"), str(REPO_ROOT / "ml")]:
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import pytest

from app.schemas.common import CourseLevel, FacultyRank
from app.schemas.course import Course
from app.schemas.faculty import Faculty, FacultyExpertise
from ml.fit.scoring import (
    FitResult,
    check_hc01,
    compute_fit_matrix,
    compute_hc01_mask,
    fit,
)


class TestHandComputedScoring:
    """Verify fit score and breakdown against exact hand-calculated values."""

    def test_hand_computed_exact_example(self) -> None:
        """Hand-computed breakdown verification:

        Course required tags: ['Algorithms', 'Databases'], min_proficiency=3.
        Faculty skills: Algorithms: 4, Databases: 5.
        Course text: 'CS101 Intro Intro to algorithms and databases Algorithms Databases'
        Faculty text: 'Dr. Turing Professor Algorithms Databases'

        1. Tag match:
           tag1 = 4 / 5.0 = 0.80
           tag2 = 5 / 5.0 = 1.00
           tag_score = (0.80 + 1.00) / 2 = 0.90
           weighted_tag = 0.60 * 0.90 = 0.54

        2. Past teaching:
           taught = 2, cap = 2
           past_score = min(1.0, 2 / 2.0) = 1.00
           weighted_past = 0.15 * 1.00 = 0.15

        3. TF-IDF cosine:
           Computed dynamically, non-negative in [0, 1].
           Total expected = 0.54 + 0.25 * tfidf_score + 0.15 = 0.69 + 0.25 * tfidf_score.
        """
        course = {
            "id": "c-test-1",
            "code": "CS101",
            "title": "Intro",
            "description": "Intro to algorithms and databases",
            "required_tags": ["Algorithms", "Databases"],
            "min_proficiency": 3,
        }
        faculty = {
            "id": "f-test-1",
            "name": "Dr. Turing",
            "rank": "Professor",
            "expertise": [
                {"tag": "Algorithms", "proficiency": 4},
                {"tag": "Databases", "proficiency": 5},
            ],
            "past_courses": ["c-test-1", "c-test-1"],  # taught twice
        }

        result = fit(faculty, course, past_teaching_cap=2)

        assert isinstance(result, FitResult)
        assert result.breakdown["tag_score"] == 0.90
        assert result.breakdown["tag_weighted"] == 0.54
        assert result.breakdown["past_teaching_score"] == 1.00
        assert result.breakdown["past_teaching_weighted"] == 0.15
        assert result.breakdown["times_taught"] == 2

        tfidf_score = result.breakdown["tfidf_score"]
        assert 0.0 <= tfidf_score <= 1.0
        expected_total = round(0.54 + 0.25 * tfidf_score + 0.15, 4)
        assert result.score == expected_total
        assert result.breakdown["total_score"] == expected_total

        # HC-01 passes because 4 >= 3 and 5 >= 3
        assert result.is_eligible is True
        assert result.breakdown["hc01_eligible"] is True
        assert len(result.breakdown["hc01_violations"]) == 0

    def test_past_teaching_capping(self) -> None:
        """Verify past teaching bonus scales and caps properly."""
        course = {"id": "c-100", "code": "CS100", "title": "Test", "description": "", "required_tags": []}

        # 0 times taught -> 0.0
        f0 = {"id": "f0", "name": "F0", "expertise": [], "past_courses": []}
        r0 = fit(f0, course, past_teaching_cap=2)
        assert r0.breakdown["past_teaching_score"] == 0.0
        assert r0.breakdown["past_teaching_weighted"] == 0.0

        # 1 time taught (cap=2) -> 0.50
        f1 = {"id": "f1", "name": "F1", "expertise": [], "past_courses": ["c-100"]}
        r1 = fit(f1, course, past_teaching_cap=2)
        assert r1.breakdown["past_teaching_score"] == 0.50
        assert r1.breakdown["past_teaching_weighted"] == 0.075

        # 2 times taught (cap=2) -> 1.00
        f2 = {"id": "f2", "name": "F2", "expertise": [], "past_courses": ["c-100", "c-100"]}
        r2 = fit(f2, course, past_teaching_cap=2)
        assert r2.breakdown["past_teaching_score"] == 1.00
        assert r2.breakdown["past_teaching_weighted"] == 0.15

        # 5 times taught (cap=2) -> 1.00 (capped)
        f5 = {"id": "f5", "name": "F5", "expertise": [], "past_courses": ["c-100"] * 5}
        r5 = fit(f5, course, past_teaching_cap=2)
        assert r5.breakdown["past_teaching_score"] == 1.00
        assert r5.breakdown["past_teaching_weighted"] == 0.15


class TestHC01Independence:
    """Verify HC-01 is a hard filter and does not distort the continuous fit score."""

    def test_deficient_proficiency_fails_hc01_but_retains_score(self) -> None:
        """Faculty has proficiency 2 on required tag, but min_proficiency is 4.

        Tag score = 2 / 5.0 = 0.40.
        HC-01 must be False, while fit score remains non-zero.
        """
        course = {
            "id": "c-sec",
            "code": "CS400",
            "title": "Security",
            "description": "Network security",
            "required_tags": ["Cybersecurity"],
            "min_proficiency": 4,
        }
        faculty = {
            "id": "f-novice",
            "name": "Dr. Novice",
            "expertise": [{"tag": "Cybersecurity", "proficiency": 2}],
            "past_courses": [],
        }

        is_eligible, violations = check_hc01(faculty, course)
        assert is_eligible is False
        assert len(violations) == 1
        assert "HC-01" in violations[0]
        assert "below CS400 required min_proficiency 4" in violations[0]

        res = fit(faculty, course)
        assert res.is_eligible is False
        assert res.breakdown["hc01_eligible"] is False
        assert res.breakdown["tag_score"] == 0.40  # 2 / 5
        assert res.breakdown["tag_weighted"] == 0.24  # 0.60 * 0.40
        assert res.score > 0.20  # Score is computed normally

    def test_missing_tag_fails_hc01_and_gets_zero_proficiency(self) -> None:
        course = {
            "id": "c-ai",
            "code": "CS450",
            "title": "AI",
            "description": "Deep learning and robotics",
            "required_tags": ["Robotics", "Deep Learning"],
            "min_proficiency": 2,
        }
        faculty = {
            "id": "f-ai",
            "name": "Dr. AI",
            "expertise": [{"tag": "Robotics", "proficiency": 4}],
            # Missing Deep Learning completely
        }

        is_eligible, violations = check_hc01(faculty, course)
        assert is_eligible is False
        assert len(violations) == 1
        assert "Deep Learning" in violations[0]

        res = fit(faculty, course)
        # Robotics = 4/5 = 0.8, Deep Learning = 0/5 = 0.0 -> average = 0.40
        assert res.breakdown["tag_score"] == 0.40
        assert res.breakdown["tag_weighted"] == 0.24


class TestPydanticSchemaCompatibility:
    """Verify scoring seamlessly processes Pydantic v2 domain models."""

    def test_pydantic_models_scoring(self) -> None:
        faculty = Faculty(
            id="f-01",
            name="Dr. Alan Turing",
            email="alan.turing@university.edu",
            rank=FacultyRank.PROFESSOR,
            expertise=[
                FacultyExpertise(tag="Algorithms", proficiency=5),
                FacultyExpertise(tag="Theory of Computation", proficiency=4),
            ],
            max_weekly_load_hours=12.0,
            max_courses=3,
            min_courses=1,
            max_preparations=2,
            unavailable_slots=[],
            leave_terms=[],
            preferred_course_ids=["c-cs101"],
        )

        course = Course(
            id="c-cs101",
            code="CS101",
            title="Algorithms and Computation",
            description="Foundations of algorithmic complexity and Turing machines.",
            credits=4,
            contact_hours=4.0,
            level=CourseLevel.UNDERGRADUATE,
            required_tags=["Algorithms", "Theory of Computation"],
            min_proficiency=3,
            is_lab=False,
            required_resource_ids=[],
        )

        res = fit(faculty, course, past_teaching_count=1, past_teaching_cap=2)
        assert isinstance(res, FitResult)
        assert float(res) > 0.50
        # Tag match: (5/5 + 4/5) / 2 = 0.90 -> 0.60 * 0.90 = 0.54
        assert res.breakdown["tag_score"] == 0.90
        assert res.breakdown["tag_weighted"] == 0.54
        assert res.is_eligible is True


class TestVectorizedMatrix:
    """Verify full faculty x course matrix generation in float32."""

    def test_vectorized_matrix_shape_and_bounds(self) -> None:
        faculties = [
            {
                "id": f"f-{i}",
                "name": f"Faculty {i}",
                "expertise": [{"tag": "Algorithms", "proficiency": (i % 5) + 1}],
                "past_courses": [f"c-{i % 3}"],
            }
            for i in range(10)
        ]

        courses = [
            {
                "id": f"c-{j}",
                "code": f"CS{100 + j}",
                "title": f"Course {j}",
                "description": f"Curriculum for course {j} involving algorithms and software.",
                "required_tags": ["Algorithms"],
                "min_proficiency": 2,
            }
            for j in range(5)
        ]

        matrix = compute_fit_matrix(faculties, courses)

        assert matrix.shape == (10, 5)
        assert matrix.dtype == np.float32
        assert np.all(matrix >= 0.0)
        assert np.all(matrix <= 1.0)

    def test_vectorized_hc01_mask(self) -> None:
        faculties = [
            {"id": "f0", "name": "F0", "expertise": [{"tag": "Math", "proficiency": 1}]},
            {"id": "f1", "name": "F1", "expertise": [{"tag": "Math", "proficiency": 5}]},
        ]
        courses = [
            {"id": "c0", "code": "M1", "title": "M1", "required_tags": ["Math"], "min_proficiency": 3},
            {"id": "c1", "code": "M2", "title": "M2", "required_tags": [], "min_proficiency": 1},
        ]

        mask = compute_hc01_mask(faculties, courses)
        assert mask.shape == (2, 2)
        assert mask.dtype == bool
        # f0 (prof 1) vs c0 (req 3) -> False
        assert mask[0, 0] is np.False_ or mask[0, 0] == False
        # f0 vs c1 (no req) -> True
        assert mask[0, 1] == True
        # f1 (prof 5) vs c0 (req 3) -> True
        assert mask[1, 0] == True
        # f1 vs c1 -> True
        assert mask[1, 1] == True


class TestEdgeCases:
    """Validate behavior on empty text, disjoint vocabulary, and zero inputs."""

    def test_disjoint_vocabulary_gives_zero_tfidf(self) -> None:
        course = {
            "id": "c-bio",
            "code": "BIO101",
            "title": "Cell Biology",
            "description": "Photosynthesis mitochondria ribosome membrane",
            "required_tags": ["Biology"],
            "min_proficiency": 1,
        }
        faculty = {
            "id": "f-cs",
            "name": "Dr. CS",
            "expertise": [{"tag": "Compilers", "proficiency": 5}],
            "past_courses": [],
        }

        res = fit(faculty, course)
        assert res.breakdown["tfidf_score"] == 0.0
        assert res.breakdown["tfidf_weighted"] == 0.0

    def test_course_without_required_tags_gives_perfect_tag_match(self) -> None:
        course = {
            "id": "c-sem",
            "code": "SEM500",
            "title": "Graduate Seminar",
            "description": "Open research discussion seminar",
            "required_tags": [],
            "min_proficiency": 1,
        }
        faculty = {"id": "f-any", "name": "Dr. Any", "expertise": []}

        res = fit(faculty, course)
        assert res.breakdown["tag_score"] == 1.00
        assert res.breakdown["tag_weighted"] == 0.60
        assert res.is_eligible is True
