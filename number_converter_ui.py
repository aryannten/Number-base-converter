import tkinter as tk
from tkinter import ttk, messagebox
from idlelib.tooltip import Hovertip
from converter_utils import convert_number_logic, validate_number, get_prefixed_result, save_to_history, read_history
import json
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import re

class ModernNumberConverter:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Number Base Converter")
        self.root.geometry("600x600")
        self.root.minsize(500, 550)
        self.root.resizable(True, True)
        
        # Configuration
        self.config_file = Path("converter_config.json")
        self.history_file = Path("conversion_history.txt")
        self.load_config()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize UI
        self.setup_styles()
        self.setup_ui()
        
        # Bindings
        self.root.bind('<Return>', lambda event: self.convert_number())
        self.root.bind('<Escape>', lambda event: self.clear_all())
        
        # Animation variables
        self.animation_in_progress = False
        self.theme_transition_steps = 10
        self.current_transition_step = 0
        
    def load_config(self) -> None:
        """Load configuration from file or use defaults."""
        default_config = {
            "theme": "dark",
            "themes": {
                'dark': {
                    'bg': '#1e1e2e', 'text': '#cdd6f4', 'entry_bg': '#313244', 
                    'entry_fg': '#cdd6f4', 'button_bg': '#585b70', 
                    'history_bg': '#1e1e2e', 'history_fg': '#cdd6f4',
                    'highlight': '#89b4fa'
                },
                'light': {
                    'bg': '#ffffff', 'text': '#000000', 'entry_bg': '#f5f5f5',
                    'entry_fg': '#000000', 'button_bg': '#e0e0e0',
                    'history_bg': '#f0f0f0', 'history_fg': '#000000',
                    'highlight': '#1a73e8'
                },
                'solarized': {
                    'bg': '#fdf6e3', 'text': '#657b83', 'entry_bg': '#eee8d5',
                    'entry_fg': '#586e75', 'button_bg': '#93a1a1',
                    'history_bg': '#eee8d5', 'history_fg': '#586e75',
                    'highlight': '#268bd2'
                }
            },
            "recent_bases": ["Decimal", "Binary", "Octal", "Hexadecimal"],
            "font": {"family": "Segoe UI", "size": 11}
        }
        
        try:
            with self.config_file.open('r', encoding='utf-8') as f:
                self.config = {**default_config, **json.load(f)}
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = default_config
        
        self.current_theme = self.config["theme"]
        self.colors = self.config["themes"][self.current_theme]
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with self.config_file.open('w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def setup_styles(self) -> None:
        """Configure ttk styles based on current theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure fonts
        font = (self.config["font"]["family"], self.config["font"]["size"])
        bold_font = (self.config["font"]["family"], self.config["font"]["size"], 'bold')
        title_font = (self.config["font"]["family"], 18, 'bold')
        
        # Configure styles
        style.configure('.', background=self.colors['bg'], foreground=self.colors['text'])
        style.configure('TLabel', font=font)
        style.configure('TEntry', 
                       font=font,
                       fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['entry_fg'],
                       insertcolor=self.colors['text'])
        style.configure('TButton', 
                       font=bold_font,
                       background=self.colors['button_bg'],
                       foreground=self.colors['text'])
        style.configure('TCombobox', 
                       font=font,
                       fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['entry_fg'])
        style.map('TButton',
                 background=[('active', self.colors['highlight'])],
                 foreground=[('active', self.colors['text'])])
    
    def setup_ui(self) -> None:
        """Set up all UI components."""
        self.root.configure(bg=self.colors['bg'])
        
        # Main container for responsive layout
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        self.create_title()
        
        # Input section
        self.create_input_section()
        
        # Buttons
        self.create_buttons()
        
        # Result section
        self.create_result_section()
        
        # History section
        self.create_history_section()
        
        # Theme toggle
        self.create_theme_toggle()
        
        # Status bar
        self.create_status_bar()
        
        # Configure grid weights for responsive layout
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)  # History section expands
    
    def create_title(self) -> None:
        """Create the title label."""
        title_font = (self.config["font"]["family"], 18, 'bold')
        title = ttk.Label(
            self.main_frame, 
            text="Number Base Converter", 
            font=title_font
        )
        title.grid(row=0, column=0, pady=(0, 20), sticky='ew')
    
    def create_input_section(self) -> None:
        """Create the input number and base selection widgets."""
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=1, column=0, sticky='ew', pady=5)
        
        # Number input
        ttk.Label(frame, text="Number:").grid(row=0, column=0, sticky='w')
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            frame, 
            textvariable=self.input_var, 
            width=30
        )
        self.input_entry.grid(row=0, column=1, padx=10, sticky='ew')
        
        # From base
        ttk.Label(frame, text="From Base:").grid(row=1, column=0, sticky='w', pady=5)
        self.from_base = tk.StringVar(value="Decimal")
        self.from_combo = ttk.Combobox(
            frame, 
            textvariable=self.from_base, 
            state='readonly',
            values=self.config["recent_bases"]
        )
        self.from_combo.grid(row=1, column=1, padx=10, sticky='ew')
        
        # To base
        ttk.Label(frame, text="To Base:").grid(row=2, column=0, sticky='w')
        self.to_base = tk.StringVar(value="Binary")
        self.to_combo = ttk.Combobox(
            frame, 
            textvariable=self.to_base, 
            state='readonly',
            values=self.config["recent_bases"]
        )
        self.to_combo.grid(row=2, column=1, padx=10, sticky='ew')
        
        # Configure grid weights
        frame.grid_columnconfigure(1, weight=1)
    
    def create_buttons(self) -> None:
        """Create action buttons."""
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=2, column=0, sticky='ew', pady=10)
        
        # Convert button
        convert_btn = ttk.Button(
            frame, 
            text="Convert", 
            command=self.convert_number
        )
        convert_btn.grid(row=0, column=0, padx=5)
        Hovertip(convert_btn, "Convert the number to the selected base")
        
        # Clear button
        clear_btn = ttk.Button(
            frame, 
            text="Clear", 
            command=self.clear_all
        )
        clear_btn.grid(row=0, column=1, padx=5)
        Hovertip(clear_btn, "Clear all fields")
        
        # Swap button
        swap_btn = ttk.Button(
            frame, 
            text="Swap", 
            command=self.swap_bases
        )
        swap_btn.grid(row=0, column=2, padx=5)
        Hovertip(swap_btn, "Swap the 'From' and 'To' bases")
        
        # Center buttons
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
    
    def create_result_section(self) -> None:
        """Create the result display and copy button."""
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=3, column=0, sticky='ew', pady=10)
        
        ttk.Label(frame, text="Result:").grid(row=0, column=0, sticky='w')
        
        self.result_var = tk.StringVar()
        self.result_entry = ttk.Entry(
            frame, 
            textvariable=self.result_var, 
            state='readonly', 
            width=40
        )
        self.result_entry.grid(row=0, column=1, padx=10, sticky='ew')
        
        copy_btn = ttk.Button(
            frame, 
            text="📋 Copy", 
            command=self.copy_result
        )
        copy_btn.grid(row=0, column=2)
        Hovertip(copy_btn, "Copy the result to clipboard")
        
        frame.grid_columnconfigure(1, weight=1)
    
    def create_history_section(self) -> None:
        """Create the history display section."""
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=4, column=0, sticky='nsew', pady=(0, 10))
        
        ttk.Label(frame, text="Recent History:").pack(anchor='w')
        
        self.history_box = tk.Text(
            frame, 
            height=5, 
            width=65, 
            state='disabled',
            bg=self.colors['history_bg'], 
            fg=self.colors['history_fg'],
            wrap=tk.WORD
        )
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.history_box.yview)
        self.history_box.configure(yscrollcommand=scrollbar.set)
        
        self.history_box.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.update_history()
    
    def create_theme_toggle(self) -> None:
        """Create theme toggle button and theme selection."""
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=5, column=0, sticky='ew', pady=5)
        
        # Theme toggle button
        toggle_btn = ttk.Button(
            frame, 
            text="Toggle Theme 🌗", 
            command=self.toggle_theme
        )
        toggle_btn.pack(side='left')
        Hovertip(toggle_btn, "Switch between dark and light themes")
        
        # Theme selection dropdown
        theme_label = ttk.Label(frame, text="Select Theme:")
        theme_label.pack(side='left', padx=(20, 5))
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        theme_combo = ttk.Combobox(
            frame, 
            textvariable=self.theme_var, 
            values=list(self.config["themes"].keys()),
            state='readonly',
            width=12
        )
        theme_combo.pack(side='left')
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        Hovertip(theme_combo, "Select a different color theme")
    
    def create_status_bar(self) -> None:
        """Create the status bar at the bottom."""
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            anchor='w',
            relief='sunken'
        )
        status.grid(row=6, column=0, sticky='ew')
    
    def animate_theme_change(self, target_theme: str) -> None:
        """Animate the transition between themes."""
        if self.animation_in_progress:
            return
            
        self.animation_in_progress = True
        self.current_transition_step = 0
        start_colors = self.colors
        end_colors = self.config["themes"][target_theme]
        
        def update_colors(step: int) -> None:
            ratio = step / self.theme_transition_steps
            new_colors = {}
            for key in start_colors:
                if key in end_colors:
                    # Simple interpolation for demo (would need proper color space conversion)
                    new_colors[key] = self.interpolate_color(start_colors[key], end_colors[key], ratio)
            
            # Update colors and refresh UI
            self.colors = new_colors
            self.setup_styles()
            self.refresh_ui_colors()
            
            if step < self.theme_transition_steps:
                self.root.after(30, lambda: update_colors(step + 1))
            else:
                self.animation_in_progress = False
                self.current_theme = target_theme
                self.colors = end_colors
                self.config["theme"] = target_theme
                self.save_config()
        
        update_colors(1)
    
    def interpolate_color(self, color1: str, color2: str, ratio: float) -> str:
        """Interpolate between two hex colors."""
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
            return '#%02x%02x%02x' % rgb
        
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        
        new_rgb = tuple(int(r1 + (r2 - r1) * ratio) for r1, r2 in zip(rgb1, rgb2))
        return rgb_to_hex(new_rgb)
    
    def refresh_ui_colors(self) -> None:
        """Refresh UI elements with current colors."""
        # Update widgets that don't use ttk styles
        self.history_box.config(
            bg=self.colors['history_bg'],
            fg=self.colors['history_fg']
        )
        self.root.configure(bg=self.colors['bg'])
    
    def change_theme(self, event=None) -> None:
        """Change to the selected theme with animation."""
        new_theme = self.theme_var.get()
        if new_theme != self.current_theme and not self.animation_in_progress:
            self.animate_theme_change(new_theme)
    
    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        new_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.theme_var.set(new_theme)
        self.change_theme()
    
    def detect_input_base(self, number_str: str) -> Tuple[Optional[str], str]:
        """Detect input base from prefixes and return base name and cleaned number."""
        if number_str.startswith("0x"):
            return "Hexadecimal", number_str[2:]
        elif number_str.startswith("0b"):
            return "Binary", number_str[2:]
        elif number_str.startswith("0o"):
            return "Octal", number_str[2:]
        return None, number_str
    
    def convert_number(self) -> None:
        """Convert the number from the input base to the target base."""
        input_raw = self.input_var.get().strip()
        if not input_raw:
            self.status_var.set("Error: No input provided")
            return
            
        auto_base, number = self.detect_input_base(input_raw)
        if auto_base:
            self.from_base.set(auto_base)
        else:
            number = input_raw
        
        from_base = self.from_base.get()
        to_base = self.to_base.get()
        
        valid, msg = validate_number(number, from_base)
        if not valid:
            self.status_var.set(f"Error: {msg}")
            self.result_var.set("")
            return
        
        try:
            result = convert_number_logic(number, from_base, to_base)
            prefixed = get_prefixed_result(result, to_base)
            self.result_var.set(prefixed)
            self.status_var.set("Converted successfully")
            
            # Save to history
            save_to_history(self.history_file, number, from_base, prefixed, to_base)
            self.update_history()
            
            # Update recent bases if needed
            if from_base not in self.config["recent_bases"]:
                self.config["recent_bases"].insert(0, from_base)
                self.config["recent_bases"] = self.config["recent_bases"][:4]
                self.from_combo['values'] = self.config["recent_bases"]
            
            if to_base not in self.config["recent_bases"]:
                self.config["recent_bases"].insert(0, to_base)
                self.config["recent_bases"] = self.config["recent_bases"][:4]
                self.to_combo['values'] = self.config["recent_bases"]
            
            self.save_config()
            
        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            self.status_var.set(f"Error: {str(e)}")
            self.result_var.set("")
    
    def copy_result(self) -> None:
        """Copy the result to clipboard."""
        result = self.result_var.get()
        if result:
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            self.status_var.set("Result copied to clipboard")
    
    def update_history(self) -> None:
        """Update the history display with recent conversions."""
        history = read_history(self.history_file)
        self.history_box.config(state='normal')
        self.history_box.delete(1.0, tk.END)
        for line in history:
            self.history_box.insert(tk.END, line)
        self.history_box.config(state='disabled')
    
    def clear_all(self) -> None:
        """Clear all input and output fields."""
        self.input_var.set("")
        self.result_var.set("")
        self.status_var.set("Cleared")
    
    def swap_bases(self) -> None:
        """Swap the 'From' and 'To' bases."""
        current_from = self.from_base.get()
        current_to = self.to_base.get()
        self.from_base.set(current_to)
        self.to_base.set(current_from)
        self.convert_number()


def main() -> None:
    """Main entry point for the application."""
    root = tk.Tk()
    app = ModernNumberConverter(root)
    root.mainloop()


if __name__ == '__main__':
    main()