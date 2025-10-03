#!/usr/bin/env python3
"""
Find actual enrollment IDs from seed data
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env
from database import database

async def find_ids():
    """Find the actual ObjectIds from seed data"""
    print("🔍 Finding enrollment IDs...")

    # Find institutional learners
    learners = await database.institutional_learners.find().to_list(length=None)
    print(f"Found {len(learners)} institutional learners:")
    for learner in learners:
        print(f"  User: {learner['user_id']}, Institution: {learner['institution_id']}, Tutor: {learner['tutor_id']}")

    # Find institutions
    institutions = await database.institutions.find().to_list(length=None)
    print(f"\nFound {len(institutions)} institutions:")
    for inst in institutions:
        print(f"  {inst['name']}: {inst['_id']}")

    # Find tutors
    tutors = await database.tutors.find().to_list(length=None)
    print(f"\nFound {len(tutors)} tutors:")
    for tutor in tutors:
        print(f"  {tutor['name']}: {tutor['_id']}")

if __name__ == "__main__":
    asyncio.run(find_ids())
