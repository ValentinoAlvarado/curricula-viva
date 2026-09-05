from app.demo_data import COURSES, GAPS, PROGRAMS, UNIVERSITY, evidence


def test_demo_has_uni_and_three_programs():
    assert UNIVERSITY["name"] == "Universidad Nacional de Ingeniería"
    assert len(PROGRAMS) == 3
    assert {p["plan_period"] for p in PROGRAMS} == {"2018-2", "2025-1"}


def test_each_program_has_courses_and_gaps():
    for program in PROGRAMS:
        pid = program["id"]
        assert COURSES[pid]
        assert len(COURSES[pid]) >= 40
        assert GAPS[pid]


def test_gap_evidence_resolves_to_curriculum_courses():
    for gaps in GAPS.values():
        for gap in gaps:
            result = evidence(gap["id"])
            assert result["competency"] == gap["competency"]
            assert result["courses"]
            assert all(c["course_code"] for c in result["courses"])
