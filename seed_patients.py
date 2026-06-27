"""
Persistent random patient data seeder.

Creates real (database-persistent) patient records with vitals and prediction rows,
where each generated patient is aligned to a target predicted risk level.

Usage:
    python seed_patients.py
    python seed_patients.py --count 15
"""

import argparse
import json

from app import create_app
from services.patient_seed_service import seed_patients


def parse_args():
    parser = argparse.ArgumentParser(description="Seed persistent random patient data with matched predictions")
    parser.add_argument("--count", type=int, default=10, help="Number of patients to create (minimum 10)")
    return parser.parse_args()


def main():
    args = parse_args()
    app = create_app()
    with app.app_context():
        result = seed_patients(count=args.count)

    print("✅ Patient data seeded successfully")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
