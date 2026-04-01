#!/usr/bin/env python3
"""
Sleep Logger - Track sleep quality and duration.
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


def log_sleep(username: str, hours: float, quality: str,
              sleep_start: str, sleep_end: str, notes: str = None) -> dict:
    """Log sleep record."""
    db_path = get_db_path(username)
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        user_id = get_user_id(cursor, username)
        
        sleep_start_dt = datetime.fromisoformat(sleep_start.replace('Z', '+00:00'))
        sleep_end_dt = datetime.fromisoformat(sleep_end.replace('Z', '+00:00'))
        
        cursor.execute('''
            INSERT INTO sleep_records 
            (user_id, sleep_hours, sleep_quality, sleep_start, sleep_end, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, hours, quality, sleep_start_dt, sleep_end_dt, notes))
        
        conn.commit()
        
        return {
            "status": "success",
            "data": {
                "hours": hours,
                "quality": quality,
                "sleep_start": sleep_start,
                "sleep_end": sleep_end
            },
            "message": f"Logged sleep: {hours}h, quality: {quality}"
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def get_sleep_history(username: str, days: int = 7) -> dict:
    """Get sleep history."""
    db_path = get_db_path(username)
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        user_id = get_user_id(cursor, username)
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT id, sleep_hours, sleep_quality, sleep_start, sleep_end, notes
            FROM sleep_records
            WHERE user_id = ? AND sleep_start >= ?
            ORDER BY sleep_start DESC
        ''', (user_id, since))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row[0],
                "hours": row[1],
                "quality": row[2],
                "sleep_start": row[3],
                "sleep_end": row[4],
                "notes": row[5]
            })
        
        # Summary
        cursor.execute('''
            SELECT AVG(sleep_hours), 
                   SUM(CASE WHEN sleep_quality = 'excellent' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN sleep_quality = 'good' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN sleep_quality = 'fair' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN sleep_quality = 'poor' THEN 1 ELSE 0 END)
            FROM sleep_records
            WHERE user_id = ? AND sleep_start >= ?
        ''', (user_id, since))
        
        row = cursor.fetchone()
        
        return {
            "status": "success",
            "data": {
                "records": records,
                "summary": {
                    "avg_hours": round(row[0], 1) if row[0] else 0,
                    "excellent_count": row[1] or 0,
                    "good_count": row[2] or 0,
                    "fair_count": row[3] or 0,
                    "poor_count": row[4] or 0
                },
                "days": days
            }
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Sleep Logger')
    subparsers = parser.add_subparsers(dest='command')
    
    log_parser = subparsers.add_parser('log', help='Log sleep')
    log_parser.add_argument('--hours', type=float, required=True, help='Sleep hours')
    log_parser.add_argument('--quality', choices=['poor', 'fair', 'good', 'excellent'], 
                          required=True, help='Sleep quality')
    log_parser.add_argument('--start', required=True, help='Sleep start time (ISO)')
    log_parser.add_argument('--end', required=True, help='Sleep end time (ISO)')
    log_parser.add_argument('--notes', help='Notes')
    
    history_parser = subparsers.add_parser('history', help='Get sleep history')
    history_parser.add_argument('--days', type=int, default=7)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    username = os.environ.get('NUTRICOACH_USER', 'robert')
    
    if args.command == 'log':
        result = log_sleep(username, args.hours, args.quality, args.start, args.end, args.notes)
    elif args.command == 'history':
        result = get_sleep_history(username, args.days)
    else:
        result = {"status": "error", "error": "unknown_command"}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == '__main__':
    main()