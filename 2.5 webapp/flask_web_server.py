"""
Flask Web服务器 - 现代股票分析系统
提供API接口支持前端调用
"""

from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import logging
import json
import threading
import time
from datetime import datetime
import os
import sys
import math
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import wraps

# 导入我们的分析器
try:
    from web_stock_analyzer import WebStockAnalyzer
except ImportError:
    print("❌ 无法导入 web_stock_analyzer.py")
    print("请确保 web_stock_analyzer.py 文件存在于同一目录下")
    sys.exit(1)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 高并发优化配置
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # 关闭JSON格式化以提升性能
app.config['JSON_SORT_KEYS'] = False  # 关闭JSON键排序

# 全局变量
analyzer = None
analysis_tasks = {}  # 存储分析任务状态
task_results = {}   # 存储任务结果
task_lock = threading.Lock()  # 线程锁

# 线程池用于并发处理
executor = ThreadPoolExecutor(max_workers=4)  # 根据服务器配置调整

def async_task(f):
    """异步任务装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return executor.submit(f, *args, **kwargs)
    return wrapper

# 配置日志 - 只输出到命令行
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 只保留命令行输出
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
analyzer = None
analysis_tasks = {}  # 存储分析任务状态

def clean_data_for_json(obj):
    """清理数据中的NaN、Infinity等无效值，使其能够正确序列化为JSON"""
    if isinstance(obj, dict):
        return {key: clean_data_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_data_for_json(item) for item in obj]
    elif isinstance(obj, (int, float)):
        if math.isnan(obj):
            return None  # 将NaN转换为null
        elif math.isinf(obj):
            return None  # 将Infinity转换为null
        else:
            return obj
    elif isinstance(obj, np.ndarray):
        return clean_data_for_json(obj.tolist())
    elif isinstance(obj, (np.integer, np.floating)):
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return None
        else:
            return obj.item()  # 转换为Python原生类型
    else:
        return obj

# HTML模板 - 修复转义序列警告
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>现代股票分析系统 - Enhanced v3.0</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .header-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 16px;
        }

        .version-info {
            color: #6c757d;
            font-size: 14px;
        }

        .config-btn {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 8px 16px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .config-btn:hover {
            background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
            transform: translateY(-2px);
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            min-height: 600px;
        }

        .left-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .right-panel {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        .tabs {
            display: flex;
            border-bottom: 2px solid #e9ecef;
            margin-bottom: 20px;
        }

        .tab {
            padding: 12px 24px;
            background: #f8f9fa;
            border: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-weight: 600;
            margin-right: 4px;
            transition: all 0.3s ease;
        }

        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
        }

        .form-control {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .form-control:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .textarea {
            min-height: 120px;
            resize: vertical;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: #667eea;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            transform: translateY(-2px);
        }

        .btn-success {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
        }

        .btn-success:hover {
            background: linear-gradient(135deg, #4e9a2a 0%, #96d4b5 100%);
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: #f8f9fa;
            color: #495057;
            border: 2px solid #e9ecef;
        }

        .btn-secondary:hover {
            background: #e9ecef;
            border-color: #adb5bd;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }

        .progress-bar {
            width: 100%;
            height: 12px;
            background-color: #e9ecef;
            border-radius: 6px;
            overflow: hidden;
            margin: 16px 0;
            display: none;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            width: 0%;
        }

        .log-container {
            margin-top: 20px;
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .log-header h3 {
            color: #495057;
            font-size: 16px;
        }

        .log-display {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 16px;
            max-height: 250px;
            overflow-y: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.4;
        }

        .log-entry {
            margin-bottom: 4px;
            padding: 2px 0;
        }

        .log-info { color: #3498db; }
        .log-success { color: #27ae60; font-weight: bold; }
        .log-warning { color: #f39c12; font-weight: bold; }
        .log-error { color: #e74c3c; font-weight: bold; }
        .log-header-type { color: #667eea; font-weight: bold; font-size: 14px; }

        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .results-header h2 {
            color: #2c3e50;
            font-size: 20px;
        }

        .score-cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
            display: none;
        }

        .score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            color: white;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .score-card.excellent { background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); }
        .score-card.good { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .score-card.average { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .score-card.poor { background: linear-gradient(135deg, #ff4b2b 0%, #ff416c 100%); }

        .score-card h4 {
            font-size: 12px;
            margin-bottom: 8px;
            opacity: 0.9;
        }

        .score-card .score {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 4px;
        }

        .score-card .max-score {
            font-size: 10px;
            opacity: 0.8;
        }

        .data-quality {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
            display: none;
        }

        .quality-indicator {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }

        .quality-indicator .value {
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 4px;
        }

        .quality-indicator .label {
            font-size: 10px;
            color: #6c757d;
        }

        .results-content {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            min-height: 400px;
            overflow-y: auto;
        }

        .loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 300px;
            color: #6c757d;
        }

        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e9ecef;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .empty-state {
            text-align: center;
            color: #6c757d;
            padding: 60px 20px;
        }

        .empty-state h3 {
            margin-bottom: 8px;
        }

        .status-indicator {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 8px;
        }

        .status-ready { background: #d4edda; color: #155724; }
        .status-analyzing { background: #d1ecf1; color: #0c5460; }
        .status-error { background: #f8d7da; color: #721c24; }

        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
                gap: 16px;
            }
            
            .score-cards {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .ai-analysis-content {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .ai-analysis-content h1,
        .ai-analysis-content h2,
        .ai-analysis-content h3,
        .ai-analysis-content h4,
        .ai-analysis-content h5,
        .ai-analysis-content h6 {
            color: #2c3e50;
            margin-top: 16px;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .ai-analysis-content h1 { font-size: 1.5em; }
        .ai-analysis-content h2 { font-size: 1.3em; }
        .ai-analysis-content h3 { font-size: 1.1em; }

        .ai-analysis-content p {
            margin: 8px 0;
            line-height: 1.6;
        }

        .ai-analysis-content ul,
        .ai-analysis-content ol {
            margin: 8px 0;
            padding-left: 20px;
        }

        .ai-analysis-content li {
            margin: 4px 0;
            line-height: 1.5;
        }

        .ai-analysis-content strong {
            color: #1976d2;
            font-weight: 600;
        }

        .ai-analysis-content em {
            color: #f57c00;
            font-style: italic;
        }

        .ai-analysis-content code {
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            color: #d63384;
        }

        .ai-analysis-content blockquote {
            border-left: 4px solid #667eea;
            margin: 16px 0;
            padding: 8px 16px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 0 4px 4px 0;
        }

        .ai-analysis-content table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }

        .ai-analysis-content th,
        .ai-analysis-content td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }

        .ai-analysis-content th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }

        .ai-analysis-content a {
            color: #1976d2;
            text-decoration: none;
        }

        .ai-analysis-content a:hover {
            text-decoration: underline;
        }

        @media (max-width: 640px) {
            .container {
                padding: 16px;
            }
            
            .header {
                padding: 16px;
            }
            
            .header h1 {
                font-size: 24px;
            }
            
            .header-info {
                flex-direction: column;
                gap: 12px;
                align-items: flex-start;
            }
            
            .score-cards {
                grid-template-columns: 1fr;
            }
            
            .data-quality {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚀 现代股票分析系统</h1>
            <div class="header-info">
                <div class="version-info">
                    Enhanced v3.0-Web | WebStockAnalyzer | 完整LLM API支持
                    <span id="systemStatus" class="status-indicator status-ready">系统就绪</span>
                </div>
                <button class="config-btn" onclick="showConfig()">⚙️ AI配置</button>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Left Panel - Input and Controls -->
            <div class="left-panel">
                <!-- Tabs -->
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('single')">📈 单只分析</button>
                    <button class="tab" onclick="switchTab('batch')">📊 批量分析</button>
                </div>

                <!-- Single Stock Analysis -->
                <div id="singleTab" class="tab-content active">
                    <div class="form-group">
                        <label for="stockCode">股票代码</label>
                        <input type="text" id="stockCode" class="form-control" 
                               placeholder="输入股票代码（如：000001、600036、300019）">
                    </div>
                    
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="enableStreaming" checked>
                            <label for="enableStreaming">启用流式推理显示</label>
                        </div>
                    </div>
                    
                    <button id="analyzeBtn" class="btn btn-primary" onclick="analyzeSingleStock()">
                        🔍 开始深度分析
                    </button>
                    
                    <div id="singleProgress" class="progress-bar">
                        <div class="progress-bar-fill"></div>
                    </div>
                </div>

                <!-- Batch Analysis -->
                <div id="batchTab" class="tab-content">
                    <div class="form-group">
                        <label for="stockList">股票代码列表</label>
                        <textarea id="stockList" class="form-control textarea" 
                                  placeholder="输入多个股票代码，每行一个&#10;例如：&#10;000001&#10;000002&#10;600036&#10;300019"></textarea>
                    </div>
                    
                    <button id="batchAnalyzeBtn" class="btn btn-success" onclick="analyzeBatchStocks()">
                        📊 批量深度分析
                    </button>
                    
                    <div id="batchProgress" class="progress-bar">
                        <div class="progress-bar-fill"></div>
                    </div>
                    
                    <div id="currentStock" style="display: none; margin-top: 12px; color: #6c757d; font-size: 12px; font-style: italic;"></div>
                </div>

                <!-- Log Container -->
                <div class="log-container">
                    <div class="log-header">
                        <h3>📋 分析日志</h3>
                        <button class="btn btn-secondary" onclick="clearLog()" style="padding: 4px 12px; font-size: 12px;">
                            🗑️ 清空
                        </button>
                    </div>
                    <div id="logDisplay" class="log-display">
                        <div class="log-entry log-info">📋 系统就绪，等待分析任务...</div>
                    </div>
                </div>
            </div>

            <!-- Right Panel - Results -->
            <div class="right-panel">
                <div class="results-header">
                    <h2>📋 分析结果</h2>
                    <button id="exportBtn" class="btn btn-secondary" onclick="exportReport()" style="display: none;">
                        📤 导出报告
                    </button>
                </div>

                <!-- Score Cards -->
                <div id="scoreCards" class="score-cards">
                    <div class="score-card" id="comprehensiveCard">
                        <h4>综合得分</h4>
                        <div class="score">--</div>
                        <div class="max-score">/100</div>
                    </div>
                    <div class="score-card" id="technicalCard">
                        <h4>技术分析</h4>
                        <div class="score">--</div>
                        <div class="max-score">/100</div>
                    </div>
                    <div class="score-card" id="fundamentalCard">
                        <h4>基本面</h4>
                        <div class="score">--</div>
                        <div class="max-score">/100</div>
                    </div>
                    <div class="score-card" id="sentimentCard">
                        <h4>市场情绪</h4>
                        <div class="score">--</div>
                        <div class="max-score">/100</div>
                    </div>
                </div>

                <!-- Data Quality Indicators -->
                <div id="dataQuality" class="data-quality">
                    <div class="quality-indicator">
                        <div id="financialCount" class="value">--</div>
                        <div class="label">财务指标</div>
                    </div>
                    <div class="quality-indicator">
                        <div id="newsCount" class="value">--</div>
                        <div class="label">新闻数据</div>
                    </div>
                    <div class="quality-indicator">
                        <div id="completeness" class="value">--</div>
                        <div class="label">完整度</div>
                    </div>
                </div>

                <!-- Results Content -->
                <div id="resultsContent" class="results-content">
                    <div class="empty-state">
                        <h3>📊 等待分析</h3>
                        <p>请在左侧输入股票代码并开始分析</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 添加marked.js用于markdown解析 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
    
    <script>
        // Global variables
        let currentAnalysis = null;
        let isAnalyzing = false;
        const API_BASE = '';  // Flask server base URL
        
        // 配置marked.js
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,        // 支持换行
                gfm: true,          // GitHub风格markdown
                sanitize: false,    // 允许HTML（内容来自可信后端）
                smartLists: true,   // 智能列表
                smartypants: true   // 智能标点
            });
        }

        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + 'Tab').classList.add('active');
        }

        // Log functions
        function addLog(message, type = 'info') {
            const logDisplay = document.getElementById('logDisplay');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${type}`;
            
            const timestamp = new Date().toLocaleTimeString();
            let icon = '📋';
            
            switch(type) {
                case 'success': icon = '✅'; break;
                case 'warning': icon = '⚠️'; break;
                case 'error': icon = '❌'; break;
                case 'header': icon = '🎯'; break;
            }
            
            logEntry.innerHTML = `<span style="color: #999;">[${timestamp}]</span> ${icon} ${message}`;
            logDisplay.appendChild(logEntry);
            logDisplay.scrollTop = logDisplay.scrollHeight;
        }

        function clearLog() {
            document.getElementById('logDisplay').innerHTML = 
                '<div class="log-entry log-info">📋 日志已清空</div>';
        }

        // Progress bar functions
        function showProgress(elementId, show = true) {
            const progressBar = document.getElementById(elementId);
            progressBar.style.display = show ? 'block' : 'none';
            if (!show) {
                progressBar.querySelector('.progress-bar-fill').style.width = '0%';
            }
        }

        function updateProgress(elementId, percent) {
            const fill = document.getElementById(elementId).querySelector('.progress-bar-fill');
            fill.style.width = percent + '%';
        }

        // Score card functions
        function updateScoreCards(scores) {
            const cards = {
                comprehensive: document.getElementById('comprehensiveCard'),
                technical: document.getElementById('technicalCard'),
                fundamental: document.getElementById('fundamentalCard'),
                sentiment: document.getElementById('sentimentCard')
            };

            Object.keys(scores).forEach(key => {
                const card = cards[key];
                if (card) {
                    const score = scores[key];
                    card.querySelector('.score').textContent = score.toFixed(1);
                    
                    card.className = 'score-card';
                    if (score >= 80) card.classList.add('excellent');
                    else if (score >= 60) card.classList.add('good');
                    else if (score >= 40) card.classList.add('average');
                    else card.classList.add('poor');
                }
            });

            document.getElementById('scoreCards').style.display = 'grid';
        }

        function updateDataQuality(report) {
            const dataQuality = report.data_quality || {};
            const sentimentAnalysis = report.sentiment_analysis || {};
            
            document.getElementById('financialCount').textContent = 
                dataQuality.financial_indicators_count || 0;
            document.getElementById('newsCount').textContent = 
                sentimentAnalysis.total_analyzed || 0;
            document.getElementById('completeness').textContent = 
                (dataQuality.analysis_completeness || '部分').substring(0, 2);
            
            document.getElementById('dataQuality').style.display = 'grid';
        }

        // Results display
        function showLoading() {
            document.getElementById('resultsContent').innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <p>正在进行深度分析...</p>
                </div>
            `;
        }

        function displayResults(report) {
            const resultsContent = document.getElementById('resultsContent');
            
            // 处理AI分析的markdown内容
            let aiAnalysisHtml = '';
            if (report.ai_analysis) {
                if (typeof marked !== 'undefined') {
                    // 使用marked.js解析markdown
                    aiAnalysisHtml = marked.parse(report.ai_analysis);
                } else {
                    // 备用方案：简单的markdown解析
                    aiAnalysisHtml = simpleMarkdownParse(report.ai_analysis);
                }
            } else {
                aiAnalysisHtml = '<p>分析数据准备中...</p>';
            }
            
            const html = `
                <div style="line-height: 1.6;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #e9ecef; padding-bottom: 12px; margin-bottom: 20px;">
                        📈 ${report.stock_name || report.stock_code} 分析报告
                    </h2>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
                        <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                            <h4 style="color: #495057; margin-bottom: 8px;">基本信息</h4>
                            <p><strong>股票代码:</strong> ${report.stock_code}</p>
                            <p><strong>当前价格:</strong> ¥${(report.price_info?.current_price || 0).toFixed(2)}</p>
                            <p><strong>涨跌幅:</strong> ${(report.price_info?.price_change || 0).toFixed(2)}%</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                            <h4 style="color: #495057; margin-bottom: 8px;">技术指标</h4>
                            <p><strong>RSI:</strong> ${(report.technical_analysis?.rsi || 0).toFixed(1)}</p>
                            <p><strong>趋势:</strong> ${report.technical_analysis?.ma_trend || '未知'}</p>
                            <p><strong>MACD:</strong> ${report.technical_analysis?.macd_signal || '未知'}</p>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                            <h4 style="color: #495057; margin-bottom: 8px;">市场情绪</h4>
                            <p><strong>情绪趋势:</strong> ${report.sentiment_analysis?.sentiment_trend || '中性'}</p>
                            <p><strong>新闻数量:</strong> ${report.sentiment_analysis?.total_analyzed || 0} 条</p>
                            <p><strong>置信度:</strong> ${((report.sentiment_analysis?.confidence_score || 0) * 100).toFixed(1)}%</p>
                        </div>
                    </div>
                    
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3; margin-bottom: 24px;">
                        <h3 style="color: #1976d2; margin-bottom: 12px;">🎯 投资建议</h3>
                        <p style="font-size: 18px; font-weight: 600; color: #1976d2;">${report.recommendation || '数据不足'}</p>
                    </div>
                    
                    <div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800;">
                        <h3 style="color: #f57c00; margin-bottom: 12px;">🤖 AI 深度分析</h3>
                        <div style="color: #5d4037; font-size: 14px; line-height: 1.7;" class="ai-analysis-content">
                            ${aiAnalysisHtml}
                        </div>
                    </div>
                </div>
            `;
            
            resultsContent.innerHTML = html;
            document.getElementById('exportBtn').style.display = 'inline-flex';
        }

        // 简单的markdown解析器（备用方案）
        function simpleMarkdownParse(text) {
            if (!text) return '';
            
            return text
                // 标题
                .replace(/^### (.*$)/gim, '<h3 style="color: #2c3e50; margin: 16px 0 8px 0;">$1</h3>')
                .replace(/^## (.*$)/gim, '<h2 style="color: #2c3e50; margin: 20px 0 10px 0;">$1</h2>')
                .replace(/^# (.*$)/gim, '<h1 style="color: #2c3e50; margin: 24px 0 12px 0;">$1</h1>')
                // 粗体
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                // 斜体
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                // 行内代码
                .replace(/`(.*?)`/g, '<code style="background: #f1f3f4; padding: 2px 4px; border-radius: 3px; font-family: monospace;">$1</code>')
                // 链接
                .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" style="color: #1976d2;">$1</a>')
                // 列表项
                .replace(/^[\\-\\*\\+] (.*$)/gim, '<li style="margin: 4px 0;">$1</li>')
                // 段落
                .replace(/\\n\\n/g, '</p><p>')
                // 换行
                .replace(/\\n/g, '<br>');
        }

        function displayBatchResults(reports) {
            if (!reports || reports.length === 0) {
                addLog('批量分析结果为空', 'warning');
                return;
            }

            const avgScores = {
                comprehensive: reports.reduce((sum, r) => sum + r.scores.comprehensive, 0) / reports.length,
                technical: reports.reduce((sum, r) => sum + r.scores.technical, 0) / reports.length,
                fundamental: reports.reduce((sum, r) => sum + r.scores.fundamental, 0) / reports.length,
                sentiment: reports.reduce((sum, r) => sum + r.scores.sentiment, 0) / reports.length
            };

            updateScoreCards(avgScores);

            const avgFinancial = reports.reduce((sum, r) => sum + (r.data_quality?.financial_indicators_count || 0), 0) / reports.length;
            const avgNews = reports.reduce((sum, r) => sum + (r.sentiment_analysis?.total_analyzed || 0), 0) / reports.length;
            
            document.getElementById('financialCount').textContent = Math.round(avgFinancial);
            document.getElementById('newsCount').textContent = Math.round(avgNews);
            document.getElementById('completeness').textContent = '批量';
            document.getElementById('dataQuality').style.display = 'grid';

            const resultsContent = document.getElementById('resultsContent');
            
            let tableRows = reports
                .sort((a, b) => b.scores.comprehensive - a.scores.comprehensive)
                .map((report, index) => `
                    <tr style="border-bottom: 1px solid #e9ecef;">
                        <td style="padding: 12px; font-weight: 600;">${index + 1}</td>
                        <td style="padding: 12px;">${report.stock_code}</td>
                        <td style="padding: 12px;">${report.stock_name || report.stock_code}</td>
                        <td style="padding: 12px; font-weight: 600; color: ${report.scores.comprehensive >= 70 ? '#27ae60' : report.scores.comprehensive >= 50 ? '#667eea' : '#e74c3c'};">
                            ${report.scores.comprehensive.toFixed(1)}
                        </td>
                        <td style="padding: 12px;">${report.scores.technical.toFixed(1)}</td>
                        <td style="padding: 12px;">${report.scores.fundamental.toFixed(1)}</td>
                        <td style="padding: 12px;">${report.scores.sentiment.toFixed(1)}</td>
                        <td style="padding: 12px; font-weight: 600;">${report.recommendation}</td>
                    </tr>
                `).join('');

            const html = `
                <div style="line-height: 1.6;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #e9ecef; padding-bottom: 12px; margin-bottom: 20px;">
                        📊 批量分析报告 (${reports.length} 只股票)
                    </h2>
                    
                    <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
                        <h4 style="color: #495057; margin-bottom: 12px;">📋 分析汇总</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                            <div><strong>分析数量:</strong> ${reports.length} 只</div>
                            <div><strong>平均得分:</strong> ${avgScores.comprehensive.toFixed(1)}</div>
                            <div><strong>优秀股票:</strong> ${reports.filter(r => r.scores.comprehensive >= 80).length} 只</div>
                            <div><strong>良好股票:</strong> ${reports.filter(r => r.scores.comprehensive >= 60).length} 只</div>
                        </div>
                    </div>
                    
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <thead>
                                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                    <th style="padding: 16px; text-align: left;">排名</th>
                                    <th style="padding: 16px; text-align: left;">代码</th>
                                    <th style="padding: 16px; text-align: left;">名称</th>
                                    <th style="padding: 16px; text-align: left;">综合得分</th>
                                    <th style="padding: 16px; text-align: left;">技术面</th>
                                    <th style="padding: 16px; text-align: left;">基本面</th>
                                    <th style="padding: 16px; text-align: left;">情绪面</th>
                                    <th style="padding: 16px; text-align: left;">投资建议</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tableRows}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            resultsContent.innerHTML = html;
            document.getElementById('exportBtn').style.display = 'inline-flex';
        }

        // Analysis functions with API calls
        async function analyzeSingleStock() {
            const stockCode = document.getElementById('stockCode').value.trim();
            if (!stockCode) {
                addLog('请输入股票代码', 'warning');
                return;
            }

            if (isAnalyzing) {
                addLog('分析正在进行中，请稍候', 'warning');
                return;
            }

            isAnalyzing = true;
            document.getElementById('analyzeBtn').disabled = true;
            document.getElementById('systemStatus').className = 'status-indicator status-analyzing';
            document.getElementById('systemStatus').textContent = '分析中';

            addLog(`🚀 开始全面分析股票: ${stockCode}`, 'header');
            showLoading();
            showProgress('singleProgress');

            try {
                const response = await fetch(`${API_BASE}/api/analyze`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        stock_code: stockCode,
                        enable_streaming: document.getElementById('enableStreaming').checked
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                
                if (result.success) {
                    currentAnalysis = result.data;
                    updateScoreCards(result.data.scores);
                    updateDataQuality(result.data);
                    displayResults(result.data);
                    updateProgress('singleProgress', 100);
                    addLog(`✅ ${stockCode} 分析完成，综合得分: ${result.data.scores.comprehensive.toFixed(1)}`, 'success');
                } else {
                    throw new Error(result.error || '分析失败');
                }

            } catch (error) {
                addLog(`❌ 分析失败: ${error.message}`, 'error');
                document.getElementById('resultsContent').innerHTML = `
                    <div class="empty-state">
                        <h3>❌ 分析失败</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            } finally {
                isAnalyzing = false;
                document.getElementById('analyzeBtn').disabled = false;
                document.getElementById('systemStatus').className = 'status-indicator status-ready';
                document.getElementById('systemStatus').textContent = '系统就绪';
                showProgress('singleProgress', false);
            }
        }

        async function analyzeBatchStocks() {
            const stockListText = document.getElementById('stockList').value.trim();
            if (!stockListText) {
                addLog('请输入股票代码列表', 'warning');
                return;
            }

            if (isAnalyzing) {
                addLog('分析正在进行中，请稍候', 'warning');
                return;
            }

            const stockList = stockListText.split('\\n').map(s => s.trim()).filter(s => s);
            if (stockList.length === 0) {
                addLog('股票代码列表为空', 'warning');
                return;
            }

            isAnalyzing = true;
            document.getElementById('batchAnalyzeBtn').disabled = true;
            document.getElementById('systemStatus').className = 'status-indicator status-analyzing';
            document.getElementById('systemStatus').textContent = '批量分析中';

            addLog(`📊 开始批量分析 ${stockList.length} 只股票`, 'header');
            showLoading();
            showProgress('batchProgress');
            document.getElementById('currentStock').style.display = 'block';

            try {
                const response = await fetch(`${API_BASE}/api/batch_analyze`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        stock_codes: stockList
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();
                
                if (result.success) {
                    currentAnalysis = result.data;
                    displayBatchResults(result.data);
                    updateProgress('batchProgress', 100);
                    addLog(`🎉 批量分析完成！成功分析 ${result.data.length}/${stockList.length} 只股票`, 'success');
                } else {
                    throw new Error(result.error || '批量分析失败');
                }

            } catch (error) {
                addLog(`❌ 批量分析失败: ${error.message}`, 'error');
            } finally {
                isAnalyzing = false;
                document.getElementById('batchAnalyzeBtn').disabled = false;
                document.getElementById('systemStatus').className = 'status-indicator status-ready';
                document.getElementById('systemStatus').textContent = '系统就绪';
                showProgress('batchProgress', false);
                document.getElementById('currentStock').style.display = 'none';
            }
        }

        // Configuration
        function showConfig() {
            addLog('⚙️ 打开配置对话框', 'info');
            
            // 从系统信息获取当前配置状态
            fetch(`${API_BASE}/api/system_info`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const apis = data.data.configured_apis || [];
                        const versions = data.data.api_versions || {};
                        const primary = data.data.primary_api || 'openai';
                        
                        let configInfo = `🔧 Enhanced v3.0-Web AI配置状态

🎯 当前系统状态：
✅ 分析器：WebStockAnalyzer 
✅ 高并发：${data.data.max_workers}个工作线程
✅ 活跃任务：${data.data.active_tasks}个

🤖 AI API配置状态：`;

                        if (apis.length > 0) {
                            configInfo += `
✅ 已配置API：${apis.join(', ')}
🎯 主要API：${primary}

API版本详情：`;
                            apis.forEach(api => {
                                const version = versions[api] || '未知';
                                const status = version.includes('未安装') ? '❌' : '✅';
                                configInfo += `
${status} ${api}: ${version}`;
                            });
                            
                            configInfo += `

🚀 AI分析功能：完全可用
✅ 深度财务分析
✅ 技术面精准解读  
✅ 市场情绪挖掘
✅ 综合投资策略
✅ 风险机会识别`;
                        } else {
                            configInfo += `
⚠️ 未配置任何AI API密钥
🔧 当前使用：高级规则分析模式`;
                        }

                        configInfo += `

📋 配置方法：
1. 编辑项目目录下的 config.json 文件
2. 在 api_keys 部分填入您的API密钥：
   {
     "api_keys": {
       "openai": "sk-your-key",
       "anthropic": "sk-ant-your-key",
       "zhipu": "your-zhipu-key"
     }
   }
3. 重启服务器生效

🌟 推荐配置：
• OpenAI GPT-4o-mini (性价比首选)
• Claude-3-haiku (分析质量优秀)
• 智谱AI ChatGLM (国内网络稳定)

💡 提示：
• 至少配置一个API密钥获得最佳体验
• 支持自定义API Base URL
• 支持新旧版本OpenAI库自动适配
• 配置多个API作为备用保证稳定性

📁 相关文件：
• 配置文件：config.json
• 分析器：web_stock_analyzer.py  
• 服务器：flask_app.py`;

                        alert(configInfo);
                    }
                })
                .catch(error => {
                    const fallbackInfo = `🔧 Enhanced v3.0-Web AI配置管理

❌ 无法获取当前配置状态，请检查服务器连接

📋 基本配置方法：
1. 在项目目录创建或编辑 config.json
2. 填入AI API密钥
3. 重启服务器

💡 如需帮助，请查看控制台日志`;
                    alert(fallbackInfo);
                });
        }

        // Export report
        function exportReport() {
            if (!currentAnalysis) {
                addLog('⚠️ 没有可导出的报告', 'warning');
                return;
            }

            try {
                addLog('📤 开始导出分析报告...', 'info');
                
                const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
                let content, filename, reportType;

                if (Array.isArray(currentAnalysis)) {
                    reportType = `批量分析(${currentAnalysis.length}只股票)`;
                    filename = `batch_analysis_${timestamp}.md`;
                    content = generateBatchMarkdown(currentAnalysis);
                } else {
                    reportType = `单个股票(${currentAnalysis.stock_code})`;
                    filename = `stock_analysis_${currentAnalysis.stock_code}_${timestamp}.md`;
                    content = generateSingleMarkdown(currentAnalysis);
                }

                const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
                URL.revokeObjectURL(url);

                addLog(`✅ ${reportType}报告导出成功: ${filename}`, 'success');
                
                const fileSize = (content.length / 1024).toFixed(1);
                setTimeout(() => {
                    alert(`分析报告已导出！\\n\\n📄 文件名：${filename}\\n📊 报告类型：${reportType}\\n📏 文件大小：${fileSize} KB\\n🔧 分析器：Enhanced v3.0-Web | WebStockAnalyzer`);
                }, 100);

            } catch (error) {
                const errorMsg = `导出失败：${error.message}`;
                addLog(`❌ ${errorMsg}`, 'error');
                alert(errorMsg);
            }
        }

        function generateSingleMarkdown(report) {
            // 确保AI分析内容以markdown格式导出
            const aiAnalysis = report.ai_analysis || '分析数据准备中...';
            
            return `# 📈 股票分析报告 (Enhanced v3.0-Web)

## 🏢 基本信息
| 项目 | 值 |
|------|-----|
| **股票代码** | ${report.stock_code} |
| **股票名称** | ${report.stock_name} |
| **分析时间** | ${report.analysis_date} |
| **当前价格** | ¥${report.price_info.current_price.toFixed(2)} |
| **价格变动** | ${report.price_info.price_change.toFixed(2)}% |

## 📊 综合评分

### 🎯 总体评分：${report.scores.comprehensive.toFixed(1)}/100

| 维度 | 得分 | 评级 |
|------|------|------|
| **技术分析** | ${report.scores.technical.toFixed(1)}/100 | ${getScoreRating(report.scores.technical)} |
| **基本面分析** | ${report.scores.fundamental.toFixed(1)}/100 | ${getScoreRating(report.scores.fundamental)} |
| **情绪分析** | ${report.scores.sentiment.toFixed(1)}/100 | ${getScoreRating(report.scores.sentiment)} |

## 🎯 投资建议

### ${report.recommendation}

## 🤖 AI综合分析

${aiAnalysis}

---
*报告生成时间：${new Date().toLocaleString('zh-CN')}*  
*分析器版本：Enhanced v3.0-Web*  
*分析器类：WebStockAnalyzer*  
*数据来源：多维度综合分析*
`;
        }

        function generateBatchMarkdown(reports) {
            let content = `# 📊 批量股票分析报告 - Enhanced v3.0-Web

**分析时间：** ${new Date().toLocaleString('zh-CN')}
**分析数量：** ${reports.length} 只股票
**分析器版本：** Enhanced v3.0-Web
**分析器类：** WebStockAnalyzer

## 📋 分析汇总

| 排名 | 股票代码 | 股票名称 | 综合得分 | 技术面 | 基本面 | 情绪面 | 投资建议 |
|------|----------|----------|----------|--------|--------|--------|----------|
`;

            reports.sort((a, b) => b.scores.comprehensive - a.scores.comprehensive)
                   .forEach((report, index) => {
                content += `| ${index + 1} | ${report.stock_code} | ${report.stock_name} | ${report.scores.comprehensive.toFixed(1)} | ${report.scores.technical.toFixed(1)} | ${report.scores.fundamental.toFixed(1)} | ${report.scores.sentiment.toFixed(1)} | ${report.recommendation} |\\n`;
            });

            content += `\\n## 📈 详细分析\\n\\n`;
            
            reports.forEach(report => {
                content += generateSingleMarkdown(report);
                content += '\\n---\\n\\n';
            });

            return content;
        }

        function getScoreRating(score) {
            if (score >= 80) return '优秀';
            if (score >= 60) return '良好';
            if (score >= 40) return '一般';
            return '较差';
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            addLog('🚀 现代股票分析系统已启动', 'success');
            addLog('📋 Enhanced v3.0-Web | WebStockAnalyzer | 完整LLM API支持', 'info');
            addLog('🔥 高并发优化：线程池 + 异步处理 + 任务队列', 'info');
            addLog('🤖 AI分析：支持OpenAI/Claude/智谱AI智能切换', 'info');
            addLog('💡 支持股票代码：000001, 600036, 300019等', 'info');
            
            // 检查服务器连接和系统信息
            fetch(`${API_BASE}/api/system_info`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        addLog('✅ 后端服务器连接成功', 'success');
                        addLog(`🔧 系统状态：${data.data.active_tasks} 个活跃任务`, 'info');
                        addLog(`🧵 线程池：${data.data.max_workers} 个工作线程`, 'info');
                        
                        if (data.data.api_configured) {
                            const apis = data.data.configured_apis || [];
                            const versions = data.data.api_versions || {};
                            const primary = data.data.primary_api || 'openai';
                            
                            addLog(`🤖 AI API已配置: ${apis.join(', ')}`, 'success');
                            addLog(`🎯 主要API: ${primary}`, 'info');
                            
                            // 显示API版本信息
                            apis.forEach(api => {
                                const version = versions[api] || '';
                                if (version) {
                                    addLog(`   - ${api}: ${version}`, 'info');
                                }
                            });
                            
                            addLog('🚀 支持完整AI深度分析', 'success');
                        } else {
                            addLog('⚠️ 未配置AI API，将使用高级规则分析', 'warning');
                            addLog('💡 配置AI API密钥以获得最佳分析体验', 'info');
                        }
                    }
                })
                .catch(error => {
                    addLog('❌ 后端服务器连接失败，请检查服务器状态', 'error');
                });
        });
    </script>
</body>
</html>"""

def init_analyzer():
    """初始化分析器"""
    global analyzer
    try:
        logger.info("正在初始化WebStockAnalyzer...")
        analyzer = WebStockAnalyzer()
        logger.info("✅ WebStockAnalyzer初始化成功")
        return True
    except Exception as e:
        logger.error(f"❌ 分析器初始化失败: {e}")
        return False

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status', methods=['GET'])
def status():
    """系统状态检查"""
    try:
        return jsonify({
            'success': True,
            'status': 'ready',
            'message': 'Web股票分析系统运行正常',
            'analyzer_available': analyzer is not None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@async_task
def analyze_stock_async(stock_code, enable_streaming=False):
    """异步股票分析"""
    try:
        return analyzer.analyze_stock(stock_code, enable_streaming)
    except Exception as e:
        logger.error(f"异步分析失败 {stock_code}: {e}")
        raise

@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    """单只股票分析 - 支持高并发"""
    try:
        if not analyzer:
            return jsonify({
                'success': False,
                'error': '分析器未初始化'
            }), 500
        
        data = request.json
        stock_code = data.get('stock_code', '').strip()
        enable_streaming = data.get('enable_streaming', False)
        
        if not stock_code:
            return jsonify({
                'success': False,
                'error': '股票代码不能为空'
            }), 400
        
        # 检查是否有相同的分析正在进行
        with task_lock:
            if stock_code in analysis_tasks:
                return jsonify({
                    'success': False,
                    'error': f'股票 {stock_code} 正在分析中，请稍候'
                }), 429
            
            # 标记开始分析
            analysis_tasks[stock_code] = {
                'start_time': datetime.now(),
                'status': 'analyzing'
            }
        
        logger.info(f"开始分析股票: {stock_code}")
        
        try:
            # 执行分析
            report = analyzer.analyze_stock(stock_code, enable_streaming)
            
            # 清理数据中的NaN值
            cleaned_report = clean_data_for_json(report)
            
            logger.info(f"股票分析完成: {stock_code}")
            
            return jsonify({
                'success': True,
                'data': cleaned_report,
                'message': f'股票 {stock_code} 分析完成'
            })
            
        finally:
            # 清理任务状态
            with task_lock:
                analysis_tasks.pop(stock_code, None)
        
    except Exception as e:
        # 清理任务状态
        with task_lock:
            analysis_tasks.pop(stock_code, None)
        
        logger.error(f"股票分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch_analyze', methods=['POST'])
def batch_analyze():
    """批量股票分析 - 优化并发处理"""
    try:
        if not analyzer:
            return jsonify({
                'success': False,
                'error': '分析器未初始化'
            }), 500
        
        data = request.json
        stock_codes = data.get('stock_codes', [])
        
        if not stock_codes:
            return jsonify({
                'success': False,
                'error': '股票代码列表不能为空'
            }), 400
        
        # 限制批量分析数量以保证性能
        if len(stock_codes) > 10:
            return jsonify({
                'success': False,
                'error': '批量分析最多支持10只股票'
            }), 400
        
        logger.info(f"开始批量分析 {len(stock_codes)} 只股票")
        
        results = []
        failed_stocks = []
        
        # 使用线程池并发处理
        futures = {}
        for stock_code in stock_codes:
            future = analyze_stock_async(stock_code, False)
            futures[future] = stock_code
        
        # 收集结果
        for future in futures:
            stock_code = futures[future]
            try:
                report = future.result(timeout=60)  # 60秒超时
                results.append(report)
                logger.info(f"✓ {stock_code} 分析完成")
            except Exception as e:
                failed_stocks.append(stock_code)
                logger.error(f"❌ {stock_code} 分析失败: {e}")
        
        # 清理数据中的NaN值
        cleaned_results = clean_data_for_json(results)
        
        success_count = len(results)
        total_count = len(stock_codes)
        
        logger.info(f"批量分析完成，成功分析 {success_count}/{total_count} 只股票")
        
        response_data = {
            'success': True,
            'data': cleaned_results,
            'message': f'批量分析完成，成功分析 {success_count}/{total_count} 只股票'
        }
        
        if failed_stocks:
            response_data['failed_stocks'] = failed_stocks
            response_data['message'] += f'，失败股票: {", ".join(failed_stocks)}'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"批量分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/task_status/<stock_code>', methods=['GET'])
def get_task_status(stock_code):
    """获取分析任务状态"""
    try:
        with task_lock:
            task_info = analysis_tasks.get(stock_code)
            
        if not task_info:
            return jsonify({
                'success': True,
                'status': 'not_found',
                'message': f'未找到股票 {stock_code} 的分析任务'
            })
        
        # 计算分析时长
        elapsed_time = (datetime.now() - task_info['start_time']).total_seconds()
        
        return jsonify({
            'success': True,
            'status': task_info['status'],
            'elapsed_time': elapsed_time,
            'message': f'股票 {stock_code} 正在分析中'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system_info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        with task_lock:
            active_tasks = len(analysis_tasks)
        
        # 检测配置的API
        configured_apis = []
        api_versions = {}
        
        if analyzer:
            for api_name, api_key in analyzer.api_keys.items():
                if api_name != 'notes' and api_key and api_key.strip():
                    configured_apis.append(api_name)
                    
                    # 检测API版本/状态
                    if api_name == 'openai':
                        try:
                            import openai
                            if hasattr(openai, 'OpenAI'):
                                api_versions[api_name] = "新版本"
                            else:
                                api_versions[api_name] = "旧版本"
                        except ImportError:
                            api_versions[api_name] = "未安装"
                    elif api_name == 'anthropic':
                        try:
                            import anthropic
                            api_versions[api_name] = "已安装"
                        except ImportError:
                            api_versions[api_name] = "未安装"
                    elif api_name == 'zhipu':
                        try:
                            import zhipuai
                            api_versions[api_name] = "已安装"
                        except ImportError:
                            api_versions[api_name] = "未安装"
        
        return jsonify({
            'success': True,
            'data': {
                'analyzer_available': analyzer is not None,
                'active_tasks': active_tasks,
                'max_workers': executor._max_workers,
                'configured_apis': configured_apis,
                'api_versions': api_versions,
                'api_configured': len(configured_apis) > 0,
                'primary_api': analyzer.config.get('ai', {}).get('model_preference', 'openai') if analyzer else None,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

def main():
    """主函数"""
    print("🚀 启动Web版现代股票分析系统...")
    print("🔥 高并发优化版本 | 完整LLM API支持")
    print("=" * 60)
    
    # 检查依赖
    missing_deps = []
    
    try:
        import akshare
        print("   ✅ akshare: 已安装")
    except ImportError:
        missing_deps.append("akshare")
        print("   ❌ akshare: 未安装")
    
    try:
        import pandas
        print("   ✅ pandas: 已安装")
    except ImportError:
        missing_deps.append("pandas")
        print("   ❌ pandas: 未安装")
    
    try:
        import flask
        print("   ✅ flask: 已安装")
    except ImportError:
        missing_deps.append("flask")
        print("   ❌ flask: 未安装")
    
    try:
        import flask_cors
        print("   ✅ flask-cors: 已安装")
    except ImportError:
        missing_deps.append("flask-cors")
        print("   ❌ flask-cors: 未安装")
    
    # 检查AI依赖
    ai_deps = []
    try:
        import openai
        # 检测OpenAI版本
        if hasattr(openai, 'OpenAI'):
            ai_deps.append("OpenAI (新版)")
        else:
            ai_deps.append("OpenAI (旧版)")
    except ImportError:
        pass
    
    try:
        import anthropic
        ai_deps.append("Claude")
    except ImportError:
        pass
    
    try:
        import zhipuai
        ai_deps.append("智谱AI")
    except ImportError:
        pass
    
    if ai_deps:
        print(f"   🤖 AI支持: {', '.join(ai_deps)}")
    else:
        print("   ⚠️  AI依赖: 未安装 (pip install openai anthropic zhipuai)")
    
    # 检查配置文件
    if os.path.exists('config.json'):
        print("   ✅ config.json: 已存在")
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_keys = config.get('api_keys', {})
                configured_apis = [name for name, key in api_keys.items() 
                                 if name != 'notes' and key and key.strip()]
                if configured_apis:
                    print(f"   🔑 已配置API: {', '.join(configured_apis)}")
                else:
                    print("   ⚠️  API密钥: 未配置")
        except Exception as e:
            print(f"   ❌ config.json: 格式错误 - {e}")
    else:
        print("   ⚠️  config.json: 不存在，将使用默认配置")
    
    if missing_deps:
        print(f"❌ 缺少必要依赖: {', '.join(missing_deps)}")
        print(f"请运行以下命令安装: pip install {' '.join(missing_deps)}")
        return
    
    print("=" * 60)
    
    # 初始化分析器
    if not init_analyzer():
        print("❌ 分析器初始化失败，程序退出")
        return
    
    print("✅ 系统初始化完成！")
    print("🔥 高并发特性:")
    print(f"   - 线程池: {executor._max_workers} 个工作线程")
    print("   - 异步分析: 支持")
    print("   - 任务队列: 支持")
    print("   - 重复请求防护: 启用")
    print("   - 批量并发优化: 启用")
    print("🤖 AI分析特性:")
    if analyzer:
        api_keys = analyzer.api_keys
        configured_apis = [name for name, key in api_keys.items() 
                          if name != 'notes' and key and key.strip()]
        if configured_apis:
            print(f"   - 已配置API: {', '.join(configured_apis)}")
            primary_api = analyzer.config.get('ai', {}).get('model_preference', 'openai')
            print(f"   - 主要API: {primary_api}")
            
            # 显示自定义配置
            api_base = analyzer.config.get('ai', {}).get('api_base_urls', {}).get('openai')
            if api_base:
                print(f"   - 自定义API地址: {api_base}")
            
            model = analyzer.config.get('ai', {}).get('models', {}).get(primary_api, 'default')
            print(f"   - 使用模型: {model}")
            
            print("   - LLM深度分析: 完整支持")
        else:
            print("   - API配置: 未配置")
            print("   - 分析模式: 高级规则分析")
    else:
        print("   - 分析器: 未初始化")
    
    print("   - 多模型支持: OpenAI/Claude/智谱AI")
    print("   - 智能切换: 启用")
    print("   - 版本兼容: 新旧版本自动适配")
    print("   - 规则分析备用: 启用")
    print("📋 分析配置:")
    if analyzer:
        params = analyzer.analysis_params
        weights = analyzer.analysis_weights
        print(f"   - 技术分析周期: {params.get('technical_period_days', 180)} 天")
        print(f"   - 财务指标数量: {params.get('financial_indicators_count', 20)} 项")
        print(f"   - 新闻分析数量: {params.get('max_news_count', 100)} 条")
        print(f"   - 分析权重: 技术{weights['technical']:.1f} | 基本面{weights['fundamental']:.1f} | 情绪{weights['sentiment']:.1f}")
    else:
        print("   - 配置: 使用默认值")
    
    print("📋 性能优化:")
    print("   - 日志文件: 已禁用")
    print("   - JSON压缩: 启用")
    print("   - 缓存优化: 启用")
    print("🌐 Web服务器启动中...")
    print("📱 请在浏览器中访问: http://localhost:5000")
    print("🔧 API接口文档:")
    print("   - GET  /api/status - 系统状态")
    print("   - POST /api/analyze - 单只股票分析")
    print("   - POST /api/batch_analyze - 批量股票分析")
    print("   - GET  /api/task_status/<code> - 任务状态")
    print("   - GET  /api/system_info - 系统信息")
    print("=" * 60)
    
    # 启动Flask服务器
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生产环境关闭debug
            threaded=True,
            use_reloader=False,  # 关闭自动重载提升性能
            processes=1  # 单进程模式，使用线程池处理并发
        )
    except KeyboardInterrupt:
        print("\n👋 系统已关闭")
        # 清理线程池
        executor.shutdown(wait=True)
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        executor.shutdown(wait=True)

if __name__ == '__main__':
    main()
