#!/usr/bin/env python3
"""
Exercise Logger - Track workouts and physical activities.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta


def get_db_path(username: str) -> str:
    """Get database file path for a user."""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(skill_dir, 'data', f"{username}.db")


def get_user_id(cursor, username: str) -> int:
    """Get user ID from username."""
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"User not found: {username}")
    return row[0]


def log_exercise(username: str, exercise_type: str, duration: int, 
                 calories: float = 0, intensity: str = 'moderate', 
                 notes: str = None, exercised_at: str = None) -> dict:
    """Log an exercise session."""
    db_path = get_db_path(username)
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found", "message": "User database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        user_id = get_user_id(cursor, username)
        
        # Parse exercised_at or use current time
        if exercised_at:
            exercised_at = datetime.fromisoformat(exercised_at.replace('Z', '+00:00'))
        else:
            exercised_at = datetime.now()
        
        cursor.execute('''
            INSERT INTO exercises 
            (user_id, exercise_type, duration_minutes, calories_burned, intensity, notes, exercised_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, exercise_type, duration, calories, intensity, notes, exercised_at))
        
        conn.commit()
        
        return {
            "status": "success",
            "data": {
                "id": cursor.lastrowid,
                "exercise_type": exercise_type,
                "duration_minutes": duration,
                "calories_burned": calories,
                "intensity": intensity,
                "exercised_at": exercised_at.isoformat()
            },
            "message": f"Logged {exercise_type}: {duration} min, {calories} cal"
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def get_exercise_history(username: str, days: int = 7) -> dict:
    """Get exercise history for the past N days."""
    db_path = get_db_path(username)
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        user_id = get_user_id(cursor, username)
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT id, exercise_type, duration_minutes, calories_burned, 
                   intensity, notes, exercised_at
            FROM exercises
            WHERE user_id = ? AND exercised_at >= ?
            ORDER BY exercised_at DESC
        ''', (user_id, since))
        
        exercises = []
        for row in cursor.fetchall():
            exercises.append({
                "id": row[0],
                "exercise_type": row[1],
                "duration_minutes": row[2],
                "calories_burned": row[3],
                "intensity": row[4],
                "notes": row[5],
                "exercised_at": row[6]
            })
        
        # Get summary
        cursor.execute('''
            SELECT SUM(duration_minutes), SUM(calories_burned), COUNT(*)
            FROM exercises
            WHERE user_id = ? AND exercised_at >= ?
        ''', (user_id, since))
        
        row = cursor.fetchone()
        
        return {
            "status": "success",
            "data": {
                "exercises": exercises,
                "summary": {
                    "total_duration_minutes": row[0] or 0,
                    "total_calories": row[1] or 0,
                    "session_count": row[2] or 0
                },
                "days": days
            }
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Exercise Logger')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Log exercise
    log_parser = subparsers.add_parser('log', help='Log an exercise')
    log_parser.add_argument('--type', required=True, help='Exercise type (e.g., running, cycling, swimming)')
    log_parser.add_argument('--duration', type=int, required=True, help='Duration in minutes')
    log_parser.add_argument('--calories', type=float, default=0, help='Calories burned')
    log_parser.add_argument('--intensity', choices=['light', 'moderate', 'intense'], default='moderate')
    log_parser.add_argument('--notes', help='Notes')
    log_parser.add_argument('--at', help='Exercise time (ISO format)')
    
    # History
    history_parser = subparsers.add_parser('history', help='Get exercise history')
    history_parser.add_argument('--days', type=int, default=7, help='Number of days')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Get username from environment or CLI
    username = os.environ.get('NUTRICOACH_USER', 'robert')
    
    if args.command == 'log':
        result = log_exercise(
            username, args.type, args.duration,
            args.calories, args.intensity, args.notes, args.at
        )
    elif args.command == 'history':
        result = get_exercise_history(username, args.days)
    else:
        result = {"status": "error", "error": "unknown_command"}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == '__main__':
    main()