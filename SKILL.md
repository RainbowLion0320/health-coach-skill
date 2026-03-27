---
name: health-coach
description: |
  Personal health data management and intelligent diet recommendation system.
  Use when users need to:
  - Record and track body metrics (weight, height, BMI, body fat)
  - Log daily meals and dietary intake
  - Query food nutrition information
  - Get personalized diet recommendations based on health goals
  - Analyze nutrition trends and generate reports
  - Identify foods from photos and estimate nutritional content
  
  Supports multi-user data isolation, time-series tracking, and extensible food database.
---

# Health Coach Skill

A comprehensive personal health management system for tracking body metrics, logging meals, analyzing nutrition, and receiving intelligent diet recommendations.

## Quick Start

### 1. Initialize Database

```bash
python3 scripts/init_db.py --user <username>
```

Creates isolated SQLite database for the user with all required tables.

### 2. Set Up User Profile

```bash
python3 scripts/user_profile.py --user <username> set \
  --name "Robert" \
  --gender male \
  --birth-date 1994-05-15 \
  --height-cm 175 \
  --target-weight 70 \
  --activity-level moderate \
  --goal-type maintain
```

### 3. Log Daily Weight

```bash
python3 scripts/body_metrics.py --user <username> log-weight --weight 72.5
```

### 4. Log a Meal

```bash
python3 scripts/meal_logger.py --user <username> log \
  --meal-type lunch \
  --foods "米饭:150g, 鸡胸肉:100g, 西兰花:100g"
```

### 5. Get Diet Recommendation

```bash
python3 scripts/diet_recommender.py --user <username> recommend --meal-type dinner
```

## Architecture

See [references/ARCHITECTURE.md](references/ARCHITECTURE.md) for system design and data flow.

## Database Schema

See [references/DATABASE_SCHEMA.md](references/DATABASE_SCHEMA.md) for complete ER diagram and table definitions.

## API Reference

See [references/API_REFERENCE.md](references/API_REFERENCE.md) for all script parameters and return formats.

## Food Database

See [references/FOOD_DATABASE.md](references/FOOD_DATABASE.md) for nutrition data sources and extension guide.

## Data Storage

Each user has an isolated SQLite database stored at:
```
~/.openclaw/workspace/skills/health-coach/data/<username>.db
```

## Common Workflows

### Daily Logging Workflow
1. Morning: Log weight with `body_metrics.py log-weight`
2. After meals: Log food with `meal_logger.py log`
3. Evening: Review daily nutrition summary

### Weekly Review Workflow
1. Generate weekly report with `report_generator.py weekly`
2. Check weight trend
3. Adjust targets if needed with `user_profile.py update`

### Photo Food Recognition
1. Save food photo to accessible path
2. Run: `python3 scripts/food_analyzer.py --user <username> identify --image <path>`
3. Review identified foods and confirm/edit quantities
4. Log confirmed foods with `meal_logger.py log`
