# widgets/syntax_highlighter.py (修正版)

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import QRegularExpression
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatter import Formatter

class _PygmentsFormatter(Formatter):
    """自定义Pygments Formatter，用于将token映射到QTextCharFormat"""
    def __init__(self):
        super().__init__()
        self.data = []

    def format(self, tokensource, outfile):
        self.data = []
        for ttype, value in tokensource:
            self.data.append((ttype, value))

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.formatter = _PygmentsFormatter()
        
        # --- 关键修正 ---
        # 在高亮器初始化时，必须先将lexer设为None，否则后续调用会立即报错。
        self.lexer = None
        
        # 从Pygments样式中获取颜色定义 (使用默认样式)
        from pygments.styles import get_style_by_name
        style = get_style_by_name('default')
        self.formats = {}
        for token, s in style:
            fmt = QTextCharFormat()
            if s['color']:
                fmt.setForeground(QColor(f"#{s['color']}"))
            if s['bgcolor']:
                fmt.setBackground(QColor(f"#{s['bgcolor']}"))
            if s['bold']:
                fmt.setFontWeight(QFont.Weight.Bold)
            if s['italic']:
                fmt.setFontItalic(True)
            if s['underline']:
                fmt.setFontUnderline(True)
            self.formats[token] = fmt

    def set_language(self, language):
        """设置要高亮的语言"""
        try:
            self.lexer = get_lexer_by_name(language, stripall=True)
        except:
            self.lexer = None # 如果语言无效，则不进行高亮

    def highlightBlock(self, text):
        """Qt在需要重绘文本块时会自动调用此方法"""
        if self.lexer is None:
            # 如果没有有效的lexer，则不执行任何操作
            return

        # 使用Pygments进行词法分析
        highlight(text, self.lexer, self.formatter)
        
        # 应用格式
        start_index = 0
        for ttype, value in self.formatter.data:
            length = len(value)
            fmt = self.formats.get(ttype)
            if fmt:
                self.setFormat(start_index, length, fmt)
            start_index += length