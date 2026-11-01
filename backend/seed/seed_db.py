"""
Database Seeder
================
Loads skills.json, questions.json, and students.json into SQLite.
Run once: python seed_db.py
"""
import json
import sys
import os

# Allow running from the seed/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select
from app.models.db import engine, init_db, Skill, Question, Student, StudentSkillState

SEED_DIR = os.path.dirname(__file__)


def load_json(filename):
    with open(os.path.join(SEED_DIR, filename)) as f:
        return json.load(f)


def seed():
    init_db()

    with Session(engine) as session:
        # ── Skills ──────────────────────────────────────────────────────────
        existing_skills = session.exec(select(Skill)).all()
        if not existing_skills:
            skills_data = load_json("skills.json")
            for s in skills_data:
                skill = Skill(
                    id=s["id"],
                    name=s["name"],
                    description=s["description"],
                    chapter=s["chapter"],
                    class_grade=s["class"],
                    p_l0=s["p_l0"],
                    p_t=s["p_t"],
                    p_s=s["p_s"],
                    p_g=s["p_g"],
                )
                session.add(skill)
            session.commit()
            print(f"✅ Seeded {len(skills_data)} skills")
        else:
            print(f"⏭  Skills already exist ({len(existing_skills)} found), skipping")

        # ── Questions ────────────────────────────────────────────────────────
        existing_questions = session.exec(select(Question)).all()
        if not existing_questions:
            questions_data = load_json("questions.json")
            for q in questions_data:
                question = Question(
                    id=q["id"],
                    skill_id=q["skill_id"],
                    difficulty=q["difficulty"],
                    text=q["text"],
                    options=json.dumps(q["options"]),
                    correct_answer=q["correct_answer"],
                    explanation=q["explanation"],
                    error_hints=json.dumps(q["error_hints"]),
                )
                session.add(question)
            session.commit()
            print(f"✅ Seeded {len(questions_data)} questions")
        else:
            print(f"⏭  Questions already exist ({len(existing_questions)} found), skipping")

        # ── Students ─────────────────────────────────────────────────────────
        existing_students = session.exec(select(Student)).all()
        if not existing_students:
            students_data = load_json("students.json")
            for s in students_data:
                student = Student(
                    id=s["id"],
                    name=s["name"],
                    grade=s["grade"],
                    school=s["school"],
                    avatar=s.get("avatar", "🧑‍🎓"),
                )
                session.add(student)
            session.commit()
            print(f"✅ Seeded {len(students_data)} students")
        else:
            print(f"⏭  Students already exist ({len(existing_students)} found), skipping")

        # ── Initial BKT states ───────────────────────────────────────────────
        # Seed a few realistic answer histories for demo purposes
        skills_db = session.exec(select(Skill)).all()
        students_db = session.exec(select(Student)).all()

        # Pre-configure different mastery profiles for demo
        # Aarav: strong student (high mastery on most skills)
        # Priya: average student
        # Rohan: struggling on some skills
        # Sneha: strong on algebra, weak on geometry
        # Kiran: brand new, very low mastery everywhere

        demo_mastery = {
            1: {1: 0.78, 2: 0.65, 3: 0.45, 4: 0.82, 5: 0.70, 6: 0.55, 7: 0.60, 8: 0.50},
            2: {1: 0.45, 2: 0.50, 3: 0.35, 4: 0.48, 5: 0.40, 6: 0.55, 7: 0.42, 8: 0.38},
            3: {1: 0.20, 2: 0.25, 3: 0.18, 4: 0.22, 5: 0.15, 6: 0.30, 7: 0.20, 8: 0.18},
            4: {1: 0.65, 2: 0.70, 3: 0.30, 4: 0.55, 5: 0.35, 6: 0.75, 7: 0.88, 8: 0.32},
            5: {1: 0.12, 2: 0.15, 3: 0.10, 4: 0.12, 5: 0.10, 6: 0.14, 7: 0.11, 8: 0.13},
        }

        demo_opportunities = {
            1: {1: 12, 2: 8,  3: 5,  4: 14, 5: 9,  6: 7,  7: 8,  8: 6},
            2: {1: 7,  2: 6,  3: 5,  4: 7,  5: 5,  6: 8,  7: 6,  8: 5},
            3: {1: 3,  2: 3,  3: 3,  4: 3,  5: 3,  6: 4,  7: 3,  8: 3},
            4: {1: 9,  2: 10, 3: 4,  4: 8,  5: 5,  6: 11, 7: 13, 8: 4},
            5: {1: 1,  2: 1,  3: 1,  4: 1,  5: 1,  6: 1,  7: 1,  8: 1},
        }

        states_added = 0
        for student in students_db:
            for skill in skills_db:
                existing = session.exec(
                    select(StudentSkillState).where(
                        StudentSkillState.student_id == student.id,
                        StudentSkillState.skill_id == skill.id,
                    )
                ).first()
                if not existing:
                    mastery = demo_mastery.get(student.id, {}).get(skill.id, skill.p_l0)
                    opps    = demo_opportunities.get(student.id, {}).get(skill.id, 0)
                    session.add(StudentSkillState(
                        student_id=student.id,
                        skill_id=skill.id,
                        mastery=mastery,
                        opportunities=opps,
                    ))
                    states_added += 1

        session.commit()
        if states_added:
            print(f"✅ Seeded {states_added} student-skill states")

    print("\n🎉 Database seeded successfully!")


if __name__ == "__main__":
    seed()
