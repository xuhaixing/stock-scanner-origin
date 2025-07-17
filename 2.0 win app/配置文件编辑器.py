"""
配置管理器GUI - 可视化配置编辑器
"""

import sys
import os
import json
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLineEdit, QPushButton, QLabel, QTextEdit,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QMessageBox, QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

class ConfigManagerWindow(QMainWindow):
    """配置管理器主窗口"""
    
    config_updated = pyqtSignal()
    
    def __init__(self, config_file='config.json'):
        super().__init__()
        self.config_file = config_file
        self.config = {}
        self.widgets = {}  # 存储配置控件
        
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("🔧 AI股票分析系统 - 配置管理器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("🤖 AI股票分析系统配置")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 创建各个配置选项卡
        self.create_ai_tab()
        self.create_analysis_tab()
        self.create_cache_tab()
        self.create_advanced_tab()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 预设配置按钮
        preset_layout = QHBoxLayout()
        preset_label = QLabel("快速配置:")
        preset_layout.addWidget(preset_label)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["自定义", "短线交易", "长线投资", "波段交易"])
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        preset_layout.addWidget(self.preset_combo)
        
        button_layout.addLayout(preset_layout)
        button_layout.addStretch()
        
        # 操作按钮
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.reset_btn = QPushButton("🔄 重置默认")
        self.reset_btn.clicked.connect(self.reset_to_default)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        self.test_btn = QPushButton("🧪 测试连接")
        self.test_btn.clicked.connect(self.test_api_connections)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("📝 请配置您的API密钥以启用AI分析功能")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.status_label)
        
    def create_ai_tab(self):
        """创建AI配置选项卡"""
        ai_widget = QScrollArea()
        ai_content = QWidget()
        ai_layout = QVBoxLayout(ai_content)
        
        # API密钥配置
        api_group = QGroupBox("🔑 AI API配置")
        api_layout = QFormLayout(api_group)
        
        # OpenAI配置
        openai_group = QGroupBox("OpenAI (推荐)")
        openai_layout = QFormLayout(openai_group)
        
        self.widgets['openai_key'] = QLineEdit()
        self.widgets['openai_key'].setPlaceholderText("sk-...")
        self.widgets['openai_key'].setEchoMode(QLineEdit.EchoMode.Password)
        openai_layout.addRow("API密钥:", self.widgets['openai_key'])
        
        self.widgets['openai_model'] = QComboBox()
        self.widgets['openai_model'].addItems([
            "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
        ])
        openai_layout.addRow("模型选择:", self.widgets['openai_model'])
        
        self.widgets['openai_base'] = QLineEdit()
        self.widgets['openai_base'].setPlaceholderText("https://api.openai.com/v1")
        openai_layout.addRow("API地址:", self.widgets['openai_base'])
        
        api_layout.addRow(openai_group)
        
        # Claude配置
        claude_group = QGroupBox("Anthropic Claude")
        claude_layout = QFormLayout(claude_group)
        
        self.widgets['anthropic_key'] = QLineEdit()
        self.widgets['anthropic_key'].setPlaceholderText("sk-ant-...")
        self.widgets['anthropic_key'].setEchoMode(QLineEdit.EchoMode.Password)
        claude_layout.addRow("API密钥:", self.widgets['anthropic_key'])
        
        self.widgets['anthropic_model'] = QComboBox()
        self.widgets['anthropic_model'].addItems([
            "claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"
        ])
        claude_layout.addRow("模型选择:", self.widgets['anthropic_model'])
        
        api_layout.addRow(claude_group)
        
        # 智谱AI配置
        zhipu_group = QGroupBox("智谱AI (国内)")
        zhipu_layout = QFormLayout(zhipu_group)
        
        self.widgets['zhipu_key'] = QLineEdit()
        self.widgets['zhipu_key'].setPlaceholderText("...")
        self.widgets['zhipu_key'].setEchoMode(QLineEdit.EchoMode.Password)
        zhipu_layout.addRow("API密钥:", self.widgets['zhipu_key'])
        
        api_layout.addRow(zhipu_group)
        
        ai_layout.addWidget(api_group)
        
        # AI参数配置
        params_group = QGroupBox("🎛️ AI参数配置")
        params_layout = QFormLayout(params_group)
        
        self.widgets['model_preference'] = QComboBox()
        self.widgets['model_preference'].addItems(["openai", "anthropic", "zhipu"])
        params_layout.addRow("首选AI服务:", self.widgets['model_preference'])
        
        self.widgets['max_tokens'] = QSpinBox()
        self.widgets['max_tokens'].setRange(500, 8000)
        self.widgets['max_tokens'].setValue(4000)
        params_layout.addRow("最大Token数:", self.widgets['max_tokens'])
        
        self.widgets['temperature'] = QDoubleSpinBox()
        self.widgets['temperature'].setRange(0.0, 2.0)
        self.widgets['temperature'].setSingleStep(0.1)
        self.widgets['temperature'].setValue(0.7)
        params_layout.addRow("创造性参数:", self.widgets['temperature'])
        
        ai_layout.addWidget(params_group)
        
        ai_widget.setWidget(ai_content)
        self.tab_widget.addTab(ai_widget, "🤖 AI配置")
        
    def create_analysis_tab(self):
        """创建分析配置选项卡"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        
        # 分析权重配置
        weights_group = QGroupBox("⚖️ 分析权重配置")
        weights_layout = QFormLayout(weights_group)
        
        self.widgets['technical_weight'] = QDoubleSpinBox()
        self.widgets['technical_weight'].setRange(0.0, 1.0)
        self.widgets['technical_weight'].setSingleStep(0.1)
        self.widgets['technical_weight'].setValue(0.4)
        weights_layout.addRow("技术分析权重:", self.widgets['technical_weight'])
        
        self.widgets['fundamental_weight'] = QDoubleSpinBox()
        self.widgets['fundamental_weight'].setRange(0.0, 1.0)
        self.widgets['fundamental_weight'].setSingleStep(0.1)
        self.widgets['fundamental_weight'].setValue(0.4)
        weights_layout.addRow("基本面权重:", self.widgets['fundamental_weight'])
        
        self.widgets['sentiment_weight'] = QDoubleSpinBox()
        self.widgets['sentiment_weight'].setRange(0.0, 1.0)
        self.widgets['sentiment_weight'].setSingleStep(0.1)
        self.widgets['sentiment_weight'].setValue(0.2)
        weights_layout.addRow("情绪分析权重:", self.widgets['sentiment_weight'])
        
        # 权重自动调整提示
        weight_note = QLabel("💡 权重总和应为1.0，系统会自动调整")
        weight_note.setStyleSheet("color: #666; font-style: italic;")
        weights_layout.addRow(weight_note)
        
        analysis_layout.addWidget(weights_group)
        
        # 分析参数配置
        params_group = QGroupBox("📊 分析参数")
        params_layout = QFormLayout(params_group)
        
        self.widgets['max_news_count'] = QSpinBox()
        self.widgets['max_news_count'].setRange(10, 500)
        self.widgets['max_news_count'].setValue(100)
        params_layout.addRow("最大新闻数量:", self.widgets['max_news_count'])
        
        self.widgets['technical_period_days'] = QSpinBox()
        self.widgets['technical_period_days'].setRange(30, 1000)
        self.widgets['technical_period_days'].setValue(365)
        params_layout.addRow("技术分析周期(天):", self.widgets['technical_period_days'])
        
        analysis_layout.addWidget(params_group)
        
        # 流式分析配置
        streaming_group = QGroupBox("🔄 流式分析")
        streaming_layout = QFormLayout(streaming_group)
        
        self.widgets['streaming_enabled'] = QCheckBox("启用流式分析")
        streaming_layout.addRow(self.widgets['streaming_enabled'])
        
        self.widgets['streaming_delay'] = QDoubleSpinBox()
        self.widgets['streaming_delay'].setRange(0.0, 2.0)
        self.widgets['streaming_delay'].setSingleStep(0.1)
        self.widgets['streaming_delay'].setValue(0.1)
        streaming_layout.addRow("流式延迟(秒):", self.widgets['streaming_delay'])
        
        analysis_layout.addWidget(streaming_group)
        
        analysis_layout.addStretch()
        self.tab_widget.addTab(analysis_widget, "📈 分析配置")
        
    def create_cache_tab(self):
        """创建缓存配置选项卡"""
        cache_widget = QWidget()
        cache_layout = QVBoxLayout(cache_widget)
        
        # 缓存时间配置
        cache_group = QGroupBox("💾 数据缓存配置")
        cache_layout_form = QFormLayout(cache_group)
        
        self.widgets['price_cache_hours'] = QSpinBox()
        self.widgets['price_cache_hours'].setRange(0, 24)
        self.widgets['price_cache_hours'].setValue(1)
        cache_layout_form.addRow("价格数据缓存(小时):", self.widgets['price_cache_hours'])
        
        self.widgets['fundamental_cache_hours'] = QSpinBox()
        self.widgets['fundamental_cache_hours'].setRange(0, 48)
        self.widgets['fundamental_cache_hours'].setValue(6)
        cache_layout_form.addRow("基本面数据缓存(小时):", self.widgets['fundamental_cache_hours'])
        
        self.widgets['news_cache_hours'] = QSpinBox()
        self.widgets['news_cache_hours'].setRange(0, 12)
        self.widgets['news_cache_hours'].setValue(2)
        cache_layout_form.addRow("新闻数据缓存(小时):", self.widgets['news_cache_hours'])
        
        # 缓存说明
        cache_note = QLabel("""💡 缓存说明：
• 较短缓存时间：数据更新及时，但API调用次数增加
• 较长缓存时间：减少API调用，但数据可能不够实时
• 建议根据使用频率和成本考虑调整""")
        cache_note.setStyleSheet("color: #666; font-style: italic; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        cache_layout_form.addRow(cache_note)
        
        cache_layout.addWidget(cache_group)
        cache_layout.addStretch()
        
        self.tab_widget.addTab(cache_widget, "💾 缓存配置")
        
    def create_advanced_tab(self):
        """创建高级配置选项卡"""
        advanced_widget = QScrollArea()
        advanced_content = QWidget()
        advanced_layout = QVBoxLayout(advanced_content)
        
        # 数据源配置
        datasource_group = QGroupBox("📡 数据源配置")
        datasource_layout = QFormLayout(datasource_group)
        
        self.widgets['akshare_token'] = QLineEdit()
        self.widgets['akshare_token'].setPlaceholderText("如需要请填入akshare token")
        datasource_layout.addRow("AKShare Token:", self.widgets['akshare_token'])
        
        advanced_layout.addWidget(datasource_group)
        
        # 界面配置
        ui_group = QGroupBox("🎨 界面配置")
        ui_layout = QFormLayout(ui_group)
        
        self.widgets['theme'] = QComboBox()
        self.widgets['theme'].addItems(["default", "dark", "light"])
        ui_layout.addRow("主题:", self.widgets['theme'])
        
        self.widgets['language'] = QComboBox()
        self.widgets['language'].addItems(["zh_CN", "en_US"])
        ui_layout.addRow("语言:", self.widgets['language'])
        
        advanced_layout.addWidget(ui_group)
        
        # 日志配置
        logging_group = QGroupBox("📝 日志配置")
        logging_layout = QFormLayout(logging_group)
        
        self.widgets['log_level'] = QComboBox()
        self.widgets['log_level'].addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("日志级别:", self.widgets['log_level'])
        
        self.widgets['log_file'] = QLineEdit()
        self.widgets['log_file'].setText("stock_analyzer.log")
        logging_layout.addRow("日志文件:", self.widgets['log_file'])
        
        advanced_layout.addWidget(logging_group)
        
        # 配置文件操作
        config_group = QGroupBox("⚙️ 配置文件操作")
        config_layout = QVBoxLayout(config_group)
        
        # 导入导出按钮
        import_export_layout = QHBoxLayout()
        
        import_btn = QPushButton("📥 导入配置")
        import_btn.clicked.connect(self.import_config)
        import_export_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 导出配置")
        export_btn.clicked.connect(self.export_config)
        import_export_layout.addWidget(export_btn)
        
        config_layout.addLayout(import_export_layout)
        
        # 配置文件预览
        preview_label = QLabel("📄 配置文件预览:")
        config_layout.addWidget(preview_label)
        
        self.config_preview = QTextEdit()
        self.config_preview.setMaximumHeight(200)
        self.config_preview.setStyleSheet("font-family: 'Courier New', monospace; font-size: 10px;")
        config_layout.addWidget(self.config_preview)
        
        advanced_layout.addWidget(config_group)
        
        advanced_widget.setWidget(advanced_content)
        self.tab_widget.addTab(advanced_widget, "⚙️ 高级配置")
        
    def load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                
            self.populate_widgets()
            self.update_config_preview()
            self.update_status()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置文件失败: {e}")
            
    def populate_widgets(self):
        """用配置数据填充控件"""
        try:
            # API密钥
            api_keys = self.config.get('api_keys', {})
            self.widgets['openai_key'].setText(api_keys.get('openai', ''))
            self.widgets['anthropic_key'].setText(api_keys.get('anthropic', ''))
            self.widgets['zhipu_key'].setText(api_keys.get('zhipu', ''))
            
            # AI配置
            ai_config = self.config.get('ai', {})
            models = ai_config.get('models', {})
            api_base_urls = ai_config.get('api_base_urls', {})
            
            self.widgets['model_preference'].setCurrentText(ai_config.get('model_preference', 'openai'))
            self.widgets['openai_model'].setCurrentText(models.get('openai', 'gpt-4o-mini'))
            self.widgets['anthropic_model'].setCurrentText(models.get('anthropic', 'claude-3-haiku-20240307'))
            self.widgets['openai_base'].setText(api_base_urls.get('openai', 'https://api.openai.com/v1'))
            
            self.widgets['max_tokens'].setValue(ai_config.get('max_tokens', 4000))
            self.widgets['temperature'].setValue(ai_config.get('temperature', 0.7))
            
            # 分析权重
            weights = self.config.get('analysis_weights', {})
            self.widgets['technical_weight'].setValue(weights.get('technical', 0.4))
            self.widgets['fundamental_weight'].setValue(weights.get('fundamental', 0.4))
            self.widgets['sentiment_weight'].setValue(weights.get('sentiment', 0.2))
            
            # 缓存配置
            cache_config = self.config.get('cache', {})
            self.widgets['price_cache_hours'].setValue(cache_config.get('price_hours', 1))
            self.widgets['fundamental_cache_hours'].setValue(cache_config.get('fundamental_hours', 6))
            self.widgets['news_cache_hours'].setValue(cache_config.get('news_hours', 2))
            
            # 流式配置
            streaming = self.config.get('streaming', {})
            self.widgets['streaming_enabled'].setChecked(streaming.get('enabled', True))
            self.widgets['streaming_delay'].setValue(streaming.get('delay', 0.1))
            
            # 分析参数
            params = self.config.get('analysis_params', {})
            self.widgets['max_news_count'].setValue(params.get('max_news_count', 100))
            self.widgets['technical_period_days'].setValue(params.get('technical_period_days', 365))
            
            # 高级配置
            datasources = self.config.get('data_sources', {})
            self.widgets['akshare_token'].setText(datasources.get('akshare_token', ''))
            
            ui_config = self.config.get('ui', {})
            self.widgets['theme'].setCurrentText(ui_config.get('theme', 'default'))
            self.widgets['language'].setCurrentText(ui_config.get('language', 'zh_CN'))
            
            logging_config = self.config.get('logging', {})
            self.widgets['log_level'].setCurrentText(logging_config.get('level', 'INFO'))
            self.widgets['log_file'].setText(logging_config.get('file', 'stock_analyzer.log'))
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"填充配置数据时出错: {e}")
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "api_keys": {"openai": "", "anthropic": "", "zhipu": ""},
            "ai": {
                "model_preference": "openai",
                "models": {
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-haiku-20240307",
                    "zhipu": "chatglm_turbo"
                },
                "max_tokens": 4000,
                "temperature": 0.7,
                "api_base_urls": {"openai": "https://api.openai.com/v1"}
            },
            "analysis_weights": {"technical": 0.4, "fundamental": 0.4, "sentiment": 0.2},
            "cache": {"price_hours": 1, "fundamental_hours": 6, "news_hours": 2},
            "streaming": {"enabled": True, "show_thinking": True, "delay": 0.1},
            "analysis_params": {"max_news_count": 100, "technical_period_days": 365},
            "logging": {"level": "INFO", "file": "stock_analyzer.log"},
            "data_sources": {"akshare_token": ""},
            "ui": {"theme": "default", "language": "zh_CN"}
        }
    
    def collect_config_from_widgets(self):
        """从控件收集配置数据"""
        config = {}
        
        # API密钥
        config['api_keys'] = {
            'openai': self.widgets['openai_key'].text().strip(),
            'anthropic': self.widgets['anthropic_key'].text().strip(),
            'zhipu': self.widgets['zhipu_key'].text().strip()
        }
        
        # AI配置
        config['ai'] = {
            'model_preference': self.widgets['model_preference'].currentText(),
            'models': {
                'openai': self.widgets['openai_model'].currentText(),
                'anthropic': self.widgets['anthropic_model'].currentText(),
                'zhipu': 'chatglm_turbo'
            },
            'max_tokens': self.widgets['max_tokens'].value(),
            'temperature': self.widgets['temperature'].value(),
            'api_base_urls': {
                'openai': self.widgets['openai_base'].text().strip() or 'https://api.openai.com/v1'
            }
        }
        
        # 分析权重（自动归一化）
        total_weight = (self.widgets['technical_weight'].value() + 
                       self.widgets['fundamental_weight'].value() + 
                       self.widgets['sentiment_weight'].value())
        
        if total_weight > 0:
            config['analysis_weights'] = {
                'technical': self.widgets['technical_weight'].value() / total_weight,
                'fundamental': self.widgets['fundamental_weight'].value() / total_weight,
                'sentiment': self.widgets['sentiment_weight'].value() / total_weight
            }
        else:
            config['analysis_weights'] = {'technical': 0.4, 'fundamental': 0.4, 'sentiment': 0.2}
        
        # 缓存配置
        config['cache'] = {
            'price_hours': self.widgets['price_cache_hours'].value(),
            'fundamental_hours': self.widgets['fundamental_cache_hours'].value(),
            'news_hours': self.widgets['news_cache_hours'].value()
        }
        
        # 流式配置
        config['streaming'] = {
            'enabled': self.widgets['streaming_enabled'].isChecked(),
            'show_thinking': True,
            'delay': self.widgets['streaming_delay'].value()
        }
        
        # 分析参数
        config['analysis_params'] = {
            'max_news_count': self.widgets['max_news_count'].value(),
            'technical_period_days': self.widgets['technical_period_days'].value()
        }
        
        # 数据源
        config['data_sources'] = {
            'akshare_token': self.widgets['akshare_token'].text().strip()
        }
        
        # UI配置
        config['ui'] = {
            'theme': self.widgets['theme'].currentText(),
            'language': self.widgets['language'].currentText()
        }
        
        # 日志配置
        config['logging'] = {
            'level': self.widgets['log_level'].currentText(),
            'file': self.widgets['log_file'].text().strip()
        }
        
        return config
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config = self.collect_config_from_widgets()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            self.config = config
            self.update_config_preview()
            self.update_status()
            
            QMessageBox.information(self, "成功", "配置已保存成功！\n重启程序后生效。")
            self.config_updated.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
    
    def reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(self, "确认", "确定要重置为默认配置吗？\n当前配置将丢失。")
        if reply == QMessageBox.StandardButton.Yes:
            self.config = self.get_default_config()
            self.populate_widgets()
            self.update_config_preview()
            self.update_status()
    
    def load_preset(self, preset_name):
        """加载预设配置"""
        if preset_name == "自定义":
            return
            
        presets = {
            "短线交易": {
                "analysis_weights": {"technical": 0.6, "fundamental": 0.2, "sentiment": 0.2},
                "cache": {"price_hours": 0.5, "fundamental_hours": 4, "news_hours": 1}
            },
            "长线投资": {
                "analysis_weights": {"technical": 0.2, "fundamental": 0.6, "sentiment": 0.2},
                "cache": {"price_hours": 2, "fundamental_hours": 12, "news_hours": 6}
            },
            "波段交易": {
                "analysis_weights": {"technical": 0.4, "fundamental": 0.3, "sentiment": 0.3},
                "cache": {"price_hours": 1, "fundamental_hours": 6, "news_hours": 2}
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            
            # 应用权重设置
            weights = preset.get("analysis_weights", {})
            self.widgets['technical_weight'].setValue(weights.get('technical', 0.4))
            self.widgets['fundamental_weight'].setValue(weights.get('fundamental', 0.4))
            self.widgets['sentiment_weight'].setValue(weights.get('sentiment', 0.2))
            
            # 应用缓存设置
            cache = preset.get("cache", {})
            self.widgets['price_cache_hours'].setValue(cache.get('price_hours', 1))
            self.widgets['fundamental_cache_hours'].setValue(cache.get('fundamental_hours', 6))
            self.widgets['news_cache_hours'].setValue(cache.get('news_hours', 2))
    
    def test_api_connections(self):
        """测试API连接"""
        # 这里可以添加实际的API测试逻辑
        QMessageBox.information(self, "测试结果", "API连接测试功能开发中...")
    
    def import_config(self):
        """导入配置文件"""
        QMessageBox.information(self, "导入配置", "配置导入功能开发中...")
    
    def export_config(self):
        """导出配置文件"""
        QMessageBox.information(self, "导出配置", "配置导出功能开发中...")
    
    def update_config_preview(self):
        """更新配置预览"""
        try:
            config_text = json.dumps(self.config, ensure_ascii=False, indent=2)
            self.config_preview.setPlainText(config_text)
        except Exception as e:
            self.config_preview.setPlainText(f"预览失败: {e}")
    
    def update_status(self):
        """更新状态显示"""
        api_keys = self.config.get('api_keys', {})
        configured_apis = [api for api, key in api_keys.items() if key and key.strip()]
        
        if configured_apis:
            self.status_label.setText(f"✅ 已配置API: {', '.join(configured_apis)}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("⚠️ 请配置至少一个AI API密钥")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    window = ConfigManagerWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
