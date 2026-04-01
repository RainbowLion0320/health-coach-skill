"""
Internationalization (i18n) Support for NutriCoach.
Supports: Chinese (zh-CN), English (en-US)
"""

# Translation strings
TRANSLATIONS = {
    "zh-CN": {
        # Navigation
        "nav_overview": "概览",
        "nav_diet": "饮食",
        "nav_pantry": "食材库",
        "nav_recipes": "菜谱",
        "nav_exercise": "运动",
        "nav_water": "饮水",
        "nav_sleep": "睡眠",
        "nav_settings": "设置",
        
        # Overview
        "overview_title": "健康概览",
        "overview_weight_trend": "体重趋势",
        "overview_nutrition_trend": "营养趋势",
        "overview_today_summary": "今日摘要",
        
        # Weight & Nutrition
        "weight_trend": "体重趋势 (最近30天)",
        "nutrition_trend": "营养趋势 (最近30天)",
        "today_summary": "今日概览",
        "calories": "卡路里",
        "protein": "蛋白质",
        "carbs": "碳水",
        "fat": "脂肪",
        "fiber": "纤维",
        
        # Diet
        "add_meal": "添加饮食",
        "breakfast": "早餐",
        "lunch": "午餐",
        "dinner": "晚餐",
        "snack": "零食",
        
        # Pantry
        "pantry_title": "食材库存",
        "add_item": "添加食材",
        "category": "分类",
        "quantity": "数量",
        "expiry": "过期日期",
        
        # Exercise
        "exercise_title": "运动记录",
        "log_exercise": "记录运动",
        "duration": "时长",
        "intensity": "强度",
        
        # Water
        "water_title": "饮水记录",
        "log_water": "记录饮水",
        "daily_goal": "每日目标",
        
        # Sleep
        "sleep_title": "睡眠记录",
        "log_sleep": "记录睡眠",
        "hours": "睡眠时长",
        "quality": "睡眠质量",
        
        # Common
        "save": "保存",
        "cancel": "取消",
        "delete": "删除",
        "edit": "编辑",
        "loading": "加载中...",
        "no_data": "暂无数据",
        "today": "今天",
        "yesterday": "昨天",
        
        # Quality ratings
        "quality_excellent": "优秀",
        "quality_good": "良好",
        "quality_fair": "一般",
        "quality_poor": "较差",
        
        # Intensity
        "intensity_light": "轻度",
        "intensity_moderate": "中度",
        "intensity_intense": "激烈",
    },
    
    "en-US": {
        # Navigation
        "nav_overview": "Overview",
        "nav_diet": "Diet",
        "nav_pantry": "Pantry",
        "nav_recipes": "Recipes",
        "nav_exercise": "Exercise",
        "nav_water": "Water",
        "nav_sleep": "Sleep",
        "nav_settings": "Settings",
        
        # Overview
        "overview_title": "Health Overview",
        "overview_weight_trend": "Weight Trend",
        "overview_nutrition_trend": "Nutrition Trend",
        "overview_today_summary": "Today's Summary",
        
        # Weight & Nutrition
        "weight_trend": "Weight Trend (Last 30 Days)",
        "nutrition_trend": "Nutrition Trend (Last 30 Days)",
        "today_summary": "Today's Summary",
        "calories": "Calories",
        "protein": "Protein",
        "carbs": "Carbs",
        "fat": "Fat",
        "fiber": "Fiber",
        
        # Diet
        "add_meal": "Add Meal",
        "breakfast": "Breakfast",
        "lunch": "Lunch",
        "dinner": "Dinner",
        "snack": "Snack",
        
        # Pantry
        "pantry_title": "Pantry Inventory",
        "add_item": "Add Item",
        "category": "Category",
        "quantity": "Quantity",
        "expiry": "Expiry Date",
        
        # Exercise
        "exercise_title": "Exercise Log",
        "log_exercise": "Log Exercise",
        "duration": "Duration",
        "intensity": "Intensity",
        
        # Water
        "water_title": "Water Intake",
        "log_water": "Log Water",
        "daily_goal": "Daily Goal",
        
        # Sleep
        "sleep_title": "Sleep Log",
        "log_sleep": "Log Sleep",
        "hours": "Hours",
        "quality": "Quality",
        
        # Common
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "loading": "Loading...",
        "no_data": "No Data",
        "today": "Today",
        "yesterday": "Yesterday",
        
        # Quality ratings
        "quality_excellent": "Excellent",
        "quality_good": "Good",
        "quality_fair": "Fair",
        "quality_poor": "Poor",
        
        # Intensity
        "intensity_light": "Light",
        "intensity_moderate": "Moderate",
        "intensity_intense": "Intense",
    }
}


def get_translation(lang: str, key: str, default: str = None) -> str:
    """Get translated string."""
    if lang not in TRANSLATIONS:
        lang = "zh-CN"
    
    return TRANSLATIONS.get(lang, {}).get(key, default or key)


def get_available_languages():
    """Get list of available language codes."""
    return list(TRANSLATIONS.keys())


def get_language_name(lang: str) -> str:
    """Get human-readable language name."""
    names = {
        "zh-CN": "中文",
        "en-US": "English"
    }
    return names.get(lang, lang)