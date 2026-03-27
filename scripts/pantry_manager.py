#!/usr/bin/env python3
"""
Pantry (home ingredients) management for Health Coach.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


def get_db_path(username: str) -> str:
    """Get database file path for a user."""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(skill_dir, 'data')
    return os.path.join(data_dir, f"{username}.db")


def add_item(args) -> Dict[str, Any]:
    """Add item to pantry."""
    db_path = get_db_path(args.user)
    
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found", "message": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (args.user,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return {"status": "error", "error": "user_not_found", "message": "User not found"}
        
        user_id = user_row[0]
        
        # Try to match with food database
        cursor.execute('''
            SELECT id FROM custom_foods 
            WHERE user_id IN (?, 1) AND name LIKE ?
            LIMIT 1
        ''', (user_id, f'%{args.food}%'))
        
        food_match = cursor.fetchone()
        food_id = food_match[0] if food_match else None
        
        # Parse dates
        purchase_date = args.purchase or datetime.now().strftime('%Y-%m-%d')
        expiry_date = args.expiry
        
        # Auto-calculate expiry if not provided
        if not expiry_date and food_id:
            # Default expiry based on location
            defaults = {
                'fridge': 7,
                'freezer': 90,
                'pantry': 30
            }
            days = defaults.get(args.location, 7)
            expiry_date = (datetime.strptime(purchase_date, '%Y-%m-%d') + timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO pantry 
            (user_id, food_name, food_id, quantity_g, quantity_desc, location, 
             purchase_date, expiry_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, args.food, food_id, args.quantity, args.quantity_desc,
            args.location, purchase_date, expiry_date, args.notes
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        
        return {
            "status": "success",
            "data": {"item_id": item_id, "food_name": args.food},
            "message": f"Added to pantry: {args.food}",
            "expiry": expiry_date
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def list_items(args) -> Dict[str, Any]:
    """List pantry items."""
    db_path = get_db_path(args.user)
    
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found", "message": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (args.user,))
        user_id = cursor.fetchone()[0]
        
        query = '''
            SELECT p.id, p.food_name, p.quantity_desc, p.location,
                   p.purchase_date, p.expiry_date, p.notes,
                   c.calories_per_100g, c.protein_per_100g
            FROM pantry p
            LEFT JOIN custom_foods c ON p.food_id = c.id
            WHERE p.user_id = ?
        '''
        params = [user_id]
        
        if args.location:
            query += ' AND p.location = ?'
            params.append(args.location)
        
        if args.expiring:
            # Items expiring within N days
            future = (datetime.now() + timedelta(days=args.expiring)).strftime('%Y-%m-%d')
            query += ' AND p.expiry_date <= ?'
            params.append(future)
        
        query += ' ORDER BY p.expiry_date ASC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        items = []
        today = datetime.now().date()
        
        for row in rows:
            expiry = row[5]
            days_left = None
            if expiry:
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                days_left = (expiry_date - today).days
            
            items.append({
                "id": row[0],
                "food_name": row[1],
                "quantity": row[2],
                "location": row[3],
                "purchase_date": row[4],
                "expiry_date": expiry,
                "days_left": days_left,
                "notes": row[6],
                "nutrition_hint": {
                    "calories": row[7],
                    "protein": row[8]
                } if row[7] else None
            })
        
        return {
            "status": "success",
            "data": {
                "count": len(items),
                "items": items
            }
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def remove_item(args) -> Dict[str, Any]:
    """Remove item from pantry."""
    db_path = get_db_path(args.user)
    
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found", "message": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (args.user,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute('''
            DELETE FROM pantry WHERE id = ? AND user_id = ?
        ''', (args.item_id, user_id))
        
        conn.commit()
        
        return {
            "status": "success",
            "message": f"Removed item {args.item_id}"
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def get_pantry_nutrition_summary(username: str) -> Dict[str, Any]:
    """Get total nutrition potential of pantry."""
    db_path = get_db_path(username)
    
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT SUM(c.calories_per_100g * p.quantity_g / 100),
                   SUM(c.protein_per_100g * p.quantity_g / 100),
                   SUM(c.carbs_per_100g * p.quantity_g / 100),
                   SUM(c.fat_per_100g * p.quantity_g / 100)
            FROM pantry p
            JOIN custom_foods c ON p.food_id = c.id
            WHERE p.user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        return {
            "status": "success",
            "data": {
                "total_calories": round(row[0] or 0, 0),
                "total_protein_g": round(row[1] or 0, 1),
                "total_carbs_g": round(row[2] or 0, 1),
                "total_fat_g": round(row[3] or 0, 1)
            }
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def use_item(args) -> Dict[str, Any]:
    """Record usage of pantry item."""
    db_path = get_db_path(args.user)
    
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found", "message": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (args.user,))
        user_id = cursor.fetchone()[0]
        
        # Check current remaining
        cursor.execute('SELECT food_name, remaining_g FROM pantry WHERE id = ? AND user_id = ?',
                      (args.item_id, user_id))
        row = cursor.fetchone()
        
        if not row:
            return {"status": "error", "error": "item_not_found", "message": "Item not found"}
        
        food_name, current_remaining = row
        
        if current_remaining is None:
            current_remaining = 0
        
        if args.amount > current_remaining:
            return {
                "status": "error",
                "error": "insufficient_quantity",
                "message": f"Only {current_remaining}g remaining, cannot use {args.amount}g"
            }
        
        # Record usage
        remaining_after = current_remaining - args.amount
        
        cursor.execute('''
            INSERT INTO pantry_usage 
            (pantry_id, user_id, used_g, remaining_after_g, used_for_meal_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (args.item_id, user_id, args.amount, remaining_after, args.meal_id, args.notes))
        
        # Update pantry remaining (trigger will also do this, but let's be explicit)
        cursor.execute('''
            UPDATE pantry SET remaining_g = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (remaining_after, args.item_id))
        
        conn.commit()
        
        return {
            "status": "success",
            "data": {
                "food_name": food_name,
                "used_g": args.amount,
                "remaining_g": remaining_after,
                "usage_percentage": round((args.amount / (current_remaining + args.amount)) * 100, 1) if (current_remaining + args.amount) > 0 else 0
            },
            "message": f"Used {args.amount}g of {food_name}, {remaining_after}g remaining"
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def check_remaining(args) -> Dict[str, Any]:
    """Check remaining quantities in pantry."""
    db_path = get_db_path(args.user)
    
    if not os.path.exists(db_path):
        return {"status": "error", "error": "database_not_found", "message": "Database not found"}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE username = ?', (args.user,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT p.id, p.food_name, p.quantity_g, p.remaining_g, 
                   p.quantity_desc, p.location, p.expiry_date,
                   c.calories_per_100g, c.protein_per_100g
            FROM pantry p
            LEFT JOIN custom_foods c ON p.food_id = c.id
            WHERE p.user_id = ? AND (p.remaining_g IS NULL OR p.remaining_g > 0)
            ORDER BY p.remaining_g ASC
        ''', (user_id,))
        
        items = []
        for row in cursor.fetchall():
            initial = row[2] or 0
            remaining = row[3] or 0
            usage_pct = round((initial - remaining) / initial * 100, 1) if initial > 0 else 0
            
            items.append({
                "id": row[0],
                "food_name": row[1],
                "initial_g": initial,
                "remaining_g": remaining,
                "used_g": initial - remaining,
                "usage_percentage": usage_pct,
                "quantity_desc": row[4],
                "location": row[5],
                "expiry_date": row[6],
                "nutrition_per_100g": {
                    "calories": row[7],
                    "protein": row[8]
                } if row[7] else None
            })
        
        # Calculate total remaining nutrition
        total_calories = sum((i['nutrition_per_100g']['calories'] or 0) * i['remaining_g'] / 100 
                            for i in items if i['nutrition_per_100g'])
        total_protein = sum((i['nutrition_per_100g']['protein'] or 0) * i['remaining_g'] / 100 
                           for i in items if i['nutrition_per_100g'])
        
        return {
            "status": "success",
            "data": {
                "items": items,
                "total_items": len(items),
                "total_remaining_calories": round(total_calories),
                "total_remaining_protein_g": round(total_protein, 1)
            }
        }
        
    except sqlite3.Error as e:
        return {"status": "error", "error": "database_error", "message": str(e)}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Pantry manager')
    parser.add_argument('--user', required=True, help='Username')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add item
    add_parser = subparsers.add_parser('add', help='Add item to pantry')
    add_parser.add_argument('--food', required=True, help='Food name')
    add_parser.add_argument('--quantity', type=float, help='Quantity in grams')
    add_parser.add_argument('--quantity-desc', help='Quantity description (e.g., 2个)')
    add_parser.add_argument('--location', default='fridge', 
                           choices=['fridge', 'freezer', 'pantry', 'counter'],
                           help='Storage location')
    add_parser.add_argument('--purchase', help='Purchase date (YYYY-MM-DD)')
    add_parser.add_argument('--expiry', help='Expiry date (YYYY-MM-DD)')
    add_parser.add_argument('--notes', help='Notes')
    
    # List items
    list_parser = subparsers.add_parser('list', help='List pantry items')
    list_parser.add_argument('--location', choices=['fridge', 'freezer', 'pantry', 'counter'])
    list_parser.add_argument('--expiring', type=int, metavar='DAYS',
                            help='Show items expiring within N days')
    
    # Remove item
    remove_parser = subparsers.add_parser('remove', help='Remove item')
    remove_parser.add_argument('--item-id', type=int, required=True, help='Item ID')
    
    # Summary
    subparsers.add_parser('summary', help='Get pantry nutrition summary')
    
    # Use item
    use_parser = subparsers.add_parser('use', help='Record usage of pantry item')
    use_parser.add_argument('--item-id', type=int, required=True, help='Pantry item ID')
    use_parser.add_argument('--amount', type=float, required=True, help='Amount used in grams')
    use_parser.add_argument('--meal-id', type=int, help='Link to meal ID (optional)')
    use_parser.add_argument('--notes', help='Notes')
    
    # Check remaining
    subparsers.add_parser('remaining', help='Check remaining quantities')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        result = add_item(args)
    elif args.command == 'list':
        result = list_items(args)
    elif args.command == 'remove':
        result = remove_item(args)
    elif args.command == 'summary':
        result = get_pantry_nutrition_summary(args.user)
    elif args.command == 'use':
        result = use_item(args)
    elif args.command == 'remaining':
        result = check_remaining(args)
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == '__main__':
    main()
