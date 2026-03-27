#!/usr/bin/env python3
"""
Health Coach Web Dashboard Server.
Lightweight Flask server for visual reports and analysis.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Global user context (set at startup)
CURRENT_USER = None
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(script_name: str, *args) -> Dict[str, Any]:
    """Run a skill script and return parsed JSON."""
    script_path = os.path.join(SKILL_DIR, 'scripts', script_name)
    cmd = ['python3', script_path, '--user', CURRENT_USER] + list(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"status": "error", "error": result.stderr}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.route('/')
def dashboard():
    """Main dashboard page."""
    # Get summary data
    nutrition = run_script('report_generator.py', 'nutrition', '--days', '7')
    weight = run_script('body_metrics.py', 'list', '--days', '30')
    
    return render_template('dashboard.html',
                         user=CURRENT_USER,
                         nutrition=nutrition,
                         weight=weight)


@app.route('/api/summary')
def api_summary():
    """Get summary data for dashboard."""
    # Today's nutrition
    daily = run_script('meal_logger.py', 'daily-summary')
    
    # Weekly nutrition trend
    weekly = run_script('report_generator.py', 'nutrition', '--days', '7')
    
    # Weight trend
    weight = run_script('body_metrics.py', 'trend', '--days', '30')
    
    return jsonify({
        "daily": daily,
        "weekly": weekly,
        "weight": weight
    })


@app.route('/api/weight-history')
def api_weight_history():
    """Get weight history for chart."""
    days = request.args.get('days', '30')
    result = run_script('body_metrics.py', 'list', '--days', days)
    
    if result.get('status') == 'success':
        records = result.get('data', {}).get('records', [])
        # Format for chart
        chart_data = [
            {
                "date": r['recorded_at'].split(' ')[0] if ' ' in r['recorded_at'] else r['recorded_at'],
                "weight": r['weight_kg'],
                "bmi": r.get('bmi')
            }
            for r in records
        ]
        return jsonify({"status": "success", "data": chart_data})
    
    return jsonify(result)


@app.route('/api/nutrition-history')
def api_nutrition_history():
    """Get nutrition history for chart."""
    days = request.args.get('days', '7')
    result = run_script('meal_logger.py', 'list', '--days', days)
    
    if result.get('status') == 'success':
        meals = result.get('data', {}).get('meals', [])
        
        # Aggregate by date
        daily_nutrition = {}
        for meal in meals:
            date = meal['eaten_at'].split(' ')[0] if ' ' in meal['eaten_at'] else meal['eaten_at'][:10]
            if date not in daily_nutrition:
                daily_nutrition[date] = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
            
            daily_nutrition[date]["calories"] += meal.get('total_calories', 0) or 0
            daily_nutrition[date]["protein"] += meal.get('total_protein_g', 0) or 0
            daily_nutrition[date]["carbs"] += meal.get('total_carbs_g', 0) or 0
            daily_nutrition[date]["fat"] += meal.get('total_fat_g', 0) or 0
        
        # Format for chart
        chart_data = [
            {"date": date, **values}
            for date, values in sorted(daily_nutrition.items())
        ]
        
        return jsonify({"status": "success", "data": chart_data})
    
    return jsonify(result)


@app.route('/api/meals')
def api_meals():
    """Get recent meals."""
    days = request.args.get('days', '3')
    result = run_script('meal_logger.py', 'list', '--days', days)
    return jsonify(result)


@app.route('/api/profile')
def api_profile():
    """Get user profile."""
    result = run_script('user_profile.py', 'get')
    return jsonify(result)


@app.route('/api/pantry')
def api_pantry():
    """Get pantry items."""
    result = run_script('pantry_manager.py', 'remaining')
    return jsonify(result)


@app.route('/api/pantry/expiring')
def api_pantry_expiring():
    """Get expiring pantry items."""
    days = request.args.get('days', '7')
    result = run_script('pantry_manager.py', 'list', '--expiring', days)
    return jsonify(result)


@app.route('/api/pantry/use', methods=['POST'])
def api_pantry_use():
    """Record pantry item usage."""
    data = request.json
    item_id = data.get('item_id')
    amount = data.get('amount')
    notes = data.get('notes', '')
    
    result = run_script('pantry_manager.py', 'use', 
                       '--item-id', str(item_id), 
                       '--amount', str(amount),
                       '--notes', notes)
    return jsonify(result)


@app.route('/api/pantry/add', methods=['POST'])
def api_pantry_add():
    """Add item to pantry."""
    data = request.json
    food = data.get('food')
    quantity = data.get('quantity')
    expiry = data.get('expiry')
    location = data.get('location', 'fridge')
    
    result = run_script('pantry_manager.py', 'add',
                       '--food', food,
                       '--quantity', str(quantity),
                       '--expiry', expiry,
                       '--location', location)
    return jsonify(result)


def create_templates():
    """Create template directory and files if not exist."""
    template_dir = os.path.join(SKILL_DIR, 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    # Create dashboard.html
    dashboard_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Coach - {{ user }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        header h1 { font-size: 2em; margin-bottom: 10px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .card h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #667eea;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .stat:last-child { border-bottom: none; }
        .stat-value {
            font-weight: bold;
            color: #667eea;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .pantry-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .pantry-item:last-child { border-bottom: none; }
        .pantry-name { font-weight: 500; }
        .pantry-qty { color: #666; font-size: 0.9em; }
        .expiry-badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        .expiry-urgent { background: #fee; color: #c33; }
        .expiry-soon { background: #ffeaa7; color: #d63031; }
        .expiry-ok { background: #e8f5e9; color: #2e7d32; }
        .shopping-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 15px;
        }
        .shopping-btn:hover { background: #5568d3; }
        .action-btn {
            background: #f0f0f0;
            border: none;
            padding: 5px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85em;
            margin-left: 10px;
        }
        .action-btn:hover { background: #e0e0e0; }
        .action-btn.use { background: #667eea; color: white; }
        .action-btn.use:hover { background: #5568d3; }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            width: 90%;
            max-width: 400px;
        }
        .modal h3 { margin-bottom: 20px; }
        .modal input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 6px;
            box-sizing: border-box;
        }
        .modal-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .modal-buttons button {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        .modal-buttons .confirm { background: #667eea; color: white; }
        .modal-buttons .cancel { background: #f0f0f0; }
        .add-btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 15px;
            margin-right: 10px;
        }
        .add-btn:hover { background: #45a049; }
        .success-msg {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏃 Health Coach</h1>
            <p>用户: {{ user }} | 健康数据面板</p>
        </header>
        
        <div class="grid">
            <!-- Today's Summary -->
            <div class="card">
                <h2>📊 今日概览</h2>
                <div id="daily-summary">
                    <div class="loading">加载中...</div>
                </div>
            </div>
            
            <!-- Weight Trend -->
            <div class="card">
                <h2>⚖️ 体重趋势 (30天)</h2>
                <div class="chart-container">
                    <canvas id="weightChart"></canvas>
                </div>
            </div>
            
            <!-- Nutrition Trend -->
            <div class="card">
                <h2>🍽️ 营养摄入 (7天)</h2>
                <div class="chart-container">
                    <canvas id="nutritionChart"></canvas>
                </div>
            </div>
            
            <!-- Profile -->
            <div class="card">
                <h2>👤 身体数据</h2>
                <div id="profile">
                    <div class="loading">加载中...</div>
                </div>
            </div>
            
            <!-- Pantry -->
            <div class="card" style="grid-column: span 2;">
                <h2>🥬 食材库存</h2>
                <div id="pantry-summary" style="margin-bottom: 15px;"></div>
                <div id="pantry-list">
                    <div class="loading">加载中...</div>
                </div>
                <div style="margin-top: 15px;">
                    <button class="add-btn" onclick="openAddModal()">➕ 添加食材</button>
                    <button class="shopping-btn" onclick="generateShoppingList()">🛒 生成购物清单</button>
                </div>
                <div id="shopping-list" style="margin-top: 15px; display: none;"></div>
                <div id="success-msg" class="success-msg"></div>
            </div>
        </div>
    </div>
    
    <!-- Use Item Modal -->
    <div id="useModal" class="modal">
        <div class="modal-content">
            <h3>🍳 记录使用</h3>
            <p id="useModalItemName" style="margin-bottom: 15px; font-weight: 500;"></p>
            <input type="number" id="useAmount" placeholder="使用重量 (g)" min="1">
            <input type="text" id="useNotes" placeholder="备注（可选，如：做沙拉）">
            <div class="modal-buttons">
                <button class="confirm" onclick="confirmUse()">确认</button>
                <button class="cancel" onclick="closeModal('useModal')">取消</button>
            </div>
        </div>
    </div>
    
    <!-- Add Item Modal -->
    <div id="addModal" class="modal">
        <div class="modal-content">
            <h3>➕ 添加食材</h3>
            <input type="text" id="addFoodName" placeholder="食材名称（如：鸡胸肉）">
            <input type="number" id="addQuantity" placeholder="重量 (g)" min="1">
            <input type="date" id="addExpiry" placeholder="过期日期">
            <select id="addLocation" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px;">
                <option value="fridge">冰箱</option>
                <option value="freezer">冷冻</option>
                <option value="pantry"> pantry</option>
                <option value="counter">台面</option>
            </select>
            <div class="modal-buttons">
                <button class="confirm" onclick="confirmAdd()">添加</button>
                <button class="cancel" onclick="closeModal('addModal')">取消</button>
            </div>
        </div>
    </div>
    
    <script>
        // Load daily summary
        fetch('/api/summary')
            .then(r => r.json())
            .then(data => {
                const daily = data.daily?.data || {};
                document.getElementById('daily-summary').innerHTML = `
                    <div class="stat">
                        <span>热量</span>
                        <span class="stat-value">${Math.round(daily.totals?.calories || 0)} / ${Math.round(daily.tdee || 2000)} kcal</span>
                    </div>
                    <div class="stat">
                        <span>蛋白质</span>
                        <span class="stat-value">${Math.round(daily.totals?.protein_g || 0)} g</span>
                    </div>
                    <div class="stat">
                        <span>碳水</span>
                        <span class="stat-value">${Math.round(daily.totals?.carbs_g || 0)} g</span>
                    </div>
                    <div class="stat">
                        <span>脂肪</span>
                        <span class="stat-value">${Math.round(daily.totals?.fat_g || 0)} g</span>
                    </div>
                    <div class="stat">
                        <span>剩余</span>
                        <span class="stat-value">${Math.round(daily.remaining_calories || 0)} kcal</span>
                    </div>
                `;
            });
        
        // Load weight chart
        fetch('/api/weight-history?days=30')
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    const ctx = document.getElementById('weightChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.data.map(d => d.date),
                            datasets: [{
                                label: '体重 (kg)',
                                data: data.data.map(d => d.weight),
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                tension: 0.4,
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
                }
            });
        
        // Load nutrition chart
        fetch('/api/nutrition-history?days=7')
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    const ctx = document.getElementById('nutritionChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.data.map(d => d.date.slice(5)),
                            datasets: [
                                {
                                    label: '热量',
                                    data: data.data.map(d => d.calories),
                                    backgroundColor: '#667eea'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
            });
        
        // Load pantry
        fetch('/api/pantry')
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    const summary = data.data;
                    document.getElementById('pantry-summary').innerHTML = `
                        <div class="stat">
                            <span>总食材</span>
                            <span class="stat-value">${summary.total_items} 种</span>
                        </div>
                        <div class="stat">
                            <span>剩余热量</span>
                            <span class="stat-value">${summary.total_remaining_calories} kcal</span>
                        </div>
                        <div class="stat">
                            <span>剩余蛋白质</span>
                            <span class="stat-value">${summary.total_remaining_protein_g} g</span>
                        </div>
                    `;
                    
                    const items = summary.items;
                    const today = new Date();
                    
                    document.getElementById('pantry-list').innerHTML = items.map(item => {
                        let expiryClass = 'expiry-ok';
                        let expiryText = '新鲜';
                        
                        if (item.expiry_date) {
                            const expiry = new Date(item.expiry_date);
                            const daysLeft = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
                            
                            if (daysLeft <= 1) {
                                expiryClass = 'expiry-urgent';
                                expiryText = '今天过期';
                            } else if (daysLeft <= 3) {
                                expiryClass = 'expiry-soon';
                                expiryText = `${daysLeft}天后过期`;
                            } else {
                                expiryText = `${daysLeft}天后过期`;
                            }
                        }
                        
                        return `
                            <div class="pantry-item">
                                <div>
                                    <div class="pantry-name">${item.food_name}</div>
                                    <div class="pantry-qty">剩余 ${item.remaining_g}g (初始 ${item.initial_g}g)</div>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <span class="expiry-badge ${expiryClass}" style="margin-right: 10px;">${expiryText}</span>
                                    ${item.remaining_g > 0 ? `
                                        <button class="action-btn use" onclick="openUseModal(${item.id}, '${item.food_name}', ${item.remaining_g})">使用</button>
                                    ` : ''}
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            });
        
        // Shopping list generator
        function generateShoppingList() {
            fetch('/api/pantry/expiring?days=3')
                .then(r => r.json())
                .then(data => {
                    const div = document.getElementById('shopping-list');
                    if (data.status === 'success' && data.data.count > 0) {
                        const expiring = data.data.items;
                        div.innerHTML = `
                            <h3>🛒 建议购买（快过期/已用完）</h3>
                            <ul style="list-style: none; padding: 0;">
                                ${expiring.map(i => `
                                    <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
                                        ${i.food_name} - ${i.days_left <= 0 ? '已过期' : i.days_left + '天后过期'}
                                    </li>
                                `).join('')}
                            </ul>
                        `;
                    } else {
                        div.innerHTML = '<p>✓ 暂无急需补充的食材</p>';
                    }
                    div.style.display = 'block';
                });
        }
        
        // Modal functions
        let currentItemId = null;
        let currentItemName = null;
        
        function openUseModal(itemId, itemName, maxAmount) {
            currentItemId = itemId;
            currentItemName = itemName;
            document.getElementById('useModalItemName').textContent = itemName + ' (最多 ' + maxAmount + 'g)';
            document.getElementById('useAmount').max = maxAmount;
            document.getElementById('useAmount').value = '';
            document.getElementById('useNotes').value = '';
            document.getElementById('useModal').classList.add('active');
        }
        
        function openAddModal() {
            document.getElementById('addFoodName').value = '';
            document.getElementById('addQuantity').value = '';
            document.getElementById('addExpiry').value = '';
            document.getElementById('addModal').classList.add('active');
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }
        
        function confirmUse() {
            const amount = parseFloat(document.getElementById('useAmount').value);
            const notes = document.getElementById('useNotes').value;
            
            if (!amount || amount <= 0) {
                alert('请输入有效的使用重量');
                return;
            }
            
            fetch('/api/pantry/use', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    item_id: currentItemId,
                    amount: amount,
                    notes: notes
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(`已记录：使用 ${amount}g ${currentItemName}`);
                    closeModal('useModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    alert('记录失败：' + (data.message || data.error));
                }
            });
        }
        
        function confirmAdd() {
            const food = document.getElementById('addFoodName').value.trim();
            const quantity = parseFloat(document.getElementById('addQuantity').value);
            const expiry = document.getElementById('addExpiry').value;
            const location = document.getElementById('addLocation').value;
            
            if (!food) {
                alert('请输入食材名称');
                return;
            }
            if (!quantity || quantity <= 0) {
                alert('请输入有效的重量');
                return;
            }
            
            fetch('/api/pantry/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    food: food,
                    quantity: quantity,
                    expiry: expiry,
                    location: location
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    showSuccess(`已添加：${food} ${quantity}g`);
                    closeModal('addModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    alert('添加失败：' + (data.message || data.error));
                }
            });
        }
        
        function showSuccess(message) {
            const msg = document.getElementById('success-msg');
            msg.textContent = message;
            msg.style.display = 'block';
            setTimeout(() => msg.style.display = 'none', 3000);
        }
        
        // Close modal on outside click
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.classList.remove('active');
            }
        }
        
        // Load nutrition chart
        fetch('/api/nutrition-history?days=7')
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    const ctx = document.getElementById('nutritionChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.data.map(d => d.date.slice(5)),
                            datasets: [
                                {
                                    label: '热量',
                                    data: data.data.map(d => d.calories),
                                    backgroundColor: '#667eea'
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
            });
        
        // Load profile
        fetch('/api/profile')
            .then(r => r.json())
            .then(data => {
                const p = data.data || {};
                document.getElementById('profile').innerHTML = `
                    <div class="stat">
                        <span>身高</span>
                        <span class="stat-value">${p.height_cm} cm</span>
                    </div>
                    <div class="stat">
                        <span>BMR</span>
                        <span class="stat-value">${Math.round(p.bmr || 0)} kcal</span>
                    </div>
                    <div class="stat">
                        <span>TDEE</span>
                        <span class="stat-value">${Math.round(p.tdee || 0)} kcal</span>
                    </div>
                    <div class="stat">
                        <span>目标</span>
                        <span class="stat-value">${p.goal_type === 'lose' ? '减脂' : p.goal_type === 'gain' ? '增肌' : '维持'}</span>
                    </div>
                `;
            });
    </script>
</body>
</html>'''
    
    template_path = os.path.join(template_dir, 'dashboard.html')
    if not os.path.exists(template_path):
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        print(f"Created template: {template_path}")
    
    return template_dir


def main():
    global CURRENT_USER
    
    parser = argparse.ArgumentParser(description='Health Coach Web Dashboard')
    parser.add_argument('--user', required=True, help='Username')
    parser.add_argument('--port', type=int, default=5000, help='Port (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1', help='Host (default: 127.0.0.1)')
    
    args = parser.parse_args()
    CURRENT_USER = args.user
    
    # Create templates
    template_dir = create_templates()
    app.template_folder = template_dir
    
    print(f"🌐 Health Coach Dashboard")
    print(f"   User: {CURRENT_USER}")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Press Ctrl+C to stop")
    print()
    
    try:
        app.run(host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        sys.exit(0)


if __name__ == '__main__':
    main()
