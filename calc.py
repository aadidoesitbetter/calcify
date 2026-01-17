import tkinter as tk
from tkinter import ttk, messagebox
import math
import threading
import json
import urllib.request
from datetime import datetime

# --- Constants & Configuration ---
LARGE_FONT_STYLE = ("Courier New", 40, "bold")
SMALL_FONT_STYLE = ("Courier New", 16)
DIGITS_FONT_STYLE = ("Courier New", 24, "bold")
DEFAULT_FONT_STYLE = ("Courier New", 20)

# "Nothing" Aesthetic Palette (Inferred from image/style)
BG_COLOR = "#E6E6E6"       # Light Grey Background
DISPLAY_COLOR = "#E6E6E6"  # Similar to BG for seamless look
BTN_NUM_BG = "#F2F2F2"     # White/Light Grey for numbers
BTN_NUM_FG = "#000000"     # Black text
BTN_OP_BG = "#1A1A1A"      # Black for operators
BTN_OP_FG = "#FFFFFF"      # White text
BTN_ACCENT_BG = "#D71921"  # Nothing Red
BTN_ACCENT_FG = "#FFFFFF"  # White text

# Currency API
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

class Calculator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("400x700")
        self.window.resizable(0, 0)
        self.window.title("Nothing Calculator")
        self.window.configure(bg=BG_COLOR)

        self.total_expression = ""
        self.current_expression = ""
        self.mode = "Standard"  # Standard, Scientific, Converter
        
        # Currency Data
        self.currency_rates = {}
        self.currency_last_updated = None
        self.conversion_input_value = ""

        # UI Setup
        self.create_menu()
        self.display_frame = self.create_display_frame()
        self.total_label, self.label = self.create_display_labels()
        
        self.buttons_frame = self.create_buttons_frame()
        
        # Initial Render
        self.render_standard_ui()
        
        # Start background currency fetch
        self.fetch_currency_thread()

    def create_menu(self):
        # A simple mode switcher at the top
        self.menu_frame = tk.Frame(self.window, bg=BG_COLOR)
        self.menu_frame.pack(fill="x", padx=10, pady=5)
        
        styles = ["Standard", "Scientific", "Converter"]
        self.mode_var = tk.StringVar(value="Standard")
        
        mode_menu = ttk.Combobox(self.menu_frame, textvariable=self.mode_var, values=styles, state="readonly", font=SMALL_FONT_STYLE, width=15)
        mode_menu.pack(side=tk.LEFT)
        mode_menu.bind("<<ComboboxSelected>>", self.on_mode_change)

    def on_mode_change(self, event):
        new_mode = self.mode_var.get()
        if new_mode != self.mode:
            self.mode = new_mode
            self.clear_ui()
            if self.mode == "Standard":
                self.render_standard_ui()
            elif self.mode == "Scientific":
                self.render_scientific_ui()
            elif self.mode == "Converter":
                self.render_converter_ui()

    def clear_ui(self):
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        # Reset display for safety
        self.current_expression = ""
        self.total_expression = ""
        self.update_label()
        self.update_total_label()

    def create_display_frame(self):
        frame = tk.Frame(self.window, height=180, bg=BG_COLOR)
        frame.pack(expand=False, fill="both", padx=10, pady=(20, 10))
        return frame

    def create_display_labels(self):
        total_label = tk.Label(self.display_frame, text=self.total_expression, anchor=tk.E, bg=BG_COLOR,
                               fg=BTN_NUM_FG, padx=10, font=SMALL_FONT_STYLE)
        total_label.pack(expand=True, fill='both')

        label = tk.Label(self.display_frame, text=self.current_expression, anchor=tk.E, bg=BG_COLOR,
                         fg=BTN_NUM_FG, padx=10, font=LARGE_FONT_STYLE)
        label.pack(expand=True, fill='both')

        return total_label, label

    def create_buttons_frame(self):
        frame = tk.Frame(self.window, bg=BG_COLOR)
        frame.pack(expand=True, fill="both")
        return frame

    # --- Standard UI ---
    def render_standard_ui(self):
        digits = {
            7: (1, 0), 8: (1, 1), 9: (1, 2),
            4: (2, 0), 5: (2, 1), 6: (2, 2),
            1: (3, 0), 2: (3, 1), 3: (3, 2),
            0: (4, 1), '.': (4, 2)
        }
        
        # Configure Grid
        for i in range(5):
            self.buttons_frame.rowconfigure(i, weight=1)
            self.buttons_frame.columnconfigure(i, weight=1)

        # Clear (AC)
        self.make_button("AC", 0, 0, command=self.clear, bg=BTN_OP_BG, fg=BTN_OP_FG)
        # Brackets
        self.make_button("()", 0, 1, command=self.brackets, bg=BTN_OP_BG, fg=BTN_OP_FG)
        # Percent
        self.make_button("%", 0, 2, command=self.percent, bg=BTN_OP_BG, fg=BTN_OP_FG)
        # Divide
        self.make_button("\u00F7", 0, 3, command=lambda: self.append_operator("/"), bg=BTN_OP_BG, fg=BTN_OP_FG)

        # Digits
        for digit, grid_pos in digits.items():
            self.make_button(str(digit), grid_pos[0], grid_pos[1], command=lambda x=digit: self.add_to_expression(x))
        
        # 00 button (Optional, maybe just empty or 0 spanning? Let's add an empty space or something. 
        # Actually standard layout often has 0 spanning 2 cols or a button at start)
        # In the Nothing image: 0 is single, next to dot, next to delete.
        # Let's verify layout.
        # Row 4: [0] [.] [DEL] [=]
        self.make_button("\u232B", 4, 0, command=self.backspace, bg=BTN_NUM_BG, fg=BTN_NUM_FG) # DEL at start? Or 0?
        # Let's stick to standard numpad:
        # 7 8 9 /
        # 4 5 6 *
        # 1 2 3 -
        # . 0 = +
        # Wait, the Nothing image has:
        # [AC] [()] [%] [/]
        # [7] [8] [9] [X]
        # [6] [5] [4] [-]
        # [3] [2] [1] [+]
        # [0] [.] [DEL] [=]
        
        # Let's match typical standard calc structure
        self.make_button("\u00D7", 1, 3, command=lambda: self.append_operator("*"), bg=BTN_OP_BG, fg=BTN_OP_FG)
        self.make_button("-", 2, 3, command=lambda: self.append_operator("-"), bg=BTN_OP_BG, fg=BTN_OP_FG)
        self.make_button("+", 3, 3, command=lambda: self.append_operator("+"), bg=BTN_OP_BG, fg=BTN_OP_FG)
        
        # Bottom row adjustment
        # Re-map 0 and .
        # 0 at (4,0)
        self.make_button("0", 4, 0, command=lambda: self.add_to_expression(0))
        # . at (4,1)
        self.make_button(".", 4, 1, command=lambda: self.add_to_expression("."))
        # Backspace at (4,2)
        self.make_button("\u232B", 4, 2, command=self.backspace, bg=BTN_NUM_BG, fg=BTN_NUM_FG)
        # Equals at (4,3)
        self.make_button("=", 4, 3, command=self.evaluate, bg=BTN_ACCENT_BG, fg=BTN_ACCENT_FG)

    # --- Scientific UI ---
    def render_scientific_ui(self):
        # 5 columns for Scientific
        for i in range(6):
            self.buttons_frame.rowconfigure(i, weight=1)
        for i in range(5):
            self.buttons_frame.columnconfigure(i, weight=1)

        # Scientific Functions Row 0 & 1
        sci_ops = [
            ("sin", lambda: self.sci_func("math.sin")),
            ("cos", lambda: self.sci_func("math.cos")),
            ("tan", lambda: self.sci_func("math.tan")),
            ("log", lambda: self.sci_func("math.log10")),
            ("ln", lambda: self.sci_func("math.log")),
            ("(", lambda: self.add_to_expression("(")),
            (")", lambda: self.add_to_expression(")")),
            ("^", lambda: self.append_operator("**")),
            ("\u221A", lambda: self.sci_func("math.sqrt")), # Sqrt
            ("\u03C0", lambda: self.add_to_expression("math.pi")), # Pi
            ("e", lambda: self.add_to_expression("math.e"))
        ]

        # Explicit placement for sci Mode
        # Side panel + Num pad style
        
        # Col 0: Sci functions
        r, c = 0, 0
        for label, cmd in sci_ops:
            self.make_button(label, r, c, command=cmd, bg=BTN_OP_BG, fg=BTN_OP_FG, font=SMALL_FONT_STYLE)
            c += 1
            if c > 4:
                c = 0
                r += 1

        # Use remaining space for Numpad
        # Reset Row Index for keypad
        start_row = 3
        
        # Standard Digit Pad Logic shifted down
        digits = {
            7: (start_row, 0), 8: (start_row, 1), 9: (start_row, 2),
            4: (start_row+1, 0), 5: (start_row+1, 1), 6: (start_row+1, 2),
            1: (start_row+2, 0), 2: (start_row+2, 1), 3: (start_row+2, 2),
            0: (start_row+3, 1), '.': (start_row+3, 0) # 0 at 1, . at 0
        }
        
        for digit, grid_pos in digits.items():
             self.make_button(str(digit), grid_pos[0], grid_pos[1], command=lambda x=digit: self.add_to_expression(x))

        # Operators Column (Col 3, 4)
        ops = ["/", "*", "-", "+"]
        for i, op in enumerate(ops):
            self.make_button(op, start_row + i, 3, command=lambda x=op: self.append_operator(x), bg=BTN_OP_BG, fg=BTN_OP_FG)
            
        # AC, Del, Allocations
        self.make_button("AC", start_row, 4, command=self.clear, bg=BTN_ACCENT_BG, fg=BTN_ACCENT_FG)
        self.make_button("DEL", start_row+1, 4, command=self.backspace, bg=BTN_OP_BG, fg=BTN_OP_FG)
        self.make_button("=", start_row+2, 4, rowspan=2, command=self.evaluate, bg=BTN_ACCENT_BG, fg=BTN_ACCENT_FG)

    # --- Converter UI ---
    def render_converter_ui(self):
        # 1. Type Selector (Length, Weight, Currency)
        # 2. From Unit -> To Unit
        # 3. Input -> Output
        
        control_frame = tk.Frame(self.buttons_frame, bg=BG_COLOR)
        control_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Conv Type
        tk.Label(control_frame, text="Conversion Type:", bg=BG_COLOR, font=SMALL_FONT_STYLE).pack(anchor="w")
        self.conv_type = ttk.Combobox(control_frame, values=["Length", "Weight", "Currency"], state="readonly", font=SMALL_FONT_STYLE)
        self.conv_type.set("Length")
        self.conv_type.pack(fill="x", pady=(0, 20))
        self.conv_type.bind("<<ComboboxSelected>>", self.refresh_converter_options)
        
        # Units Frame
        units_frame = tk.Frame(control_frame, bg=BG_COLOR)
        units_frame.pack(fill="x", pady=10)
        
        self.unit_from = ttk.Combobox(units_frame, values=[], state="readonly", font=SMALL_FONT_STYLE, width=10)
        self.unit_from.pack(side="left", expand=True, fill="x", padx=(0,5))
        
        tk.Label(units_frame, text="to", bg=BG_COLOR).pack(side="left")
        
        self.unit_to = ttk.Combobox(units_frame, values=[], state="readonly", font=SMALL_FONT_STYLE, width=10)
        self.unit_to.pack(side="left", expand=True, fill="x", padx=(5,0))
        
        # Bind events
        self.unit_from.bind("<<ComboboxSelected>>", self.convert)
        self.unit_to.bind("<<ComboboxSelected>>", self.convert)
        
        # Numeric Pad for Converter (Since content area is different)
        # We need a numeric pad to input into "current_expression" (which acts as Input)
        # and we display Result in "total_expression" (as Output)
        
        # Re-use standard keypad logic but inside a frame below controls?
        # Or just use the existing keypad area?
        # Let's build a mini-keypad at bottom of control_frame
        
        keypad_frame = tk.Frame(self.buttons_frame, bg=BG_COLOR)
        keypad_frame.pack(fill="both", expand=True)
        
        for i in range(4): keypad_frame.rowconfigure(i, weight=1)
        for i in range(3): keypad_frame.columnconfigure(i, weight=1)
        
        digits = [
            (7,0,0), (8,0,1), (9,0,2),
            (4,1,0), (5,1,1), (6,1,2),
            (1,2,0), (2,2,1), (3,2,2),
            ('.',3,0), (0,3,1), ('DEL',3,2)
        ]
        
        for val, r, c in digits:
            cmd = self.backspace if val == 'DEL' else lambda x=val: self.add_to_expression_conv(x)
            btn = tk.Button(keypad_frame, text=str(val), font=DIGITS_FONT_STYLE, bg=BTN_NUM_BG, fg=BTN_NUM_FG,
                            activebackground=BG_COLOR, relief=tk.FLAT, command=cmd)
            btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
            
        self.refresh_converter_options()

    def refresh_converter_options(self, event=None):
        ctype = self.conv_type.get()
        values = []
        if ctype == "Length":
            values = ["m", "km", "ft", "mi", "cm", "inch"]
        elif ctype == "Weight":
            values = ["kg", "g", "lb", "oz"]
        elif ctype == "Currency":
            values = list(self.currency_rates.keys()) if self.currency_rates else ["USD", "EUR", "GBP", "JPY", "INR"]
            
        self.unit_from['values'] = values
        self.unit_to['values'] = values
        
        if values:
            self.unit_from.current(0)
            self.unit_to.current(1 if len(values) > 1 else 0)
            
        self.convert()

    def add_to_expression_conv(self, value):
        if value == '.' and '.' in self.current_expression:
            return
        self.current_expression += str(value)
        self.update_label()
        self.convert()
        
    def convert(self, event=None):
        try:
            val = float(self.current_expression) if self.current_expression else 0
            ctype = self.conv_type.get()
            u_from = self.unit_from.get()
            u_to = self.unit_to.get()
            
            result = 0
            
            if ctype == "Length":
                # Base unit: meter
                to_m = {"m":1, "km":1000, "ft":0.3048, "mi":1609.34, "cm":0.01, "inch":0.0254}
                val_m = val * to_m.get(u_from, 1)
                result = val_m / to_m.get(u_to, 1)
                
            elif ctype == "Weight":
                # Base unit: kg
                to_kg = {"kg":1, "g":0.001, "lb":0.453592, "oz":0.0283495}
                val_kg = val * to_kg.get(u_from, 1)
                result = val_kg / to_kg.get(u_to, 1)
                
            elif ctype == "Currency":
                if self.currency_rates:
                    rate_from = self.currency_rates.get(u_from, 1)
                    rate_to = self.currency_rates.get(u_to, 1)
                    # Convert to base (USD) then to target
                    val_usd = val / rate_from
                    result = val_usd * rate_to
                else:
                     result = 0 # API not loaded
            
            self.total_expression = f"= {result:.4f}"
            self.update_total_label()
            
        except Exception as e:
            self.total_expression = "Error"
            self.update_total_label()

    # --- Helpers ---
    def make_button(self, text, row, col, command, bg=BTN_NUM_BG, fg=BTN_NUM_FG, font=DIGITS_FONT_STYLE, rowspan=1, columnspan=1):
        # Using a Canvas to make rounded buttons would be ideal but complex. 
        # Using standard buttons with padding and specific colors.
        btn = tk.Button(self.buttons_frame, text=text, bg=bg, fg=fg, font=font,
                        borderwidth=0, command=command, activebackground=bg, activeforeground=fg)
        btn.grid(row=row, column=col, rowspan=rowspan, columnspan=columnspan, sticky="nsew", padx=2, pady=2)
        return btn

    def add_to_expression(self, value):
        self.current_expression += str(value)
        self.update_label()

    def append_operator(self, operator):
        self.current_expression += str(operator)
        self.total_expression += self.current_expression
        self.current_expression = ""
        self.update_total_label()
        self.update_label()

    def clear(self):
        self.current_expression = ""
        self.total_expression = ""
        self.update_label()
        self.update_total_label()

    def backspace(self):
        self.current_expression = self.current_expression[:-1]
        self.update_label()
        if self.mode == "Converter":
            self.convert()

    def percent(self):
        try:
            self.current_expression = str(eval(f"{self.current_expression}/100"))
            self.update_label()
        except:
            self.current_expression = "Error"
            self.update_label()

    def brackets(self):
        # Simple toggle logic or just add (
        # For simplicity, let's just add ()
        # Or better: check open count.
        if self.current_expression.count("(") > self.current_expression.count(")"):
             self.add_to_expression(")")
        else:
             self.add_to_expression("(")

    def sci_func(self, func_name):
        self.current_expression += f"{func_name}("
        self.update_label()

    def evaluate(self):
        self.total_expression += self.current_expression
        try:
            # Allow math functions
            self.current_expression = str(eval(self.total_expression, {"__builtins__": None}, {"math": math, "sin": math.sin, "cos": math.cos, "tan": math.tan}))
            self.total_expression = ""
        except Exception as e:
            self.current_expression = "Error"
            print(f"Eval error: {e}")
        finally:
            self.update_label()
            self.update_total_label()

    def update_total_label(self):
        self.total_label.config(text=self.total_expression)

    def update_label(self):
        self.label.config(text=self.current_expression or "0")

    # --- Networking ---
    def fetch_currency_thread(self):
        thread = threading.Thread(target=self._fetch_currency_data, daemon=True)
        thread.start()

    def _fetch_currency_data(self):
        try:
            print("Fetching currency data...")
            with urllib.request.urlopen(CURRENCY_API_URL) as response:
                data = json.loads(response.read().decode())
                self.currency_rates = data.get("rates", {})
                self.currency_last_updated = datetime.now()
                print("Currency data fetched.")
                # If in converter mode, refresh list
                if self.mode == "Converter":
                    self.window.after(0, self.refresh_converter_options)
        except Exception as e:
            print(f"Failed to fetch currency: {e}")
            # Fallback data could be set here
            pass

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    calc = Calculator()
    calc.run()
