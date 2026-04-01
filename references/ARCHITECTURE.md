# NutriCoach Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│              (CLI Scripts / Agent Conversation)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Services Layer                       │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│   User      │   Body      │   Meal      │   Diet            │
│   Profile   │   Metrics   │   Logger    │   Recommender     │
│   Service   │   Service   │   Service   │   Service         │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       └─────────────┴──────┬──────┴────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│              (SQLite with repository pattern)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                        │
│         (User-isolated SQLite databases)                     │
│    ~/.openclaw/workspace/skills/nutricoach/data/*.db       │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Profile Setup Flow

```
User Input → Validation → Calculate BMR/TDEE → Store in users table
                                              ↓
                                    Initialize related tables
```

### 2. Daily Weight Logging Flow

```
Weight Input → Validate → Calculate BMI → Store in body_metrics
                ↓                              ↓
            Check range                  Update user stats
            anomalies
```

### 3. Meal Logging Flow

```
Food Input → Parse foods → Query nutrition DB → Calculate totals
    ↓                                              ↓
Photo? → Vision API → Identify food → Confirm → Store in meals
                                                food_items
```

### 4. Recommendation Flow

```
User Goal + History → Calculate needs → Query suitable foods
         ↓                                    ↓
   Current intake                      Filter by preferences
         ↓                                    ↓
   Remaining budget → Generate options → Rank by nutrition
```

## Extensibility Points

### 1. Nutrition Data Sources

```python
# Interface: NutritionProvider
class NutritionProvider:
    def search(self, food_name: str) -> List[FoodItem]
    def get_by_id(self, food_id: str) -> FoodItem
    def batch_import(self, data: List[Dict]) -> int

# Implementations:
# - USDAFoodProvider (USDA FoodData Central API)
# - CNFoodProvider (中国食物成分表)
# - CustomFoodProvider (用户自定义)
```

### 2. Recommendation Algorithms

```python
# Interface: RecommendationEngine
class RecommendationEngine:
    def recommend(self, user: User, meal_type: str, constraints: Dict) -> List[MealOption]

# Implementations:
# - BalancedMacroEngine (均衡宏量营养素)
# - LowCarbEngine (低碳)
# - HighProteinEngine (高蛋白)
# - CalorieDeficitEngine (热量缺口)
```

### 3. Analysis Reports

```python
# Interface: ReportGenerator
class ReportGenerator:
    def generate(self, user: User, period: str) -> Report

# Implementations:
# - WeeklySummaryReport
# - MonthlyTrendReport
# - NutritionAnalysisReport
# - GoalProgressReport
```

## Multi-User Isolation

Each user has a dedicated database file:

```
data/
├── robert.db          # Robert's health data
├── alice.db           # Alice's health data
└── bob.db             # Bob's health data
```

Benefits:
- True data isolation
- Easy backup/restore per user
- No schema migration complexity
- Portable (single file per user)

## Configuration

### User Configuration

User-specific config: `data/user_config.yaml` (not in git)

```yaml
# Vision OCR Configuration (Optional)
vision:
  api_key: "your-api-key"
  base_url: "https://api.moonshot.cn/v1"
  model: "kimi-k2.5"
```

**Priority**: Environment variable > Config file > Default (local OCR)

### Global Defaults

Default values are hardcoded in scripts:
- BMR formula: Mifflin-St Jeor
- Activity multipliers: standard values
- Macro split: 30/40/30 (protein/carbs/fat)
- Data retention: 365 days

---

## 2026-04-01 更新：新增功能模块

### 1. 运动记录模块 (Exercise Logger)

**功能**: 记录运动类型、时长、消耗卡路里
**CLI**: `python3 scripts/exercise_logger.py log --type running --duration 30`
**Web API**: `/api/exercise-log`, `/api/exercise-history`
**数据库表**: `exercises`

### 2. 饮水记录模块 (Water Logger)

**功能**: 记录每日饮水量，支持目标设定
**CLI**: `python3 scripts/water_logger.py log 250`
**Web API**: `/api/water-log`, `/api/water-history`
**数据库表**: `water_intake`
**默认目标**: 2000ml/天

### 3. 睡眠记录模块 (Sleep Logger)

**功能**: 记录睡眠时长和质量
**CLI**: `python3 scripts/sleep_logger.py log --hours 7.5 --quality good`
**Web API**: `/api/sleep-log`, `/api/sleep-history`
**数据库表**: `sleep_records`
**质量等级**: poor/fair/good/excellent

### 4. 多语言支持 (i18n)

**支持语言**: 中文(zh-CN)、英文(en-US)
**实现方式**: 
- 前端: `scripts/web/i18n.py` 翻译字典
- 切换方式: Web UI 右上角语言按钮
- 存储: localStorage 持久化用户选择

### 5. 数据库表结构更新

新增表：
```sql
-- 运动记录
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    exercise_type TEXT,
    duration_minutes INTEGER,
    calories_burned REAL,
    intensity TEXT,
    exercised_at DATETIME
);

-- 饮水记录
CREATE TABLE water_intake (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    amount_ml INTEGER,
    logged_at DATETIME
);

-- 睡眠记录
CREATE TABLE sleep_records (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    sleep_hours REAL,
    sleep_quality TEXT,
    sleep_start DATETIME,
    sleep_end DATETIME
);

-- 用户设置（语言等）
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    language TEXT DEFAULT 'zh-CN'
);
```

### 6. Web UI 更新

新增标签页：
- 运动 (Exercise)
- 饮水 (Water)
- 睡眠 (Sleep)

新增功能：
- 语言切换按钮
- 快速记录按钮（+250ml, +500ml 饮水）
- 进度条可视化（饮水目标完成度）

### 7. 文件清单更新

新增脚本：
- `scripts/exercise_logger.py`
- `scripts/water_logger.py`
- `scripts/sleep_logger.py`
- `scripts/web/i18n.py`

修改文件：
- `scripts/web/routes.py` - 新增 API 端点
- `scripts/web/utils.py` - 支持环境变量传参
- `scripts/web/static/app.js` - 新增加载函数和语言切换
- `templates/dashboard.html` - 新增标签页和语言按钮
