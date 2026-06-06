from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize

class ResponsiveButton(QPushButton):
    def __init__(self, text, icon=None, parent=None):
        super().__init__(parent)
        self.full_text = text
        if icon:
            self.setIcon(icon)
        self.setText(self.full_text)
        self.collapsed = False
        # Prevent the button from forcing the layout wide
        self.setMinimumWidth(40) 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # If button width goes below 140, collapse the text
        if self.width() < 140 and not self.collapsed:
            self.setText("")
            self.collapsed = True
        # If button width goes above 140, restore the text
        elif self.width() >= 140 and self.collapsed:
            self.setText(self.full_text)
            self.collapsed = False
