
def sync_learning_plan_to_user_tracking(user_id, learning_plan_id, db):
    """
    Synchronize learning plan progress to user subscription tracking.
    This should be called whenever a learning plan session is completed.
    """
    from datetime import datetime, timezone
    
    users_collection = db['users']
    learning_plans_collection = db['learning_plans']
    
    # Get user subscription period
    user = users_collection.find_one({"_id": user_id})
    if not user:
        return False
    
    current_period_start = user.get('current_period_start')
    current_period_end = user.get('current_period_end')
    
    if not current_period_start or not current_period_end:
        return False
    
    # Get learning plan sessions completed in current period
    learning_plan = learning_plans_collection.find_one({"_id": learning_plan_id})
    if not learning_plan:
        return False
    
    sessions_in_period = []
    for session in learning_plan.get('sessions', []):
        if session.get('completed', False):
            completion_date = session.get('completion_timestamp') or session.get('completion_date')
            if completion_date and current_period_start <= completion_date <= current_period_end:
                sessions_in_period.append(session)
    
    # Calculate totals and update user
    total_minutes = sum(s.get('duration_minutes', 5) for s in sessions_in_period)
    total_sessions = len(sessions_in_period)
    
    users_collection.update_one(
        {"_id": user_id},
        {
            "$set": {
                "practice_minutes_used": total_minutes,
                "practice_sessions_used": total_sessions,
                "last_sync_update": datetime.now(timezone.utc)
            }
        }
    )
    
    return True
