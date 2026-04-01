// NutriCoach Dashboard JavaScript

let currentItemId = null;
let currentItemName = null;
let currentItemRemaining = 0;
let currentItemUnit = 'g';
let currentShelfLife = 7;
let pantryViewMode = 'location';
let pantryData = null;
let currentLang = localStorage.getItem('nutricoach_lang') || 'zh-CN';

// Translation data (embedded for simplicity)
const i18n = {
    "zh-CN": {
        "nav_overview": "概览", "nav_pantry": "食材", "nav_exercise": "运动", "nav_water": "饮水", "nav_sleep": "睡眠",
        "weight_trend": "体重趋势 (最近30天)", "nutrition_trend": "营养趋势 (最近30天)",
        "today_summary": "今日概览", "calories": "热量", "protein": "蛋白质", "carbs": "碳水", "fat": "脂肪",
        "exercise_title": "运动记录", "exercise_log": "记录运动", "exercise_type": "运动类型", "duration": "时长(分钟)",
        "water_title": "饮水记录", "water_log": "记录饮水", "daily_goal": "目标", "amount_ml": "ml",
        "sleep_title": "睡眠记录", "sleep_log": "记录睡眠", "hours": "时长(小时)", "quality": "质量",
        "no_data": "暂无数据", "save": "保存", "loading": "加载中..."
    },
    "en-US": {
        "nav_overview": "Overview", "nav_pantry": "Pantry", "nav_exercise": "Exercise", "nav_water": "Water", "nav_sleep": "Sleep",
        "weight_trend": "Weight Trend (30 days)", "nutrition_trend": "Nutrition Trend (30 days)",
        "today_summary": "Today", "calories": "Calories", "protein": "Protein", "carbs": "Carbs", "fat": "Fat",
        "exercise_title": "Exercise Log", "exercise_log": "Log Exercise", "exercise_type": "Type", "duration": "Minutes",
        "water_title": "Water Intake", "water_log": "Log Water", "daily_goal": "Goal", "amount_ml": "ml",
        "sleep_title": "Sleep Log", "sleep_log": "Log Sleep", "hours": "Hours", "quality": "Quality",
        "no_data": "No data", "save": "Save", "loading": "Loading..."
    }
};

function t(key) {
    return i18n[currentLang]?.[key] || key;
}

function toggleLanguage() {
    currentLang = currentLang === 'zh-CN' ? 'en-US' : 'zh-CN';
    localStorage.setItem('nutricoach_lang', currentLang);
    
    document.getElementById('html-root').lang = currentLang;
    document.getElementById('lang-btn').textContent = currentLang === 'zh-CN' ? 'EN' : '中';
    
    // Update all translatable elements
    document.querySelectorAll('[data-i18]').forEach(el => {
        const key = el.getAttribute('data-i18');
        el.textContent = t(key);
    });
    
    // Update tab labels
    const tabLabels = {
        'overview': 'nav_overview', 'pantry': 'nav_pantry', 
        'exercise': 'nav_exercise', 'water': 'nav_water', 'sleep': 'nav_sleep'
    };
    document.querySelectorAll('.tab').forEach(tab => {
        const tabName = tab.getAttribute('onclick')?.match(/'(.+)'/)?.[1];
        if (tabName && tabLabels[tabName]) {
            tab.setAttribute('data-i18', tabLabels[tabName]);
            tab.textContent = t(tabLabels[tabName]);
        }
    });
}

// Initialize language
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('lang-btn').textContent = currentLang === 'zh-CN' ? 'EN' : '中';
});

// Tab switching
function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'pantry') loadPantry();
    else if (tabName === 'exercise') loadExercise();
    else if (tabName === 'water') loadWater();
    else if (tabName === 'sleep') loadSleep();
}

// Load overview data
fetch('/api/summary').then(r => r.json()).then(data => {
    const daily = data.daily?.data || {};
    document.getElementById('daily-summary').innerHTML = `
        <div class="stat"><span>热量</span><span class="stat-value">${Math.round(daily.totals?.calories || 0)}/${Math.round(daily.tdee || 2000)} kcal</span></div>
        <div class="stat"><span>蛋白质</span><span class="stat-value">${Math.round(daily.totals?.protein_g || 0)}g</span></div>
        <div class="stat"><span>碳水</span><span class="stat-value">${Math.round(daily.totals?.carbs_g || 0)}g</span></div>
        <div class="stat"><span>脂肪</span><span class="stat-value">${Math.round(daily.totals?.fat_g || 0)}g</span></div>
    `;
});

// Load profile
fetch('/api/profile').then(r => r.json()).then(data => {
    const p = data.data || {};
    document.getElementById('profile').innerHTML = `
        <div class="stat"><span>身高</span><span class="stat-value">${p.height_cm} cm</span></div>
        <div class="stat"><span>BMR</span><span class="stat-value">${Math.round(p.bmr || 0)} kcal</span></div>
        <div class="stat"><span>TDEE</span><span class="stat-value">${Math.round(p.tdee || 0)} kcal</span></div>
        <div class="stat"><span>目标</span><span class="stat-value">${p.goal_type === 'lose' ? '减脂' : p.goal_type === 'gain' ? '增肌' : '维持'}</span></div>
    `;
});

// Load weight history and render chart
fetch('/api/weight-history?days=30').then(r => r.json()).then(data => {
    if (data.status === 'success' && data.data?.records?.length > 0) {
        // Take last 30 records, reverse to show chronological order (earliest first)
        const records = data.data.records.slice(-30).reverse();
        const labels = records.map(r => r.recorded_at?.slice(5, 10) || '');
        const weights = records.map(r => r.weight_kg);

        new Chart(document.getElementById('weightChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '体重 (kg)',
                    data: weights,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: false }
                }
            }
        });
    } else {
        document.getElementById('weightChart').parentElement.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无体重数据</p>';
    }
});

// Load nutrition history and render chart
fetch('/api/nutrition-history?days=30').then(r => r.json()).then(data => {
    if (data.status === 'success' && data.data?.meals?.length > 0) {
        const meals = data.data.meals;
        
        // Group meals by date and sum nutrients
        const dailyTotals = {};
        meals.forEach(meal => {
            const date = meal.eaten_at?.slice(0, 10) || '';
            if (!date) return;
            
            if (!dailyTotals[date]) {
                dailyTotals[date] = { calories: 0, protein: 0, carbs: 0, fat: 0 };
            }
            dailyTotals[date].calories += meal.total_calories || 0;
            dailyTotals[date].protein += meal.total_protein_g || 0;
            dailyTotals[date].carbs += meal.total_carbs_g || 0;
            dailyTotals[date].fat += meal.total_fat_g || 0;
        });
        
        // Convert to array and sort by date
        const days = Object.entries(dailyTotals)
            .map(([date, totals]) => ({ date, ...totals }))
            .sort((a, b) => new Date(a.date) - new Date(b.date));
        
        if (days.length === 0) {
            document.getElementById('nutritionChart').parentElement.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无营养数据</p>';
            return;
        }
        
        const labels = days.map(d => d.date?.slice(5, 10) || '');
        const calories = days.map(d => d.calories || 0);
        const protein = days.map(d => d.protein || 0);
        const carbs = days.map(d => d.carbs || 0);
        const fat = days.map(d => d.fat || 0);

        new Chart(document.getElementById('nutritionChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '热量 (kcal)',
                        data: calories,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.3,
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: '蛋白质 (g)',
                        data: protein,
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.3,
                        fill: false,
                        yAxisID: 'y1'
                    },
                    {
                        label: '碳水 (g)',
                        data: carbs,
                        borderColor: '#ff9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        tension: 0.3,
                        fill: false,
                        yAxisID: 'y1'
                    },
                    {
                        label: '脂肪 (g)',
                        data: fat,
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        tension: 0.3,
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { 
                        display: true,
                        position: 'top',
                        labels: { font: { size: 11 } }
                    } 
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: '热量 (kcal)' },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: '营养素 (g)' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    } else {
        document.getElementById('nutritionChart').parentElement.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无营养数据</p>';
    }
});

// Pantry view switching
function showPantryView(mode) {
    pantryViewMode = mode;
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderPantry();
}

// Get expiry badge
function getExpiryBadge(item) {
    if (!item.expiry_date) return { class: 'expiry-ok', text: '新鲜' };
    const today = new Date();
    today.setHours(0, 0, 0, 0);  // 只比较日期部分
    const expiry = new Date(item.expiry_date);
    expiry.setHours(0, 0, 0, 0);
    const daysLeft = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { class: 'expiry-expired', text: '已过期' };
    if (daysLeft === 0) return { class: 'expiry-urgent', text: '今天' };
    if (daysLeft === 1) return { class: 'expiry-urgent', text: '明天' };
    if (daysLeft <= 3) return { class: 'expiry-soon', text: `${daysLeft}天` };
    return { class: 'expiry-ok', text: `${daysLeft}天` };
}

// Location name mapping
const LOCATION_NAMES = {
    'fridge': '冰箱',
    'freezer': '冷冻',
    'pantry': '干货区',
    'counter': '台面'
};

// Category mapping
const CATEGORY_MAP = {
    'protein': '蛋白质',
    'vegetable': '蔬菜',
    'carb': '碳水',
    'fruit': '水果',
    'dairy': '乳制品',
    'fat': '脂肪',
    'other': '其他'
};

// Render pantry item
function renderItem(item) {
    const expiry = getExpiryBadge(item);
    const percent = Math.round((item.remaining_g / item.initial_g) * 100);
    const progressClass = percent > 50 ? 'pantry-progress-high' : percent > 20 ? 'pantry-progress-medium' : 'pantry-progress-low';
    const unit = item.unit || 'g';
    const locationName = LOCATION_NAMES[item.location] || item.location || '冰箱';
    const category = item.category || 'other';
    // Escape food name for use in onclick attribute
    const escapedFoodName = item.food_name.replace(/'/g, "\\'").replace(/"/g, '\\"');

    return `
        <div class="pantry-item">
            <div class="pantry-item-header">
                <div class="pantry-info">
                    <div class="pantry-name" title="${item.food_name}">${item.food_name}</div>
                    <div class="pantry-qty">${item.remaining_g}${unit}</div>
                </div>
                <div class="pantry-actions">
                    <span class="expiry-badge ${expiry.class}">${expiry.text}</span>
                    <button class="action-btn" onclick="openEditModal(${item.id}, '${escapedFoodName}', ${item.remaining_g}, '${unit}', ${item.shelf_life_days || 7}, '${item.purchase_date || ''}', '${item.expiry_date || ''}', '${locationName}', '${category}')">编辑</button>
                </div>
            </div>
            <div class="pantry-progress">
                <div class="pantry-progress-bar ${progressClass}" style="width: ${percent}%"></div>
            </div>
        </div>
    `;
}

// Render pantry
function renderPantry() {
    if (!pantryData) return;
    let html = '';

    if (pantryViewMode === 'location') {
        const locationNames = {'冰箱': '冰箱', '冷冻': '冷冻', '干货区': '干货区', '台面': '台面'};
        for (const [location, items] of Object.entries(pantryData.grouped || {})) {
            if (items.length === 0) continue;
            html += `<div class="location-section">`;
            html += `<div class="location-title">${locationNames[location]} (${items.length})</div>`;
            html += `<div class="pantry-grid">`;
            for (const item of items) html += renderItem(item);
            html += `</div></div>`;
        }
    } else {
        const categoryIcons = {'蛋白质': '', '蔬菜': '', '碳水': '', '水果': '', '乳制品': '', '脂肪': '', '其他': ''};
        for (const [category, items] of Object.entries(pantryData.by_category || {})) {
            if (items.length === 0) continue;
            html += `<div class="location-section">`;
            html += `<div class="location-title">${categoryIcons[category]} ${category} (${items.length})</div>`;
            html += `<div class="pantry-grid">`;
            for (const item of items) html += renderItem(item);
            html += `</div></div>`;
        }
    }
    document.getElementById('pantry-content').innerHTML = html;
}

// Load pantry
function loadPantry() {
    fetch('/api/pantry').then(r => r.json()).then(data => {
        if (data.status !== 'success') {
            document.getElementById('pantry-content').innerHTML = '<p>加载失败</p>';
            return;
        }
        pantryData = data.data;
        renderPantry();
    });
}

// Calculate expiry
function calculateExpiry() {
    const purchase = document.getElementById('editPurchase').value;
    const shelfLife = parseInt(document.getElementById('editShelfLife').value);
    const expirySpan = document.getElementById('editCalculatedExpiry');
    if (purchase && shelfLife > 0) {
        const pDate = new Date(purchase);
        const eDate = new Date(pDate.getTime() + shelfLife * 24 * 60 * 60 * 1000);
        expirySpan.textContent = eDate.toLocaleDateString('zh-CN');
    } else {
        expirySpan.textContent = '-';
    }
}

// Modal functions
function openEditModal(id, name, remaining, unit, shelfLife, purchase, expiry, location, category) {
    currentItemId = id;
    currentItemName = name;
    currentItemRemaining = remaining;
    currentItemUnit = unit || 'g';
    currentShelfLife = shelfLife;
    document.getElementById('editModalItemName').textContent = `${name} (剩余 ${remaining}${currentItemUnit})`;
    document.getElementById('editUseAmount').placeholder = `使用重量 (${currentItemUnit})`;
    document.getElementById('editUseAmount').value = '';
    document.getElementById('editPurchase').value = purchase || '';
    document.getElementById('editShelfLife').value = shelfLife || 7;
    document.getElementById('editLocation').value = location || '冰箱';
    document.getElementById('editCategory').value = category || 'other';
    calculateExpiry();
    document.getElementById('editModal').classList.add('active');
}

function openAddModal() {
    document.getElementById('addFoodName').value = '';
    document.getElementById('addQuantity').value = '';
    document.getElementById('addExpiry').value = '';
    document.getElementById('addLocation').value = 'auto';
    document.getElementById('addModal').classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

function confirmUseFromEdit() {
    const amount = parseFloat(document.getElementById('editUseAmount').value);
    const unit = currentItemUnit || 'g';
    if (!amount || amount <= 0) {
        alert('请输入有效的使用量');
        return;
    }
    if (amount > currentItemRemaining) {
        alert(`使用量不能超过剩余量 (${currentItemRemaining}${unit})`);
        return;
    }
    fetch('/api/pantry/use', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: currentItemId, amount: amount })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess(`已记录：使用 ${amount}${unit} ${currentItemName}`);
            currentItemRemaining -= amount;
            document.getElementById('editModalItemName').textContent = `${currentItemName} (剩余 ${currentItemRemaining}${unit})`;
            document.getElementById('editUseAmount').value = '';
            setTimeout(loadPantry, 500);
        } else {
            alert('失败：' + (data.message || data.error));
        }
    });
}

function confirmEdit() {
    const purchase = document.getElementById('editPurchase').value;
    const shelfLife = parseInt(document.getElementById('editShelfLife').value);
    const location = document.getElementById('editLocation').value;

    const body = { item_id: currentItemId };
    if (purchase) body.purchase = purchase;
    if (shelfLife > 0) body.shelf_life = shelfLife;
    if (location) body.location = location;

    fetch('/api/pantry/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess(`已更新：${currentItemName}`);
            closeModal('editModal');
            setTimeout(loadPantry, 500);
        } else {
            alert('失败：' + (data.message || data.error));
        }
    });
}

function confirmDelete() {
    if (!currentItemId) {
        alert('未选择食材');
        return;
    }
    
    if (!confirm(`确定要删除 "${currentItemName}" 吗？此操作不可恢复。`)) {
        return;
    }
    
    fetch('/api/pantry/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: currentItemId })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess(`已删除：${currentItemName}`);
            closeModal('editModal');
            setTimeout(loadPantry, 500);
        } else {
            alert('删除失败：' + (data.message || data.error));
        }
    });
}

function confirmAdd() {
    const food = document.getElementById('addFoodName').value.trim();
    const quantity = parseFloat(document.getElementById('addQuantity').value);
    const expiry = document.getElementById('addExpiry').value;
    const location = document.getElementById('addLocation').value;

    if (!food || !quantity) {
        alert('请填写完整信息');
        return;
    }

    const body = { food: food, quantity: quantity, location: location };
    if (expiry) body.expiry = expiry;

    fetch('/api/pantry/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess(`已添加：${food}`);
            closeModal('addModal');
            setTimeout(loadPantry, 500);
        } else {
            alert('失败：' + (data.message || data.error));
        }
    });
}

function showSuccess(msg) {
    const el = document.getElementById('success-msg');
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
}

// Auto-calculate expiry when inputs change
document.addEventListener('DOMContentLoaded', function() {
    const purchaseInput = document.getElementById('editPurchase');
    const shelfLifeInput = document.getElementById('editShelfLife');
    if (purchaseInput) purchaseInput.addEventListener('change', calculateExpiry);
    if (shelfLifeInput) shelfLifeInput.addEventListener('input', calculateExpiry);
});

window.onclick = function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
};

// ========== Exercise Tab ==========
function loadExercise() {
    fetch('/api/exercise-history?days=7')
        .then(r => r.json())
        .then(data => {
            const exercises = data.data?.exercises || [];
            const summary = data.data?.summary || {};
            
            if (exercises.length === 0) {
                document.getElementById('exercise-content').innerHTML = 
                    '<p style="text-align:center;color:#999;padding:40px;">' + t('no_data') + '</p>';
                return;
            }
            
            let html = '<div class="summary-stats">';
            html += '<div class="stat"><span>总时长</span><span class="stat-value">' + (summary.total_duration_minutes || 0) + ' min</span></div>';
            html += '<div class="stat"><span>消耗热量</span><span class="stat-value">' + (summary.total_calories || 0) + ' kcal</span></div>';
            html += '<div class="stat"><span>运动次数</span><span class="stat-value">' + (summary.session_count || 0) + '</span></div>';
            html += '</div><ul class="item-list">';
            
            exercises.forEach(ex => {
                html += '<li class="item-card"><span>' + ex.exercise_type + '</span>';
                html += '<span>' + ex.duration_minutes + ' min, ' + ex.calories_burned + ' cal</span></li>';
            });
            html += '</ul>';
            
            document.getElementById('exercise-content').innerHTML = html;
        });
}

function showExerciseModal() {
    const type = prompt('运动类型 (如: running, cycling, swimming):');
    if (!type) return;
    const duration = parseInt(prompt('时长(分钟):'));
    if (!duration) return;
    const calories = parseInt(prompt('消耗卡路里:') || '0');
    
    fetch('/api/exercise-log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ exercise_type: type, duration_minutes: duration, calories_burned: calories })
    }).then(r => r.json()).then(data => {
        if (data.status === 'success') showSuccess('运动已记录');
        loadExercise();
    });
}

// ========== Water Tab ==========
function loadWater() {
    fetch('/api/water-history?days=1')
        .then(r => r.json())
        .then(data => {
            const daily = data.data?.daily || [];
            const summary = data.data?.summary || {};
            
            let html = '<div class="water-today">';
            html += '<div class="water-progress"><div class="water-bar" style="width:' + 
                Math.min((summary.total_ml / 2000) * 100, 100) + '%"></div></div>';
            html += '<p>今日: <strong>' + (summary.total_ml || 0) + '</strong> / 2000 ml</p>';
            html += '</div>';
            
            if (daily.length === 0) {
                html += '<p style="text-align:center;color:#999;">' + t('no_data') + '</p>';
            }
            
            document.getElementById('water-content').innerHTML = html;
        });
}

function logWater(amount) {
    fetch('/api/water-log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ amount_ml: amount })
    }).then(r => r.json()).then(data => {
        if (data.status === 'success') showSuccess('已记录 ' + amount + 'ml');
        loadWater();
    });
}

// ========== Sleep Tab ==========
function loadSleep() {
    fetch('/api/sleep-history?days=7')
        .then(r => r.json())
        .then(data => {
            const records = data.data?.records || [];
            const summary = data.data?.summary || {};
            
            if (records.length === 0) {
                document.getElementById('sleep-content').innerHTML = 
                    '<p style="text-align:center;color:#999;padding:40px;">' + t('no_data') + '</p>';
                return;
            }
            
            let html = '<div class="summary-stats">';
            html += '<div class="stat"><span>平均时长</span><span class="stat-value">' + (summary.avg_hours || 0) + ' h</span></div>';
            html += '</div><ul class="item-list">';
            
            records.forEach(s => {
                const q = s.sleep_quality === 'excellent' ? '⭐' : s.sleep_quality === 'good' ? '👍' : '😐';
                html += '<li class="item-card"><span>' + s.sleep_hours + 'h ' + q + '</span>';
                html += '<span>' + new Date(s.sleep_start).toLocaleDateString() + '</span></li>';
            });
            html += '</ul>';
            
            document.getElementById('sleep-content').innerHTML = html;
        });
}

function showSleepModal() {
    const hours = parseFloat(prompt('睡眠时长(小时):'));
    if (!hours) return;
    const quality = prompt('睡眠质量 (poor/fair/good/excellent):');
    if (!quality) return;
    
    const now = new Date();
    const start = new Date(now.getTime() - hours * 3600000).toISOString();
    const end = now.toISOString();
    
    fetch('/api/sleep-log', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ sleep_hours: hours, sleep_quality: quality, sleep_start: start, sleep_end: end })
    }).then(r => r.json()).then(data => {
        if (data.status === 'success') showSuccess('睡眠已记录');
        loadSleep();
    });
}
