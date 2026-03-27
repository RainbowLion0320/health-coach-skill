# Database Schema

## Overview

SQLite database per user with foreign key constraints enabled.

## ER Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │  body_metrics   │     │     meals       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────┤ user_id (FK)    │     │ user_id (FK)    │
│ username (UQ)   │     │ id (PK)         │     │ id (PK)         │
│ display_name    │     │ weight_kg       │     │ meal_type       │
│ gender          │     │ height_cm       │     │ eaten_at        │
│ birth_date      │     │ body_fat_pct    │     │ notes           │
│ height_cm       │     │ bmi             │     │ total_calories  │
│ target_weight_kg│     │ recorded_at     │     │ total_protein_g │
│ activity_level  │     │ source          │     │ total_carbs_g   │
│ goal_type       │     └─────────────────┘     │ total_fat_g     │
│ bmr_formula     │              │              │ created_at      │
│ bmr             │              │              └─────────────────┘
│ tdee            │              │                        │
│ created_at      │              │                        │
│ updated_at      │              │              ┌─────────────────┐
└─────────────────┘              │              │   food_items    │
                                 │              ├─────────────────┤
                                 │              │ id (PK)         │
                                 │              │ meal_id (FK)    │
                                 │              │ food_name       │
                                 │              │ quantity_g      │
                                 │              │ calories        │
                                 │              │ protein_g       │
                                 │              │ carbs_g         │
                                 │              │ fat_g           │
                                 │              │ fiber_g         │
                                 │              │ source          │
                                 │              └─────────────────┘
                                 │
                    ┌────────────┘
                    │
         ┌─────────────────┐
         │  custom_foods   │
         ├─────────────────┤
         │ id (PK)         │
         │ user_id (FK)    │
         │ name            │
         │ category        │
         │ calories_per_100g│
         │ protein_per_100g│
         │ carbs_per_100g  │
         │ fat_per_100g    │
         │ fiber_per_100g  │
         │ is_public       │
         │ created_at      │
         └─────────────────┘
```

## Table Definitions

### users

User profile and metabolic calculations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户ID |
| username | TEXT | UNIQUE NOT NULL | 用户名（英文，用于文件名） |
| display_name | TEXT | | 显示名称 |
| gender | TEXT | CHECK (gender IN ('male', 'female')) | 性别 |
| birth_date | DATE | | 出生日期 |
| height_cm | REAL | CHECK (height_cm > 0) | 身高（厘米） |
| target_weight_kg | REAL | | 目标体重（公斤） |
| activity_level | TEXT | CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')) | 活动水平 |
| goal_type | TEXT | CHECK (goal_type IN ('lose', 'maintain', 'gain')) | 目标类型 |
| bmr_formula | TEXT | DEFAULT 'mifflin_st_jeor' | BMR计算公式 |
| bmr | REAL | | 基础代谢率（千卡） |
| tdee | REAL | | 每日总能量消耗（千卡） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**Indexes:**
- `idx_users_username` ON username

### body_metrics

Time-series body measurements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 记录ID |
| user_id | INTEGER | FOREIGN KEY users(id) ON DELETE CASCADE | 用户ID |
| weight_kg | REAL | NOT NULL CHECK (weight_kg > 0) | 体重（公斤） |
| height_cm | REAL | | 身高（厘米，快照） |
| body_fat_pct | REAL | CHECK (body_fat_pct >= 0 AND body_fat_pct <= 100) | 体脂率（%） |
| bmi | REAL | | BMI（自动计算） |
| recorded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 记录时间 |
| source | TEXT | DEFAULT 'manual' | 数据来源 |
| notes | TEXT | | 备注 |

**Indexes:**
- `idx_metrics_user_date` ON user_id, recorded_at
- `idx_metrics_recorded` ON recorded_at

### meals

Daily meal records with aggregated nutrition.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 餐食ID |
| user_id | INTEGER | FOREIGN KEY users(id) ON DELETE CASCADE | 用户ID |
| meal_type | TEXT | CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')) | 餐食类型 |
| eaten_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 进食时间 |
| notes | TEXT | | 备注 |
| total_calories | REAL | DEFAULT 0 | 总热量（千卡） |
| total_protein_g | REAL | DEFAULT 0 | 总蛋白质（克） |
| total_carbs_g | REAL | DEFAULT 0 | 总碳水（克） |
| total_fat_g | REAL | DEFAULT 0 | 总脂肪（克） |
| total_fiber_g | REAL | DEFAULT 0 | 总纤维（克） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**Indexes:**
- `idx_meals_user_date` ON user_id, eaten_at
- `idx_meals_type` ON meal_type

### food_items

Individual food items within a meal.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 食物项ID |
| meal_id | INTEGER | FOREIGN KEY meals(id) ON DELETE CASCADE | 餐食ID |
| food_name | TEXT | NOT NULL | 食物名称 |
| quantity_g | REAL | NOT NULL CHECK (quantity_g > 0) | 重量（克） |
| calories | REAL | NOT NULL | 热量（千卡） |
| protein_g | REAL | DEFAULT 0 | 蛋白质（克） |
| carbs_g | REAL | DEFAULT 0 | 碳水（克） |
| fat_g | REAL | DEFAULT 0 | 脂肪（克） |
| fiber_g | REAL | DEFAULT 0 | 纤维（克） |
| source | TEXT | DEFAULT 'database' | 数据来源 |

**Indexes:**
- `idx_food_items_meal` ON meal_id
- `idx_food_items_name` ON food_name

### custom_foods

User-defined or imported food items.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 食物ID |
| user_id | INTEGER | FOREIGN KEY users(id) ON DELETE CASCADE | 用户ID |
| name | TEXT | NOT NULL | 食物名称 |
| category | TEXT | | 分类 |
| calories_per_100g | REAL | NOT NULL | 每100克热量 |
| protein_per_100g | REAL | DEFAULT 0 | 每100克蛋白质 |
| carbs_per_100g | REAL | DEFAULT 0 | 每100克碳水 |
| fat_per_100g | REAL | DEFAULT 0 | 每100克脂肪 |
| fiber_per_100g | REAL | DEFAULT 0 | 每100克纤维 |
| is_public | BOOLEAN | DEFAULT 0 | 是否公开分享 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**Indexes:**
- `idx_custom_foods_user` ON user_id
- `idx_custom_foods_name` ON name

## SQL Initialization

```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    gender TEXT CHECK (gender IN ('male', 'female')),
    birth_date DATE,
    height_cm REAL CHECK (height_cm > 0),
    target_weight_kg REAL,
    activity_level TEXT CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
    goal_type TEXT CHECK (goal_type IN ('lose', 'maintain', 'gain')),
    bmr_formula TEXT DEFAULT 'mifflin_st_jeor',
    bmr REAL,
    tdee REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Body metrics table
CREATE TABLE IF NOT EXISTS body_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight_kg REAL NOT NULL CHECK (weight_kg > 0),
    height_cm REAL,
    body_fat_pct REAL CHECK (body_fat_pct >= 0 AND body_fat_pct <= 100),
    bmi REAL,
    recorded_at DATETIME DEFAULT