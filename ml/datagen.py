"""Synthetic data generation pipeline for University Faculty Workload Balancing System.

Generates reproducible, deterministic seed datasets and named boundary evaluation
fixtures using seeded pseudo-random number generators. All outputs conform strictly
to Pydantic v2 schemas and keep file sizes compact (< 1 MB per file).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

# Ensure backend package is on sys.path for schema imports
ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.schemas.assignment import Assignment, AssignmentSource
from app.schemas.common import (
    CourseLevel,
    DayOfWeek,
    FacultyRank,
    ResourceType,
    UserRole,
)
from app.schemas.course import Course
from app.schemas.faculty import Faculty, FacultyExpertise
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.user import User

SEED_DIR = ROOT / "data" / "seed"
FIXTURES_DIR = ROOT / "data" / "fixtures"

TERMS = ["Fall 2026", "Spring 2027", "Summer 2027"]

DAYS: list[DayOfWeek] = [
    DayOfWeek.MON,
    DayOfWeek.TUE,
    DayOfWeek.WED,
    DayOfWeek.THU,
    DayOfWeek.FRI,
]

SLOT_HOURS: list[tuple[str, str]] = [
    ("09:00", "10:30"),
    ("10:30", "12:00"),
    ("13:00", "14:30"),
    ("14:30", "16:00"),
]

DOMAIN_TAGS: list[str] = [
    "Algorithms",
    "Data Structures",
    "Computer Systems",
    "Operating Systems",
    "Database Systems",
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "Computer Networks",
    "Cybersecurity",
    "Software Engineering",
    "Web Development",
    "Cloud Computing",
    "Computer Architecture",
    "Programming Languages",
    "Theory of Computation",
    "Human-Computer Interaction",
    "Distributed Systems",
    "Data Science",
    "Robotics",
]


def generate_timeslots() -> list[TimeSlot]:
    """Generate weekly time slot grid (20 standard slots)."""
    slots: list[TimeSlot] = []
    for day in DAYS:
        for start, end in SLOT_HOURS:
            slot_id = f"TS-{day.value}-{start.replace(':', '')}"
            slots.append(
                TimeSlot(
                    id=slot_id,
                    day=day,
                    start=start,
                    end=end,
                )
            )
    return slots


def generate_resources() -> list[Resource]:
    """Generate 10 physical campus facilities (6 lecture rooms and 4 specialized labs)."""
    return [
        Resource(
            id="ROOM-101", type=ResourceType.ROOM, capacity=60, unavailable_slots=[]
        ),
        Resource(
            id="ROOM-102", type=ResourceType.ROOM, capacity=45, unavailable_slots=[]
        ),
        Resource(
            id="ROOM-103", type=ResourceType.ROOM, capacity=80, unavailable_slots=[]
        ),
        Resource(
            id="ROOM-201", type=ResourceType.ROOM, capacity=50, unavailable_slots=[]
        ),
        Resource(
            id="ROOM-202", type=ResourceType.ROOM, capacity=100, unavailable_slots=[]
        ),
        Resource(
            id="AUD-MAIN", type=ResourceType.ROOM, capacity=150, unavailable_slots=[]
        ),
        Resource(
            id="LAB-AI-1", type=ResourceType.LAB, capacity=35, unavailable_slots=[]
        ),
        Resource(
            id="LAB-SYS-2", type=ResourceType.LAB, capacity=30, unavailable_slots=[]
        ),
        Resource(
            id="LAB-NET-3", type=ResourceType.LAB, capacity=40, unavailable_slots=[]
        ),
        Resource(
            id="LAB-MEDIA-4", type=ResourceType.LAB, capacity=30, unavailable_slots=[]
        ),
    ]


def generate_courses(rng: random.Random) -> list[Course]:
    """Generate ~40 undergraduate and graduate courses across computing disciplines."""
    catalog_meta = [
        # Intro
        (
            "CS101",
            "Introduction to Computer Science",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Algorithms", "Programming Languages"],
            2,
            False,
            ["ROOM-202"],
        ),
        (
            "CS102",
            "Data Structures Fundamentals",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Data Structures", "Algorithms"],
            2,
            False,
            ["ROOM-201"],
        ),
        (
            "CS105",
            "Discrete Mathematics for Computing",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Theory of Computation"],
            2,
            False,
            ["ROOM-101"],
        ),
        (
            "CS108",
            "Introduction to Web Development",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Web Development"],
            2,
            False,
            ["ROOM-102"],
        ),
        (
            "CS150",
            "Python Programming Workshop",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Programming Languages", "Data Science"],
            2,
            False,
            ["ROOM-103"],
        ),
        # Core Systems & Theory
        (
            "CS201",
            "Computer Systems & Assembly",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Computer Systems", "Computer Architecture"],
            3,
            False,
            ["ROOM-101"],
        ),
        (
            "CS210",
            "Operating Systems Internals",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Operating Systems", "Computer Systems"],
            3,
            True,
            ["LAB-SYS-2"],
        ),
        (
            "CS220",
            "Database Management Systems",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Database Systems"],
            3,
            False,
            ["ROOM-102"],
        ),
        (
            "CS230",
            "Design & Analysis of Algorithms",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Algorithms", "Theory of Computation"],
            3,
            False,
            ["ROOM-103"],
        ),
        (
            "CS240",
            "Computer Networks & Protocols",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Computer Networks"],
            3,
            True,
            ["LAB-NET-3"],
        ),
        (
            "CS250",
            "Software Engineering Principles",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Software Engineering"],
            2,
            False,
            ["ROOM-201"],
        ),
        (
            "CS260",
            "Automata & Formal Languages",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Theory of Computation"],
            3,
            False,
            ["ROOM-101"],
        ),
        # Advanced & Applied
        (
            "CS301",
            "Artificial Intelligence Concepts",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Artificial Intelligence", "Algorithms"],
            3,
            False,
            ["ROOM-202"],
        ),
        (
            "CS310",
            "Applied Machine Learning",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Machine Learning", "Data Science"],
            3,
            True,
            ["LAB-AI-1"],
        ),
        (
            "CS315",
            "Deep Learning Foundations",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Deep Learning", "Machine Learning"],
            4,
            True,
            ["LAB-AI-1"],
        ),
        (
            "CS320",
            "Cybersecurity & Cryptography",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Cybersecurity", "Computer Networks"],
            3,
            False,
            ["ROOM-102"],
        ),
        (
            "CS330",
            "Cloud Infrastructure & DevOps",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Cloud Computing", "Distributed Systems"],
            3,
            False,
            ["ROOM-103"],
        ),
        (
            "CS340",
            "Distributed Systems Engineering",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Distributed Systems", "Operating Systems"],
            4,
            True,
            ["LAB-SYS-2"],
        ),
        (
            "CS350",
            "Human-Computer Interaction",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Human-Computer Interaction"],
            2,
            False,
            ["ROOM-101"],
        ),
        (
            "CS360",
            "Computer Graphics & Media",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Human-Computer Interaction"],
            3,
            True,
            ["LAB-MEDIA-4"],
        ),
        (
            "CS370",
            "Robotics Systems & Control",
            4,
            4.0,
            CourseLevel.UNDERGRADUATE,
            ["Robotics", "Artificial Intelligence"],
            3,
            True,
            ["LAB-AI-1"],
        ),
        (
            "CS380",
            "Compilers & Language Design",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Programming Languages", "Computer Architecture"],
            4,
            False,
            ["ROOM-102"],
        ),
        # Graduate
        (
            "CS501",
            "Advanced Algorithm Design",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Algorithms", "Theory of Computation"],
            4,
            False,
            ["ROOM-103"],
        ),
        (
            "CS510",
            "Advanced Machine Learning Theory",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Machine Learning", "Algorithms"],
            4,
            False,
            ["ROOM-201"],
        ),
        (
            "CS520",
            "Statistical Natural Language Processing",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Artificial Intelligence", "Machine Learning"],
            4,
            True,
            ["LAB-AI-1"],
        ),
        (
            "CS530",
            "Advanced Distributed Systems",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Distributed Systems", "Computer Networks"],
            4,
            True,
            ["LAB-SYS-2"],
        ),
        (
            "CS540",
            "Network Security Architecture",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Cybersecurity", "Computer Networks"],
            4,
            True,
            ["LAB-NET-3"],
        ),
        (
            "CS550",
            "Scalable Database Architectures",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Database Systems", "Cloud Computing"],
            4,
            False,
            ["ROOM-102"],
        ),
        (
            "CS560",
            "Robotics Perception & SLAM",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Robotics", "Deep Learning"],
            4,
            True,
            ["LAB-AI-1"],
        ),
        (
            "CS570",
            "Advanced Computer Architecture",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Computer Architecture", "Computer Systems"],
            4,
            False,
            ["ROOM-101"],
        ),
        (
            "CS580",
            "Quantum Computing Foundations",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Theory of Computation", "Algorithms"],
            4,
            False,
            ["ROOM-103"],
        ),
        (
            "CS590",
            "Graduate Research Seminar",
            1,
            1.0,
            CourseLevel.GRADUATE,
            ["Algorithms"],
            2,
            False,
            ["ROOM-101"],
        ),
        # Data Science & Software Eng
        (
            "DS101",
            "Introduction to Data Science",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Data Science", "Data Structures"],
            2,
            False,
            ["ROOM-202"],
        ),
        (
            "DS201",
            "Statistical Modeling for Data Science",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Data Science", "Machine Learning"],
            3,
            False,
            ["ROOM-201"],
        ),
        (
            "DS301",
            "Big Data Analytics Pipeline",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Data Science", "Cloud Computing"],
            3,
            True,
            ["LAB-AI-1"],
        ),
        (
            "DS501",
            "Advanced Big Data Architectures",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Data Science", "Distributed Systems"],
            4,
            False,
            ["ROOM-102"],
        ),
        (
            "SE101",
            "Software Construction & Tools",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Software Engineering", "Programming Languages"],
            2,
            False,
            ["ROOM-103"],
        ),
        (
            "SE201",
            "Object-Oriented Design Patterns",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Software Engineering"],
            2,
            False,
            ["ROOM-101"],
        ),
        (
            "SE301",
            "Software Testing & Verification",
            3,
            3.0,
            CourseLevel.UNDERGRADUATE,
            ["Software Engineering"],
            3,
            False,
            ["ROOM-102"],
        ),
        (
            "SE501",
            "Advanced Software Architecture",
            3,
            3.0,
            CourseLevel.GRADUATE,
            ["Software Engineering", "Distributed Systems"],
            4,
            False,
            ["ROOM-201"],
        ),
    ]

    courses: list[Course] = []
    for (
        code,
        title,
        credits,
        hours,
        level,
        tags,
        min_prof,
        is_lab,
        res_ids,
    ) in catalog_meta:
        courses.append(
            Course(
                id=f"c-{code.lower()}",
                code=code,
                title=title,
                description=f"Comprehensive curriculum for {title}.",
                credits=credits,
                contact_hours=hours,
                level=level,
                required_tags=tags,
                min_proficiency=min_prof,
                is_lab=is_lab,
                required_resource_ids=res_ids,
            )
        )
    return courses


def generate_faculty(rng: random.Random, courses: list[Course]) -> list[Faculty]:
    """Generate 25 diverse faculty members across appointment ranks with realistic skills."""
    names = [
        (
            "Alan Turing",
            FacultyRank.PROFESSOR,
            ["Algorithms", "Theory of Computation", "Artificial Intelligence"],
        ),
        (
            "Ada Lovelace",
            FacultyRank.PROFESSOR,
            ["Algorithms", "Programming Languages", "Data Structures"],
        ),
        (
            "Grace Hopper",
            FacultyRank.PROFESSOR,
            ["Programming Languages", "Operating Systems", "Software Engineering"],
        ),
        (
            "Donald Knuth",
            FacultyRank.PROFESSOR,
            ["Algorithms", "Data Structures", "Theory of Computation"],
        ),
        (
            "Barbara Liskov",
            FacultyRank.PROFESSOR,
            ["Distributed Systems", "Software Engineering", "Operating Systems"],
        ),
        (
            "Edsger Dijkstra",
            FacultyRank.PROFESSOR,
            ["Algorithms", "Operating Systems", "Theory of Computation"],
        ),
        (
            "Shafi Goldwasser",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Cybersecurity", "Theory of Computation", "Algorithms"],
        ),
        (
            "Leslie Lamport",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Distributed Systems", "Algorithms", "Operating Systems"],
        ),
        (
            "Judea Pearl",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Artificial Intelligence", "Machine Learning", "Data Science"],
        ),
        (
            "Geoffrey Hinton",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Deep Learning", "Machine Learning", "Artificial Intelligence"],
        ),
        (
            "Yann LeCun",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Deep Learning", "Computer Vision", "Machine Learning"],
        ),
        (
            "Fei-Fei Li",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Machine Learning", "Artificial Intelligence", "Computer Vision"],
        ),
        (
            "Andrew Ng",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Machine Learning", "Deep Learning", "Data Science"],
        ),
        (
            "Timnit Gebru",
            FacultyRank.ASSOCIATE_PROFESSOR,
            ["Artificial Intelligence", "Human-Computer Interaction", "Data Science"],
        ),
        (
            "Yoshua Bengio",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Deep Learning", "Machine Learning", "Artificial Intelligence"],
        ),
        (
            "Silvio Micali",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Cybersecurity", "Algorithms", "Theory of Computation"],
        ),
        (
            "Radia Perlman",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Computer Networks", "Cybersecurity", "Distributed Systems"],
        ),
        (
            "Ken Thompson",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Operating Systems", "Computer Systems", "Programming Languages"],
        ),
        (
            "Dennis Ritchie",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Computer Systems", "Operating Systems", "Programming Languages"],
        ),
        (
            "Frances Allen",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Programming Languages", "Computer Architecture", "Compilers"],
        ),
        (
            "Margaret Hamilton",
            FacultyRank.ASSISTANT_PROFESSOR,
            ["Software Engineering", "Distributed Systems", "Computer Systems"],
        ),
        (
            "Vint Cerf",
            FacultyRank.LECTURER,
            ["Computer Networks", "Web Development", "Cloud Computing"],
        ),
        (
            "Tim Berners-Lee",
            FacultyRank.LECTURER,
            ["Web Development", "Computer Networks", "Database Systems"],
        ),
        (
            "John McCarthy",
            FacultyRank.LECTURER,
            ["Programming Languages", "Artificial Intelligence", "Robotics"],
        ),
        (
            "Claude Shannon",
            FacultyRank.LECTURER,
            ["Computer Networks", "Algorithms", "Cybersecurity"],
        ),
    ]

    course_ids = [c.id for c in courses]
    faculty_list: list[Faculty] = []

    for i, (name, rank, core_tags) in enumerate(names):
        fac_id = f"f-{i+1:02d}"
        email = f"{name.lower().replace(' ', '.')}@university.edu"

        # Determine load hours and course limits based on rank
        if rank == FacultyRank.PROFESSOR:
            max_load, max_courses, min_courses, max_preps = 9.0, 3, 1, 2
        elif (
            rank == FacultyRank.ASSOCIATE_PROFESSOR
            or rank == FacultyRank.ASSISTANT_PROFESSOR
        ):
            max_load, max_courses, min_courses, max_preps = 12.0, 3, 2, 2
        else:  # LECTURER
            max_load, max_courses, min_courses, max_preps = 15.0, 4, 3, 3

        # Build expertise tags: 3 core tags at proficiency 4-5, 3 secondary tags at 2-3
        expertise: list[FacultyExpertise] = []
        for tag in core_tags:
            expertise.append(FacultyExpertise(tag=tag, proficiency=rng.choice([4, 5])))

        # Add 3 secondary random tags
        remaining_tags = [t for t in DOMAIN_TAGS if t not in core_tags]
        for tag in rng.sample(remaining_tags, 3):
            expertise.append(FacultyExpertise(tag=tag, proficiency=rng.choice([2, 3])))

        # Preferences (2 to 4 preferred courses)
        preferred_courses = rng.sample(course_ids, rng.randint(2, 4))

        # Rare sabbatical leave (approx 1 faculty on leave)
        leave_terms: list[str] = []
        if i == 5:  # e.g., Dijkstra on sabbatical in Spring 2027
            leave_terms.append("Spring 2027")

        # Unavailable slots (1 or 2 slots)
        unavailable_slots: list[str] = (
            [f"TS-FRI-{rng.choice(['1300', '1430'])}"] if rng.random() < 0.4 else []
        )

        faculty_list.append(
            Faculty(
                id=fac_id,
                name=f"Dr. {name}",
                email=email,
                rank=rank,
                expertise=expertise,
                max_weekly_load_hours=max_load,
                max_courses=max_courses,
                min_courses=min_courses,
                max_preparations=max_preps,
                unavailable_slots=unavailable_slots,
                leave_terms=leave_terms,
                preferred_course_ids=preferred_courses,
            )
        )

    return faculty_list


def generate_users(faculty: list[Faculty]) -> list[User]:
    """Generate User accounts for authentication and RBAC."""
    users: list[User] = [
        User(id="u-admin-1", email="admin@university.edu", role=UserRole.ADMIN),
        User(id="u-chair-2", email="chair@university.edu", role=UserRole.ADMIN),
    ]
    for f in faculty:
        users.append(
            User(
                id=f"u-{f.id}",
                email=f.email,
                role=UserRole.FACULTY,
                faculty_id=f.id,
            )
        )
    return users


def generate_sections(
    rng: random.Random,
    courses: list[Course],
    timeslots: list[TimeSlot],
    terms: list[str],
) -> list[Section]:
    """Generate ~60 course sections across academic terms with realistic quantile estimates."""
    sections: list[Section] = []
    slot_ids = [ts.id for ts in timeslots]

    # Target: ~25 in Fall 2026, ~25 in Spring 2027, ~10 in Summer 2027
    term_quotas = {"Fall 2026": 25, "Spring 2027": 25, "Summer 2027": 10}

    for term, count in term_quotas.items():
        # Pick courses to offer in this term
        selected_courses = rng.sample(courses, min(count, len(courses)))
        for i, course in enumerate(selected_courses):
            sec_idx = i + 1
            sec_id = f"SEC-{term[:2].upper()}{term[-2:]}-{course.code}-{sec_idx:02d}"

            # Capacity and expected sizes
            cap = (
                100
                if course.level == CourseLevel.UNDERGRADUATE and "101" in course.code
                else rng.choice([40, 50, 60])
            )
            expected = rng.randint(int(cap * 0.5), int(cap * 0.9))

            # Quantile demand forecasts: P10 <= P50 <= P90
            p10 = max(5, int(expected * 0.75))
            p50 = expected
            p90 = min(cap, int(expected * 1.25))
            p90 = max(p90, p50)

            time_slot = rng.choice(slot_ids)

            sections.append(
                Section(
                    id=sec_id,
                    course_id=course.id,
                    term=term,
                    section_cap=cap,
                    expected_size=expected,
                    size_p10=p10,
                    size_p50=p50,
                    size_p90=p90,
                    time_slot_id=time_slot,
                )
            )

    return sections


def generate_enrollment_history(
    rng: random.Random, courses: list[Course]
) -> list[dict[str, Any]]:
    """Generate 3 years (9 terms) of historical course section enrollments.

    Includes base levels, long-term trends, term seasonality, random noise, and occasional shocks.
    """
    history: list[dict[str, Any]] = []
    historical_terms = [
        ("2023-Fall", "Fall", 2023, 1),
        ("2024-Spring", "Spring", 2024, 2),
        ("2024-Summer", "Summer", 2024, 3),
        ("2024-Fall", "Fall", 2024, 4),
        ("2025-Spring", "Spring", 2025, 5),
        ("2025-Summer", "Summer", 2025, 6),
        ("2025-Fall", "Fall", 2025, 7),
        ("2026-Spring", "Spring", 2026, 8),
        ("2026-Summer", "Summer", 2026, 9),
    ]

    for course in courses:
        # Base demand based on course level and code
        base_demand = (
            85.0
            if "101" in course.code
            else (55.0 if course.level == CourseLevel.UNDERGRADUATE else 25.0)
        )
        # Growth trend per term (+1% to +4% for AI/CS)
        trend_rate = (
            0.03
            if any(
                tag in ["Artificial Intelligence", "Machine Learning", "Python"]
                for tag in course.required_tags
            )
            else 0.01
        )

        for term_label, season, year, term_idx in historical_terms:
            # Seasonality multiplier
            season_mult = (
                1.20 if season == "Fall" else (1.00 if season == "Spring" else 0.55)
            )

            # Trend component
            trend_mult = 1.0 + (trend_rate * (term_idx - 1))

            # Noise component (~10% Gaussian)
            noise = rng.gauss(0, 0.08)

            # Occasional shocks (e.g. AI curriculum boom in term 4)
            shock = 0.0
            if term_idx == 4 and "Machine Learning" in course.required_tags:
                shock = 0.35
            elif term_idx == 6 and season == "Summer":
                shock = -0.10

            enrolled = int(
                max(5.0, base_demand * season_mult * trend_mult * (1.0 + noise + shock))
            )
            section_count = max(1, math.ceil(enrolled / 45.0))
            avg_size = round(enrolled / section_count, 1)

            history.append(
                {
                    "course_id": course.id,
                    "course_code": course.code,
                    "term": term_label,
                    "season": season,
                    "year": year,
                    "term_index": term_idx,
                    "credits": course.credits,
                    "level": course.level.value,
                    "is_lab": course.is_lab,
                    "enrolled_students": enrolled,
                    "section_count": section_count,
                    "avg_section_size": avg_size,
                }
            )

    return history


# ============================================================================
# NAMED EVALUATION FIXTURES GENERATORS
# ============================================================================


def generate_fixtures(
    base_faculty: list[Faculty],
    base_courses: list[Course],
    base_sections: list[Section],
    base_resources: list[Resource],
    base_timeslots: list[TimeSlot],
    rng: random.Random,
) -> dict[str, dict[str, Any]]:
    """Generate the 10 named evaluation scenario fixtures with explicit expected outcomes."""
    fixtures: dict[str, dict[str, Any]] = {}

    # 1. balanced_baseline
    # Fully feasible: 5 faculty, 5 courses, 5 sections with clean 1-to-1 matching
    f_sub = base_faculty[:5]
    c_sub = base_courses[:5]
    s_sub = base_sections[:5]
    # Create valid assignments
    b_assignments: list[Assignment] = []
    for i in range(5):
        s_sub[i].course_id = c_sub[i].id
        s_sub[i].time_slot_id = base_timeslots[i].id
        # Ensure faculty has the required skills
        for tag in c_sub[i].required_tags:
            if not any(e.tag == tag for e in f_sub[i].expertise):
                f_sub[i].expertise.append(FacultyExpertise(tag=tag, proficiency=5))
        b_assignments.append(
            Assignment(
                id=f"asgn-base-{i}",
                section_id=s_sub[i].id,
                faculty_id=f_sub[i].id,
                source=AssignmentSource.SOLVER,
                fit_score=0.92,
                run_id="run-baseline",
            )
        )

    fixtures["balanced_baseline"] = {
        "name": "balanced_baseline",
        "expected_outcome": {
            "feasible": True,
            "reason": "Standard balanced academic scenario with adequate faculty capacity, clean expertise matches, and non-conflicting time slots.",
        },
        "scenario": {
            "faculty": [f.model_dump(mode="json") for f in f_sub],
            "courses": [c.model_dump(mode="json") for c in c_sub],
            "sections": [s.model_dump(mode="json") for s in s_sub],
            "resources": [r.model_dump(mode="json") for r in base_resources],
            "timeslots": [ts.model_dump(mode="json") for ts in base_timeslots],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in b_assignments],
    }

    # 2. tight_capacity (total demand ~98% of total capacity)
    # Total faculty load: 3 faculty * 12h = 36h. Demand = 35h (97.2%). Feasible but very tight.
    f_tight = [
        Faculty(
            id=f"f-tight-{i}",
            name=f"Dr. Tight {i}",
            email=f"tight{i}@univ.edu",
            rank=FacultyRank.ASSOCIATE_PROFESSOR,
            expertise=[FacultyExpertise(tag="Algorithms", proficiency=5)],
            max_weekly_load_hours=12.0,
            max_courses=3,
            min_courses=1,
            max_preparations=2,
        )
        for i in range(3)
    ]
    # 9 sections of 4.0h each = 36.0h (100% capacity) -> let's make 8 sections of 4.0h + 1 of 3.0h = 35.0h / 36.0h = 97.2%
    c_tight_4 = Course(
        id="c-tight-4",
        code="CS400",
        title="Tight 4h Course",
        credits=4,
        contact_hours=4.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=["Algorithms"],
        min_proficiency=3,
    )
    c_tight_3 = Course(
        id="c-tight-3",
        code="CS300",
        title="Tight 3h Course",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=["Algorithms"],
        min_proficiency=3,
    )
    s_tight: list[Section] = []
    tight_asgns: list[Assignment] = []
    slot_idx = 0
    # Faculty 0 gets 3 sections of 4.0h = 12.0h
    # Faculty 1 gets 3 sections of 4.0h = 12.0h
    # Faculty 2 gets 2 sections of 4.0h + 1 of 3.0h = 11.0h -> Total 35.0h / 36.0h = 97.2%
    for f_idx, load_spec in enumerate(
        [[4.0, 4.0, 4.0], [4.0, 4.0, 4.0], [4.0, 4.0, 3.0]]
    ):
        for s_idx, hours in enumerate(load_spec):
            sec_id = f"s-tight-{f_idx}-{s_idx}"
            course_ref = c_tight_4 if hours == 4.0 else c_tight_3
            s_tight.append(
                Section(
                    id=sec_id,
                    course_id=course_ref.id,
                    term="Fall 2026",
                    section_cap=40,
                    expected_size=30,
                    size_p10=20,
                    size_p50=30,
                    size_p90=35,
                    time_slot_id=base_timeslots[slot_idx % len(base_timeslots)].id,
                )
            )
            tight_asgns.append(
                Assignment(
                    id=f"a-tight-{f_idx}-{s_idx}",
                    section_id=sec_id,
                    faculty_id=f_tight[f_idx].id,
                    source=AssignmentSource.SOLVER,
                    fit_score=0.9,
                    run_id="run-tight",
                )
            )
            slot_idx += 1

    fixtures["tight_capacity"] = {
        "name": "tight_capacity",
        "expected_outcome": {
            "feasible": True,
            "reason": "Feasible but tightly constrained; total contact hours required (~98% capacity) leave minimal slack for load balancing.",
        },
        "scenario": {
            "faculty": [f.model_dump(mode="json") for f in f_tight],
            "courses": [
                c_tight_4.model_dump(mode="json"),
                c_tight_3.model_dump(mode="json"),
            ],
            "sections": [s.model_dump(mode="json") for s in s_tight],
            "resources": [r.model_dump(mode="json") for r in base_resources],
            "timeslots": [ts.model_dump(mode="json") for ts in base_timeslots],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in tight_asgns],
    }

    # 3. infeasible_expertise (a course nobody is qualified to teach)
    c_quantum = Course(
        id="c-quantum",
        code="CS699",
        title="Exotic Quantum Algorithms",
        credits=4,
        contact_hours=4.0,
        level=CourseLevel.GRADUATE,
        required_tags=["Quantum Algorithms"],
        min_proficiency=5,
    )
    s_quantum = Section(
        id="s-quantum-1",
        course_id=c_quantum.id,
        term="Fall 2026",
        section_cap=25,
        expected_size=15,
        size_p10=10,
        size_p50=15,
        size_p90=20,
    )
    # Available faculty only have Web and Database skills
    f_novices = [
        Faculty(
            id="f-novice-1",
            name="Dr. Web Specialist",
            email="web@univ.edu",
            rank=FacultyRank.ASSISTANT_PROFESSOR,
            expertise=[FacultyExpertise(tag="Web Development", proficiency=3)],
            max_weekly_load_hours=12.0,
            max_courses=2,
            min_courses=1,
            max_preparations=2,
        )
    ]
    asgn_quantum = [
        Assignment(
            id="a-quantum-1",
            section_id=s_quantum.id,
            faculty_id=f_novices[0].id,
            source=AssignmentSource.SOLVER,
            fit_score=0.1,
            run_id="run-quantum",
        )
    ]

    fixtures["infeasible_expertise"] = {
        "name": "infeasible_expertise",
        "expected_outcome": {
            "feasible": False,
            "reason": "Infeasible due to HC-01: Course requires Quantum Algorithms proficiency >= 5, which no available faculty member possesses.",
        },
        "scenario": {
            "faculty": [f.model_dump(mode="json") for f in f_novices],
            "courses": [c_quantum.model_dump(mode="json")],
            "sections": [s_quantum.model_dump(mode="json")],
            "resources": [],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_quantum],
    }

    # 4. leave_heavy (30% of faculty on leave in a term)
    f_leave: list[Faculty] = []
    for i in range(10):
        # 3 out of 10 on leave in Fall 2026
        leaves = ["Fall 2026"] if i < 3 else []
        f_leave.append(
            Faculty(
                id=f"f-leave-{i}",
                name=f"Dr. LeaveFaculty {i}",
                email=f"leave{i}@univ.edu",
                rank=FacultyRank.ASSOCIATE_PROFESSOR,
                expertise=[FacultyExpertise(tag="Algorithms", proficiency=4)],
                max_weekly_load_hours=12.0,
                max_courses=3,
                min_courses=1,
                max_preparations=2,
                leave_terms=leaves,
            )
        )
    c_leave = Course(
        id="c-leave-101",
        code="CS101",
        title="Intro CS",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=["Algorithms"],
        min_proficiency=3,
    )
    # Sections in Fall 2026 assigned to faculty on leave
    s_leave = [
        Section(
            id=f"s-leave-{i}",
            course_id=c_leave.id,
            term="Fall 2026",
            section_cap=40,
            expected_size=30,
            size_p10=20,
            size_p50=30,
            size_p90=35,
        )
        for i in range(3)
    ]
    asgn_leave = [
        Assignment(
            id=f"a-leave-{i}",
            section_id=s_leave[i].id,
            faculty_id=f_leave[i].id,
            source=AssignmentSource.SOLVER,
            fit_score=0.9,
            run_id="run-leave",
        )
        for i in range(3)
    ]

    fixtures["leave_heavy"] = {
        "name": "leave_heavy",
        "expected_outcome": {
            "feasible": False,
            "reason": "Infeasible due to HC-04: 30% of faculty members are on leave in Fall 2026, causing direct HC-04 sabbatical violations upon assignment.",
        },
        "scenario": {
            "faculty": [f.model_dump(mode="json") for f in f_leave],
            "courses": [c_leave.model_dump(mode="json")],
            "sections": [s.model_dump(mode="json") for s in s_leave],
            "resources": [],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_leave],
    }

    # 5. single_expert_bottleneck (one person is the only qualified instructor for 5 courses)
    f_bottleneck = Faculty(
        id="f-turing-bottleneck",
        name="Dr. Alan Turing",
        email="turing.bottleneck@univ.edu",
        rank=FacultyRank.PROFESSOR,
        expertise=[
            FacultyExpertise(tag="Advanced Cryptography", proficiency=5),
            FacultyExpertise(tag="Quantum Complexity", proficiency=5),
            FacultyExpertise(tag="Formal Verification", proficiency=5),
            FacultyExpertise(tag="Distributed Consensus", proficiency=5),
            FacultyExpertise(tag="Neural Compilers", proficiency=5),
        ],
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=1,
        max_preparations=2,  # Limit is 2 preparations!
    )
    c_b_list = [
        Course(
            id=f"c-b-{i}",
            code=f"CS80{i}",
            title=f"Bottleneck Course {i}",
            credits=3,
            contact_hours=3.0,
            level=CourseLevel.GRADUATE,
            required_tags=[tag],
            min_proficiency=5,
        )
        for i, tag in enumerate(
            [
                "Advanced Cryptography",
                "Quantum Complexity",
                "Formal Verification",
                "Distributed Consensus",
                "Neural Compilers",
            ]
        )
    ]
    s_b_list = [
        Section(
            id=f"s-b-{i}",
            course_id=c_b_list[i].id,
            term="Fall 2026",
            section_cap=30,
            expected_size=20,
            size_p10=10,
            size_p50=20,
            size_p90=25,
        )
        for i in range(5)
    ]
    # Assigning all 5 courses to Turing produces 5 preparations (limit: 2) and 15h load (limit: 12.0h)
    asgn_b = [
        Assignment(
            id=f"a-b-{i}",
            section_id=s_b_list[i].id,
            faculty_id=f_bottleneck.id,
            source=AssignmentSource.SOLVER,
            fit_score=0.98,
            run_id="run-b",
        )
        for i in range(5)
    ]

    fixtures["single_expert_bottleneck"] = {
        "name": "single_expert_bottleneck",
        "expected_outcome": {
            "feasible": False,
            "reason": "Infeasible due to HC-02 and HC-05: Single expert is the only qualified instructor for 5 distinct required courses, violating max load (15h > 12h) and max preparations (5 > 2).",
        },
        "scenario": {
            "faculty": [f_bottleneck.model_dump(mode="json")],
            "courses": [c.model_dump(mode="json") for c in c_b_list],
            "sections": [s.model_dump(mode="json") for s in s_b_list],
            "resources": [],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_b],
    }

    # 6. lab_resource_shortage
    r_tiny_lab = Resource(
        id="LAB-TINY", type=ResourceType.LAB, capacity=15, unavailable_slots=[]
    )
    c_huge_lab = Course(
        id="c-huge-lab",
        code="CS210L",
        title="Heavy Lab Course",
        credits=4,
        contact_hours=4.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=[],
        min_proficiency=1,
        is_lab=True,
        required_resource_ids=["LAB-TINY"],
    )
    s_huge_lab = Section(
        id="s-huge-lab-1",
        course_id=c_huge_lab.id,
        term="Fall 2026",
        section_cap=50,
        expected_size=40,
        size_p10=30,
        size_p50=40,
        size_p90=48,
    )
    f_dummy = Faculty(
        id="f-dummy",
        name="Dr. Lab Instructor",
        email="lab@univ.edu",
        rank=FacultyRank.LECTURER,
        max_weekly_load_hours=15.0,
        max_courses=4,
        min_courses=1,
        max_preparations=3,
    )
    asgn_lab = [
        Assignment(
            id="a-lab-1",
            section_id=s_huge_lab.id,
            faculty_id=f_dummy.id,
            source=AssignmentSource.SOLVER,
            fit_score=0.9,
            run_id="run-lab",
        )
    ]

    fixtures["lab_resource_shortage"] = {
        "name": "lab_resource_shortage",
        "expected_outcome": {
            "feasible": False,
            "reason": "Infeasible due to HC-07: Specialized lab facility capacity (15) cannot accommodate section expected enrollment (40).",
        },
        "scenario": {
            "faculty": [f_dummy.model_dump(mode="json")],
            "courses": [c_huge_lab.model_dump(mode="json")],
            "sections": [s_huge_lab.model_dump(mode="json")],
            "resources": [r_tiny_lab.model_dump(mode="json")],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_lab],
    }

    # 7. time_clash_dense
    ts_clash = TimeSlot(id="TS-CLASH", day=DayOfWeek.MON, start="09:00", end="10:30")
    c_clash1 = Course(
        id="c-clash-1",
        code="CS101",
        title="Course 1",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
    )
    c_clash2 = Course(
        id="c-clash-2",
        code="CS102",
        title="Course 2",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
    )
    s_clash1 = Section(
        id="s-clash-1",
        course_id=c_clash1.id,
        term="Fall 2026",
        section_cap=40,
        expected_size=30,
        size_p10=20,
        size_p50=30,
        size_p90=35,
        time_slot_id=ts_clash.id,
    )
    s_clash2 = Section(
        id="s-clash-2",
        course_id=c_clash2.id,
        term="Fall 2026",
        section_cap=40,
        expected_size=30,
        size_p10=20,
        size_p50=30,
        size_p90=35,
        time_slot_id=ts_clash.id,
    )
    f_clash = Faculty(
        id="f-clash",
        name="Dr. Split Identity",
        email="split@univ.edu",
        rank=FacultyRank.PROFESSOR,
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=1,
        max_preparations=2,
    )
    asgn_clash = [
        Assignment(
            id="a-clash-1",
            section_id=s_clash1.id,
            faculty_id=f_clash.id,
            source=AssignmentSource.SOLVER,
            fit_score=0.9,
            run_id="run-clash",
        ),
        Assignment(
            id="a-clash-2",
            section_id=s_clash2.id,
            faculty_id=f_clash.id,
            source=AssignmentSource.SOLVER,
            fit_score=0.9,
            run_id="run-clash",
        ),
    ]

    fixtures["time_clash_dense"] = {
        "name": "time_clash_dense",
        "expected_outcome": {
            "feasible": False,
            "reason": "Infeasible due to HC-03: Two course sections assigned to the same instructor share the exact same time slot TS-CLASH.",
        },
        "scenario": {
            "faculty": [f_clash.model_dump(mode="json")],
            "courses": [
                c_clash1.model_dump(mode="json"),
                c_clash2.model_dump(mode="json"),
            ],
            "sections": [
                s_clash1.model_dump(mode="json"),
                s_clash2.model_dump(mode="json"),
            ],
            "resources": [],
            "timeslots": [ts_clash.model_dump(mode="json")],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_clash],
    }

    # 8. demand_spike (P90 far above P50)
    # Feasible under standard expected size, but triggers extreme uncertainty ratio
    r_spike = Resource(
        id="ROOM-SPIKE", type=ResourceType.ROOM, capacity=130, unavailable_slots=[]
    )
    c_spike = Course(
        id="c-spike",
        code="CS450",
        title="Spike Course",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
        required_resource_ids=[r_spike.id],
    )
    s_spike = Section(
        id="s-spike-1",
        course_id=c_spike.id,
        term="Fall 2026",
        section_cap=125,
        expected_size=40,
        size_p10=30,
        size_p50=40,
        size_p90=120,
    )
    f_spike = Faculty(
        id="f-spike",
        name="Dr. Spike",
        email="spike@univ.edu",
        rank=FacultyRank.PROFESSOR,
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=1,
        max_preparations=2,
    )
    asgn_spike = [
        Assignment(
            id="a-spike-1",
            section_id=s_spike.id,
            faculty_id=f_spike.id,
            source=AssignmentSource.SOLVER,
            fit_score=0.95,
            run_id="run-spike",
        )
    ]

    fixtures["demand_spike"] = {
        "name": "demand_spike",
        "expected_outcome": {
            "feasible": True,
            "reason": "Feasible under P50 expected demand (40 students), but demonstrates an extreme demand spike where P90 (120 students) triples P50, testing capacity risk planning.",
        },
        "scenario": {
            "faculty": [f_spike.model_dump(mode="json")],
            "courses": [c_spike.model_dump(mode="json")],
            "sections": [s_spike.model_dump(mode="json")],
            "resources": [r_spike.model_dump(mode="json")],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_spike],
    }

    # 9. boundary_exact_limit (load exactly equals max)
    # Faculty max_weekly_load_hours = 12.0, max_courses = 3, max_preparations = 2
    # Assigned 3 sections: 2 of CS101 (4.0h each) + 1 of CS102 (4.0h) = 12.0h total, 3 courses, 2 preps.
    f_exact = Faculty(
        id="f-exact-1",
        name="Dr. Precision",
        email="exact@univ.edu",
        rank=FacultyRank.PROFESSOR,
        expertise=[FacultyExpertise(tag="Algorithms", proficiency=5)],
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=3,
        max_preparations=2,
    )
    c_exact1 = Course(
        id="c-exact-1",
        code="CS101",
        title="Exact CS1",
        credits=4,
        contact_hours=4.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=["Algorithms"],
        min_proficiency=3,
    )
    c_exact2 = Course(
        id="c-exact-2",
        code="CS102",
        title="Exact CS2",
        credits=4,
        contact_hours=4.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=["Algorithms"],
        min_proficiency=3,
    )
    s_exact1 = Section(
        id="s-exact-1",
        course_id=c_exact1.id,
        term="Fall 2026",
        section_cap=40,
        expected_size=30,
        size_p10=20,
        size_p50=30,
        size_p90=35,
    )
    s_exact2 = Section(
        id="s-exact-2",
        course_id=c_exact1.id,
        term="Fall 2026",
        section_cap=40,
        expected_size=30,
        size_p10=20,
        size_p50=30,
        size_p90=35,
    )
    s_exact3 = Section(
        id="s-exact-3",
        course_id=c_exact2.id,
        term="Fall 2026",
        section_cap=40,
        expected_size=30,
        size_p10=20,
        size_p50=30,
        size_p90=35,
    )
    asgn_exact = [
        Assignment(
            id="a-exact-1",
            section_id=s_exact1.id,
            faculty_id=f_exact.id,
            source=AssignmentSource.SOLVER,
            fit_score=1.0,
            run_id="run-exact",
        ),
        Assignment(
            id="a-exact-2",
            section_id=s_exact2.id,
            faculty_id=f_exact.id,
            source=AssignmentSource.SOLVER,
            fit_score=1.0,
            run_id="run-exact",
        ),
        Assignment(
            id="a-exact-3",
            section_id=s_exact3.id,
            faculty_id=f_exact.id,
            source=AssignmentSource.SOLVER,
            fit_score=1.0,
            run_id="run-exact",
        ),
    ]

    fixtures["boundary_exact_limit"] = {
        "name": "boundary_exact_limit",
        "expected_outcome": {
            "feasible": True,
            "reason": "Feasible on boundary: Faculty load exactly equals max_weekly_load_hours (12.0h), max_courses (3), and max_preparations (2) with zero slack.",
        },
        "scenario": {
            "faculty": [f_exact.model_dump(mode="json")],
            "courses": [
                c_exact1.model_dump(mode="json"),
                c_exact2.model_dump(mode="json"),
            ],
            "sections": [
                s_exact1.model_dump(mode="json"),
                s_exact2.model_dump(mode="json"),
                s_exact3.model_dump(mode="json"),
            ],
            "resources": [],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_exact],
    }

    # 10. boundary_zero_capacity and empty_term
    r_zero = Resource(
        id="ROOM-ZERO", type=ResourceType.ROOM, capacity=1, unavailable_slots=[]
    )
    c_zero = Course(
        id="c-zero",
        code="CS999",
        title="Zero Cap Test",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
        required_resource_ids=[r_zero.id],
    )
    s_zero = Section(
        id="s-zero-1",
        course_id=c_zero.id,
        term="Fall 2026",
        section_cap=30,
        expected_size=25,
        size_p10=15,
        size_p50=25,
        size_p90=30,
    )
    f_zero = Faculty(
        id="f-zero",
        name="Dr. Zero",
        email="zero@univ.edu",
        rank=FacultyRank.PROFESSOR,
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=1,
        max_preparations=2,
    )
    asgn_zero = [
        Assignment(
            id="a-zero-1",
            section_id=s_zero.id,
            faculty_id=f_zero.id,
            source=AssignmentSource.SOLVER,
            fit_score=0.9,
            run_id="run-zero",
        )
    ]

    fixtures["boundary_zero_capacity"] = {
        "name": "boundary_zero_capacity",
        "expected_outcome": {
            "feasible": False,
            "reason": "Infeasible due to HC-07: Resource has capacity (1) that fails to accommodate section expected enrollment (25), alongside empty term verification.",
        },
        "scenario": {
            "faculty": [f_zero.model_dump(mode="json")],
            "courses": [c_zero.model_dump(mode="json")],
            "sections": [s_zero.model_dump(mode="json")],
            "resources": [r_zero.model_dump(mode="json")],
            "timeslots": [],
            "previous_assignments": [],
        },
        "assignments": [a.model_dump(mode="json") for a in asgn_zero],
    }

    return fixtures


def generate_all(seed: int = 42, scenario_filter: str = "all") -> dict[str, Any]:
    """Execute complete deterministic data generation pipeline."""
    rng = random.Random(seed)

    timeslots = generate_timeslots()
    resources = generate_resources()
    courses = generate_courses(rng)
    faculty = generate_faculty(rng, courses)
    users = generate_users(faculty)
    sections = generate_sections(rng, courses, timeslots, TERMS)
    history = generate_enrollment_history(rng, courses)

    fixtures = generate_fixtures(faculty, courses, sections, resources, timeslots, rng)

    # Persist seed data
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    if scenario_filter in ("all", "seed"):
        (SEED_DIR / "users.json").write_text(
            json.dumps([u.model_dump(mode="json") for u in users], indent=2),
            encoding="utf-8",
        )
        (SEED_DIR / "faculty.json").write_text(
            json.dumps([f.model_dump(mode="json") for f in faculty], indent=2),
            encoding="utf-8",
        )
        (SEED_DIR / "courses.json").write_text(
            json.dumps([c.model_dump(mode="json") for c in courses], indent=2),
            encoding="utf-8",
        )
        (SEED_DIR / "sections.json").write_text(
            json.dumps([s.model_dump(mode="json") for s in sections], indent=2),
            encoding="utf-8",
        )
        (SEED_DIR / "resources.json").write_text(
            json.dumps([r.model_dump(mode="json") for r in resources], indent=2),
            encoding="utf-8",
        )
        (SEED_DIR / "timeslots.json").write_text(
            json.dumps([ts.model_dump(mode="json") for ts in timeslots], indent=2),
            encoding="utf-8",
        )
        (SEED_DIR / "enrollment_history.json").write_text(
            json.dumps(history, indent=2), encoding="utf-8"
        )
        print(f"[+] Wrote base seed data to {SEED_DIR}")

    # Persist fixtures
    if scenario_filter == "all":
        # Save individual fixture files and master scenarios.json
        (FIXTURES_DIR / "scenarios.json").write_text(
            json.dumps(fixtures, indent=2), encoding="utf-8"
        )
        for name, fixture_data in fixtures.items():
            (FIXTURES_DIR / f"{name}.json").write_text(
                json.dumps(fixture_data, indent=2), encoding="utf-8"
            )
        print(f"[+] Wrote {len(fixtures)} fixtures to {FIXTURES_DIR}")
    elif scenario_filter in fixtures:
        (FIXTURES_DIR / f"{scenario_filter}.json").write_text(
            json.dumps(fixtures[scenario_filter], indent=2), encoding="utf-8"
        )
        print(f"[+] Wrote single fixture '{scenario_filter}' to {FIXTURES_DIR}")

    return {
        "faculty_count": len(faculty),
        "courses_count": len(courses),
        "sections_count": len(sections),
        "resources_count": len(resources),
        "timeslots_count": len(timeslots),
        "enrollment_records_count": len(history),
        "fixtures_count": len(fixtures),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic Academic Data Generator"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="all",
        help="Scenario to generate ('all', 'seed', or fixture name)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random number generator seed"
    )
    args = parser.parse_args()

    print(f"[*] Running datagen with seed={args.seed}, scenario={args.scenario}...")
    summary = generate_all(seed=args.seed, scenario_filter=args.scenario)
    print(f"[*] Done. Summary: {summary}")


if __name__ == "__main__":
    main()
