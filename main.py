# main.py (最终版本)

import sys
import traceback
import requests
import pyperclip

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton, QSplitter,
    QMessageBox, QToolBar, QComboBox, QLabel,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database import db_handler
from widgets.syntax_highlighter import SyntaxHighlighter
from pygments.lexers import get_all_lexers

# API服务器的基础URL，请根据您的部署情况修改
API_BASE_URL = "http://127.0.0.1:8000"

# --- 自定义对话框，用于选择分享选项 ---
class ShareOptionsDialog(QDialog):
    """
    一个自定义对话框，用于让用户在分享时选择链接的有效期。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分享选项")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("请选择分享链接的有效期："))
        
        self.duration_combo = QComboBox()
        # 使用addItem的第二个参数(userData)来存储API需要的天数
        self.duration_combo.addItem("1 天", 1)
        self.duration_combo.addItem("7 天", 7)
        self.duration_combo.addItem("30 天", 30)
        self.duration_combo.addItem("永久", None) # 使用None表示永久
        self.duration_combo.setCurrentIndex(1) # 默认选中 "7 天"
        self.layout.addWidget(self.duration_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_selected_duration(self):
        """返回用户选择的有效期天数 (None代表永久)。"""
        return self.duration_combo.currentData()

# --- 主窗口类 ---
class MainWindow(QMainWindow):
    """
    应用程序的主窗口，包含所有UI组件和业务逻辑。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeSharer")
        self.setGeometry(100, 100, 1200, 700)
        self.current_snippet_id = None
        
        db_handler.init_db()
        self.init_ui()
        self.load_snippets_list()

    def init_ui(self):
        """初始化主窗口UI布局和组件。"""
        # 工具栏
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        btn_new = QPushButton("新建"); btn_new.clicked.connect(self.new_snippet); toolbar.addWidget(btn_new)
        btn_save = QPushButton("保存"); btn_save.clicked.connect(self.save_snippet); toolbar.addWidget(btn_save)
        btn_delete = QPushButton("删除"); btn_delete.clicked.connect(self.delete_snippet); toolbar.addWidget(btn_delete)
        toolbar.addSeparator()
        btn_share = QPushButton("在线分享"); btn_share.clicked.connect(self.share_snippet); toolbar.addWidget(btn_share)

        # 主布局
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(main_splitter)

        # 左侧面板 (列表和搜索)
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel); left_layout.setContentsMargins(0, 5, 5, 0)
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("按标题搜索..."); self.search_input.textChanged.connect(self.filter_snippets_list); left_layout.addWidget(self.search_input)
        self.snippet_list_widget = QListWidget(); self.snippet_list_widget.itemClicked.connect(self.on_snippet_selected); left_layout.addWidget(self.snippet_list_widget)

        # 右侧面板 (编辑器)
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel); right_layout.setContentsMargins(5, 5, 0, 0)
        self.title_input = QLineEdit(); self.title_input.setPlaceholderText("代码片段标题..."); right_layout.addWidget(self.title_input)
        editor_header_layout = QHBoxLayout(); editor_header_layout.addWidget(QLabel("语言:"))
        self.language_combo = QComboBox(); self.populate_language_combo(); editor_header_layout.addWidget(self.language_combo, 1); right_layout.addLayout(editor_header_layout)
        self.content_editor = QTextEdit(); self.content_editor.setPlaceholderText("在此处粘贴或编写您的代码..."); self.content_editor.setFont(QFont("Courier New", 11)); right_layout.addWidget(self.content_editor)
        
        # 语法高亮
        self.highlighter = SyntaxHighlighter(self.content_editor.document())
        self.language_combo.currentTextChanged.connect(self.update_highlighter_language)
        
        main_splitter.addWidget(left_panel); main_splitter.addWidget(right_panel); main_splitter.setSizes([300, 900])

    def load_snippets_list(self):
        """从数据库加载所有片段并更新UI列表。"""
        self.snippet_list_widget.clear()
        snippets = db_handler.get_all_snippets()
        for snippet in snippets:
            title = snippet.get('title', '无标题') or '无标题'
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, snippet['id'])
            self.snippet_list_widget.addItem(item)
        self.filter_snippets_list()

    def filter_snippets_list(self):
        """根据搜索框的文本实时过滤列表项。"""
        search_text = self.search_input.text().lower()
        for i in range(self.snippet_list_widget.count()):
            item = self.snippet_list_widget.item(i)
            item_text = item.text().lower()
            item.setHidden(search_text not in item_text)

    def on_snippet_selected(self, item):
        """当用户在列表中选择一个片段时，加载其内容到编辑器。"""
        if item is None: return
        self.current_snippet_id = item.data(Qt.ItemDataRole.UserRole)
        snippet_data = db_handler.get_snippet_by_id(self.current_snippet_id)
        if snippet_data:
            lang_alias = snippet_data.get('language', 'plaintext')
            index = self.language_combo.findData(lang_alias)
            self.language_combo.setCurrentIndex(index if index >= 0 else self.language_combo.findData("plaintext"))
            self.title_input.setText(snippet_data.get('title', ''))
            self.content_editor.setText(snippet_data.get('content', ''))

    def new_snippet(self):
        """清空编辑器，准备创建新片段。"""
        self.snippet_list_widget.setCurrentItem(None)
        self.current_snippet_id = None
        self.title_input.clear(); self.content_editor.clear()
        self.title_input.setFocus()
        self.language_combo.setCurrentIndex(self.language_combo.findData("plaintext"))

    def save_snippet(self):
        """保存当前编辑器中的内容（新建或更新）。"""
        title = self.title_input.text().strip()
        content = self.content_editor.toPlainText()
        language = self.language_combo.currentData()
        if not title or not content:
            QMessageBox.warning(self, "输入错误", "标题和内容不能为空！"); return

        if self.current_snippet_id is None:
            # 创建新片段
            new_id = db_handler.add_snippet(title, content, language)
            self.current_snippet_id = new_id
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, new_id)
            self.snippet_list_widget.insertItem(0, item)
            self.snippet_list_widget.setCurrentItem(item)
            QMessageBox.information(self, "成功", "代码片段已成功创建！")
        else:
            # 更新现有片段
            db_handler.update_snippet(self.current_snippet_id, title, content, language)
            for i in range(self.snippet_list_widget.count()):
                item = self.snippet_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_snippet_id:
                    item.setText(title); break
            QMessageBox.information(self, "成功", "代码片段已成功更新！")
        
        self.filter_snippets_list()

    def delete_snippet(self):
        """删除当前选中的片段。"""
        if self.current_snippet_id is None:
            QMessageBox.warning(self, "操作无效", "请先选择一个要删除的代码片段。"); return

        current_item = self.snippet_list_widget.currentItem()
        if not current_item: return
        
        reply = QMessageBox.question(self, "确认删除", f"您确定要删除 '{current_item.text()}' 吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db_handler.delete_snippet(self.current_snippet_id)
            row = self.snippet_list_widget.row(current_item)
            self.snippet_list_widget.takeItem(row)
            self.new_snippet()
            QMessageBox.information(self, "成功", "代码片段已删除。")

    def share_snippet(self):
        """处理在线分享逻辑，包括弹出选项对话框和调用API。"""
        if self.current_snippet_id is None:
            QMessageBox.warning(self, "操作无效", "请先选择一个要分享的代码片段。"); return
        content = self.content_editor.toPlainText()
        if not content:
            QMessageBox.warning(self, "操作无效", "无法分享空内容。"); return

        dialog = ShareOptionsDialog(self)
        if dialog.exec():
            duration = dialog.get_selected_duration()
            payload = {"content": content, "language": self.language_combo.currentData(), "expires_in_days": duration}
            try:
                response = requests.post(f"{API_BASE_URL}/api/snippets", json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                share_url = data.get("url")
                pyperclip.copy(share_url)
                QMessageBox.information(self, "分享成功", f"分享链接已复制到剪贴板！\n\n{share_url}")
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "分享失败", f"无法连接到分享服务器。\n错误: {e}")
            except Exception as e:
                QMessageBox.critical(self, "分享失败", f"发生未知错误: {e}")

    def populate_language_combo(self):
        """填充语言选择下拉框。"""
        lexers = sorted(get_all_lexers(), key=lambda x: x[0])
        self.language_combo.addItem("plaintext", "plaintext")
        for lexer in lexers:
            if lexer[1]:
                lang_name, lang_alias = lexer[0], lexer[1][0]
                self.language_combo.addItem(lang_name, lang_alias)

    def update_highlighter_language(self, text):
        """当语言选择变化时，更新语法高亮器。"""
        lang_alias = self.language_combo.currentData()
        self.highlighter.set_language(lang_alias)
        self.highlighter.rehighlight()

# --- 应用程序主入口 ---
def main():
    """
    应用程序的主入口函数，包含全局异常捕获。
    """
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
    except Exception as e:
        # 捕获任何未处理的异常，以防止程序静默崩溃
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setText("应用程序遇到严重错误，即将退出。")
        error_dialog.setInformativeText(f"{type(e).__name__}: {e}")
        error_dialog.setWindowTitle("致命错误")
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.exec()
        # 同时在控制台打印错误信息，便于调试
        traceback.print_exc()

if __name__ == '__main__':
    main()