#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from investigate_duration_calculation_current import investigate_user_duration_calculation
from database import init_db

async def run_investigation():
    try:
        print('🔌 Initializing database connection...')
        await init_db()
        print('✅ Database initialized successfully')
        
        USER_ID = '688921c268819565ef1ce3dc'
        print(f'🔍 Starting investigation for user: {USER_ID}')
        
        result = await investigate_user_duration_calculation(USER_ID)
        print('✅ Investigation completed')
        return result
    except Exception as e:
        print(f'❌ Error in investigation: {str(e)}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    asyncio.run(run_investigation())
