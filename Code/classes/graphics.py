"""
Graphics utility class for text and shape rendering on OLED display
"""


class Graphics:
    """Handles graphics operations on OLED display"""
    
    def __init__(self, display):
        """Initialize graphics with display object"""
        self.display = display
    
    def draw_text(self, text, x, y, size=1):
        """Draw text at position"""
        try:
            # Handle explicit line breaks for 8px text rows.
            lines = str(text).split("\n")
            for idx, line in enumerate(lines):
                self.display.text(line, x, y + idx * 10)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing text: {e}")
    
    def draw_centered_text(self, text, y, size=1):
        """Draw centered text at Y position"""
        try:
            lines = str(text).split("\n")
            for idx, line in enumerate(lines):
                # Estimate width: default font is roughly 8x8 in MicroPython.
                estimated_width = len(line) * 8
                x = (128 - estimated_width) // 2
                if x < 0:
                    x = 0
                self.display.text(line, x, y + idx * 10)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing centered text: {e}")
    
    def draw_icon(self, x, y, icon_data):
        """Draw custom icon bitmap"""
        try:
            # Simple icon drawing using framebuffer
            # icon_data should be a list of bytes
            for i, byte in enumerate(icon_data):
                row = i // 16
                col = i % 16
                self.display.pixel(x + col, y + row, byte)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing icon: {e}")
    
    def draw_rectangle(self, x, y, width, height, filled=False):
        """Draw rectangle"""
        try:
            if filled:
                self.display.fill_rect(x, y, width, height, 1)
            else:
                self.display.rect(x, y, width, height, 1)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing rectangle: {e}")
    
    def draw_circle(self, x, y, radius):
        """Draw circle (approximated with lines)"""
        try:
            # Draw circle using Midpoint Circle Algorithm approximation
            import math
            for i in range(0, 360, 15):
                rad = math.radians(i)
                x1 = int(x + radius * math.cos(rad))
                y1 = int(y + radius * math.sin(rad))
                self.display.pixel(x1, y1, 1)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing circle: {e}")
    
    def draw_line(self, x1, y1, x2, y2):
        """Draw line"""
        try:
            self.display.line(x1, y1, x2, y2, 1)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing line: {e}")
    
    def draw_progress_bar(self, x, y, width, height, progress):
        """Draw progress bar (0-100)"""
        try:
            filled_width = int(width * progress / 100)
            self.display.fill_rect(x, y, filled_width, height, 1)
            self.display.rect(x, y, width, height, 1)
        except Exception as e:
            print(f"[GRAPHICS] Error drawing progress bar: {e}")
    
    def clear(self):
        """Clear display"""
        self.display.fill(0)
    
    def update(self):
        """Update display"""
        self.display.show()
