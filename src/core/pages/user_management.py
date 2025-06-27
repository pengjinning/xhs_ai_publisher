import sys
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QScrollArea, QTabWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QFrame, QSplitter, QGraphicsDropShadowEffect,
    QProgressDialog
)
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter, QLinearGradient
from PyQt6.QtWidgets import QApplication

from ..services.user_service import user_service
from ..services.proxy_service import proxy_service
from ..services.fingerprint_service import fingerprint_service


class UserManagementPage(QWidget):
    """用户管理页面"""
    
    user_switched = pyqtSignal(int)  # 用户切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.init_ui()
        self.apply_styles()
        self.load_users()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题区域
        header_widget = self.create_header_widget()
        layout.addWidget(header_widget)
        
        # 主内容区域
        main_widget = self.create_main_widget()
        layout.addWidget(main_widget)
    
    def create_header_widget(self):
        """创建页面头部"""
        header = QFrame()
        header.setObjectName("headerFrame")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # 标题和图标
        title_layout = QVBoxLayout()
        
        title_label = QLabel("👥 用户管理中心")
        title_label.setObjectName("pageTitle")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        
        subtitle_label = QLabel("管理用户账户、代理配置和浏览器指纹")
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setFont(QFont("Microsoft YaHei", 10))
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # 快捷操作按钮
        quick_actions = QHBoxLayout()
        
        self.quick_add_user_btn = self.create_modern_button("➕ 快速添加", "primary")
        self.quick_add_user_btn.clicked.connect(self.add_user)
        quick_actions.addWidget(self.quick_add_user_btn)
        
        self.refresh_all_btn = self.create_modern_button("🔄 刷新数据", "secondary")
        self.refresh_all_btn.clicked.connect(self.load_users)
        quick_actions.addWidget(self.refresh_all_btn)
        
        layout.addLayout(quick_actions)
        
        return header
    
    def create_main_widget(self):
        """创建主内容区域"""
        main_widget = QFrame()
        main_widget.setObjectName("mainContentFrame")
        
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 左侧用户列表
        left_panel = self.create_user_list_panel()
        layout.addWidget(left_panel, 1)
        
        # 右侧配置面板
        right_panel = self.create_config_panel()
        layout.addWidget(right_panel, 2)
        
        return main_widget
    
    def create_user_list_panel(self):
        """创建用户列表面板"""
        panel = QFrame()
        panel.setObjectName("userListPanel")
        panel.setMinimumWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 面板标题
        panel_title = QLabel("👤 用户列表")
        panel_title.setObjectName("panelTitle")
        panel_title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(panel_title)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchEdit")
        self.search_edit.setPlaceholderText("🔍 搜索用户...")
        self.search_edit.textChanged.connect(self.filter_users)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # 用户表格
        self.user_table = QTableWidget()
        self.user_table.setObjectName("userTable")
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["用户名", "显示名", "手机号", "状态"])
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.itemSelectionChanged.connect(self.on_user_selected)
        layout.addWidget(self.user_table)
        
        # 操作按钮组
        button_group = self.create_button_group([
            ("🔄 切换用户", "switch_user", "primary"),
            ("✏️ 编辑", "edit_user", "secondary"),
            ("🗑️ 删除", "delete_user", "danger")
        ])
        layout.addWidget(button_group)
        
        return panel
    
    def create_config_panel(self):
        """创建配置面板"""
        panel = QFrame()
        panel.setObjectName("configPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 当前用户信息卡片
        self.user_info_card = self.create_user_info_card()
        layout.addWidget(self.user_info_card)
        
        # 配置标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("configTabs")
        
        # 代理配置标签页
        proxy_tab = self.create_proxy_tab()
        self.tab_widget.addTab(proxy_tab, "🌐 代理配置")
        
        # 浏览器指纹标签页
        fingerprint_tab = self.create_fingerprint_tab()
        self.tab_widget.addTab(fingerprint_tab, "🔍 浏览器指纹")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_user_info_card(self):
        """创建用户信息卡片"""
        card = QFrame()
        card.setObjectName("userInfoCard")
        card.setFixedHeight(120)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 用户头像区域
        avatar_label = QLabel("👤")
        avatar_label.setObjectName("userAvatar")
        avatar_label.setFont(QFont("", 32))
        avatar_label.setFixedSize(60, 60)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar_label)
        
        # 用户信息
        info_layout = QVBoxLayout()
        
        self.current_user_name = QLabel("请选择用户")
        self.current_user_name.setObjectName("currentUserName")
        self.current_user_name.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        
        self.current_user_phone = QLabel("未选择")
        self.current_user_phone.setObjectName("currentUserPhone")
        self.current_user_phone.setFont(QFont("Microsoft YaHei", 10))
        
        self.current_user_status = QLabel("🔴 离线")
        self.current_user_status.setObjectName("currentUserStatus")
        self.current_user_status.setFont(QFont("Microsoft YaHei", 9))
        
        info_layout.addWidget(self.current_user_name)
        info_layout.addWidget(self.current_user_phone)
        info_layout.addWidget(self.current_user_status)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        return card
    
    def create_proxy_tab(self):
        """创建代理配置标签页"""
        widget = QFrame()
        widget.setObjectName("proxyTab")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题和操作按钮
        header_layout = QHBoxLayout()
        
        proxy_title = QLabel("🌐 代理服务器配置")
        proxy_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(proxy_title)
        header_layout.addStretch()
        
        # 操作按钮
        self.add_proxy_btn = self.create_modern_button("➕ 添加", "primary", small=True)
        self.add_proxy_btn.clicked.connect(self.add_proxy)
        header_layout.addWidget(self.add_proxy_btn)
        
        self.test_proxy_btn = self.create_modern_button("🧪 测试", "secondary", small=True)
        self.test_proxy_btn.clicked.connect(self.test_proxy)
        header_layout.addWidget(self.test_proxy_btn)
        
        layout.addLayout(header_layout)
        
        # 代理列表
        self.proxy_table = QTableWidget()
        self.proxy_table.setObjectName("proxyTable")
        self.proxy_table.setColumnCount(6)
        self.proxy_table.setHorizontalHeaderLabels(["名称", "类型", "地址", "端口", "状态", "延迟"])
        self.proxy_table.horizontalHeader().setStretchLastSection(True)
        self.proxy_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.proxy_table.setAlternatingRowColors(True)
        self.proxy_table.verticalHeader().setVisible(False)
        layout.addWidget(self.proxy_table)
        
        # 操作按钮组
        button_group = self.create_button_group([
            ("⭐ 设为默认", "set_default_proxy", "primary"),
            ("✏️ 编辑", "edit_proxy", "secondary"),
            ("🗑️ 删除", "delete_proxy", "danger")
        ])
        layout.addWidget(button_group)
        
        return widget
    
    def create_fingerprint_tab(self):
        """创建浏览器指纹标签页"""
        widget = QFrame()
        widget.setObjectName("fingerprintTab")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题和操作按钮
        header_layout = QHBoxLayout()
        
        fingerprint_title = QLabel("🔍 浏览器指纹配置")
        fingerprint_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(fingerprint_title)
        header_layout.addStretch()
        
        # 操作按钮
        self.add_fingerprint_btn = self.create_modern_button("➕ 添加", "primary", small=True)
        self.add_fingerprint_btn.clicked.connect(self.add_fingerprint)
        header_layout.addWidget(self.add_fingerprint_btn)
        
        self.generate_random_btn = self.create_modern_button("🎲 随机生成", "secondary", small=True)
        self.generate_random_btn.clicked.connect(self.generate_random_fingerprint)
        header_layout.addWidget(self.generate_random_btn)
        
        self.create_presets_btn = self.create_modern_button("📋 预设", "info", small=True)
        self.create_presets_btn.clicked.connect(self.create_preset_fingerprints)
        header_layout.addWidget(self.create_presets_btn)
        
        layout.addLayout(header_layout)
        
        # 指纹列表
        self.fingerprint_table = QTableWidget()
        self.fingerprint_table.setObjectName("fingerprintTable")
        self.fingerprint_table.setColumnCount(5)
        self.fingerprint_table.setHorizontalHeaderLabels(["名称", "平台", "分辨率", "User-Agent", "状态"])
        self.fingerprint_table.horizontalHeader().setStretchLastSection(True)
        self.fingerprint_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.fingerprint_table.setAlternatingRowColors(True)
        self.fingerprint_table.verticalHeader().setVisible(False)
        layout.addWidget(self.fingerprint_table)
        
        # 操作按钮组
        button_group = self.create_button_group([
            ("⭐ 设为默认", "set_default_fingerprint", "primary"),
            ("✏️ 编辑", "edit_fingerprint", "secondary"),
            ("🗑️ 删除", "delete_fingerprint", "danger")
        ])
        layout.addWidget(button_group)
        
        return widget
    
    def create_modern_button(self, text, style_type="primary", small=False):
        """创建现代化按钮"""
        button = QPushButton(text)
        button.setObjectName(f"modernButton_{style_type}")
        
        if small:
            button.setFixedHeight(32)
            button.setFont(QFont("Microsoft YaHei", 9))
        else:
            button.setFixedHeight(40)
            button.setFont(QFont("Microsoft YaHei", 10))
        
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        button.setGraphicsEffect(shadow)
        
        return button
    
    def create_button_group(self, buttons_config):
        """创建按钮组"""
        group = QFrame()
        group.setObjectName("buttonGroup")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        for text, method_name, style in buttons_config:
            button = self.create_modern_button(text, style, small=True)
            button.clicked.connect(getattr(self, method_name))
            if method_name in ['switch_user', 'edit_user', 'delete_user']:
                button.setEnabled(False)
                setattr(self, f"{method_name}_btn", button)
            layout.addWidget(button)
        
        layout.addStretch()
        return group
    
    def apply_styles(self):
        """应用样式表"""
        self.setStyleSheet("""
            /* 主容器样式 */
            UserManagementPage {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            
            /* 头部样式 */
            #headerFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.85));
                border: none;
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            
            #pageTitle {
                color: #1a1a1a;
                font-weight: 700;
                font-size: 24px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #pageSubtitle {
                color: #333333;
                font-weight: 500;
                font-size: 14px;
            }
            
            /* 主内容区域 */
            #mainContentFrame {
                background: transparent;
            }
            
            /* 面板样式 - 玻璃态效果 */
            #userListPanel, #configPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.85));
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                backdrop-filter: blur(15px);
            }
            
            #panelTitle {
                color: #1a1a1a;
                padding: 8px 0;
                font-weight: 700;
                font-size: 18px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            
            /* 用户信息卡片 - 更炫酷的渐变 */
            #userInfoCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.3 #764ba2, stop:0.7 #f093fb, stop:1 #f5576c);
                border: none;
                border-radius: 18px;
                box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
            }
            
            #userAvatar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.3), stop:1 rgba(255,255,255,0.1));
                border: 3px solid rgba(255,255,255,0.4);
                border-radius: 30px;
                backdrop-filter: blur(10px);
            }
            
            #currentUserName {
                color: white;
                font-weight: 700;
                font-size: 16px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }
            
            #currentUserPhone, #currentUserStatus {
                color: rgba(255, 255, 255, 0.95);
                font-size: 14px;
                font-weight: 500;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            
            /* 搜索框样式 - 现代化设计 */
            #searchEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 30px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.8));
                font-size: 14px;
                color: #1a1a1a;
                font-weight: 500;
                backdrop-filter: blur(10px);
            }
            
            #searchEdit:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.95);
                outline: none;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
            }
            
            /* 表格样式 - 现代卡片设计 */
            #userTable, #proxyTable, #fingerprintTable {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.9));
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 15px;
                gridline-color: rgba(200,200,200,0.5);
                selection-background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102,126,234,0.2), stop:1 rgba(118,75,162,0.2));
                alternate-background-color: rgba(248,249,250,0.5);
                backdrop-filter: blur(10px);
            }
            
            #userTable::item, #proxyTable::item, #fingerprintTable::item {
                padding: 12px 8px;
                border-bottom: 1px solid rgba(200,200,200,0.3);
                color: #1a1a1a;
                font-weight: 500;
                font-size: 13px;
            }
            
            #userTable::item:selected, #proxyTable::item:selected, #fingerprintTable::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102,126,234,0.3), stop:1 rgba(118,75,162,0.3));
                color: #1a1a1a;
                font-weight: 600;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(248,249,250,0.9), stop:1 rgba(233,236,239,0.8));
                padding: 15px 10px;
                border: none;
                border-bottom: 2px solid rgba(102,126,234,0.3);
                font-weight: 700;
                color: #1a1a1a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 12px;
            }
            
            /* 标签页样式 - 更现代的设计 */
            #configTabs {
                background: transparent;
                border-radius: 15px;
            }
            
            #configTabs::pane {
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(255,255,255,0.8));
                backdrop-filter: blur(10px);
            }
            
            #configTabs::tab-bar {
                alignment: left;
            }
            
            #configTabs QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(248,249,250,0.8), stop:1 rgba(233,236,239,0.6));
                border: 1px solid rgba(255,255,255,0.4);
                padding: 15px 25px;
                margin-right: 3px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-weight: 600;
                color: #333333;
                font-size: 14px;
                backdrop-filter: blur(5px);
            }
            
            #configTabs QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.9));
                color: #1a1a1a;
                border-bottom-color: transparent;
                font-weight: 700;
            }
            
            #configTabs QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(233,236,239,0.9), stop:1 rgba(248,249,250,0.8));
                color: #1a1a1a;
            }
            
            /* 按钮样式 - 更精致的渐变和阴影 */
            #modernButton_primary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                padding: 0 25px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 12px;
            }
            
            #modernButton_primary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:0.5 #6a4190, stop:1 #e082e9);
                transform: translateY(-2px);
            }
            
            #modernButton_primary:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4e5bc6, stop:0.5 #5e377e, stop:1 #d071d7);
                transform: translateY(0px);
            }
            
            #modernButton_secondary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:0.5 #0984e3, stop:1 #00b894);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                padding: 0 25px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 12px;
            }
            
            #modernButton_secondary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #68a9ef, stop:0.5 #0770c1, stop:1 #00a085);
                transform: translateY(-2px);
            }
            
            #modernButton_danger {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fd79a8, stop:0.5 #e84393, stop:1 #ff6b6b);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                padding: 0 25px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 12px;
            }
            
            #modernButton_danger:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fc6996, stop:0.5 #d63384, stop:1 #ff5252);
                transform: translateY(-2px);
            }
            
            #modernButton_info {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a29bfe, stop:0.5 #6c5ce7, stop:1 #fd79a8);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 600;
                padding: 0 25px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 12px;
            }
            
            #modernButton_info:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9589fc, stop:0.5 #5f52d5, stop:1 #fc6996);
                transform: translateY(-2px);
            }
            
            /* 按钮组样式 */
            #buttonGroup {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.1), stop:1 rgba(255,255,255,0.05));
                border-top: 1px solid rgba(255,255,255,0.2);
                border-radius: 0 0 15px 15px;
                padding: 15px 0 5px 0;
                backdrop-filter: blur(5px);
            }
            
            /* 标签页内容样式 */
            #proxyTab, #fingerprintTab {
                background: transparent;
                border-radius: 15px;
            }
            
            /* 标签文本样式 */
            QLabel {
                color: #1a1a1a;
                font-weight: 500;
                font-size: 13px;
            }
            
            /* 输入框样式 */
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.9);
                border: 2px solid rgba(200,200,200,0.5);
                border-radius: 8px;
                padding: 8px 12px;
                color: #1a1a1a;
                font-size: 13px;
                font-weight: 500;
            }
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.95);
            }
            
            /* 复选框样式 */
            QCheckBox {
                color: #1a1a1a;
                font-size: 13px;
                font-weight: 500;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #667eea;
                border-radius: 4px;
                background: rgba(255,255,255,0.9);
            }
            
            QCheckBox::indicator:checked {
                background: #667eea;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            /* 滚动条美化 */
            QScrollBar:vertical {
                background: rgba(255,255,255,0.1);
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6a4190);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
    
    def filter_users(self):
        """过滤用户列表"""
        search_text = self.search_edit.text().lower()
        for row in range(self.user_table.rowCount()):
            should_show = False
            for col in range(self.user_table.columnCount()):
                item = self.user_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.user_table.setRowHidden(row, not should_show)
    
    def load_users(self):
        """加载用户列表"""
        try:
            users = user_service.get_all_users()
            self.current_user = user_service.get_current_user()
            
            self.user_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.user_table.setItem(row, 0, QTableWidgetItem(user.username))
                self.user_table.setItem(row, 1, QTableWidgetItem(user.display_name or ""))
                self.user_table.setItem(row, 2, QTableWidgetItem(user.phone))
                
                status = "🟢 当前用户" if user.is_current else ("🔵 已登录" if user.is_logged_in else "⚪ 未登录")
                self.user_table.setItem(row, 3, QTableWidgetItem(status))
                
                # 存储用户ID
                self.user_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, user.id)
            
            # 调整列宽
            self.user_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载用户列表失败: {str(e)}")
    
    def on_user_selected(self):
        """用户选择事件处理"""
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            user_id = self.user_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            if user_id:
                # 获取用户信息
                user = user_service.get_user_by_id(user_id)
                if user:
                    self.current_user = user
                    
                    # 启用操作按钮
                    self.switch_user_btn.setEnabled(True)
                    self.edit_user_btn.setEnabled(True)
                    self.delete_user_btn.setEnabled(True)
                    
                    # 更新用户信息卡片
                    self.current_user_name.setText(user.display_name or user.username)
                    self.current_user_phone.setText(user.phone or "未设置")
                    
                    # 更新状态显示
                    if hasattr(user, 'is_current') and user.is_current:
                        self.current_user_status.setText("🟢 当前用户")
                    elif hasattr(user, 'is_logged_in') and user.is_logged_in:
                        self.current_user_status.setText("🔵 已登录")
                    else:
                        self.current_user_status.setText("⚪ 离线")
                    
                    # 加载用户配置
                    self.load_user_configs(user_id)
        else:
            # 重置用户信息
            self.current_user = None
            self.switch_user_btn.setEnabled(False)
            self.edit_user_btn.setEnabled(False)
            self.delete_user_btn.setEnabled(False)
            
            # 重置用户信息卡片
            self.current_user_name.setText("请选择用户")
            self.current_user_phone.setText("未选择")
            self.current_user_status.setText("🔴 离线")
    
    def load_user_configs(self, user_id):
        """加载用户配置"""
        self.load_proxy_configs(user_id)
        self.load_fingerprint_configs(user_id)
    
    def load_proxy_configs(self, user_id):
        """加载代理配置"""
        try:
            proxies = proxy_service.get_user_proxy_configs(user_id)
            self.proxy_table.setRowCount(len(proxies))
            
            for row, proxy in enumerate(proxies):
                self.proxy_table.setItem(row, 0, QTableWidgetItem(proxy.name))
                self.proxy_table.setItem(row, 1, QTableWidgetItem(proxy.proxy_type.upper()))
                self.proxy_table.setItem(row, 2, QTableWidgetItem(proxy.host))
                self.proxy_table.setItem(row, 3, QTableWidgetItem(str(proxy.port)))
                
                status = "⭐ 默认" if proxy.is_default else ("🟢 可用" if proxy.is_active else "🔴 禁用")
                self.proxy_table.setItem(row, 4, QTableWidgetItem(status))
                
                latency = f"{proxy.test_latency}ms" if proxy.test_latency else "未测试"
                self.proxy_table.setItem(row, 5, QTableWidgetItem(latency))
                
                # 存储代理ID
                self.proxy_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, proxy.id)
            
            self.proxy_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载代理配置失败: {str(e)}")
    
    def load_fingerprint_configs(self, user_id):
        """加载浏览器指纹配置"""
        try:
            fingerprints = fingerprint_service.get_user_fingerprints(user_id)
            self.fingerprint_table.setRowCount(len(fingerprints))
            
            for row, fingerprint in enumerate(fingerprints):
                self.fingerprint_table.setItem(row, 0, QTableWidgetItem(fingerprint.name))
                self.fingerprint_table.setItem(row, 1, QTableWidgetItem(fingerprint.platform or ""))
                
                resolution = f"{fingerprint.viewport_width}x{fingerprint.viewport_height}"
                self.fingerprint_table.setItem(row, 2, QTableWidgetItem(resolution))
                
                ua_short = fingerprint.user_agent[:50] + "..." if fingerprint.user_agent and len(fingerprint.user_agent) > 50 else (fingerprint.user_agent or "")
                self.fingerprint_table.setItem(row, 3, QTableWidgetItem(ua_short))
                
                status = "⭐ 默认" if fingerprint.is_default else ("🟢 可用" if fingerprint.is_active else "🔴 禁用")
                self.fingerprint_table.setItem(row, 4, QTableWidgetItem(status))
                
                # 存储指纹ID
                self.fingerprint_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, fingerprint.id)
            
            self.fingerprint_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载浏览器指纹配置失败: {str(e)}")
    
    def add_user(self):
        """添加用户"""
        dialog = UserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                user_data = dialog.get_user_data()
                user_service.create_user(**user_data)
                self.load_users()
                QMessageBox.information(self, "成功", "用户创建成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建用户失败: {str(e)}")
    
    def switch_user(self):
        """切换用户"""
        current_row = self.user_table.currentRow()
        if current_row >= 0:
            user_id = self.user_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            username = self.user_table.item(current_row, 0).text()
            
            reply = QMessageBox.question(
                self, "确认切换", 
                f"确定要切换到用户 '{username}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    user_service.switch_user(user_id)
                    self.user_switched.emit(user_id)
                    self.load_users()
                    QMessageBox.information(self, "成功", f"已切换到用户 '{username}'")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"切换用户失败: {str(e)}")
    
    def delete_user(self):
        """删除用户"""
        current_row = self.user_table.currentRow()
        if current_row >= 0:
            user_id = self.user_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            username = self.user_table.item(current_row, 0).text()
            
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除用户 '{username}' 吗？\n这将删除该用户的所有配置信息。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    user_service.delete_user(user_id)
                    self.load_users()
                    QMessageBox.information(self, "成功", f"用户 '{username}' 已删除")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"删除用户失败: {str(e)}")
    
    def add_proxy(self):
        """添加代理配置"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        user_id = self.user_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = ProxyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                proxy_data = dialog.get_proxy_data()
                proxy_service.create_proxy_config(user_id, **proxy_data)
                self.load_proxy_configs(user_id)
                QMessageBox.information(self, "成功", "代理配置创建成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建代理配置失败: {str(e)}")
    
    def test_proxy(self):
        """测试代理"""
        current_row = self.proxy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择代理配置")
            return
        
        proxy_id = self.proxy_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        proxy_name = self.proxy_table.item(current_row, 0).text()
        
        # 显示测试进度对话框
        progress = QProgressDialog("正在测试代理连接...", "取消", 0, 0, self)
        progress.setWindowTitle("代理测试")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            # 创建异步任务来测试代理
            import asyncio
            import threading
            
            def run_test():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(proxy_service.test_proxy_config(proxy_id, timeout=10))
                    loop.close()
                    return result
                except Exception as e:
                    return {'test_result': False, 'error_message': str(e)}
            
            # 在线程中运行测试
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_test)
                
                # 等待测试完成，同时处理UI事件
                while not future.done():
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        future.cancel()
                        return
                    import time
                    time.sleep(0.1)
                
                result = future.result()
            
            progress.close()
            
            # 显示测试结果
            if result['test_result']:
                latency = result.get('latency', 0)
                QMessageBox.information(
                    self, "测试成功", 
                    f"代理 '{proxy_name}' 连接正常！\n延迟: {latency}ms"
                )
            else:
                error_msg = result.get('error_message', '未知错误')
                QMessageBox.warning(
                    self, "测试失败", 
                    f"代理 '{proxy_name}' 连接失败！\n错误: {error_msg}"
                )
            
            # 重新加载代理配置以更新测试结果
            user_row = self.user_table.currentRow()
            if user_row >= 0:
                user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
                self.load_proxy_configs(user_id)
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "错误", f"测试代理时发生错误: {str(e)}")
    
    def set_default_proxy(self):
        """设置默认代理"""
        current_row = self.proxy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择代理配置")
            return
        
        user_row = self.user_table.currentRow()
        if user_row < 0:
            return
        
        user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
        proxy_id = self.proxy_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        try:
            proxy_service.set_default_proxy_config(user_id, proxy_id)
            self.load_proxy_configs(user_id)
            QMessageBox.information(self, "成功", "默认代理配置已设置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置默认代理失败: {str(e)}")
    
    def edit_proxy(self):
        """编辑代理配置"""
        current_row = self.proxy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择代理配置")
            return
        
        proxy_id = self.proxy_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        # 获取现有代理配置
        proxy_config = proxy_service.get_proxy_config_by_id(proxy_id)
        if not proxy_config:
            QMessageBox.critical(self, "错误", "代理配置不存在")
            return
        
        dialog = ProxyDialog(self)
        dialog.setWindowTitle("编辑代理配置")
        
        # 填充现有数据
        dialog.name_edit.setText(proxy_config.name)
        dialog.type_combo.setCurrentText(proxy_config.proxy_type)
        dialog.host_edit.setText(proxy_config.host)
        dialog.port_spin.setValue(proxy_config.port)
        if proxy_config.username:
            dialog.username_edit.setText(proxy_config.username)
        if proxy_config.password:
            dialog.password_edit.setText(proxy_config.password)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                proxy_data = dialog.get_proxy_data()
                proxy_service.update_proxy_config(proxy_id, **proxy_data)
                
                user_row = self.user_table.currentRow()
                if user_row >= 0:
                    user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
                    self.load_proxy_configs(user_id)
                
                QMessageBox.information(self, "成功", "代理配置已更新")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新代理配置失败: {str(e)}")
    
    def delete_proxy(self):
        """删除代理配置"""
        current_row = self.proxy_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择代理配置")
            return
        
        proxy_id = self.proxy_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        proxy_name = self.proxy_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除代理配置 '{proxy_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                proxy_service.delete_proxy_config(proxy_id)
                user_row = self.user_table.currentRow()
                if user_row >= 0:
                    user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
                    self.load_proxy_configs(user_id)
                QMessageBox.information(self, "成功", f"代理配置 '{proxy_name}' 已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除代理配置失败: {str(e)}")
    
    def add_fingerprint(self):
        """添加浏览器指纹"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        user_id = self.user_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = FingerprintDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                fingerprint_data = dialog.get_fingerprint_data()
                fingerprint_service.create_fingerprint(user_id, **fingerprint_data)
                self.load_fingerprint_configs(user_id)
                QMessageBox.information(self, "成功", "浏览器指纹配置创建成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建浏览器指纹配置失败: {str(e)}")
    
    def generate_random_fingerprint(self):
        """生成随机浏览器指纹"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        user_id = self.user_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        try:
            import time
            name = f"随机指纹_{int(time.time())}"
            fingerprint_service.generate_random_fingerprint(user_id, name)
            self.load_fingerprint_configs(user_id)
            QMessageBox.information(self, "成功", "随机浏览器指纹已生成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成随机指纹失败: {str(e)}")
    
    def create_preset_fingerprints(self):
        """创建预设浏览器指纹"""
        current_row = self.user_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择用户")
            return
        
        user_id = self.user_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        try:
            created_fingerprints = fingerprint_service.create_preset_fingerprints(user_id)
            self.load_fingerprint_configs(user_id)
            QMessageBox.information(self, "成功", f"已创建 {len(created_fingerprints)} 个预设指纹配置！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建预设指纹失败: {str(e)}")
    
    def set_default_fingerprint(self):
        """设置默认浏览器指纹"""
        current_row = self.fingerprint_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择浏览器指纹配置")
            return
        
        user_row = self.user_table.currentRow()
        if user_row < 0:
            return
        
        user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
        fingerprint_id = self.fingerprint_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        try:
            fingerprint_service.set_default_fingerprint(user_id, fingerprint_id)
            self.load_fingerprint_configs(user_id)
            QMessageBox.information(self, "成功", "默认浏览器指纹配置已设置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置默认浏览器指纹失败: {str(e)}")
    
    def edit_fingerprint(self):
        """编辑浏览器指纹"""
        current_row = self.fingerprint_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择浏览器指纹配置")
            return
        
        fingerprint_id = self.fingerprint_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        # 获取现有浏览器指纹配置
        fingerprint_config = fingerprint_service.get_fingerprint_by_id(fingerprint_id)
        if not fingerprint_config:
            QMessageBox.critical(self, "错误", "浏览器指纹配置不存在")
            return
        
        dialog = FingerprintDialog(self)
        dialog.setWindowTitle("编辑浏览器指纹")
        
        # 填充现有数据
        dialog.name_edit.setText(fingerprint_config.name)
        if fingerprint_config.user_agent:
            dialog.user_agent_edit.setPlainText(fingerprint_config.user_agent)
        dialog.viewport_width_spin.setValue(fingerprint_config.viewport_width)
        dialog.viewport_height_spin.setValue(fingerprint_config.viewport_height)
        if fingerprint_config.platform:
            dialog.platform_combo.setCurrentText(fingerprint_config.platform)
        if fingerprint_config.timezone:
            dialog.timezone_edit.setText(fingerprint_config.timezone)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                fingerprint_data = dialog.get_fingerprint_data()
                fingerprint_service.update_fingerprint(fingerprint_id, **fingerprint_data)
                
                user_row = self.user_table.currentRow()
                if user_row >= 0:
                    user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
                    self.load_fingerprint_configs(user_id)
                
                QMessageBox.information(self, "成功", "浏览器指纹配置已更新")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新浏览器指纹配置失败: {str(e)}")
    
    def delete_fingerprint(self):
        """删除浏览器指纹"""
        current_row = self.fingerprint_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择浏览器指纹配置")
            return
        
        fingerprint_id = self.fingerprint_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        fingerprint_name = self.fingerprint_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除浏览器指纹配置 '{fingerprint_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                fingerprint_service.delete_fingerprint(fingerprint_id)
                user_row = self.user_table.currentRow()
                if user_row >= 0:
                    user_id = self.user_table.item(user_row, 0).data(Qt.ItemDataRole.UserRole)
                    self.load_fingerprint_configs(user_id)
                QMessageBox.information(self, "成功", f"浏览器指纹配置 '{fingerprint_name}' 已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除浏览器指纹配置失败: {str(e)}")
    
    def edit_user(self):
        """编辑用户"""
        if not self.current_user:
            QMessageBox.warning(self, "警告", "请先选择要编辑的用户")
            return
            
        dialog = UserDialog(self)
        dialog.setWindowTitle("编辑用户")
        
        # 填充现有数据
        dialog.username_edit.setText(self.current_user.username)
        dialog.phone_edit.setText(self.current_user.phone or "")
        dialog.display_name_edit.setText(self.current_user.display_name or "")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_user_data()
            
            try:
                user_service.update_user(self.current_user.id, user_data)
                QMessageBox.information(self, "成功", "用户信息已更新")
                self.load_users()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新用户失败: {str(e)}")


class UserDialog(QDialog):
    """用户添加/编辑对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加用户")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.init_ui()
        self.apply_dialog_styles()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 对话框标题
        title_label = QLabel("👤 用户信息")
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 表单容器
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 用户名输入
        self.username_edit = QLineEdit()
        self.username_edit.setObjectName("dialogInput")
        self.username_edit.setPlaceholderText("请输入用户名")
        form_layout.addRow("用户名:", self.username_edit)
        
        # 手机号输入
        self.phone_edit = QLineEdit()
        self.phone_edit.setObjectName("dialogInput")
        self.phone_edit.setPlaceholderText("请输入手机号")
        form_layout.addRow("手机号:", self.phone_edit)
        
        # 显示名称输入
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setObjectName("dialogInput")
        self.display_name_edit.setPlaceholderText("请输入显示名称（可选）")
        form_layout.addRow("显示名称:", self.display_name_edit)
        
        layout.addWidget(form_container)
        layout.addStretch()
        
        # 按钮容器
        button_container = QFrame()
        button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("dialogOkButton")
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        layout.addWidget(button_container)
    
    def apply_dialog_styles(self):
        """应用对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102,126,234,0.95), stop:0.5 rgba(118,75,162,0.9), stop:1 rgba(240,147,251,0.95));
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                backdrop-filter: blur(20px);
            }
            
            #dialogTitle {
                color: white;
                padding: 15px;
                font-weight: 700;
                text-shadow: 0 2px 8px rgba(0,0,0,0.3);
                font-size: 16px;
            }
            
            #formContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.9));
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 15px;
                padding: 25px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            
            QLabel {
                color: #2c3e50;
                font-weight: 600;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }
            
            #dialogInput {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogInput:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1), 0 4px 20px rgba(102,126,234,0.15);
            }
            
            #dialogCombo {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogCombo:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #dialogCombo::drop-down {
                border: none;
                background: transparent;
                width: 30px;
            }
            
            #dialogCombo::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #667eea;
                margin-right: 15px;
            }
            
            #dialogCombo QAbstractItemView {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(102,126,234,0.3);
                border-radius: 8px;
                selection-background-color: rgba(102,126,234,0.2);
                backdrop-filter: blur(10px);
            }
            
            #dialogSpin {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogSpin:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #dialogTextEdit {
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                padding: 12px;
                backdrop-filter: blur(5px);
            }
            
            #dialogTextEdit:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #buttonContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.1), stop:1 rgba(255,255,255,0.05));
                border-radius: 12px;
                padding: 15px 0;
                backdrop-filter: blur(5px);
            }
            
            #dialogOkButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 700;
                padding: 15px 35px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                box-shadow: 0 4px 15px rgba(102,126,234,0.4);
            }
            
            #dialogOkButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:0.5 #6a4190, stop:1 #e082e9);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102,126,234,0.5);
            }
            
            #dialogOkButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(102,126,234,0.3);
            }
            
            #dialogCancelButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 700;
                padding: 15px 35px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                box-shadow: 0 4px 15px rgba(116,185,255,0.4);
            }
            
            #dialogCancelButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #68a9ef, stop:1 #0770c1);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(116,185,255,0.5);
            }
            
            #dialogCancelButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(116,185,255,0.3);
            }
        """)
    
    def get_user_data(self):
        return {
            'username': self.username_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'display_name': self.display_name_edit.text().strip() or None
        }


class ProxyDialog(QDialog):
    """代理配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("代理配置")
        self.setModal(True)
        self.setFixedSize(450, 400)
        self.init_ui()
        self.apply_dialog_styles()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 对话框标题
        title_label = QLabel("🌐 代理服务器配置")
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 表单容器
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 配置名称
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("dialogInput")
        self.name_edit.setPlaceholderText("请输入配置名称")
        form_layout.addRow("配置名称:", self.name_edit)
        
        # 代理类型
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("dialogCombo")
        self.type_combo.addItems(['http', 'https', 'socks5'])
        form_layout.addRow("代理类型:", self.type_combo)
        
        # 主机地址
        self.host_edit = QLineEdit()
        self.host_edit.setObjectName("dialogInput")
        self.host_edit.setPlaceholderText("请输入主机地址")
        form_layout.addRow("主机地址:", self.host_edit)
        
        # 端口
        self.port_spin = QSpinBox()
        self.port_spin.setObjectName("dialogSpin")
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(8080)
        form_layout.addRow("端口:", self.port_spin)
        
        # 用户名
        self.username_edit = QLineEdit()
        self.username_edit.setObjectName("dialogInput")
        self.username_edit.setPlaceholderText("用户名（可选）")
        form_layout.addRow("用户名:", self.username_edit)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName("dialogInput")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("密码（可选）")
        form_layout.addRow("密码:", self.password_edit)
        
        layout.addWidget(form_container)
        layout.addStretch()
        
        # 按钮容器
        button_container = QFrame()
        button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("dialogOkButton")
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        layout.addWidget(button_container)
    
    def apply_dialog_styles(self):
        """应用对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102,126,234,0.95), stop:0.5 rgba(118,75,162,0.9), stop:1 rgba(240,147,251,0.95));
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                backdrop-filter: blur(20px);
            }
            
            #dialogTitle {
                color: white;
                padding: 15px;
                font-weight: 700;
                text-shadow: 0 2px 8px rgba(0,0,0,0.3);
                font-size: 16px;
            }
            
            #formContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.9));
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 15px;
                padding: 25px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            
            QLabel {
                color: #2c3e50;
                font-weight: 600;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }
            
            #dialogInput {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogInput:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1), 0 4px 20px rgba(102,126,234,0.15);
            }
            
            #dialogCombo {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogCombo:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #dialogCombo::drop-down {
                border: none;
                background: transparent;
                width: 30px;
            }
            
            #dialogCombo::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #667eea;
                margin-right: 15px;
            }
            
            #dialogCombo QAbstractItemView {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(102,126,234,0.3);
                border-radius: 8px;
                selection-background-color: rgba(102,126,234,0.2);
                backdrop-filter: blur(10px);
            }
            
            #dialogSpin {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogSpin:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #dialogTextEdit {
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                padding: 12px;
                backdrop-filter: blur(5px);
            }
            
            #dialogTextEdit:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #buttonContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.1), stop:1 rgba(255,255,255,0.05));
                border-radius: 12px;
                padding: 15px 0;
                backdrop-filter: blur(5px);
            }
            
            #dialogOkButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 700;
                padding: 15px 35px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                box-shadow: 0 4px 15px rgba(102,126,234,0.4);
            }
            
            #dialogOkButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:0.5 #6a4190, stop:1 #e082e9);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102,126,234,0.5);
            }
            
            #dialogOkButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(102,126,234,0.3);
            }
            
            #dialogCancelButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 700;
                padding: 15px 35px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                box-shadow: 0 4px 15px rgba(116,185,255,0.4);
            }
            
            #dialogCancelButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #68a9ef, stop:1 #0770c1);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(116,185,255,0.5);
            }
            
            #dialogCancelButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(116,185,255,0.3);
            }
        """)
    
    def get_proxy_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'proxy_type': self.type_combo.currentText(),
            'host': self.host_edit.text().strip(),
            'port': self.port_spin.value(),
            'username': self.username_edit.text().strip() or None,
            'password': self.password_edit.text().strip() or None
        }


class FingerprintDialog(QDialog):
    """浏览器指纹配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("浏览器指纹配置")
        self.setModal(True)
        self.setFixedSize(500, 500)
        self.init_ui()
        self.apply_dialog_styles()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 对话框标题
        title_label = QLabel("🔍 浏览器指纹配置")
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 表单容器
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 配置名称
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("dialogInput")
        self.name_edit.setPlaceholderText("请输入配置名称")
        form_layout.addRow("配置名称:", self.name_edit)
        
        # User-Agent
        self.user_agent_edit = QTextEdit()
        self.user_agent_edit.setObjectName("dialogTextEdit")
        self.user_agent_edit.setMaximumHeight(80)
        self.user_agent_edit.setPlaceholderText("请输入User-Agent字符串")
        form_layout.addRow("User-Agent:", self.user_agent_edit)
        
        # 视窗宽度
        self.viewport_width_spin = QSpinBox()
        self.viewport_width_spin.setObjectName("dialogSpin")
        self.viewport_width_spin.setRange(800, 3840)
        self.viewport_width_spin.setValue(1920)
        form_layout.addRow("视窗宽度:", self.viewport_width_spin)
        
        # 视窗高度
        self.viewport_height_spin = QSpinBox()
        self.viewport_height_spin.setObjectName("dialogSpin")
        self.viewport_height_spin.setRange(600, 2160)
        self.viewport_height_spin.setValue(1080)
        form_layout.addRow("视窗高度:", self.viewport_height_spin)
        
        # 平台
        self.platform_combo = QComboBox()
        self.platform_combo.setObjectName("dialogCombo")
        self.platform_combo.addItems(['Win32', 'MacIntel', 'Linux x86_64'])
        form_layout.addRow("平台:", self.platform_combo)
        
        # 时区
        self.timezone_edit = QLineEdit()
        self.timezone_edit.setObjectName("dialogInput")
        self.timezone_edit.setText('Asia/Shanghai')
        self.timezone_edit.setPlaceholderText("请输入时区")
        form_layout.addRow("时区:", self.timezone_edit)
        
        layout.addWidget(form_container)
        layout.addStretch()
        
        # 按钮容器
        button_container = QFrame()
        button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("dialogOkButton")
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        layout.addWidget(button_container)
    
    def apply_dialog_styles(self):
        """应用对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102,126,234,0.95), stop:0.5 rgba(118,75,162,0.9), stop:1 rgba(240,147,251,0.95));
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                backdrop-filter: blur(20px);
            }
            
            #dialogTitle {
                color: white;
                padding: 15px;
                font-weight: 700;
                text-shadow: 0 2px 8px rgba(0,0,0,0.3);
                font-size: 16px;
            }
            
            #formContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.9));
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 15px;
                padding: 25px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            
            QLabel {
                color: #2c3e50;
                font-weight: 600;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }
            
            #dialogInput {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogInput:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1), 0 4px 20px rgba(102,126,234,0.15);
            }
            
            #dialogCombo {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogCombo:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #dialogCombo::drop-down {
                border: none;
                background: transparent;
                width: 30px;
            }
            
            #dialogCombo::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #667eea;
                margin-right: 15px;
            }
            
            #dialogCombo QAbstractItemView {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(102,126,234,0.3);
                border-radius: 8px;
                selection-background-color: rgba(102,126,234,0.2);
                backdrop-filter: blur(10px);
            }
            
            #dialogSpin {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogSpin:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #dialogTextEdit {
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #495057;
                font-weight: 500;
                padding: 12px;
                backdrop-filter: blur(5px);
            }
            
            #dialogTextEdit:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.98);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }
            
            #buttonContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.1), stop:1 rgba(255,255,255,0.05));
                border-radius: 12px;
                padding: 15px 0;
                backdrop-filter: blur(5px);
            }
            
            #dialogOkButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 700;
                padding: 15px 35px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                box-shadow: 0 4px 15px rgba(102,126,234,0.4);
            }
            
            #dialogOkButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:0.5 #6a4190, stop:1 #e082e9);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102,126,234,0.5);
            }
            
            #dialogOkButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(102,126,234,0.3);
            }
            
            #dialogCancelButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff, stop:1 #0984e3);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: 700;
                padding: 15px 35px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                box-shadow: 0 4px 15px rgba(116,185,255,0.4);
            }
            
            #dialogCancelButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #68a9ef, stop:1 #0770c1);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(116,185,255,0.5);
            }
            
            #dialogCancelButton:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(116,185,255,0.3);
            }
        """)
    
    def get_fingerprint_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'user_agent': self.user_agent_edit.toPlainText().strip() or None,
            'viewport_width': self.viewport_width_spin.value(),
            'viewport_height': self.viewport_height_spin.value(),
            'platform': self.platform_combo.currentText(),
            'timezone': self.timezone_edit.text().strip(),
            'locale': 'zh-CN'
        } 