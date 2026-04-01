#!/usr/bin/env python3
"""
Water Intake Logger - Track daily water consumption.
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


def log_water(username: str, amount_ml: int, logged_at: str = None) -> dict:
    """Log water intake."""
    db_path = get_db_path(username)
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        user_id = get_user_id(cursor, username)
        
        if logged_at:
            logged_at = datetime.fromisoformat(logged_at.replace('Z', '+00:00'))
        else:
            logged_at = datetime.now()
        
        cursor.execute('''
            INSERT INTO water_intake (user_id, amount_ml, logged_at)
            VALUES (?, ?, ?)
        ''', (user_id, amount_ml, logged_at))
        
        conn.commit()
        
        return {
            "status": "success",
            "data": {"amount_ml": amount_ml, "logged_at": logged_at.isoformat()},
            "message": f"Logged {amount_ml}ml water"
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def get_water_history(username: str, days: int = 1) -> dict:
    """Get water intake history."""
    db_path = get_db_path(username)
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        user_id = get_user_id(cursor, username)
        
        since = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT SUM(amount_ml), COUNT(*), DATE(logged_at) as day
            FROM water_intake
            WHERE user_id = ? AND logged_at >= ?
            GROUP BY DATE(logged_at)
            ORDER BY day DESC
        ''', (user_id, since))
        
        daily = []
        total = 0
        for row in cursor.fetchall():
            daily.append({"date": row[2], "total_ml": row[0], "entries": row[1]})
            total += row[0]
        
        return {
            "status": "success",
            "data": {
                "daily": daily,
                "summary": {"total_ml": total, "avg_ml_per_day": total / days if days > 0 else 0},
                "days": days,
                "goal_ml": 2000
            }
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Water Intake Logger')
    subparsers = parser.add_subparsers(dest='command')
    
    log_parser = subparsers.add_parser('log', help='Log water intake')
    log_parser.add_argument('amount', type=int, help='Amount in ml')
    log_parser.add_argument('--at', help='Time (ISO format)')
    
    history_parser = subparsers.add_parser('history', help='Get water history')
    history_parser.add_argument('--days', type=int, default=1)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    username = os.environ.get('NUTRICOACH_USER', 'robert')
    
    if args.command == 'log':
        result = log_water(username, args.amount, args.at)
    elif args.command == 'history':
        result = get_water_history(username, args.days)
    else:
        result = {"status": "error", "error": "unknown_command"}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == '__main__':
    main()