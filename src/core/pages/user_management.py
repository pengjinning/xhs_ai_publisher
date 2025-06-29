import sys
import os
# 添加项目根目录到Python路径，解决相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# PyQt6 核心模块导入
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

# 使用绝对导入
try:
    from src.core.services.user_service import user_service
    from src.core.services.proxy_service import proxy_service
    from src.core.services.fingerprint_service import fingerprint_service
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    try:
        from ..services.user_service import user_service
        from ..services.proxy_service import proxy_service
        from ..services.fingerprint_service import fingerprint_service
    except ImportError:
        # 如果相对导入也失败，创建模拟服务
        print("警告: 无法导入服务模块，使用模拟数据")
        
        class MockService:
            def get_all_users(self):
                return []
            def get_user_by_id(self, user_id):
                return None
            def create_user(self, data):
                return True
            def update_user(self, user_id, data):
                return True
            def delete_user(self, user_id):
                return True
            def get_user_proxies(self, user_id):
                return []
            def get_user_fingerprints(self, user_id):
                return []
            def create_proxy(self, data):
                return True
            def create_fingerprint(self, data):
                return True
            def test_proxy(self, proxy_data):
                return True
            def update_proxy(self, proxy_id, data):
                return True
            def update_fingerprint(self, fp_id, data):
                return True
            def delete_proxy(self, proxy_id):
                return True
            def delete_fingerprint(self, fp_id):
                return True
        
        user_service = MockService()
        proxy_service = MockService()
        fingerprint_service = MockService()


class UserManagementPage(QWidget):
    """用户管理页面"""
    
    user_switched = pyqtSignal(int)  # 用户切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_user = None
        self.selected_proxy = None
        self.selected_fingerprint = None
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
        """
        创建代理配置标签页
        
        包含：
        - 标题和操作按钮（添加代理、测试代理）
        - 代理列表表格（显示名称、类型、地址、端口、状态、延迟）
        - 操作按钮组（设为默认、编辑、删除）
        
        Returns:
            QFrame: 代理配置标签页组件
        """
        widget = QFrame()
        widget.setObjectName("proxyTab")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题和操作按钮区域
        header_layout = QHBoxLayout()
        
        # 代理配置标题
        proxy_title = QLabel("🌐 代理服务器配置")
        proxy_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(proxy_title)
        header_layout.addStretch()
        
        # 操作按钮区域
        # 添加代理按钮
        self.add_proxy_btn = self.create_modern_button("➕ 添加", "primary", small=True)
        self.add_proxy_btn.clicked.connect(self.add_proxy)
        self.add_proxy_btn.setEnabled(False)
        header_layout.addWidget(self.add_proxy_btn)
        
        # 测试代理按钮
        self.test_proxy_btn = self.create_modern_button("🧪 测试", "secondary", small=True)
        self.test_proxy_btn.clicked.connect(self.test_proxy)
        self.test_proxy_btn.setEnabled(False)
        header_layout.addWidget(self.test_proxy_btn)
        
        layout.addLayout(header_layout)
        
        # 代理列表表格
        self.proxy_table = QTableWidget()
        self.proxy_table.setObjectName("proxyTable")
        self.proxy_table.setColumnCount(6)  # 6列：名称、类型、地址、端口、状态、延迟
        self.proxy_table.setHorizontalHeaderLabels(["名称", "类型", "地址", "端口", "状态", "延迟"])
        self.proxy_table.horizontalHeader().setStretchLastSection(True)  # 最后一列自动拉伸
        self.proxy_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # 整行选择
        self.proxy_table.setAlternatingRowColors(True)  # 交替行颜色
        self.proxy_table.verticalHeader().setVisible(False)  # 隐藏行号
        self.proxy_table.itemSelectionChanged.connect(self.on_proxy_selected)
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
        """
        创建浏览器指纹标签页
        
        包含：
        - 标题和操作按钮（添加指纹、随机生成、预设）
        - 浏览器指纹列表表格（显示名称、平台、分辨率、User-Agent、状态）
        - 操作按钮组（设为默认、编辑、删除）
        
        Returns:
            QFrame: 浏览器指纹标签页组件
        """
        widget = QFrame()
        widget.setObjectName("fingerprintTab")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 标题和操作按钮区域
        header_layout = QHBoxLayout()
        
        # 浏览器指纹标题
        fingerprint_title = QLabel("🔍 浏览器指纹配置")
        fingerprint_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        header_layout.addWidget(fingerprint_title)
        header_layout.addStretch()
        
        # 操作按钮区域
        # 添加指纹按钮
        self.add_fingerprint_btn = self.create_modern_button("➕ 添加", "primary", small=True)
        self.add_fingerprint_btn.clicked.connect(self.add_fingerprint)
        self.add_fingerprint_btn.setEnabled(False)
        header_layout.addWidget(self.add_fingerprint_btn)
        
        # 随机生成指纹按钮
        self.generate_random_btn = self.create_modern_button("🎲 随机生成", "secondary", small=True)
        self.generate_random_btn.clicked.connect(self.generate_random_fingerprint)
        self.generate_random_btn.setEnabled(False)
        header_layout.addWidget(self.generate_random_btn)
        
        # 创建预设指纹按钮
        self.create_presets_btn = self.create_modern_button("📋 预设", "info", small=True)
        self.create_presets_btn.clicked.connect(self.create_preset_fingerprints)
        self.create_presets_btn.setEnabled(False)
        header_layout.addWidget(self.create_presets_btn)
        
        layout.addLayout(header_layout)
        
        # 浏览器指纹列表表格
        self.fingerprint_table = QTableWidget()
        self.fingerprint_table.setObjectName("fingerprintTable")
        self.fingerprint_table.setColumnCount(5)  # 5列：名称、平台、分辨率、User-Agent、状态
        self.fingerprint_table.setHorizontalHeaderLabels(["名称", "平台", "分辨率", "User-Agent", "状态"])
        self.fingerprint_table.horizontalHeader().setStretchLastSection(True)  # 最后一列自动拉伸
        self.fingerprint_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # 整行选择
        self.fingerprint_table.setAlternatingRowColors(True)  # 交替行颜色
        self.fingerprint_table.verticalHeader().setVisible(False)  # 隐藏行号
        self.fingerprint_table.itemSelectionChanged.connect(self.on_fingerprint_selected)
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
        """
        创建现代化样式按钮
        
        Args:
            text (str): 按钮文本
            style_type (str): 按钮样式类型（primary/secondary/danger/info）
            small (bool): 是否为小尺寸按钮
            
        Returns:
            QPushButton: 配置好的按钮组件
        """
        button = QPushButton(text)
        button.setObjectName(f"modernButton_{style_type}")
        
        # 根据尺寸设置按钮高度和字体
        if small:
            button.setFixedHeight(32)
            button.setFont(QFont("Microsoft YaHei", 9))
        else:
            button.setFixedHeight(40)
            button.setFont(QFont("Microsoft YaHei", 10))
        
        # 设置鼠标悬停时的手型光标
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)  # 模糊半径
        shadow.setColor(QColor(0, 0, 0, 60))  # 阴影颜色（黑色，60%透明度）
        shadow.setOffset(0, 2)  # 阴影偏移量
        button.setGraphicsEffect(shadow)
        
        return button
    
    def create_button_group(self, buttons_config):
        """
        创建按钮组
        
        Args:
            buttons_config (list): 按钮配置列表，每个元素为(文本, 方法名, 样式)的元组
            
        Returns:
            QFrame: 包含所有按钮的容器组件
        """
        group = QFrame()
        group.setObjectName("buttonGroup")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        
        # 根据配置创建按钮
        for text, method_name, style in buttons_config:
            button = self.create_modern_button(text, style, small=True)
            button.clicked.connect(getattr(self, method_name))  # 连接到对应的方法
            
            # 对于需要选中项才能操作的按钮，初始状态设为禁用
            if method_name in [
                'switch_user', 'edit_user', 'delete_user',
                'set_default_proxy', 'edit_proxy', 'delete_proxy',
                'set_default_fingerprint', 'edit_fingerprint', 'delete_fingerprint'
            ]:
                button.setEnabled(False)
                setattr(self, f"{method_name}_btn", button)  # 保存按钮引用以便后续启用/禁用
            
            layout.addWidget(button)
        
        layout.addStretch()  # 在按钮组右侧添加弹性空间
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
                color: #1a202c;
                font-weight: 700;
                font-size: 24px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            #pageSubtitle {
                color: #2d3748;
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
                color: #1a202c !important;
                padding: 8px 0;
                font-weight: 700;
                font-size: 18px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            
            /* 用户信息卡片 - 统一风格 */
            #userInfoCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(255,255,255,0.8));
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 18px;
                box-shadow: 0 8px 32px rgba(0,0,0, 0.1);
                backdrop-filter: blur(15px);
            }
            
            #userAvatar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.3), stop:1 rgba(255,255,255,0.1));
                border: 3px solid rgba(255,255,255,0.4);
                border-radius: 30px;
                backdrop-filter: blur(10px);
                color: #4a5568;
            }
            
            #currentUserName {
                color: #1a202c;
                font-weight: 700;
                font-size: 16px;
                text-shadow: none;
            }
            
            #currentUserPhone, #currentUserStatus {
                color: #2d3748;
                font-size: 14px;
                font-weight: 500;
                text-shadow: none;
            }
            
            /* 搜索框样式 - 现代化设计 */
            #searchEdit {
                padding: 15px 20px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 30px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.8));
                font-size: 14px;
                color: #1a202c;
                font-weight: 500;
                backdrop-filter: blur(10px);
            }
            
            #searchEdit:focus {
                border-color: #667eea;
                background: rgba(255,255,255,0.95);
                outline: none;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
                color: #1a202c;
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
                padding: 16px 10px;
                border-bottom: 1px solid rgba(200,200,200,0.3);
                color: #1a202c;
                font-weight: 600;
                font-size: 14px;
            }
            
            #userTable::item:selected, #proxyTable::item:selected, #fingerprintTable::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102,126,234,0.3), stop:1 rgba(118,75,162,0.3));
                color: #1a202c;
                font-weight: 700;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(248,249,250,0.9), stop:1 rgba(233,236,239,0.8));
                padding: 15px 10px;
                border: none;
                border-bottom: 2px solid rgba(102,126,234,0.3);
                font-weight: 700;
                color: #1a202c;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 13px;
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
                color: #2d3748;
                font-size: 14px;
                backdrop-filter: blur(5px);
            }
            
            #configTabs QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.95), stop:1 rgba(255,255,255,0.9));
                color: #1a202c;
                border-bottom-color: transparent;
                font-weight: 700;
            }
            
            #configTabs QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(233,236,239,0.9), stop:1 rgba(248,249,250,0.8));
                color: #1a202c;
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
            
            /* 标签文本样式 - 分别设置不同区域的文字颜色 */
            #userListPanel QLabel, #configPanel QLabel {
                color: #1a202c;
                font-weight: 500;
                font-size: 13px;
            }
            
            /* 头部标题文字 */
            #headerFrame QLabel {
                color: #1a202c;
                font-weight: 600;
            }
            
            /* 表格标题文字 */
            #panelTitle {
                color: #1a202c !important;
                padding: 8px 0;
                font-weight: 700;
                font-size: 18px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            
            /* 标签页标题文字 */
            #proxyTab QLabel, #fingerprintTab QLabel {
                color: #1a202c;
                font-weight: 600;
                font-size: 14px;
            }
            
            /* 更具体的标签页内容文字样式 */
            #proxyTab QLabel:first-child, #fingerprintTab QLabel:first-child {
                color: #1a202c;
                font-weight: 700;
                font-size: 16px;
            }
            
            /* 表单标签文字 */
            QFormLayout QLabel {
                color: #2d3748;
                font-weight: 600;
                font-size: 14px;
            }
            
            /* 输入框样式 */
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.95);
                border: 2px solid rgba(200,200,200,0.5);
                border-radius: 8px;
                padding: 8px 12px;
                color: #1a202c;
                font-size: 14px;
                font-weight: 600;
            }
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #667eea;
                background: rgba(255,255,255,1.0);
                color: #1a202c;
            }
            
            /* 复选框样式 */
            QCheckBox {
                color: #1a202c;
                font-size: 14px;
                font-weight: 600;
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
            
            /* 消息框文字样式 */
            QMessageBox {
                color: #1a202c;
                background: rgba(255,255,255,0.95);
            }
            
            QMessageBox QLabel {
                color: #1a202c;
                font-size: 14px;
                font-weight: 500;
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
        """
        过滤用户列表（搜索功能）
        
        根据搜索框中的文本过滤用户表格中的行：
        - 搜索文本会与用户名、显示名、手机号、状态进行匹配
        - 匹配时忽略大小写
        - 隐藏不匹配的行，显示匹配的行
        """
        search_text = self.search_edit.text().lower()  # 获取搜索文本并转为小写
        
        # 遍历表格的每一行
        for row in range(self.user_table.rowCount()):
            should_show = False  # 标记该行是否应该显示
            
            # 检查该行的每一列是否包含搜索文本
            for col in range(self.user_table.columnCount()):
                item = self.user_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            # 根据匹配结果显示或隐藏行
            self.user_table.setRowHidden(row, not should_show)
    
    def load_users(self, select_user_id=None):
        """
        加载用户列表数据
        
        从用户服务获取所有用户数据并填充到用户表格中：
        - 获取所有用户和当前用户信息
        - 清空并重新填充用户表格
        - 设置用户状态显示（当前用户/已登录/未登录）
        - 调整表格列宽以适应内容
        """
        try:
            # 从服务层获取用户数据
            users = user_service.get_all_users()
            self.current_user = user_service.get_current_user()
            
            # 设置表格行数
            self.user_table.setRowCount(len(users))
            
            # 填充用户数据到表格
            for row, user in enumerate(users):
                # 用户名列
                self.user_table.setItem(row, 0, QTableWidgetItem(user.username))
                # 显示名列
                self.user_table.setItem(row, 1, QTableWidgetItem(user.display_name or ""))
                # 手机号列
                self.user_table.setItem(row, 2, QTableWidgetItem(user.phone))
                
                # 状态列 - 根据用户状态显示不同的图标和文本
                if user.is_current:
                    status = "🟢 当前用户"
                elif user.is_logged_in:
                    status = "🔵 已登录"
                else:
                    status = "⚪ 未登录"
                self.user_table.setItem(row, 3, QTableWidgetItem(status))
                
                # 在第一列存储用户ID，用于后续操作
                self.user_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, user.id)
            
                # 如果有指定的用户ID，选中该行
                if select_user_id and user.id == select_user_id:
                    self.user_table.selectRow(row)
            
            # 自动调整列宽以适应内容
            self.user_table.resizeColumnsToContents()
            
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(self, "错误", f"加载用户列表失败: {str(e)}")
    
    def on_user_selected(self):
        """
        用户选择事件处理
        
        当用户在用户列表中选择一行时触发：
        - 获取选中用户的信息
        - 启用相关操作按钮
        - 更新用户信息卡片显示
        - 加载该用户的配置信息（代理和指纹）
        """
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        if selected_rows:
            # 获取选中行的信息
            row = selected_rows[0].row()
            user_id = self.user_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            if user_id:
                # 从服务层获取完整的用户信息
                user = user_service.get_user_by_id(user_id)
                if user:
                    self.selected_user = user
                    
                    # 启用用户操作按钮
                    self.switch_user_btn.setEnabled(True)
                    self.edit_user_btn.setEnabled(True)
                    self.delete_user_btn.setEnabled(True)
                    
                    # 更新用户信息卡片显示
                    self.current_user_name.setText(user.display_name or user.username)
                    self.current_user_phone.setText(user.phone or "未设置")
                    
                    # 更新用户状态显示
                    if hasattr(user, 'is_current') and user.is_current:
                        self.current_user_status.setText("🟢 当前用户")
                    elif hasattr(user, 'is_logged_in') and user.is_logged_in:
                        self.current_user_status.setText("🔵 已登录")
                    else:
                        self.current_user_status.setText("⚪ 离线")
                    
                    # 加载该用户的配置信息
                    self.load_user_configs(user_id)
        else:
            # 没有选中用户时的处理
            self.selected_user = None
            
            # 禁用用户操作按钮
            self.switch_user_btn.setEnabled(False)
            self.edit_user_btn.setEnabled(False)
            self.delete_user_btn.setEnabled(False)
            
            # 禁用添加配置的按钮
            self.add_proxy_btn.setEnabled(False)
            self.add_fingerprint_btn.setEnabled(False)
            self.generate_random_btn.setEnabled(False)
            self.create_presets_btn.setEnabled(False)

            # 重置用户信息卡片显示
            self.current_user_name.setText("请选择用户")
            self.current_user_phone.setText("未选择")
            self.current_user_status.setText("🔴 离线")
            
            # 清空配置表
            self.proxy_table.setRowCount(0)
            self.fingerprint_table.setRowCount(0)
            self.on_proxy_selected()
            self.on_fingerprint_selected()
    
    def on_proxy_selected(self):
        """代理选择事件处理"""
        selected_rows = self.proxy_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            proxy_id = self.proxy_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.selected_proxy = proxy_service.get_proxy_config_by_id(proxy_id)
            
            # 启用按钮
            self.test_proxy_btn.setEnabled(True)
            self.set_default_proxy_btn.setEnabled(True)
            self.edit_proxy_btn.setEnabled(True)
            self.delete_proxy_btn.setEnabled(True)
        else:
            self.selected_proxy = None
            # 禁用按钮
            self.test_proxy_btn.setEnabled(False)
            self.set_default_proxy_btn.setEnabled(False)
            self.edit_proxy_btn.setEnabled(False)
            self.delete_proxy_btn.setEnabled(False)

    def on_fingerprint_selected(self):
        """指纹选择事件处理"""
        selected_rows = self.fingerprint_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            fp_id = self.fingerprint_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.selected_fingerprint = fingerprint_service.get_fingerprint_by_id(fp_id)

            # 启用按钮
            self.set_default_fingerprint_btn.setEnabled(True)
            self.edit_fingerprint_btn.setEnabled(True)
            self.delete_fingerprint_btn.setEnabled(True)
        else:
            self.selected_fingerprint = None
            # 禁用按钮
            self.set_default_fingerprint_btn.setEnabled(False)
            self.edit_fingerprint_btn.setEnabled(False)
            self.delete_fingerprint_btn.setEnabled(False)
    
    def load_user_configs(self, user_id):
        """
        加载用户配置信息
        
        Args:
            user_id (int): 用户ID
            
        加载指定用户的所有配置信息，包括：
        - 代理服务器配置
        - 浏览器指纹配置
        """
        self.load_proxy_configs(user_id)      # 加载代理配置
        self.load_fingerprint_configs(user_id)  # 加载浏览器指纹配置
    
    def load_proxy_configs(self, user_id, select_proxy_id=None):
        """
        加载代理配置数据
        
        Args:
            user_id (int): 用户ID
            
        从代理服务获取指定用户的代理配置并填充到代理表格中：
        - 显示代理名称、类型、地址、端口、状态、延迟
        - 标记默认代理和可用状态
        - 调整表格列宽
        """
        try:
            # 从服务层获取代理配置数据
            proxies = proxy_service.get_user_proxy_configs(user_id)
            self.proxy_table.setRowCount(len(proxies))
            
            # 填充代理数据到表格
            for row, proxy in enumerate(proxies):
                # 代理名称列
                self.proxy_table.setItem(row, 0, QTableWidgetItem(proxy.name))
                # 代理类型列（转为大写显示）
                self.proxy_table.setItem(row, 1, QTableWidgetItem(proxy.proxy_type.upper()))
                # 主机地址列
                self.proxy_table.setItem(row, 2, QTableWidgetItem(proxy.host))
                # 端口列
                self.proxy_table.setItem(row, 3, QTableWidgetItem(str(proxy.port)))
                
                # 状态列 - 根据代理状态显示不同的图标和文本
                if proxy.is_default:
                    status = "⭐ 默认"
                elif proxy.is_active:
                    status = "🟢 可用"
                else:
                    status = "🔴 禁用"
                self.proxy_table.setItem(row, 4, QTableWidgetItem(status))
                
                # 延迟列 - 显示测试延迟或未测试状态
                latency = f"{proxy.test_latency}ms" if proxy.test_latency else "未测试"
                self.proxy_table.setItem(row, 5, QTableWidgetItem(latency))
                
                # 在第一列存储代理ID，用于后续操作
                self.proxy_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, proxy.id)
            
                if select_proxy_id and proxy.id == select_proxy_id:
                    self.proxy_table.selectRow(row)
            
            # 自动调整列宽以适应内容
            self.proxy_table.resizeColumnsToContents()
            
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(self, "错误", f"加载代理配置失败: {str(e)}")
    
    def load_fingerprint_configs(self, user_id, select_fingerprint_id=None):
        """
        加载浏览器指纹配置数据
        
        Args:
            user_id (int): 用户ID
            
        从指纹服务获取指定用户的浏览器指纹配置并填充到指纹表格中：
        - 显示指纹名称、平台、分辨率、User-Agent、状态
        - 截断过长的User-Agent字符串
        - 标记默认指纹和可用状态
        """
        try:
            # 从服务层获取浏览器指纹数据
            fingerprints = fingerprint_service.get_user_fingerprints(user_id)
            self.fingerprint_table.setRowCount(len(fingerprints))
            
            # 填充指纹数据到表格
            for row, fingerprint in enumerate(fingerprints):
                # 指纹名称列
                self.fingerprint_table.setItem(row, 0, QTableWidgetItem(fingerprint.name))
                # 平台列
                self.fingerprint_table.setItem(row, 1, QTableWidgetItem(fingerprint.platform or ""))
                
                # 分辨率列 - 格式化为 "宽x高"
                resolution = f"{fingerprint.viewport_width}x{fingerprint.viewport_height}"
                self.fingerprint_table.setItem(row, 2, QTableWidgetItem(resolution))
                
                # User-Agent列 - 截断过长的字符串并添加省略号
                if fingerprint.user_agent and len(fingerprint.user_agent) > 50:
                    ua_short = fingerprint.user_agent[:50] + "..."
                else:
                    ua_short = fingerprint.user_agent or ""
                self.fingerprint_table.setItem(row, 3, QTableWidgetItem(ua_short))
                
                # 状态列 - 根据指纹状态显示不同的图标和文本
                if fingerprint.is_default:
                    status = "⭐ 默认"
                elif fingerprint.is_active:
                    status = "🟢 可用"
                else:
                    status = "🔴 禁用"
                self.fingerprint_table.setItem(row, 4, QTableWidgetItem(status))
                
                # 在第一列存储指纹ID，用于后续操作
                self.fingerprint_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, fingerprint.id)
            
                if select_fingerprint_id and fingerprint.id == select_fingerprint_id:
                    self.fingerprint_table.selectRow(row)
            
            # 自动调整列宽以适应内容
            self.fingerprint_table.resizeColumnsToContents()
            
        except Exception as e:
            # 显示错误消息
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
        """
        切换当前系统的活动用户
        
        - 检查是否已选择用户
        - 检查是否重复切换
        - 调用服务层执行切换
        - 刷新用户列表并重新选中刚刚切换的用户
        """
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先从列表中选择要切换的用户。")
            return

        user_id = self.selected_user.id
        username = self.selected_user.username

        if self.selected_user.is_current:
            QMessageBox.information(self, "提示", f"用户 '{username}' 已经是当前系统的活动用户。")
            return
            
        reply = QMessageBox.question(
            self, "确认切换", 
            f"确定要将系统的活动用户切换为 '{username}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                user_service.switch_user(user_id)
                self.user_switched.emit(user_id)  # 发出信号，通知应用其他部分
                self.load_users(select_user_id=user_id)
                QMessageBox.information(self, "成功", f"已成功切换到用户 '{username}'。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换用户失败: {str(e)}")
    
    def delete_user(self):
        """
        删除选中的用户
        
        - 检查是否已选择用户
        - 弹出确认对话框
        - 调用服务层执行删除
        - 刷新用户列表
        """
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先从列表中选择要删除的用户。")
            return
        
        user_id = self.selected_user.id
        username = self.selected_user.username
            
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要永久删除用户 '{username}' 吗？\n这将删除该用户的所有配置信息，此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                user_service.delete_user(user_id)
                self.load_users()  # 刷新列表，此时选择会丢失
                QMessageBox.information(self, "成功", f"用户 '{username}' 已被成功删除。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除用户失败: {str(e)}")
    
    def add_proxy(self):
        """添加代理配置"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择要为其添加代理的用户。")
            return
        
        user_id = self.selected_user.id
        
        dialog = ProxyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                proxy_data = dialog.get_proxy_data()
                # 基本验证
                if not proxy_data['name'] or not proxy_data['host'] or not proxy_data['port']:
                    QMessageBox.warning(self, "输入错误", "配置名称、主机地址和端口是必填项。")
                    return
                
                proxy_service.create_proxy_config(user_id=user_id, **proxy_data)
                self.load_proxy_configs(user_id)
                QMessageBox.information(self, "成功", "代理配置创建成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建代理配置失败: {str(e)}")
    
    def test_proxy(self):
        """测试选定的代理"""
        if not self.selected_proxy:
            QMessageBox.warning(self, "警告", "请先从列表中选择要测试的代理。")
            return
        
        proxy_id = self.selected_proxy.id
        proxy_name = self.selected_proxy.name
        
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
            if self.selected_user:
                self.load_proxy_configs(self.selected_user.id, select_proxy_id=proxy_id)
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "错误", f"测试代理时发生错误: {str(e)}")
    
    def set_default_proxy(self):
        """设置默认代理"""
        if not self.selected_user or not self.selected_proxy:
            QMessageBox.warning(self, "警告", "请先选择一个用户和一个代理配置。")
            return
        
        user_id = self.selected_user.id
        proxy_id = self.selected_proxy.id
        
        try:
            proxy_service.set_default_proxy_config(user_id, proxy_id)
            self.load_proxy_configs(user_id, select_proxy_id=proxy_id)
            QMessageBox.information(self, "成功", "默认代理配置已更新。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置默认代理失败: {str(e)}")
    
    def edit_proxy(self):
        """编辑选定的代理配置"""
        if not self.selected_proxy:
            QMessageBox.warning(self, "警告", "请先选择要编辑的代理配置。")
            return
        
        proxy_id = self.selected_proxy.id
        
        # 获取现有代理配置
        proxy_config = proxy_service.get_proxy_config_by_id(proxy_id)
        if not proxy_config:
            QMessageBox.critical(self, "错误", f"无法找到ID为 {proxy_id} 的代理配置。")
            return
        
        dialog = ProxyDialog(self)
        dialog.setWindowTitle("编辑代理配置")
        
        # 填充现有数据
        dialog.name_edit.setText(proxy_config.name)
        dialog.type_combo.setCurrentText(proxy_config.proxy_type.upper())
        dialog.host_edit.setText(proxy_config.host)
        dialog.port_spin.setValue(proxy_config.port)
        dialog.username_edit.setText(proxy_config.username or "")
        dialog.password_edit.setText(proxy_config.password or "")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                proxy_data = dialog.get_proxy_data()
                # 基本验证
                if not proxy_data['name'] or not proxy_data['host'] or not proxy_data['port']:
                    QMessageBox.warning(self, "输入错误", "配置名称、主机地址和端口是必填项。")
                    return
                    
                proxy_service.update_proxy_config(proxy_id, **proxy_data)
                
                if self.selected_user:
                    self.load_proxy_configs(self.selected_user.id, select_proxy_id=proxy_id)
                
                QMessageBox.information(self, "成功", "代理配置已成功更新。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新代理配置失败: {str(e)}")
    
    def delete_proxy(self):
        """删除选定的代理配置"""
        if not self.selected_proxy:
            QMessageBox.warning(self, "警告", "请先选择要删除的代理配置。")
            return
        
        proxy_id = self.selected_proxy.id
        proxy_name = self.selected_proxy.name
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要永久删除代理配置 '{proxy_name}' 吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                proxy_service.delete_proxy_config(proxy_id)
                if self.selected_user:
                    self.load_proxy_configs(self.selected_user.id)
                QMessageBox.information(self, "成功", f"代理配置 '{proxy_name}' 已被成功删除。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除代理配置失败: {str(e)}")
    
    def add_fingerprint(self):
        """为当前选定的用户添加浏览器指纹"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择要为其添加指纹的用户。")
            return
        
        user_id = self.selected_user.id
        
        dialog = FingerprintDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                fingerprint_data = dialog.get_fingerprint_data()
                # 基本验证
                if not fingerprint_data['name']:
                    QMessageBox.warning(self, "输入错误", "配置名称是必填项。")
                    return

                fingerprint_service.create_fingerprint(user_id=user_id, **fingerprint_data)
                self.load_fingerprint_configs(user_id)
                QMessageBox.information(self, "成功", "浏览器指纹配置创建成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建浏览器指纹配置失败: {str(e)}")
    
    def generate_random_fingerprint(self):
        """为选定的用户生成随机浏览器指纹"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择一个用户以生成随机指纹。")
            return
        
        user_id = self.selected_user.id
        
        try:
            import time
            name = f"随机指纹_{int(time.time())}"
            fingerprint_service.generate_random_fingerprint(user_id, name)
            self.load_fingerprint_configs(user_id)
            QMessageBox.information(self, "成功", "随机浏览器指纹已生成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成随机指纹失败: {str(e)}")
    
    def create_preset_fingerprints(self):
        """为选定的用户创建预设浏览器指纹"""
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先选择一个用户以创建预设指纹。")
            return
        
        user_id = self.selected_user.id
        
        try:
            created_fingerprints = fingerprint_service.create_preset_fingerprints(user_id)
            self.load_fingerprint_configs(user_id)
            QMessageBox.information(self, "成功", f"已创建 {len(created_fingerprints)} 个预设指纹配置！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建预设指纹失败: {str(e)}")
    
    def set_default_fingerprint(self):
        """设置默认浏览器指纹"""
        if not self.selected_user or not self.selected_fingerprint:
            QMessageBox.warning(self, "警告", "请先选择一个用户和一个指纹配置。")
            return
        
        user_id = self.selected_user.id
        fingerprint_id = self.selected_fingerprint.id
        
        try:
            fingerprint_service.set_default_fingerprint(user_id, fingerprint_id)
            self.load_fingerprint_configs(user_id, select_fingerprint_id=fingerprint_id)
            QMessageBox.information(self, "成功", "默认浏览器指纹配置已更新。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置默认浏览器指纹失败: {str(e)}")
    
    def edit_fingerprint(self):
        """编辑选定的浏览器指纹"""
        if not self.selected_fingerprint:
            QMessageBox.warning(self, "警告", "请先选择要编辑的浏览器指纹。")
            return
        
        fingerprint_id = self.selected_fingerprint.id
        
        # 获取现有浏览器指纹配置
        fingerprint_config = fingerprint_service.get_fingerprint_by_id(fingerprint_id)
        if not fingerprint_config:
            QMessageBox.critical(self, "错误", f"无法找到ID为 {fingerprint_id} 的指纹配置。")
            return
        
        dialog = FingerprintDialog(self)
        dialog.setWindowTitle("编辑浏览器指纹")
        
        # 填充现有数据
        dialog.name_edit.setText(fingerprint_config.name)
        dialog.user_agent_edit.setPlainText(fingerprint_config.user_agent or "")
        dialog.viewport_width_spin.setValue(fingerprint_config.viewport_width)
        dialog.viewport_height_spin.setValue(fingerprint_config.viewport_height)
        dialog.platform_combo.setCurrentText(fingerprint_config.platform or "")
        dialog.timezone_edit.setText(fingerprint_config.timezone or "")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                fingerprint_data = dialog.get_fingerprint_data()
                # 基本验证
                if not fingerprint_data['name']:
                    QMessageBox.warning(self, "输入错误", "配置名称是必填项。")
                    return

                fingerprint_service.update_fingerprint(fingerprint_id, **fingerprint_data)
                
                if self.selected_user:
                    self.load_fingerprint_configs(self.selected_user.id, select_fingerprint_id=fingerprint_id)
                
                QMessageBox.information(self, "成功", "浏览器指纹配置已成功更新。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新浏览器指纹配置失败: {str(e)}")
    
    def delete_fingerprint(self):
        """删除选定的浏览器指纹"""
        if not self.selected_fingerprint:
            QMessageBox.warning(self, "警告", "请先选择要删除的浏览器指纹配置。")
            return
        
        fingerprint_id = self.selected_fingerprint.id
        fingerprint_name = self.selected_fingerprint.name
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要永久删除浏览器指纹配置 '{fingerprint_name}' 吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                fingerprint_service.delete_fingerprint(fingerprint_id)
                if self.selected_user:
                    self.load_fingerprint_configs(self.selected_user.id)
                QMessageBox.information(self, "成功", f"浏览器指纹配置 '{fingerprint_name}' 已被成功删除。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除浏览器指纹配置失败: {str(e)}")
    
    def edit_user(self):
        """
        编辑选中的用户信息
        
        - 检查是否已选择用户
        - 弹出编辑对话框并填充现有数据
        - 对用户输入进行基本验证
        - 调用服务层执行更新
        - 刷新用户列表并重新选中该用户
        """
        if not self.selected_user:
            QMessageBox.warning(self, "警告", "请先从列表中选择要编辑的用户。")
            return
            
        dialog = UserDialog(self)
        dialog.setWindowTitle("编辑用户")
        
        # 填充现有数据到对话框
        dialog.username_edit.setText(self.selected_user.username)
        dialog.phone_edit.setText(self.selected_user.phone or "")
        dialog.display_name_edit.setText(self.selected_user.display_name or "")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_user_data()
            
            # 输入验证
            if not user_data['username'] or not user_data['phone']:
                QMessageBox.warning(self, "输入错误", "用户名和手机号是必填项。")
                return

            try:
                user_service.update_user(self.selected_user.id, user_data)
                QMessageBox.information(self, "成功", "用户信息已成功更新。")
                self.load_users(select_user_id=self.selected_user.id)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新用户信息失败: {str(e)}")


class UserDialog(QDialog):
    """
    用户添加/编辑对话框
    
    这是一个模态对话框，用于添加新用户或编辑现有用户的信息。
    
    功能特点：
    - 支持添加和编辑两种模式
    - 包含用户名、手机号、显示名称三个输入字段
    - 采用现代化的玻璃态设计风格
    - 输入验证和错误处理
    - 响应式布局设计
    
    使用方法：
    1. 创建对话框实例
    2. 可选择性填充现有数据（编辑模式）
    3. 调用exec()显示对话框
    4. 根据返回值判断用户操作（接受/取消）
    5. 调用get_user_data()获取用户输入的数据
    """
    
    def __init__(self, parent=None):
        """
        初始化用户对话框
        
        Args:
            parent: 父窗口对象，用于模态显示
        """
        super().__init__(parent)
        self.setWindowTitle("添加用户")
        self.setModal(True)  # 设置为模态对话框
        self.setFixedSize(400, 300)  # 固定对话框大小
        self.init_ui()  # 初始化用户界面
        self.apply_dialog_styles()  # 应用样式表
    
    def init_ui(self):
        """
        初始化对话框用户界面
        
        创建对话框的UI结构：
        1. 对话框标题
        2. 表单输入区域（用户名、手机号、显示名称）
        3. 按钮区域（确定、取消）
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 对话框标题
        title_label = QLabel("👤 用户信息")
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 表单容器 - 包含所有输入字段
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)  # 标签右对齐
        
        # 用户名输入字段
        self.username_edit = QLineEdit()
        self.username_edit.setObjectName("dialogInput")
        self.username_edit.setPlaceholderText("请输入用户名")
        form_layout.addRow("用户名:", self.username_edit)
        
        # 手机号输入字段
        self.phone_edit = QLineEdit()
        self.phone_edit.setObjectName("dialogInput")
        self.phone_edit.setPlaceholderText("请输入手机号")
        form_layout.addRow("手机号:", self.phone_edit)
        
        # 显示名称输入字段（可选）
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setObjectName("dialogInput")
        self.display_name_edit.setPlaceholderText("请输入显示名称（可选）")
        form_layout.addRow("显示名称:", self.display_name_edit)
        
        layout.addWidget(form_container)
        layout.addStretch()  # 在表单和按钮之间添加弹性空间
        
        # 按钮容器
        button_container = QFrame()
        button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)  # 连接到对话框的reject槽
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("dialogOkButton")
        ok_btn.clicked.connect(self.accept)  # 连接到对话框的accept槽
        
        button_layout.addStretch()  # 按钮右对齐
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        layout.addWidget(button_container)
    
    def apply_dialog_styles(self):
        """
        应用对话框样式
        
        设置对话框的现代化玻璃态样式，包括：
        - 渐变背景和毛玻璃效果
        - 输入框的圆角和阴影
        - 按钮的渐变色和悬停效果
        - 整体的色彩搭配和字体设置
        """
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102,126,234,0.95), stop:0.5 rgba(118,75,162,0.9), stop:1 rgba(240,147,251,0.95));
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                backdrop-filter: blur(20px);
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            
            #dialogTitle {
                color: #1a1a1a !important;
                padding: 15px;
                font-weight: 700;
                text-shadow: 0 1px 2px rgba(255,255,255,0.3);
                font-size: 16px;
            }
            
            #formContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.98), stop:1 rgba(255,255,255,0.95));
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 15px;
                padding: 25px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            
            QFormLayout QLabel, QLabel {
                color: #1a1a1a !important;
                font-weight: 700;
                font-size: 14px;
                text-shadow: none;
            }
            
            #dialogInput {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,1.0), stop:1 rgba(248,249,250,0.98));
                font-size: 14px;
                color: #1a1a1a !important;
                font-weight: 600;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogInput:focus {
                border-color: #667eea;
                background: rgba(255,255,255,1.0);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1), 0 4px 20px rgba(102,126,234,0.15);
                color: #1a1a1a !important;
            }
            
            #dialogInput::placeholder {
                color: #6b7280 !important;
                font-weight: 500;
            }
            
            #dialogCombo {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,1.0), stop:1 rgba(248,249,250,0.98));
                font-size: 14px;
                color: #1a1a1a !important;
                font-weight: 600;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogCombo:focus {
                border-color: #667eea;
                background: rgba(255,255,255,1.0);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
                color: #1a1a1a !important;
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
                background: rgba(255,255,255,0.98);
                border: 1px solid rgba(102,126,234,0.3);
                border-radius: 8px;
                selection-background-color: rgba(102,126,234,0.2);
                backdrop-filter: blur(10px);
                color: #1a1a1a !important;
            }
            
            #dialogSpin {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,1.0), stop:1 rgba(248,249,250,0.98));
                font-size: 14px;
                color: #1a1a1a !important;
                font-weight: 600;
                min-width: 220px;
                backdrop-filter: blur(5px);
            }
            
            #dialogSpin:focus {
                border-color: #667eea;
                background: rgba(255,255,255,1.0);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
                color: #1a1a1a !important;
            }
            
            #dialogTextEdit {
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,1.0), stop:1 rgba(248,249,250,0.98));
                font-size: 14px;
                color: #1a1a1a !important;
                font-weight: 600;
                padding: 12px;
                backdrop-filter: blur(5px);
            }
            
            #dialogTextEdit:focus {
                border-color: #667eea;
                background: rgba(255,255,255,1.0);
                outline: none;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
                color: #1a1a1a !important;
            }
            
            #buttonContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.15), stop:1 rgba(255,255,255,0.1));
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
        """
        获取用户输入的数据
        
        Returns:
            dict: 包含用户信息的字典，包括：
                - username: 用户名
                - phone: 手机号
                - display_name: 显示名称（可选）
        """
        return {
            'username': self.username_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'display_name': self.display_name_edit.text().strip() or None
        }


class FingerprintDialog(QDialog):
    """
    浏览器指纹配置对话框
    
    这是一个专门用于配置浏览器指纹的模态对话框。
    
    功能特点：
    - 支持添加和编辑浏览器指纹配置
    - 包含指纹名称、User-Agent、视窗尺寸、平台、时区等配置项
    - 提供默认值和占位符文本
    - 现代化的玻璃态设计风格
    - 输入验证和数据格式化
    
    配置项说明：
    - 配置名称：用于标识该指纹配置的名称
    - User-Agent：浏览器标识字符串
    - 视窗宽度/高度：浏览器窗口的显示尺寸
    - 平台：操作系统平台标识
    - 时区：浏览器的时区设置
    """
    
    def __init__(self, parent=None):
        """
        初始化浏览器指纹对话框
        
        Args:
            parent: 父窗口对象，用于模态显示
        """
        super().__init__(parent)
        self.setWindowTitle("浏览器指纹配置")
        self.setModal(True)  # 设置为模态对话框
        self.setFixedSize(500, 500)  # 固定对话框大小（比用户对话框更大）
        self.init_ui()  # 初始化用户界面
        self.apply_dialog_styles()  # 应用样式表
    
    def init_ui(self):
        """
        初始化对话框用户界面
        
        创建浏览器指纹配置对话框的UI结构：
        1. 对话框标题
        2. 表单输入区域（各种指纹配置项）
        3. 按钮区域（确定、取消）
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 对话框标题
        title_label = QLabel("🔍 浏览器指纹配置")
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 表单容器 - 包含所有配置输入字段
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)  # 标签右对齐
        
        # 配置名称输入字段
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("dialogInput")
        self.name_edit.setPlaceholderText("请输入配置名称")
        form_layout.addRow("配置名称:", self.name_edit)
        
        # User-Agent输入字段（多行文本）
        self.user_agent_edit = QTextEdit()
        self.user_agent_edit.setObjectName("dialogTextEdit")
        self.user_agent_edit.setMaximumHeight(80)  # 限制高度
        self.user_agent_edit.setPlaceholderText("请输入User-Agent字符串")
        form_layout.addRow("User-Agent:", self.user_agent_edit)
        
        # 视窗宽度输入字段
        self.viewport_width_spin = QSpinBox()
        self.viewport_width_spin.setObjectName("dialogSpin")
        self.viewport_width_spin.setRange(800, 3840)  # 支持从800到4K分辨率
        self.viewport_width_spin.setValue(1920)  # 默认1920
        form_layout.addRow("视窗宽度:", self.viewport_width_spin)
        
        # 视窗高度输入字段
        self.viewport_height_spin = QSpinBox()
        self.viewport_height_spin.setObjectName("dialogSpin")
        self.viewport_height_spin.setRange(600, 2160)  # 支持从600到4K分辨率
        self.viewport_height_spin.setValue(1080)  # 默认1080
        form_layout.addRow("视窗高度:", self.viewport_height_spin)
        
        # 平台选择下拉框
        self.platform_combo = QComboBox()
        self.platform_combo.setObjectName("dialogCombo")
        self.platform_combo.addItems(['Win32', 'MacIntel', 'Linux x86_64'])  # 常见平台
        form_layout.addRow("平台:", self.platform_combo)
        
        # 时区输入字段
        self.timezone_edit = QLineEdit()
        self.timezone_edit.setObjectName("dialogInput")
        self.timezone_edit.setText('Asia/Shanghai')  # 默认中国时区
        self.timezone_edit.setPlaceholderText("请输入时区")
        form_layout.addRow("时区:", self.timezone_edit)
        
        layout.addWidget(form_container)
        layout.addStretch()  # 在表单和按钮之间添加弹性空间
        
        # 按钮容器
        button_container = QFrame()
        button_container.setObjectName("buttonContainer")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialogCancelButton")
        cancel_btn.clicked.connect(self.reject)  # 连接到对话框的reject槽
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("dialogOkButton")
        ok_btn.clicked.connect(self.accept)  # 连接到对话框的accept槽
        
        button_layout.addStretch()  # 按钮右对齐
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        layout.addWidget(button_container)
    
    def apply_dialog_styles(self):
        """
        应用浏览器指纹对话框样式
        
        设置对话框的现代化玻璃态样式，与用户对话框保持一致的设计风格，
        包括渐变背景、毛玻璃效果、圆角边框和阴影等视觉效果。
        """
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102,126,234,0.95), stop:0.5 rgba(118,75,162,0.9), stop:1 rgba(240,147,251,0.95));
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 20px;
                backdrop-filter: blur(20px);
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            
            #dialogTitle {
                color: #1a1a1a !important;
                padding: 15px;
                font-weight: 700;
                text-shadow: 0 1px 2px rgba(255,255,255,0.3);
                font-size: 16px;
            }
            
            #formContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.98), stop:1 rgba(255,255,255,0.95));
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 15px;
                padding: 25px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            
            QFormLayout QLabel, QLabel {
                color: #1a1a1a !important;
                font-weight: 700;
                font-size: 14px;
                text-shadow: none;
            }
            
            #dialogInput {
                padding: 15px 20px;
                border: 2px solid rgba(102,126,234,0.2);
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,0.9), stop:1 rgba(248,249,250,0.95));
                font-size: 14px;
                color: #1a1a1a !important;
                font-weight: 600;
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
                color: #1a1a1a !important;
                font-weight: 600;
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
                color: #1a1a1a !important;
                font-weight: 600;
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
                color: #1a1a1a !important;
                font-weight: 600;
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
        """
        获取浏览器指纹配置数据
        
        Returns:
            dict: 包含浏览器指纹配置信息的字典，包括：
                - name: 配置名称
                - user_agent: User-Agent字符串（可选）
                - viewport_width: 视窗宽度
                - viewport_height: 视窗高度
                - platform: 平台标识
                - timezone: 时区设置
                - locale: 语言区域设置（固定为zh-CN）
        """
        return {
            'name': self.name_edit.text().strip(),
            'user_agent': self.user_agent_edit.toPlainText().strip() or None,
            'viewport_width': self.viewport_width_spin.value(),
            'viewport_height': self.viewport_height_spin.value(),
            'platform': self.platform_combo.currentText(),
            'timezone': self.timezone_edit.text().strip(),
            'locale': 'zh-CN'  # 固定为中文简体
        }


class ProxyDialog(QDialog):
    """
    代理配置对话框
    
    这是一个模态对话框，用于添加新代理或编辑现有代理的配置。
    
    功能特点：
    - 支持添加和编辑两种模式
    - 包含配置名称、类型、主机、端口、用户名和密码等输入字段
    - 采用现代化的玻璃态设计风格
    - 密码字段自动隐藏
    """
    
    def __init__(self, parent=None):
        """
        初始化代理对话框
        """
        super().__init__(parent)
        self.setWindowTitle("代理配置")
        self.setModal(True)
        self.setFixedSize(450, 420)
        self.init_ui()
        self.apply_dialog_styles()
    
    def init_ui(self):
        """
        初始化对话框用户界面
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_label = QLabel("🌐 代理服务器配置")
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("dialogInput")
        self.name_edit.setPlaceholderText("例如：家庭代理")
        form_layout.addRow("配置名称:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("dialogCombo")
        self.type_combo.addItems(['HTTP', 'SOCKS5'])
        form_layout.addRow("代理类型:", self.type_combo)
        
        self.host_edit = QLineEdit()
        self.host_edit.setObjectName("dialogInput")
        self.host_edit.setPlaceholderText("例如：127.0.0.1")
        form_layout.addRow("主机地址:", self.host_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setObjectName("dialogSpin")
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(1080)
        form_layout.addRow("端口:", self.port_spin)
        
        self.username_edit = QLineEdit()
        self.username_edit.setObjectName("dialogInput")
        self.username_edit.setPlaceholderText("（可选）")
        form_layout.addRow("用户名:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName("dialogInput")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("（可选）")
        form_layout.addRow("密码:", self.password_edit)
        
        layout.addWidget(form_container)
        layout.addStretch()
        
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
        """
        应用对话框样式
        """
        # 复用FingerprintDialog的样式
        style_sheet = FingerprintDialog(self).styleSheet()
        self.setStyleSheet(style_sheet)
    
    def get_proxy_data(self):
        """
        获取用户输入的代理数据
        
        Returns:
            dict: 包含代理配置信息的字典
        """
        return {
            'name': self.name_edit.text().strip(),
            'proxy_type': self.type_combo.currentText().lower(),
            'host': self.host_edit.text().strip(),
            'port': self.port_spin.value(),
            'username': self.username_edit.text().strip() or None,
            'password': self.password_edit.text().strip() or None,
        } 