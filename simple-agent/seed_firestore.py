# Copyright 2026 Google LLC
"""Seed script for Firestore database with initial gym workout routines."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-c2062bba7c2d"

ROUTINES = [
    {
        "routine_id": "fat-burn-hiit",
        "name": "Full Body HIIT Fat Incinerator",
        "target_muscle": "full_body",
        "difficulty": "intermediate",
        "duration_minutes": 30,
        "calories_burned_est": 380,
        "description": "High-intensity interval training designed to maximize calorie burn and elevate metabolic rate.",
        "exercises": [
            {"name": "Burpees", "sets": 4, "reps": "15 reps", "rest_seconds": 30},
            {"name": "Kettlebell Swings", "sets": 4, "reps": "20 reps", "rest_seconds": 30},
            {"name": "Mountain Climbers", "sets": 4, "reps": "45 seconds", "rest_seconds": 30},
            {"name": "Dumbbell Thrusters", "sets": 3, "reps": "12 reps", "rest_seconds": 45},
        ],
    },
    {
        "routine_id": "upper-body-blast",
        "name": "Upper Body Hypertrophy & Deficit Circuit",
        "target_muscle": "upper_body",
        "difficulty": "beginner",
        "duration_minutes": 45,
        "calories_burned_est": 320,
        "description": "Chest, back, and arm supersets that maintain lean muscle mass during weight loss phases.",
        "exercises": [
            {"name": "Incline Dumbbell Bench Press", "sets": 3, "reps": "12 reps", "rest_seconds": 60},
            {"name": "Lat Pulldown", "sets": 3, "reps": "12 reps", "rest_seconds": 60},
            {"name": "Dumbbell Overhead Shoulder Press", "sets": 3, "reps": "10 reps", "rest_seconds": 60},
            {"name": "Cable Bicep Curls superset with Tricep Pushdowns", "sets": 3, "reps": "15 reps", "rest_seconds": 45},
        ],
    },
    {
        "routine_id": "lower-body-sculpt",
        "name": "Legs & Glutes Calorie Burner",
        "target_muscle": "legs",
        "difficulty": "intermediate",
        "duration_minutes": 50,
        "calories_burned_est": 450,
        "description": "Heavy compound leg exercises to activate large muscle groups and burn maximum energy.",
        "exercises": [
            {"name": "Barbell Squats", "sets": 4, "reps": "10 reps", "rest_seconds": 90},
            {"name": "Romanian Deadlifts", "sets": 4, "reps": "12 reps", "rest_seconds": 60},
            {"name": "Walking Lunges", "sets": 3, "reps": "20 steps", "rest_seconds": 60},
            {"name": "Leg Press", "sets": 3, "reps": "15 reps", "rest_seconds": 60},
        ],
    },
    {
        "routine_id": "core-cardio-burn",
        "name": "Core Shred & Incline Cardio",
        "target_muscle": "core",
        "difficulty": "beginner",
        "duration_minutes": 35,
        "calories_burned_est": 280,
        "description": "Direct abdominal conditioning paired with treadmill incline intervals for steady-state fat loss.",
        "exercises": [
            {"name": "Hanging Leg Raises", "sets": 3, "reps": "12 reps", "rest_seconds": 45},
            {"name": "Plank Hold", "sets": 3, "reps": "60 seconds", "rest_seconds": 45},
            {"name": "Cable Woodchoppers", "sets": 3, "reps": "15 reps/side", "rest_seconds": 45},
            {"name": "Treadmill Incline Walk (12% incline, 3.5 mph)", "sets": 1, "reps": "20 minutes", "rest_seconds": 0},
        ],
    },
]


def seed_routines():
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("gym_routines")
    print(f"Seeding {len(ROUTINES)} routines into Firestore collection 'gym_routines' in project '{PROJECT_ID}'...")
    for routine in ROUTINES:
        doc_ref = collection.document(routine["routine_id"])
        doc_ref.set(routine)
        print(f"  ✓ Seeded: {routine['routine_id']} ({routine['name']})")
    print("Done seeding Firestore!")


if __name__ == "__main__":
    seed_routines()
