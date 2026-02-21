"""
DECORUM - A Two-Player Cooperative House Decorating Game
=========================================================
Premium Edition with fancy graphics, animations, and effects
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import json
import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import re
import math

# ============== GAME DATA ==============

ROOM_NAMES = ["Bathroom", "Bedroom", "Living Room", "Kitchen"]
ROOM_ICONS = ["🚿", "🛏️", "🛋️", "🍳"]

class Color(Enum):
    RED = ("Red", "#FF6B6B", "#FFE8E8", "#C0392B")
    YELLOW = ("Yellow", "#FFD93D", "#FFF9E6", "#F39C12")  
    BLUE = ("Blue", "#6BCBFF", "#E8F6FF", "#2980B9")
    GREEN = ("Green", "#6BCB77", "#E8FFE8", "#27AE60")
    
    @property
    def name_str(self): return self.value[0]
    @property
    def hex_color(self): return self.value[1]
    @property
    def light_hex(self): return self.value[2]
    @property
    def dark_hex(self): return self.value[3]

class Style(Enum):
    MODERN = ("Modern", "◆", "#9B59B6")
    ANTIQUE = ("Antique", "❖", "#E67E22")
    RETRO = ("Retro", "◈", "#1ABC9C")
    UNUSUAL = ("Unusual", "✦", "#E91E63")
    
    @property
    def name_str(self): return self.value[0]
    @property
    def symbol(self): return self.value[1]
    @property
    def color(self): return self.value[2]

class ObjectType(Enum):
    LAMP = ("Lamp", "💡", "#FFE066")
    WALL_HANGING = ("Wall Hanging", "🖼️", "#A29BFE")
    CURIO = ("Curio", "🏺", "#FFEAA7")
    
    @property
    def name_str(self): return self.value[0]
    @property
    def emoji(self): return self.value[1]
    @property
    def bg_color(self): return self.value[2]

@dataclass
class GameObject:
    obj_type: ObjectType
    color: Color
    style: Style
    
    def __str__(self):
        return f"{self.style.name_str} {self.color.name_str} {self.obj_type.name_str}"

@dataclass 
class Room:
    name: str
    icon: str
    wall_color: Color
    lamp: Optional[GameObject] = None
    wall_hanging: Optional[GameObject] = None
    curio: Optional[GameObject] = None
    
    def get_slot(self, obj_type: ObjectType) -> Optional[GameObject]:
        if obj_type == ObjectType.LAMP: return self.lamp
        elif obj_type == ObjectType.WALL_HANGING: return self.wall_hanging
        else: return self.curio
    
    def set_slot(self, obj_type: ObjectType, obj: Optional[GameObject]):
        if obj_type == ObjectType.LAMP: self.lamp = obj
        elif obj_type == ObjectType.WALL_HANGING: self.wall_hanging = obj
        else: self.curio = obj
    
    def is_slot_empty(self, obj_type: ObjectType) -> bool:
        return self.get_slot(obj_type) is None
    
    def get_all_objects(self) -> List[GameObject]:
        return [o for o in [self.lamp, self.wall_hanging, self.curio] if o]
    
    def has_empty_slot(self) -> bool:
        return self.lamp is None or self.wall_hanging is None or self.curio is None

class House:
    def __init__(self):
        self.rooms = [Room(ROOM_NAMES[i], ROOM_ICONS[i], list(Color)[i]) for i in range(4)]
    
    def get_all_objects(self) -> List[GameObject]:
        return [obj for room in self.rooms for obj in room.get_all_objects()]
    
    def count_by_color(self, color: Color) -> int:
        return sum(1 for obj in self.get_all_objects() if obj.color == color)
    
    def count_by_style(self, style: Style) -> int:
        return sum(1 for obj in self.get_all_objects() if obj.style == style)
    
    def count_walls_by_color(self, color: Color) -> int:
        return sum(1 for room in self.rooms if room.wall_color == color)
    
    def room_has_color(self, room_idx: int, color: Color) -> bool:
        return any(obj.color == color for obj in self.rooms[room_idx].get_all_objects())
    
    def room_has_style(self, room_idx: int, style: Style) -> bool:
        return any(obj.style == style for obj in self.rooms[room_idx].get_all_objects())

# ============== CONDITIONS ==============

class Condition:
    def check(self, house: House) -> bool: raise NotImplementedError
    def __str__(self): raise NotImplementedError

class MinObjectsOfColor(Condition):
    def __init__(self, color: Color, count: int):
        self.color, self.count = color, count
    def check(self, house: House) -> bool:
        return house.count_by_color(self.color) >= self.count
    def __str__(self):
        return f"At least {self.count} {self.color.name_str} object(s)"

class MaxObjectsOfColor(Condition):
    def __init__(self, color: Color, count: int):
        self.color, self.count = color, count
    def check(self, house: House) -> bool:
        return house.count_by_color(self.color) <= self.count
    def __str__(self):
        return f"At most {self.count} {self.color.name_str} object(s)"

class NoObjectsOfColor(Condition):
    def __init__(self, color: Color):
        self.color = color
    def check(self, house: House) -> bool:
        return house.count_by_color(self.color) == 0
    def __str__(self):
        return f"No {self.color.name_str} objects in house"

class MinObjectsOfStyle(Condition):
    def __init__(self, style: Style, count: int):
        self.style, self.count = style, count
    def check(self, house: House) -> bool:
        return house.count_by_style(self.style) >= self.count
    def __str__(self):
        return f"At least {self.count} {self.style.name_str} object(s)"

class AllStylesPresent(Condition):
    def check(self, house: House) -> bool:
        return all(house.count_by_style(s) > 0 for s in Style)
    def __str__(self):
        return "All 4 styles must be present"

class RoomHasColor(Condition):
    def __init__(self, room_idx: int, room_name: str, color: Color):
        self.room_idx, self.room_name, self.color = room_idx, room_name, color
    def check(self, house: House) -> bool:
        return house.room_has_color(self.room_idx, self.color)
    def __str__(self):
        return f"{self.room_name}: needs {self.color.name_str} object"

class RoomHasStyle(Condition):
    def __init__(self, room_idx: int, room_name: str, style: Style):
        self.room_idx, self.room_name, self.style = room_idx, room_name, style
    def check(self, house: House) -> bool:
        return house.room_has_style(self.room_idx, self.style)
    def __str__(self):
        return f"{self.room_name}: needs {self.style.name_str} object"

class RoomHasObjectType(Condition):
    def __init__(self, room_idx: int, room_name: str, obj_type: ObjectType):
        self.room_idx, self.room_name, self.obj_type = room_idx, room_name, obj_type
    def check(self, house: House) -> bool:
        return house.rooms[self.room_idx].get_slot(self.obj_type) is not None
    def __str__(self):
        return f"{self.room_name}: needs a {self.obj_type.name_str}"

class RoomWallColor(Condition):
    def __init__(self, room_idx: int, room_name: str, color: Color):
        self.room_idx, self.room_name, self.color = room_idx, room_name, color
    def check(self, house: House) -> bool:
        return house.rooms[self.room_idx].wall_color == self.color
    def __str__(self):
        return f"{self.room_name}: walls must be {self.color.name_str}"

class EveryRoomHasType(Condition):
    def __init__(self, obj_type: ObjectType):
        self.obj_type = obj_type
    def check(self, house: House) -> bool:
        return all(room.get_slot(self.obj_type) is not None for room in house.rooms)
    def __str__(self):
        return f"Every room needs a {self.obj_type.name_str}"

def generate_random_conditions(count_per_player: int = 3):
    all_conditions = []
    for color in Color:
        all_conditions.append(MinObjectsOfColor(color, random.randint(1, 3)))
    for style in Style:
        all_conditions.append(MinObjectsOfStyle(style, random.randint(1, 2)))
    for i, room_name in enumerate(ROOM_NAMES):
        for color in Color:
            all_conditions.append(RoomHasColor(i, room_name, color))
            all_conditions.append(RoomWallColor(i, room_name, color))
        for obj_type in ObjectType:
            all_conditions.append(RoomHasObjectType(i, room_name, obj_type))
    random.shuffle(all_conditions)
    return all_conditions[:count_per_player], all_conditions[count_per_player:count_per_player*2]

def parse_condition_text(text: str) -> Optional[Condition]:
    text = text.strip().lower()
    room_map = {name.lower(): i for i, name in enumerate(ROOM_NAMES)}
    colors = {c.name_str.lower(): c for c in Color}
    styles = {s.name_str.lower(): s for s in Style}
    types = {t.name_str.lower(): t for t in ObjectType}
    types["wall hanging"] = ObjectType.WALL_HANGING
    
    m = re.search(r"at least (\d+) (\w+) object", text)
    if m:
        count, what = int(m.group(1)), m.group(2)
        if what in colors: return MinObjectsOfColor(colors[what], count)
        if what in styles: return MinObjectsOfStyle(styles[what], count)
    
    m = re.search(r"no (\w+) objects? in house", text)
    if m and m.group(1) in colors:
        return NoObjectsOfColor(colors[m.group(1)])
    
    for room_name, room_idx in room_map.items():
        if room_name in text:
            for color_name, color in colors.items():
                if f"must have a {color_name} object" in text:
                    return RoomHasColor(room_idx, ROOM_NAMES[room_idx], color)
                if f"walls must be {color_name}" in text:
                    return RoomWallColor(room_idx, ROOM_NAMES[room_idx], color)
            for type_name, obj_type in types.items():
                if f"must have a {type_name}" in text:
                    return RoomHasObjectType(room_idx, ROOM_NAMES[room_idx], obj_type)
    
    for type_name, obj_type in types.items():
        if f"every room must have a {type_name}" in text:
            return EveryRoomHasType(obj_type)
    
    return None

# Valid object combinations per rulebook (12 total)
VALID_OBJECTS_MAP = {
    ObjectType.LAMP: {
        Style.MODERN: Color.BLUE,
        Style.ANTIQUE: Color.YELLOW,
        Style.RETRO: Color.RED,
        Style.UNUSUAL: Color.GREEN,
    },
    ObjectType.WALL_HANGING: {
        Style.MODERN: Color.RED,
        Style.ANTIQUE: Color.GREEN,
        Style.RETRO: Color.BLUE,
        Style.UNUSUAL: Color.YELLOW,
    },
    ObjectType.CURIO: {
        Style.MODERN: Color.GREEN,
        Style.ANTIQUE: Color.BLUE,
        Style.RETRO: Color.YELLOW,
        Style.UNUSUAL: Color.RED,
    },
}

def is_valid_object(obj_type: ObjectType, color: Color, style: Style) -> bool:
    return VALID_OBJECTS_MAP.get(obj_type, {}).get(style) == color

def contrast_text_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    luminance = (0.299 * r) + (0.587 * g) + (0.114 * b)
    return "#2B2B2B" if luminance > 160 else "#FFFFFF"

ALL_OBJECTS = [
    GameObject(obj_type, VALID_OBJECTS_MAP[obj_type][style], style)
    for obj_type in ObjectType
    for style in Style
]

# ============== PREMIUM GUI ==============

class StyledButton(tk.Button):
    """Styled button with hover effects"""
    def __init__(self, parent, text="", command=None, bg_color="#6C5CE7", 
                 hover_color="#5B4ED1", fg_color="white", font_size=12, 
                 icon="", padx=20, pady=10, **kwargs):
        display_text = f"{icon}  {text}" if icon else text
        super().__init__(parent, text=display_text, font=("Segoe UI", font_size, "bold"),
                        bg=bg_color, fg=fg_color, relief=tk.FLAT,
                        activebackground=hover_color, activeforeground=fg_color,
                        cursor="hand2", command=command, padx=padx, pady=pady, **kwargs)
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        self.bind("<Enter>", lambda e: self.configure(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.configure(bg=self.bg_color))


class DecorumGame:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ DECORUM ✨")
        self.root.geometry("1500x950")
        self.root.configure(bg="#FAF3E8")
        self.root.resizable(True, True)
        
        self.house = House()
        self.current_player = 0
        self.player_names = ["Player 1", "Player 2"]
        self.player_conditions = [[], []]
        self.selected_room = None
        self.selected_slot = None
        self.turn_count = 0
        self.max_turns = None
        self.heart_to_heart_used = 0
        self.max_heart_to_heart = 3
        self.last_reactions = [None, None]  # Track reactions
        self.action_taken_this_turn = False  # Track if player took action
        self.waiting_for_reaction = False    # Track if waiting for partner reaction
        self.last_action = None              # Track last action for undo
        self.room_borders = {}
        self.room_glows = {}
        self.slot_containers = {}
        self.selection_labels = {}
        self.reaction_label = None
        
        # Pastel color palette (inspired by Decorum game)
        self.THEME = {
            'bg': '#FAF3E8',           # Warm cream background
            'bg_alt': '#F5EDE0',       # Slightly darker cream
            'panel': '#FFFFFF',         # White panels
            'panel_shadow': '#E8DFD0',  # Soft shadow
            'accent_coral': '#FF8A80',   # Soft coral
            'accent_mint': '#80CBC4',    # Soft mint
            'accent_lavender': '#B39DDB', # Soft lavender
            'accent_peach': '#FFAB91',   # Soft peach
            'accent_gold': '#FFD54F',    # Warm gold
            'accent_rose': '#F48FB1',    # Soft rose
            'text_dark': '#4A4A4A',      # Dark text
            'text_medium': '#757575',    # Medium text
            'text_light': '#9E9E9E',     # Light text
            'success': '#81C784',        # Success green
            'warning': '#FFB74D',        # Warning orange
            'error': '#E57373',          # Error red
            'border': '#E0D5C5',         # Soft border
        }
        
        # Player colors (coral for P1, sky blue for P2)
        self.player_colors = ['#FF8A80', '#81D4FA']
        self.player_dark_colors = ['#E57373', '#4FC3F7']
        
        # Room pastel colors
        self.room_colors = [
            {'bg': '#FFE0E0', 'accent': '#FF8A80', 'name': 'Rose'},      # Living Room
            {'bg': '#E0F0FF', 'accent': '#81D4FA', 'name': 'Sky'},       # Bedroom  
            {'bg': '#E8F5E9', 'accent': '#A5D6A7', 'name': 'Mint'},      # Kitchen
            {'bg': '#FFF3E0', 'accent': '#FFCC80', 'name': 'Peach'},     # Bathroom
        ]
        
        self.show_splash_screen()

    def bind_tooltip(self, widget, text_func):
        """Simple tooltip on hover"""
        def on_enter(event):
            if not text_func():
                return
            tip = tk.Toplevel(self.root)
            tip.overrideredirect(True)
            tip.configure(bg="#333333")
            x = event.x_root + 10
            y = event.y_root + 10
            tip.geometry(f"+{x}+{y}")
            label = tk.Label(tip, text=text_func(), font=("Segoe UI", 9),
                            bg="#333333", fg="white", padx=6, pady=4)
            label.pack()
            widget._tooltip = tip
        def on_leave(event):
            tip = getattr(widget, "_tooltip", None)
            if tip:
                tip.destroy()
                widget._tooltip = None
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def show_splash_screen(self):
        """Animated splash screen with warm aesthetics"""
        self.splash = tk.Frame(self.root, bg=self.THEME['bg'])
        self.splash.pack(fill=tk.BOTH, expand=True)
        
        # Centered content
        center = tk.Frame(self.splash, bg=self.THEME['bg'])
        center.place(relx=0.5, rely=0.5, anchor='center')
        
        # House icon with decorative elements
        tk.Label(center, text="🏠", font=("Segoe UI", 96),
                bg=self.THEME['bg'], fg=self.THEME['accent_coral']).pack()
        
        tk.Label(center, text="D E C O R U M", font=("Georgia", 52, "bold"),
                bg=self.THEME['bg'], fg=self.THEME['text_dark']).pack(pady=10)
        
        tk.Label(center, text="─── ✿ ───", 
                font=("Segoe UI", 18), bg=self.THEME['bg'], 
                fg=self.THEME['accent_lavender']).pack(pady=5)
        
        tk.Label(center, text="A Cooperative Decorating Experience", 
                font=("Georgia", 18, "italic"), bg=self.THEME['bg'], 
                fg=self.THEME['text_medium']).pack(pady=15)
        
        # Decorative icons
        icons_frame = tk.Frame(center, bg=self.THEME['bg'])
        icons_frame.pack(pady=30)
        for icon in ["💡", "🖼️", "🏺", "🎨"]:
            tk.Label(icons_frame, text=icon, font=("Segoe UI", 28),
                    bg=self.THEME['bg']).pack(side=tk.LEFT, padx=15)
        
        # Loading animation
        self.loading_label = tk.Label(center, text="● ○ ○", 
                                     font=("Segoe UI", 18),
                                     bg=self.THEME['bg'], fg=self.THEME['accent_mint'])
        self.loading_label.pack(pady=30)
        self.animate_loading(0)
        
        self.root.after(2500, self.show_setup)
    
    def animate_loading(self, count):
        if hasattr(self, 'splash') and self.splash.winfo_exists():
            patterns = ["● ○ ○", "○ ● ○", "○ ○ ●", "○ ● ○"]
            self.loading_label.config(text=patterns[count % 4])
            self.root.after(250, lambda: self.animate_loading(count + 1))
    
    def show_setup(self):
        """Setup screen with warm pastel styling"""
        if hasattr(self, 'splash'):
            self.splash.destroy()
        
        self.setup_frame = tk.Frame(self.root, bg=self.THEME['bg'])
        self.setup_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header bar
        header = tk.Frame(self.setup_frame, bg=self.THEME['panel'], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🏠 DECORUM", font=("Georgia", 26, "bold"),
                bg=self.THEME['panel'], fg=self.THEME['text_dark']).pack(side=tk.LEFT, padx=30, pady=15)
        
        tk.Label(header, text="✿ Game Setup", font=("Georgia", 14, "italic"),
                bg=self.THEME['panel'], fg=self.THEME['accent_coral']).pack(side=tk.RIGHT, padx=30, pady=20)
        
        # Soft shadow line
        tk.Frame(self.setup_frame, bg=self.THEME['border'], height=2).pack(fill=tk.X)
        
        # Main content area
        content = tk.Frame(self.setup_frame, bg=self.THEME['bg'])
        content.pack(expand=True, fill=tk.BOTH, padx=60, pady=40)
        
        # Players Card
        players_card = tk.Frame(content, bg=self.THEME['panel'], padx=50, pady=35,
                               highlightbackground=self.THEME['border'], highlightthickness=1)
        players_card.pack(pady=20)
        
        tk.Label(players_card, text="👥 Players", font=("Georgia", 18, "bold"),
                bg=self.THEME['panel'], fg=self.THEME['text_dark']).pack(anchor='w', pady=(0,20))
        
        # Player 1
        p1_frame = tk.Frame(players_card, bg=self.THEME['panel'])
        p1_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(p1_frame, text="🔴", font=("Segoe UI", 16),
                bg=self.THEME['panel']).pack(side=tk.LEFT)
        tk.Label(p1_frame, text="Player 1:", font=("Segoe UI", 13),
                bg=self.THEME['panel'], fg=self.player_colors[0], width=10, anchor='w').pack(side=tk.LEFT, padx=(5,10))
        self.p1_entry = tk.Entry(p1_frame, font=("Segoe UI", 13), width=25,
                                bg=self.THEME['bg_alt'], fg=self.THEME['text_dark'],
                                insertbackground=self.THEME['text_dark'], relief=tk.FLAT,
                                highlightbackground=self.THEME['border'], highlightthickness=1)
        self.p1_entry.insert(0, "Alice")
        self.p1_entry.pack(side=tk.LEFT, ipady=10, padx=5)
        
        # Player 2
        p2_frame = tk.Frame(players_card, bg=self.THEME['panel'])
        p2_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(p2_frame, text="🔵", font=("Segoe UI", 16),
                bg=self.THEME['panel']).pack(side=tk.LEFT)
        tk.Label(p2_frame, text="Player 2:", font=("Segoe UI", 13),
                bg=self.THEME['panel'], fg=self.player_colors[1], width=10, anchor='w').pack(side=tk.LEFT, padx=(5,10))
        self.p2_entry = tk.Entry(p2_frame, font=("Segoe UI", 13), width=25,
                                bg=self.THEME['bg_alt'], fg=self.THEME['text_dark'],
                                insertbackground=self.THEME['text_dark'], relief=tk.FLAT,
                                highlightbackground=self.THEME['border'], highlightthickness=1)
        self.p2_entry.insert(0, "Bob")
        self.p2_entry.pack(side=tk.LEFT, ipady=10, padx=5)
        
        # Game Mode Card
        mode_card = tk.Frame(content, bg=self.THEME['panel'], padx=50, pady=35,
                            highlightbackground=self.THEME['border'], highlightthickness=1)
        mode_card.pack(pady=20)
        
        tk.Label(mode_card, text="🎮 Game Mode", font=("Georgia", 18, "bold"),
                bg=self.THEME['panel'], fg=self.THEME['text_dark']).pack(anchor='w', pady=(0,25))
        
        buttons_frame = tk.Frame(mode_card, bg=self.THEME['panel'])
        buttons_frame.pack()
        
        StyledButton(buttons_frame, "Random Conditions", lambda: self.start_game("random"),
                    bg_color=self.THEME['accent_mint'], hover_color="#4DB6AC",
                    fg_color="white", icon="🎲", font_size=12, padx=25, pady=12).pack(side=tk.LEFT, padx=10)
        
        StyledButton(buttons_frame, "Custom Conditions", lambda: self.start_game("custom"),
                    bg_color=self.THEME['accent_lavender'], hover_color="#9575CD",
                    fg_color="white", icon="📝", font_size=12, padx=25, pady=12).pack(side=tk.LEFT, padx=10)
        
        StyledButton(buttons_frame, "Load Scenario", lambda: self.start_game("file"),
                    bg_color=self.THEME['accent_peach'], hover_color="#FF8A65",
                    fg_color="white", icon="📁", font_size=12, padx=25, pady=12).pack(side=tk.LEFT, padx=10)
        
        # How to play hint
        hint_frame = tk.Frame(content, bg=self.THEME['bg_alt'], padx=30, pady=20)
        hint_frame.pack(pady=30, fill=tk.X)
        
        tk.Label(hint_frame, text="💡 How to Play", font=("Georgia", 14, "bold"),
                bg=self.THEME['bg_alt'], fg=self.THEME['text_dark']).pack(anchor='w')
        tk.Label(hint_frame, text="Work together to decorate the house! Each player has secret conditions.\n"
                                  "Use reactions (😊 😐 😠) to hint at how changes affect your conditions.\n"
                                  "You have 30 turns and 3 Heart-to-Hearts to discuss openly.",
                font=("Segoe UI", 11), bg=self.THEME['bg_alt'], fg=self.THEME['text_medium'],
                justify='left').pack(anchor='w', pady=(10,0))
    
    def start_game(self, mode):
        self.player_names = [self.p1_entry.get() or "Player 1", self.p2_entry.get() or "Player 2"]
        self.setup_frame.destroy()
        # Reset game state
        self.house = House()
        self.current_player = 0
        self.turn_count = 0
        self.action_taken_this_turn = False
        self.selected_room = None
        self.selected_slot = None
        self.heart_to_heart_used = 0
        self.last_reactions = [None, None]
        
        if mode == "random":
            self.player_conditions[0], self.player_conditions[1] = generate_random_conditions()
            self.show_conditions_reveal()
        elif mode == "custom":
            self.show_custom_conditions_dialog()
        elif mode == "file":
            self.load_scenario_file()
    
    def show_custom_conditions_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Custom Conditions")
        dialog.geometry("900x780")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 900, 780)
        
        tk.Label(dialog, text="📝 Guided Conditions & Starting Setup", font=("Georgia", 22, "bold"),
                bg=self.THEME['bg'], fg=self.THEME['text_dark']).pack(pady=20)
        
        content = tk.Frame(dialog, bg=self.THEME['bg'])
        content.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable area for both players
        canvas = tk.Canvas(content, bg=self.THEME['bg'], highlightthickness=0)
        scroll = tk.Frame(canvas, bg=self.THEME['bg'])
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0, 0), window=scroll, anchor="nw", width=860)
        scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        colors = {c.name_str: c for c in Color}
        styles = {s.name_str: s for s in Style}
        types = {t.name_str: t for t in ObjectType}
        
        def build_player_section(parent, player_idx):
            section = tk.Frame(parent, bg=self.THEME['panel'], padx=20, pady=15,
                              highlightbackground=self.THEME['border'], highlightthickness=1)
            section.pack(fill=tk.X, padx=40, pady=8)
            
            tk.Label(section, text=f"{'🔴' if player_idx==0 else '🔵'} {self.player_names[player_idx]}'s Conditions",
                    font=("Segoe UI", 13, "bold"), bg=self.THEME['panel'],
                    fg=self.player_colors[player_idx]).pack(anchor='w')
            
            conds = []
            list_frame = tk.Frame(section, bg=self.THEME['bg_alt'])
            list_frame.pack(fill=tk.X, pady=6)
            list_items = []
            
            def refresh():
                for w in list_frame.winfo_children():
                    w.destroy()
                list_items.clear()
                for idx, c in enumerate(conds):
                    chip = tk.Frame(list_frame, bg="#FFFFFF", padx=8, pady=4,
                                   highlightbackground=self.THEME['border'], highlightthickness=1)
                    chip.pack(fill=tk.X, pady=2)
                    icon = "🎯" if isinstance(c, (RoomHasColor, RoomWallColor, RoomHasObjectType)) else "📌"
                    tk.Label(chip, text=icon, font=("Segoe UI", 10),
                            bg="#FFFFFF", fg=self.THEME['text_medium']).pack(side=tk.LEFT, padx=(0,6))
                    tk.Label(chip, text=str(c), font=("Segoe UI", 10),
                            bg="#FFFFFF", fg=self.THEME['text_dark'], anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)
                    tk.Button(chip, text="✕", font=("Segoe UI", 9),
                             bg="#FFFFFF", fg=self.THEME['text_light'],
                             relief=tk.FLAT, command=lambda i=idx: remove_at(i)).pack(side=tk.RIGHT)
                    list_items.append(chip)
            
            def add_cond(cond):
                conds.append(cond)
                refresh()

            def remove_at(i):
                if 0 <= i < len(conds):
                    del conds[i]
                    refresh()
            
            def clear_all():
                conds.clear()
                refresh()
            
            def add_random():
                random_conds = generate_random_conditions()[player_idx]
                conds.extend(random_conds)
                refresh()
            
            btn_row = tk.Frame(section, bg=self.THEME['panel'])
            btn_row.pack(fill=tk.X, pady=(0,8))
            tk.Button(btn_row, text="Clear All", command=clear_all,
                     bg=self.THEME['bg_alt'], fg=self.THEME['text_dark'], relief=tk.FLAT).pack(side=tk.LEFT, padx=4)
            tk.Button(btn_row, text="Add 3 Random", command=add_random,
                     bg=self.THEME['accent_mint'], fg='white', relief=tk.FLAT).pack(side=tk.RIGHT, padx=4)
            
            builder = tk.Frame(section, bg=self.THEME['panel'])
            builder.pack(fill=tk.X, pady=(6,0))
            
            # Room has color object
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="Room has color object:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            room_var = tk.StringVar(value=ROOM_NAMES[0])
            ttk.Combobox(row, textvariable=room_var, values=ROOM_NAMES, state='readonly', width=12).pack(side=tk.LEFT, padx=4)
            color_var = tk.StringVar(value=Color.RED.name_str)
            ttk.Combobox(row, textvariable=color_var, values=list(colors.keys()), state='readonly', width=8).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                RoomHasColor(ROOM_NAMES.index(room_var.get()), room_var.get(), colors[color_var.get()])),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # Room walls must be color
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="Room walls must be color:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            room_var2 = tk.StringVar(value=ROOM_NAMES[0])
            ttk.Combobox(row, textvariable=room_var2, values=ROOM_NAMES, state='readonly', width=12).pack(side=tk.LEFT, padx=4)
            color_var2 = tk.StringVar(value=Color.BLUE.name_str)
            ttk.Combobox(row, textvariable=color_var2, values=list(colors.keys()), state='readonly', width=8).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                RoomWallColor(ROOM_NAMES.index(room_var2.get()), room_var2.get(), colors[color_var2.get()])),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # Room must have object type
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="Room must have object type:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            room_var3 = tk.StringVar(value=ROOM_NAMES[0])
            ttk.Combobox(row, textvariable=room_var3, values=ROOM_NAMES, state='readonly', width=12).pack(side=tk.LEFT, padx=4)
            type_var = tk.StringVar(value=ObjectType.LAMP.name_str)
            ttk.Combobox(row, textvariable=type_var, values=list(types.keys()), state='readonly', width=10).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                RoomHasObjectType(ROOM_NAMES.index(room_var3.get()), room_var3.get(), types[type_var.get()])),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # At least N objects of color
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="At least N objects of color:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            count_var = tk.StringVar(value="2")
            ttk.Combobox(row, textvariable=count_var, values=["1", "2", "3"], state='readonly', width=4).pack(side=tk.LEFT, padx=4)
            color_var3 = tk.StringVar(value=Color.RED.name_str)
            ttk.Combobox(row, textvariable=color_var3, values=list(colors.keys()), state='readonly', width=8).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                MinObjectsOfColor(colors[color_var3.get()], int(count_var.get()))),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # At least N objects of style
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="At least N objects of style:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            count_var2 = tk.StringVar(value="2")
            ttk.Combobox(row, textvariable=count_var2, values=["1", "2"], state='readonly', width=4).pack(side=tk.LEFT, padx=4)
            style_var = tk.StringVar(value=Style.MODERN.name_str)
            ttk.Combobox(row, textvariable=style_var, values=list(styles.keys()), state='readonly', width=10).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                MinObjectsOfStyle(styles[style_var.get()], int(count_var2.get()))),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # No objects of color
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="No objects of color:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            color_var4 = tk.StringVar(value=Color.GREEN.name_str)
            ttk.Combobox(row, textvariable=color_var4, values=list(colors.keys()), state='readonly', width=8).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                NoObjectsOfColor(colors[color_var4.get()])),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # Every room must have type
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="Every room must have type:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            type_var2 = tk.StringVar(value=ObjectType.LAMP.name_str)
            ttk.Combobox(row, textvariable=type_var2, values=list(types.keys()), state='readonly', width=10).pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="Add", command=lambda: add_cond(
                EveryRoomHasType(types[type_var2.get()])),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            # All styles present
            row = tk.Frame(builder, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text="All styles present:", font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).pack(side=tk.LEFT)
            tk.Button(row, text="Add", command=lambda: add_cond(AllStylesPresent()),
                bg=self.THEME['bg_alt'], relief=tk.FLAT).pack(side=tk.RIGHT)
            
            return conds
        
        p1_conditions = build_player_section(scroll, 0)
        p2_conditions = build_player_section(scroll, 1)
        
        # ===== Starting House Setup =====
        setup_card = tk.Frame(scroll, bg=self.THEME['panel'], padx=25, pady=20,
                             highlightbackground=self.THEME['border'], highlightthickness=1)
        setup_card.pack(fill=tk.X, padx=40, pady=10)
        
        tk.Label(setup_card, text="🏠 Starting House Setup (optional)", 
                font=("Segoe UI", 13, "bold"), bg=self.THEME['panel'], 
                fg=self.THEME['text_dark']).pack(anchor='w')
        
        setup_grid = tk.Frame(setup_card, bg=self.THEME['panel'])
        setup_grid.pack(pady=10)
        
        # Build 4 rows (rooms) x wall color + 3 object slots
        setup_vars = {}
        wall_vars = {}
        room_headers = ["Living Room", "Bedroom", "Kitchen", "Bathroom"]
        type_headers = [ObjectType.LAMP, ObjectType.WALL_HANGING, ObjectType.CURIO]
        
        tk.Label(setup_grid, text="", bg=self.THEME['panel']).grid(row=0, column=0, padx=5)
        tk.Label(setup_grid, text="🎨 Wall Color", font=("Segoe UI", 9, "bold"),
                bg=self.THEME['panel'], fg=self.THEME['text_medium']).grid(row=0, column=1, padx=10, pady=5)
        for col, obj_type in enumerate(type_headers, start=2):
            tk.Label(setup_grid, text=f"{obj_type.emoji} {obj_type.name_str}", font=("Segoe UI", 9, "bold"),
                    bg=self.THEME['panel'], fg=self.THEME['text_medium']).grid(row=0, column=col, padx=10, pady=5)
        
        def combo_label(obj_type, style):
            color = VALID_OBJECTS_MAP[obj_type][style]
            return f"{style.name_str} {color.name_str}"
        
        for r, room_name in enumerate(room_headers, start=1):
            tk.Label(setup_grid, text=room_name, font=("Segoe UI", 9),
                    bg=self.THEME['panel'], fg=self.THEME['text_dark']).grid(row=r, column=0, sticky='w', padx=5)
            wall_var = tk.StringVar(value=self.house.rooms[r-1].wall_color.name_str)
            wall_combo = ttk.Combobox(setup_grid, textvariable=wall_var, values=list(colors.keys()),
                                     state='readonly', width=12)
            wall_combo.grid(row=r, column=1, padx=6, pady=3)
            wall_vars[r-1] = wall_var
            for c, obj_type in enumerate(type_headers, start=2):
                var = tk.StringVar(value="Empty")
                values = ["Empty"] + [combo_label(obj_type, s) for s in Style]
                combo = ttk.Combobox(setup_grid, textvariable=var, values=values,
                                    state='readonly', width=16)
                combo.grid(row=r, column=c, padx=6, pady=3)
                setup_vars[(r-1, obj_type)] = var
        
        def apply():
            if not p1_conditions or not p2_conditions:
                messagebox.showwarning("Missing Conditions",
                    "Please add at least 1 condition for each player (or use Add 3 Random).")
                return
            
            self.player_conditions = [list(p1_conditions), list(p2_conditions)]
            
            # Apply wall colors
            for room_idx, var in wall_vars.items():
                self.house.rooms[room_idx].wall_color = colors[var.get()]
            
            # Apply starting setup
            for (room_idx, obj_type), var in setup_vars.items():
                choice = var.get()
                if choice == "Empty":
                    continue
                parts = choice.split()
                style_name, color_name = parts[0], parts[1]
                style = styles[style_name]
                color = colors[color_name]
                if is_valid_object(obj_type, color, style):
                    self.house.rooms[room_idx].set_slot(obj_type, GameObject(obj_type, color, style))
            
            dialog.destroy()
            self.show_conditions_reveal()
            canvas.unbind_all("<MouseWheel>")
        
        StyledButton(dialog, "Start Game", apply,
                    bg_color=self.THEME['accent_mint'], hover_color="#4DB6AC",
                    fg_color="white", icon="▶", font_size=14, padx=40, pady=14).pack(pady=18)
    
    def load_scenario_file(self):
        filename = filedialog.askopenfilename(title="Select Scenario", filetypes=[("JSON", "*.json")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                for line in data.get("player1_conditions", []):
                    cond = parse_condition_text(line)
                    if cond: self.player_conditions[0].append(cond)
                for line in data.get("player2_conditions", []):
                    cond = parse_condition_text(line)
                    if cond: self.player_conditions[1].append(cond)
                if "starting_objects" in data:
                    for obj_data in data["starting_objects"]:
                        room_idx = obj_data.get("room", 0)
                        obj_type = ObjectType[obj_data["type"].upper().replace(" ", "_")]
                        color = Color[obj_data["color"].upper()]
                        style = Style[obj_data["style"].upper()]
                        if is_valid_object(obj_type, color, style):
                            self.house.rooms[room_idx].set_slot(obj_type, GameObject(obj_type, color, style))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
                self.player_conditions[0], self.player_conditions[1] = generate_random_conditions()
        else:
            self.player_conditions[0], self.player_conditions[1] = generate_random_conditions()
        self.show_conditions_reveal()
    
    def show_conditions_reveal(self):
        """Condition reveal with warm styling"""
        for i, name in enumerate(self.player_names):
            reveal = tk.Toplevel(self.root)
            reveal.title(f"{name}'s Conditions")
            reveal.geometry("520x450")
            reveal.configure(bg=self.THEME['bg'])
            reveal.transient(self.root)
            reveal.grab_set()
            self.center_window(reveal, 520, 450)
            
            # Header with player color
            header_color = self.player_colors[i]
            
            tk.Label(reveal, text="🔒", font=("Segoe UI", 52),
                    bg=self.THEME['bg'], fg=header_color).pack(pady=20)
            
            tk.Label(reveal, text=f"{name}'s Secret Conditions", 
                    font=("Georgia", 20, "bold"),
                    bg=self.THEME['bg'], fg=header_color).pack()
            
            tk.Label(reveal, text="─── ✿ ───", 
                    font=("Segoe UI", 14), bg=self.THEME['bg'], 
                    fg=self.THEME['border']).pack(pady=10)
            
            # Conditions card
            cond_frame = tk.Frame(reveal, bg=self.THEME['panel'], padx=35, pady=25,
                                 highlightbackground=self.THEME['border'], highlightthickness=1)
            cond_frame.pack(pady=15, padx=40, fill=tk.X)
            
            for c in self.player_conditions[i]:
                tk.Label(cond_frame, text=f"✦  {c}", font=("Segoe UI", 12),
                        bg=self.THEME['panel'], fg=self.THEME['text_dark'],
                        anchor='w').pack(fill=tk.X, pady=5)
            
            tk.Label(reveal, text="⚠️ Keep this secret from the other player!", 
                    font=("Segoe UI", 11),
                    bg=self.THEME['bg'], fg=self.THEME['error']).pack(pady=15)
            
            StyledButton(reveal, "Got it!", reveal.destroy,
                        bg_color=header_color, hover_color=self.player_dark_colors[i],
                        fg_color="white", font_size=12, padx=30, pady=10).pack(pady=10)
            
            self.root.wait_window(reveal)
        
        self.build_game_ui()
    
    def center_window(self, win, w, h):
        win.update_idletasks()
        x = (win.winfo_screenwidth() - w) // 2
        y = (win.winfo_screenheight() - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")
    
    def build_game_ui(self):
        """Build the main game interface with improved UX"""
        for w in self.root.winfo_children():
            w.destroy()
        
        # ===== HEADER BAR =====
        header = tk.Frame(self.root, bg=self.THEME['panel'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Logo
        logo_frame = tk.Frame(header, bg=self.THEME['panel'])
        logo_frame.pack(side=tk.LEFT, padx=25)
        tk.Label(logo_frame, text="🏠", font=("Segoe UI", 32),
                bg=self.THEME['panel']).pack(side=tk.LEFT)
        tk.Label(logo_frame, text="DECORUM", font=("Georgia", 24, "bold"),
                bg=self.THEME['panel'], fg=self.THEME['text_dark']).pack(side=tk.LEFT, padx=10)
        
        # Round counter (increments after both players)
        turn_frame = tk.Frame(header, bg=self.THEME['bg_alt'], padx=20, pady=8)
        turn_frame.pack(side=tk.LEFT, padx=30)
        round_count = (self.turn_count // 2) + 1
        tk.Label(turn_frame, text=f"⏱ Round {round_count}",
                font=("Segoe UI", 12, "bold"), bg=self.THEME['bg_alt'], fg=self.THEME['success']).pack()
        tk.Label(turn_frame, text=f"Actions taken: {self.turn_count}",
                font=("Segoe UI", 9), bg=self.THEME['bg_alt'], fg=self.THEME['text_medium']).pack()
        
        # Heart-to-heart counter
        hth_frame = tk.Frame(header, bg=self.THEME['bg_alt'], padx=15, pady=8)
        hth_frame.pack(side=tk.LEFT, padx=5)
        hearts_left = self.max_heart_to_heart - self.heart_to_heart_used
        heart_icons = "❤️" * hearts_left + "🤍" * self.heart_to_heart_used
        tk.Label(hth_frame, text=f"Heart-to-Heart: {heart_icons}",
                font=("Segoe UI", 11), bg=self.THEME['bg_alt'], fg=self.THEME['text_medium']).pack()
        
        # Current player indicator (prominent)
        player_indicator = tk.Frame(header, bg=self.player_colors[self.current_player], padx=25, pady=12)
        player_indicator.pack(side=tk.RIGHT, padx=25, pady=15)
        
        player_emoji = "🔴" if self.current_player == 0 else "🔵"
        tk.Label(player_indicator, text=f"{player_emoji} {self.player_names[self.current_player]}'s Turn",
                font=("Segoe UI", 14, "bold"), bg=self.player_colors[self.current_player], fg='white').pack()
        
        # Shadow line
        tk.Frame(self.root, bg=self.THEME['border'], height=2).pack(fill=tk.X)
        
        # ===== MAIN CONTENT =====
        main = tk.Frame(self.root, bg=self.THEME['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== LEFT: HOUSE PANEL =====
        house_panel = tk.Frame(main, bg=self.THEME['panel'],
                              highlightbackground=self.THEME['border'], highlightthickness=1)
        house_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,15))
        
        # House header
        house_header = tk.Frame(house_panel, bg=self.THEME['panel'])
        house_header.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(house_header, text="🏡 The House", font=("Georgia", 18, "bold"),
                bg=self.THEME['panel'], fg=self.THEME['text_dark']).pack(side=tk.LEFT)
        
        # Selection info in header
        if self.selected_room is not None:
            room = self.house.rooms[self.selected_room]
            sel_text = f"Selected: {room.name}"
            if self.selected_slot:
                obj = room.get_slot(self.selected_slot)
                sel_text += f" → {self.selected_slot.name_str}"
                if obj:
                    sel_text += f" ({obj.color.name_str} {obj.style.name_str})"
            tk.Label(house_header, text=sel_text, font=("Segoe UI", 11),
                    bg=self.THEME['panel'], fg=self.THEME['accent_coral']).pack(side=tk.RIGHT)
        else:
            tk.Label(house_header, text="Click a room to select it",
                    font=("Segoe UI", 11), bg=self.THEME['panel'], 
                    fg=self.THEME['text_light']).pack(side=tk.RIGHT)
        
        # Rooms grid (2x2)
        rooms_frame = tk.Frame(house_panel, bg=self.THEME['panel'])
        rooms_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5,20))
        
        self.room_borders.clear()
        self.room_glows.clear()
        for i, room in enumerate(self.house.rooms):
            row, col = i // 2, i % 2
            room_card = self.create_room_card(rooms_frame, room, i)
            room_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        rooms_frame.grid_columnconfigure(0, weight=1)
        rooms_frame.grid_columnconfigure(1, weight=1)
        rooms_frame.grid_rowconfigure(0, weight=1)
        rooms_frame.grid_rowconfigure(1, weight=1)
        
        # ===== RIGHT: CONTROL PANEL =====
        control = tk.Frame(main, bg=self.THEME['panel'], width=320,
                          highlightbackground=self.THEME['border'], highlightthickness=1)
        control.pack(side=tk.RIGHT, fill=tk.Y)
        control.pack_propagate(False)
        
        # Scrollable control area
        control_canvas = tk.Canvas(control, bg=self.THEME['panel'], highlightthickness=0)
        control_scroll = tk.Frame(control_canvas, bg=self.THEME['panel'])
        
        control_canvas.pack(fill=tk.BOTH, expand=True)
        control_canvas.create_window((0, 0), window=control_scroll, anchor="nw", width=318)
        
        # ===== TURN STATE INDICATOR =====
        if self.action_taken_this_turn:
            # Action taken - show waiting for reaction / end turn
            state_frame = tk.Frame(control_scroll, bg=self.THEME['accent_gold'], padx=15, pady=15)
            state_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(state_frame, text="✓ Action Complete!", font=("Georgia", 14, "bold"),
                    bg=self.THEME['accent_gold'], fg=self.THEME['text_dark']).pack()
            tk.Label(state_frame, text=f"Partner ({self.player_names[1-self.current_player]}) may react,\nthen end your turn.",
                    font=("Segoe UI", 10), bg=self.THEME['accent_gold'], 
                    fg=self.THEME['text_dark'], justify='center').pack(pady=(5,0))
            
            StyledButton(state_frame, "↩ Undo Last Action", self.undo_last_action,
                        bg_color=self.THEME['accent_rose'], hover_color="#EC407A",
                        fg_color="white", font_size=10, padx=12, pady=6).pack(pady=(8,0))
        else:
            # Current Selection Card (compact)
            sel_card = tk.Frame(control_scroll, bg=self.room_colors[self.selected_room]['bg'] if self.selected_room is not None else self.THEME['bg_alt'],
                               padx=15, pady=12)
            sel_card.pack(fill=tk.X, padx=10, pady=10)
            
            if self.selected_room is not None:
                room = self.house.rooms[self.selected_room]
                header_row = tk.Frame(sel_card, bg=sel_card.cget('bg'))
                header_row.pack(fill=tk.X)
                tk.Label(header_row, text=room.icon, font=("Segoe UI", 28),
                        bg=sel_card.cget('bg')).pack(side=tk.LEFT)
                name_label = tk.Label(header_row, text=room.name, font=("Georgia", 14, "bold"),
                        bg=sel_card.cget('bg'), fg=self.THEME['text_dark'])
                name_label.pack(side=tk.LEFT, padx=8)
                
                # Deselect button
                desel_btn = tk.Button(header_row, text="✕", font=("Segoe UI", 10),
                                     bg=sel_card.cget('bg'), fg=self.THEME['text_light'],
                                     relief=tk.FLAT, cursor='hand2', bd=0,
                                     command=self.deselect_room)
                desel_btn.pack(side=tk.RIGHT)
                
                wall_label = tk.Label(header_row, text=f"🎨{room.wall_color.name_str}",
                        font=("Segoe UI", 9), bg=sel_card.cget('bg'),
                        fg=self.THEME['text_medium'])
                wall_label.pack(side=tk.RIGHT, padx=10)
                
                if self.selected_slot:
                    obj = room.get_slot(self.selected_slot)
                    slot_text = f"{self.selected_slot.emoji} {self.selected_slot.name_str}"
                    if obj:
                        slot_text += f" • {obj.color.name_str} {obj.style.name_str}"
                    slot_label = tk.Label(sel_card, text=slot_text, font=("Segoe UI", 10),
                            bg=sel_card.cget('bg'), fg=self.THEME['text_medium'])
                    slot_label.pack(anchor='w', pady=(5,0))
                    self.selection_labels["slot"] = slot_label
                self.selection_labels["room"] = name_label
                self.selection_labels["wall"] = wall_label
            else:
                empty_label = tk.Label(sel_card, text="📍 Click a room to select", font=("Segoe UI", 11),
                        bg=sel_card.cget('bg'), fg=self.THEME['text_light'])
                empty_label.pack()
                tk.Label(sel_card, text="(1 action per turn)", font=("Segoe UI", 9),
                        bg=sel_card.cget('bg'), fg=self.THEME['text_light']).pack()
                self.selection_labels["empty"] = empty_label
        
        # ===== END TURN - ALWAYS VISIBLE =====
        end_frame = tk.Frame(control_scroll, bg=self.player_colors[self.current_player], padx=3, pady=3)
        end_frame.pack(fill=tk.X, padx=10, pady=(5,10))
        
        end_text = f"⏭️  END TURN" if not self.action_taken_this_turn else f"⏭️  END TURN (Done!)"
        StyledButton(end_frame, end_text, self.end_turn,
                    bg_color=self.player_colors[self.current_player],
                    hover_color=self.player_dark_colors[self.current_player],
                    fg_color="white", font_size=12, padx=15, pady=10).pack(fill=tk.X)
        
        # ===== ACTIONS SECTION =====
        if self.action_taken_this_turn:
            # Actions disabled - show grayed out
            tk.Label(control_scroll, text="─── Action Used ───", font=("Georgia", 11),
                    bg=self.THEME['panel'], fg=self.THEME['text_light']).pack(pady=(5,8))
            
            disabled_frame = tk.Frame(control_scroll, bg='#E0E0E0', padx=10, pady=15)
            disabled_frame.pack(fill=tk.X, padx=10)
            tk.Label(disabled_frame, text="1 action per turn\n(already taken)", font=("Segoe UI", 10),
                    bg='#E0E0E0', fg='#999999', justify='center').pack()
        else:
            # Actions available
            tk.Label(control_scroll, text="─── Actions (pick 1) ───", font=("Georgia", 11),
                    bg=self.THEME['panel'], fg=self.THEME['text_light']).pack(pady=(5,8))
            
            actions_frame = tk.Frame(control_scroll, bg=self.THEME['panel'])
            actions_frame.pack(fill=tk.X, padx=10)
            
            # 2x2 grid for actions
            action_row1 = tk.Frame(actions_frame, bg=self.THEME['panel'])
            action_row1.pack(fill=tk.X, pady=2)
            action_row2 = tk.Frame(actions_frame, bg=self.THEME['panel'])
            action_row2.pack(fill=tk.X, pady=2)
            
            StyledButton(action_row1, "➕ Add", self.action_add,
                        bg_color=self.THEME['success'], hover_color="#66BB6A",
                        fg_color="white", font_size=10, padx=8, pady=6).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            StyledButton(action_row1, "➖ Remove", self.action_remove,
                        bg_color=self.THEME['error'], hover_color="#EF5350",
                        fg_color="white", font_size=10, padx=8, pady=6).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            
            StyledButton(action_row2, "🔄 Swap", self.action_swap,
                        bg_color=self.THEME['accent_lavender'], hover_color="#9575CD",
                        fg_color="white", font_size=10, padx=8, pady=6).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            StyledButton(action_row2, "🎨 Paint", self.action_paint,
                        bg_color=self.THEME['accent_peach'], hover_color="#FF8A65",
                        fg_color="white", font_size=10, padx=8, pady=6).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # ===== REACTIONS SECTION =====
        tk.Label(control_scroll, text="─── Reactions ───", font=("Georgia", 11),
                bg=self.THEME['panel'], fg=self.THEME['text_light']).pack(pady=(12,8))
        
        react_frame = tk.Frame(control_scroll, bg=self.THEME['panel'])
        react_frame.pack()
        
        # Reactions are for the OTHER player after action is taken
        reactions = [("😊", "happy", self.THEME['success']), 
                    ("😐", "neutral", "#BDBDBD"), 
                    ("😠", "unhappy", self.THEME['error'])]
        
        for emoji, reaction, color in reactions:
            btn = tk.Button(react_frame, text=emoji, font=("Segoe UI", 22), width=3,
                           bg=self.THEME['bg_alt'], fg=self.THEME['text_dark'],
                           relief=tk.FLAT, cursor='hand2', bd=0,
                           activebackground=color,
                           command=lambda r=reaction: self.react(r))
            btn.pack(side=tk.LEFT, padx=6)
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.configure(bg=c))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.THEME['bg_alt']))
        
        # Reaction hint / persistent indicator
        if self.action_taken_this_turn:
            tk.Label(control_scroll, text=f"👆 {self.player_names[1-self.current_player]}: React to the change!",
                    font=("Segoe UI", 9, "bold"), bg=self.THEME['panel'],
                    fg=self.THEME['accent_coral']).pack(pady=(5,0))
        if self.last_reactions[1-self.current_player]:
            react_emoji = {"happy": "😊", "neutral": "😐", "unhappy": "😠"}
            last_r = self.last_reactions[1-self.current_player]
            self.reaction_label = tk.Label(control_scroll, text=f"Partner reaction: {react_emoji.get(last_r, '')}",
                    font=("Segoe UI", 11, "bold"), bg=self.THEME['panel'],
                    fg=self.THEME['accent_coral'])
            self.reaction_label.pack(pady=(6,0))
        
        # Game Actions Section  
        tk.Label(control_scroll, text="───────────", font=("Georgia", 10),
                bg=self.THEME['panel'], fg=self.THEME['text_light']).pack(pady=8)
        
        game_actions = tk.Frame(control_scroll, bg=self.THEME['panel'])
        game_actions.pack(fill=tk.X, padx=10)
        
        StyledButton(game_actions, "👁️ My Conditions", self.show_my_conditions,
                    bg_color=self.THEME['bg_alt'], hover_color=self.THEME['border'],
                    fg_color=self.THEME['text_dark'], font_size=10, padx=10, pady=5).pack(fill=tk.X, pady=2)
        
        StyledButton(game_actions, "💕 Heart-to-Heart", self.heart_to_heart,
                    bg_color=self.THEME['accent_rose'], hover_color="#EC407A",
                    fg_color="white", font_size=10, padx=10, pady=5).pack(fill=tk.X, pady=2)
        
        StyledButton(game_actions, "✓ Check Win", self.check_win,
                    bg_color=self.THEME['accent_gold'], hover_color="#FFC107",
                    fg_color=self.THEME['text_dark'], font_size=10, padx=10, pady=6).pack(fill=tk.X, pady=4)
    
    def create_room_card(self, parent, room, idx):
        """Create a simple, space-efficient room card"""
        is_selected = (idx == self.selected_room)

        border_color = room.wall_color.hex_color
        border_width = 5 if is_selected else 3

        shadow = tk.Frame(parent, bg="#D8D1C6")
        outer = tk.Frame(shadow, bg=border_color, padx=border_width, pady=border_width)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.room_borders[idx] = outer

        card_bg = room.wall_color.light_hex
        header_bg = room.wall_color.dark_hex

        card = tk.Frame(outer, bg=card_bg)
        card.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(card, bg=header_bg, height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=f"{room.icon} {room.name}", font=("Georgia", 11, "bold"),
                bg=header_bg, fg="white").pack(side=tk.LEFT, padx=10)
        tk.Label(header, text=f"● {room.wall_color.name_str}", font=("Segoe UI", 9, "bold"),
                bg=header_bg, fg="white").pack(side=tk.RIGHT, padx=10)

        for w in [header] + list(header.winfo_children()):
            w.bind("<Button-1>", lambda e, i=idx: self.select_room(i))
            w.configure(cursor="hand2")

        if is_selected:
            glow = tk.Frame(card, bg=self.THEME['accent_gold'], height=3)
            glow.pack(fill=tk.X)
            self.room_glows[idx] = glow

        body = tk.Frame(card, bg=card_bg, padx=6, pady=6)
        body.pack(fill=tk.BOTH, expand=True)

        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)
        body.grid_rowconfigure(2, weight=1)

        slot_wall = self.create_object_slot(body, room, idx, ObjectType.WALL_HANGING, False, large=True)
        slot_lamp = self.create_object_slot(body, room, idx, ObjectType.LAMP, False, large=True)
        slot_curio = self.create_object_slot(body, room, idx, ObjectType.CURIO, False, large=True)

        slot_wall.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        slot_lamp.grid(row=1, column=0, sticky="nsew", pady=(0, 4))
        slot_curio.grid(row=2, column=0, sticky="nsew")

        return shadow
    
    def create_object_slot(self, parent, room, room_idx, obj_type, dimmed=False, large=False):
        """Create a compact horizontal object slot"""
        slot_frame = tk.Frame(parent, bg=parent.cget('bg'))

        obj = room.get_slot(obj_type)
        is_slot_selected = (room_idx == self.selected_room and obj_type == self.selected_slot)

        slot_bg = self.THEME['accent_gold'] if is_slot_selected else '#FFFFFF'
        inner_pad = 3 if is_slot_selected else 1

        slot_container = tk.Frame(slot_frame, bg=slot_bg, padx=inner_pad, pady=inner_pad)
        slot_container.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(slot_container, bg='#FFFFFF', padx=6, pady=5)
        inner.pack(fill=tk.BOTH, expand=True)

        row = tk.Frame(inner, bg=inner.cget('bg'))
        row.pack(fill=tk.BOTH, expand=True)

        type_label = tk.Label(row, text=f"{obj_type.emoji} {obj_type.name_str}",
                              font=("Segoe UI", 9, "bold"),
                              bg=inner.cget('bg'), fg=self.THEME['text_dark'],
                              anchor='w', justify='left')
        type_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        if obj:
            tile_bg = obj.color.hex_color if not dimmed else '#CFCBC4'
            tile_size = 30 if large else 26
            tile = tk.Frame(row, bg=tile_bg, width=tile_size, height=tile_size)
            tile.pack(side=tk.LEFT, padx=(0, 6))
            tile.pack_propagate(False)
            fg = contrast_text_color(tile_bg)
            tk.Label(tile, text=obj.style.symbol, font=("Segoe UI", 10, "bold"), bg=tile_bg, fg=fg).pack(expand=True)

            meta = tk.Label(row, text=f"{obj.style.name_str} • {obj.color.name_str}",
                            font=("Segoe UI", 8), bg=inner.cget('bg'),
                            fg=self.THEME['text_medium'], anchor='e', justify='right',
                            wraplength=180 if large else 120)
            meta.pack(side=tk.RIGHT)

            self.bind_tooltip(slot_container, lambda: obj.obj_type.name_str + "\n" + obj.style.name_str + " " + obj.color.name_str)
        else:
            tile = tk.Frame(row, bg='#F0ECE5', width=30 if large else 26, height=30 if large else 26)
            tile.pack(side=tk.LEFT, padx=(0, 6))
            tile.pack_propagate(False)
            tk.Label(tile, text="+", font=("Segoe UI", 10, "bold"), bg='#F0ECE5', fg='#AFA8A0').pack(expand=True)

            meta = tk.Label(row, text="Empty", font=("Segoe UI", 8),
                            bg=inner.cget('bg'), fg='#AFA8A0', anchor='e')
            meta.pack(side=tk.RIGHT)

            self.bind_tooltip(slot_container, lambda: f"Empty {obj_type.name_str} slot")

        def bind_click(widget):
            try:
                widget.bind("<Button-1>", lambda e, ri=room_idx, ot=obj_type: self.on_slot_click(ri, ot))
                widget.configure(cursor="hand2")
            except:
                pass
            for child in widget.winfo_children():
                bind_click(child)

        bind_click(slot_frame)

        return slot_frame
    
    def on_slot_click(self, room_idx, obj_type):
        """Handle slot click - select and optionally open picker"""
        room = self.house.rooms[room_idx]
        obj = room.get_slot(obj_type)
        
        # If action already taken, ignore clicks
        if self.action_taken_this_turn:
            return
        
        # First, select the slot
        self.selected_room = room_idx
        self.selected_slot = obj_type
        
        if obj:
            # Slot has object - show options dialog
            self.show_slot_options_dialog(room_idx, obj_type, obj)
        else:
            # Empty slot - directly open object picker
            self.show_object_picker(self.do_add, obj_type)
    
    def show_slot_options_dialog(self, room_idx, obj_type, obj):
        """Show options for a filled slot"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Object Options")
        dialog.geometry("380x320")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 380, 320)
        
        # Object info
        tk.Label(dialog, text=obj_type.emoji, font=("Segoe UI", 48),
                bg=self.THEME['bg']).pack(pady=15)
        tk.Label(dialog, text=f"{obj.style.symbol} {obj.color.name_str} {obj.style.name_str}",
                font=("Georgia", 16, "bold"), bg=self.THEME['bg'],
                fg=obj.color.dark_hex).pack()
        tk.Label(dialog, text=obj_type.name_str, font=("Segoe UI", 12),
                bg=self.THEME['bg'], fg=self.THEME['text_medium']).pack(pady=(5,20))
        
        # Options
        options_frame = tk.Frame(dialog, bg=self.THEME['bg'])
        options_frame.pack(fill=tk.X, padx=40)
        
        def do_swap():
            dialog.destroy()
            self.show_object_picker(self.do_swap, obj_type)
        
        def do_remove():
            prev_obj = self.house.rooms[room_idx].get_slot(obj_type)
            self.house.rooms[room_idx].set_slot(obj_type, None)
            self.last_action = ("set_slot", room_idx, obj_type, prev_obj)
            self.action_taken_this_turn = True
            self.selected_room = None
            self.selected_slot = None
            dialog.destroy()
            self.build_game_ui()
        
        StyledButton(options_frame, "Swap with Different Object", do_swap,
                    bg_color=self.THEME['accent_lavender'], hover_color="#9575CD",
                    fg_color="white", icon="🔄", font_size=11, padx=15, pady=10).pack(fill=tk.X, pady=5)
        
        StyledButton(options_frame, "Remove Object", do_remove,
                    bg_color=self.THEME['error'], hover_color="#EF5350",
                    fg_color="white", icon="🗑️", font_size=11, padx=15, pady=10).pack(fill=tk.X, pady=5)
        
        StyledButton(options_frame, "Cancel", dialog.destroy,
                    bg_color=self.THEME['bg_alt'], hover_color=self.THEME['border'],
                    fg_color=self.THEME['text_dark'], font_size=10, padx=15, pady=8).pack(fill=tk.X, pady=10)
    
    def select_room(self, idx):
        # Toggle selection if clicking same room
        if self.action_taken_this_turn:
            return
        if self.selected_room == idx:
            self.selected_room = None
            self.selected_slot = None
        else:
            self.selected_room = idx
            self.selected_slot = None
        self.update_selection_visuals()
    
    def deselect_room(self):
        """Deselect to see full house view"""
        self.selected_room = None
        self.selected_slot = None
        self.update_selection_visuals()

    def undo_last_action(self):
        """Undo the last action taken this turn"""
        if not self.last_action:
            return
        action = self.last_action[0]
        if action == "set_slot":
            _, room_idx, obj_type, prev_obj = self.last_action
            self.house.rooms[room_idx].set_slot(obj_type, prev_obj)
        elif action == "paint":
            _, room_idx, prev_color = self.last_action
            self.house.rooms[room_idx].wall_color = prev_color
        self.last_action = None
        self.action_taken_this_turn = False
        self.build_game_ui()
    
    def select_slot(self, room_idx, obj_type):
        if self.action_taken_this_turn:
            return
        self.selected_room = room_idx
        self.selected_slot = obj_type
        self.update_selection_visuals()

    def update_selection_visuals(self):
        """Update selection highlights without full re-render"""
        for i, border in self.room_borders.items():
            if i == self.selected_room:
                border.configure(bg=self.house.rooms[i].wall_color.hex_color)
            else:
                border.configure(bg=self.house.rooms[i].wall_color.hex_color)
        if self.selection_labels.get("empty") and self.selected_room is not None:
            self.selection_labels["empty"].destroy()
        if self.selection_labels.get("room") and self.selected_room is not None:
            room = self.house.rooms[self.selected_room]
            self.selection_labels["room"].configure(text=room.name)
        if self.selection_labels.get("wall") and self.selected_room is not None:
            room = self.house.rooms[self.selected_room]
            self.selection_labels["wall"].configure(text=f"🎨{room.wall_color.name_str}")
        if self.selection_labels.get("slot"):
            if self.selected_room is not None and self.selected_slot is not None:
                room = self.house.rooms[self.selected_room]
                obj = room.get_slot(self.selected_slot)
                slot_text = f"{self.selected_slot.emoji} {self.selected_slot.name_str}"
                if obj:
                    slot_text += f" • {obj.color.name_str} {obj.style.name_str}"
                self.selection_labels["slot"].configure(text=slot_text)
    
    def heart_to_heart(self):
        """Use a heart-to-heart for open discussion"""
        if self.heart_to_heart_used >= self.max_heart_to_heart:
            self.show_fancy_message("No Heart-to-Hearts Left", 
                "You've used all 3 heart-to-hearts!\nCommunicate through reactions only.", "warning")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Heart-to-Heart")
        dialog.geometry("480x380")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 480, 380)
        
        tk.Label(dialog, text="💕", font=("Segoe UI", 56),
                bg=self.THEME['bg']).pack(pady=20)
        tk.Label(dialog, text="Heart-to-Heart", font=("Georgia", 22, "bold"),
                bg=self.THEME['bg'], fg=self.THEME['accent_rose']).pack()
        
        remaining = self.max_heart_to_heart - self.heart_to_heart_used - 1
        tk.Label(dialog, text=f"({remaining} remaining after this)",
                font=("Segoe UI", 11), bg=self.THEME['bg'],
                fg=self.THEME['text_medium']).pack(pady=5)
        
        info_frame = tk.Frame(dialog, bg=self.THEME['bg_alt'], padx=30, pady=20)
        info_frame.pack(fill=tk.X, padx=40, pady=20)
        
        tk.Label(info_frame, text="During a Heart-to-Heart, both players can\n"
                                  "openly discuss their conditions and strategy.\n\n"
                                  "Take your time to talk it out! ☕",
                font=("Segoe UI", 12), bg=self.THEME['bg_alt'],
                fg=self.THEME['text_dark'], justify='center').pack()
        
        def confirm():
            self.heart_to_heart_used += 1
            dialog.destroy()
            self.show_fancy_message("Heart-to-Heart Started! 💕",
                "Discuss openly with your partner.\nClick OK when you're done.", "info")
            self.build_game_ui()
        
        btns = tk.Frame(dialog, bg=self.THEME['bg'])
        btns.pack(pady=15)
        
        StyledButton(btns, "Start Discussion", confirm,
                    bg_color=self.THEME['accent_rose'], hover_color="#EC407A",
                    fg_color="white", icon="💬", font_size=12, padx=20, pady=10).pack(side=tk.LEFT, padx=10)
        
        StyledButton(btns, "Cancel", dialog.destroy,
                    bg_color=self.THEME['bg_alt'], hover_color=self.THEME['border'],
                    fg_color=self.THEME['text_dark'], font_size=11, padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    
    def action_add(self):
        if self.action_taken_this_turn:
            self.show_fancy_message("Action Already Taken", "You can only take 1 action per turn.\nEnd your turn to continue.", "warning")
            return
        if self.selected_room is None or self.selected_slot is None:
            self.show_fancy_message("Select a Slot", "👆 Click on an empty slot in a room first!", "info")
            return
        room = self.house.rooms[self.selected_room]
        if not room.is_slot_empty(self.selected_slot):
            self.show_fancy_message("Slot Occupied", "This slot has an object. Click on it to swap or remove.", "warning")
            return
        self.show_object_picker(self.do_add, self.selected_slot)
    
    def do_add(self, obj):
        if obj and self.selected_room is not None:
            room = self.house.rooms[self.selected_room]
            prev_obj = room.get_slot(obj.obj_type)
            room.set_slot(obj.obj_type, obj)
            self.last_action = ("set_slot", self.selected_room, obj.obj_type, prev_obj)
            self.action_taken_this_turn = True
            self.selected_room = None
            self.selected_slot = None
            self.build_game_ui()
    
    def action_remove(self):
        if self.action_taken_this_turn:
            self.show_fancy_message("Action Already Taken", "You can only take 1 action per turn.\nEnd your turn to continue.", "warning")
            return
        if self.selected_room is None or self.selected_slot is None:
            self.show_fancy_message("Select a Slot", "👆 Click on an object to remove it!", "info")
            return
        room = self.house.rooms[self.selected_room]
        if room.is_slot_empty(self.selected_slot):
            self.show_fancy_message("Empty Slot", "This slot is already empty!", "info")
            return
        prev_obj = room.get_slot(self.selected_slot)
        room.set_slot(self.selected_slot, None)
        self.last_action = ("set_slot", self.selected_room, self.selected_slot, prev_obj)
        self.action_taken_this_turn = True
        self.selected_room = None
        self.selected_slot = None
        self.build_game_ui()
    
    def action_swap(self):
        if self.action_taken_this_turn:
            self.show_fancy_message("Action Already Taken", "You can only take 1 action per turn.\nEnd your turn to continue.", "warning")
            return
        if self.selected_room is None or self.selected_slot is None:
            self.show_fancy_message("Select a Slot", "👆 Click on an object to swap it!", "info")
            return
        room = self.house.rooms[self.selected_room]
        if room.is_slot_empty(self.selected_slot):
            self.show_fancy_message("Empty Slot", "Use 'Add' for empty slots, or click directly on the slot.", "info")
            return
        self.show_object_picker(self.do_swap, self.selected_slot)
    
    def do_swap(self, obj):
        if obj and self.selected_room is not None:
            room = self.house.rooms[self.selected_room]
            prev_obj = room.get_slot(obj.obj_type)
            room.set_slot(obj.obj_type, obj)
            self.last_action = ("set_slot", self.selected_room, obj.obj_type, prev_obj)
            self.action_taken_this_turn = True
            self.selected_room = None
            self.selected_slot = None
            self.build_game_ui()
    
    def action_paint(self):
        if self.action_taken_this_turn:
            self.show_fancy_message("Action Already Taken", "You can only take 1 action per turn.\nEnd your turn to continue.", "warning")
            return
        if self.selected_room is None:
            self.show_fancy_message("Select a Room", "👆 Click on a room first to paint its walls!", "info")
            return
        
        room = self.house.rooms[self.selected_room]
        room_style = self.room_colors[self.selected_room]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Paint Walls")
        dialog.geometry("520x360")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 520, 360)
        
        tk.Label(dialog, text="🎨", font=("Segoe UI", 52),
                bg=self.THEME['bg'], fg=room.wall_color.hex_color).pack(pady=20)
        
        tk.Label(dialog, text=f"Paint {room.name}", font=("Georgia", 20, "bold"),
                bg=self.THEME['bg'], fg=self.THEME['text_dark']).pack()
        
        tk.Label(dialog, text=f"Current: {room.wall_color.name_str}",
                font=("Segoe UI", 12), bg=self.THEME['bg'],
                fg=self.THEME['text_medium']).pack(pady=10)
        
        tk.Label(dialog, text="Choose new wall color:", font=("Segoe UI", 11),
                bg=self.THEME['bg'], fg=self.THEME['text_light']).pack(pady=(10,6))
        
        colors_frame = tk.Frame(dialog, bg=self.THEME['bg'])
        colors_frame.pack(pady=10)
        
        for color in Color:
            card = tk.Frame(colors_frame, bg="#FFFFFF", padx=8, pady=8,
                           highlightbackground=self.THEME['border'], highlightthickness=1)
            card.pack(side=tk.LEFT, padx=8)
            
            swatch = tk.Frame(card, bg=color.hex_color, width=64, height=64)
            swatch.pack()
            swatch.pack_propagate(False)
            
            tk.Label(card, text=color.name_str, font=("Segoe UI", 10, "bold"),
                    bg="#FFFFFF", fg=self.THEME['text_dark']).pack(pady=(6,0))
            
            select_btn = tk.Button(card, text="Select", font=("Segoe UI", 9, "bold"),
                                  bg=color.hex_color, fg='white',
                                  relief=tk.FLAT, cursor='hand2',
                                  activebackground=color.dark_hex,
                                  command=lambda c=color: self.do_paint(c, dialog))
            select_btn.pack(pady=(6,0), ipadx=6, ipady=2)
            
            # Make entire card clickable
            def bind_pick(widget):
                widget.bind("<Button-1>", lambda e, c=color: self.do_paint(c, dialog))
                for child in widget.winfo_children():
                    bind_pick(child)
            bind_pick(card)
            
            select_btn.bind("<Enter>", lambda e, b=select_btn, c=color: b.configure(bg=c.dark_hex))
            select_btn.bind("<Leave>", lambda e, b=select_btn, c=color: b.configure(bg=c.hex_color))
        
        StyledButton(dialog, "Cancel", dialog.destroy,
                    bg_color=self.THEME['bg_alt'], hover_color=self.THEME['border'],
                    fg_color=self.THEME['text_dark'], font_size=10, padx=20, pady=8).pack(pady=20)
    
    def do_paint(self, color, dialog):
        if self.selected_room is not None:
            prev_color = self.house.rooms[self.selected_room].wall_color
            self.house.rooms[self.selected_room].wall_color = color
            self.last_action = ("paint", self.selected_room, prev_color)
            self.action_taken_this_turn = True
            self.selected_room = None
            self.selected_slot = None
        dialog.destroy()
        self.build_game_ui()
    
    def show_object_picker(self, callback, filter_type):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Object")
        dialog.geometry("520x560")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 520, 560)
        
        tk.Label(dialog, text=f"{filter_type.emoji}  Select {filter_type.name_str}", 
                font=("Georgia", 20, "bold"),
                bg=self.THEME['bg'], fg=self.THEME['text_dark']).pack(pady=18)
        
        tk.Label(dialog, text="Valid combinations only (rulebook page 6)",
                font=("Segoe UI", 10), bg=self.THEME['bg'],
                fg=self.THEME['text_medium']).pack(pady=(0,10))
        
        options_frame = tk.Frame(dialog, bg=self.THEME['bg'])
        options_frame.pack(expand=True, fill=tk.BOTH, padx=25, pady=10)
        
        # Build 4 valid options for this object type (one per style)
        objects = [GameObject(filter_type, VALID_OBJECTS_MAP[filter_type][style], style) for style in Style]
        
        def pick(obj):
            callback(obj)
            dialog.destroy()
        
        for idx, obj in enumerate(objects):
            row, col = divmod(idx, 2)
            card_bg = obj.color.light_hex
            
            card = tk.Frame(options_frame, bg=card_bg,
                           highlightbackground=obj.color.dark_hex, highlightthickness=2)
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
            
            tk.Label(card, text=obj.style.symbol, font=("Segoe UI", 20),
                    bg=card_bg, fg=obj.style.color).pack(pady=(12,0))
            
            tk.Label(card, text=obj.style.name_str, font=("Georgia", 14, "bold"),
                    bg=card_bg, fg=self.THEME['text_dark']).pack()
            
            tk.Label(card, text=f"{obj.color.name_str} {filter_type.name_str}",
                    font=("Segoe UI", 10), bg=card_bg, fg=self.THEME['text_medium']).pack(pady=(0,8))
            
            select_btn = tk.Button(card, text="Select", font=("Segoe UI", 10, "bold"),
                                  bg=obj.color.hex_color, fg='white',
                                  relief=tk.FLAT, cursor='hand2',
                                  activebackground=obj.color.dark_hex,
                                  command=lambda o=obj: pick(o))
            select_btn.pack(pady=(0,12), ipadx=10, ipady=4)
            
            select_btn.bind("<Enter>", lambda e, b=select_btn, c=obj.color: b.configure(bg=c.dark_hex))
            select_btn.bind("<Leave>", lambda e, b=select_btn, c=obj.color: b.configure(bg=c.hex_color))
            
            for w in [card] + list(card.winfo_children()):
                w.bind("<Button-1>", lambda e, o=obj: pick(o))
                w.configure(cursor="hand2")
        
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)
        
        StyledButton(dialog, "Cancel", dialog.destroy,
                    bg_color=self.THEME['bg_alt'], hover_color=self.THEME['border'],
                    fg_color=self.THEME['text_dark'], font_size=10, padx=20, pady=8).pack(pady=10)
    
    def react(self, reaction):
        # Store reaction for display
        self.last_reactions[self.current_player] = reaction
        # Update reaction label if present, otherwise rebuild minimal UI
        react_emoji = {"happy": "😊", "neutral": "😐", "unhappy": "😠"}
        if self.reaction_label:
            self.reaction_label.configure(text=f"Partner reaction: {react_emoji.get(reaction, '')}")
        else:
            self.build_game_ui()
    
    def show_my_conditions(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("My Conditions")
        dialog.geometry("480x450")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 480, 450)
        
        player_color = self.player_colors[self.current_player]
        
        tk.Label(dialog, text="🔒", font=("Segoe UI", 42),
                bg=self.THEME['bg'], fg=player_color).pack(pady=20)
        
        tk.Label(dialog, text=f"{self.player_names[self.current_player]}'s Conditions",
                font=("Georgia", 18, "bold"),
                bg=self.THEME['bg'], fg=player_color).pack()
        
        cond_frame = tk.Frame(dialog, bg=self.THEME['panel'], padx=30, pady=25,
                             highlightbackground=self.THEME['border'], highlightthickness=1)
        cond_frame.pack(fill=tk.X, padx=35, pady=20)
        
        all_met = True
        for c in self.player_conditions[self.current_player]:
            met = c.check(self.house)
            if not met: all_met = False
            
            row = tk.Frame(cond_frame, bg=self.THEME['panel'])
            row.pack(fill=tk.X, pady=5)
            
            status_color = self.THEME['success'] if met else self.THEME['error']
            status_icon = "✅" if met else "❌"
            
            tk.Label(row, text=status_icon, font=("Segoe UI", 14),
                    bg=self.THEME['panel'], fg=status_color).pack(side=tk.LEFT)
            tk.Label(row, text=str(c), font=("Segoe UI", 11),
                    bg=self.THEME['panel'], fg=self.THEME['text_dark']).pack(side=tk.LEFT, padx=12)
        
        # Status summary
        if all_met:
            status_text = "🎉 All YOUR conditions are met!"
            status_color = self.THEME['success']
        else:
            status_text = "⏳ Some conditions still need work"
            status_color = self.THEME['warning']
        
        tk.Label(dialog, text=status_text, font=("Segoe UI", 12, "bold"),
                bg=self.THEME['bg'], fg=status_color).pack(pady=15)
        
        StyledButton(dialog, "Close", dialog.destroy,
                    bg_color=player_color, hover_color=self.player_dark_colors[self.current_player],
                    fg_color="white", font_size=11, padx=25, pady=8).pack(pady=5)
    
    def check_win(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Condition Check")
        dialog.geometry("560x520")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 560, 520)

        player_idx = self.current_player
        player_name = self.player_names[player_idx]
        player_color = self.player_colors[player_idx]
        player_emoji = "🔴" if player_idx == 0 else "🔵"
        conditions = self.player_conditions[player_idx]
        results = [c.check(self.house) for c in conditions]
        met_count = sum(1 for met in results if met)
        total_count = len(conditions)
        all_met = (total_count > 0 and met_count == total_count)

        tk.Label(dialog, text=f"{player_emoji} {player_name}", font=("Georgia", 22, "bold"),
                bg=self.THEME['bg'], fg=player_color).pack(pady=(20, 6))

        tk.Label(dialog, text=f"Actions taken: {self.turn_count}",
                font=("Segoe UI", 10), bg=self.THEME['bg'],
                fg=self.THEME['text_medium']).pack(pady=(0, 10))

        if total_count == 0:
            status_text = "No conditions set for current player."
            status_color = self.THEME['warning']
            icon = "📋"
        elif all_met:
            status_text = "All your conditions are met!"
            status_color = self.THEME['success']
            icon = "✅"
        else:
            status_text = f"{met_count}/{total_count} conditions met"
            status_color = self.THEME['warning']
            icon = "⏳"

        tk.Label(dialog, text=icon, font=("Segoe UI", 34),
                bg=self.THEME['bg'], fg=status_color).pack(pady=(4, 0))
        tk.Label(dialog, text=status_text, font=("Segoe UI", 12, "bold"),
                bg=self.THEME['bg'], fg=status_color).pack(pady=(4, 12))

        player_frame = tk.Frame(dialog, bg=self.THEME['panel'], padx=20, pady=14,
                               highlightbackground=self.THEME['border'], highlightthickness=1)
        player_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        if total_count == 0:
            tk.Label(player_frame, text="Add conditions in setup to use this check.",
                    font=("Segoe UI", 10), bg=self.THEME['panel'],
                    fg=self.THEME['text_light']).pack(anchor='w')
        else:
            for cond, met in zip(conditions, results):
                row = tk.Frame(player_frame, bg=self.THEME['panel'])
                row.pack(fill=tk.X, pady=3)
                icon_text = "✅" if met else "❌"
                color = self.THEME['success'] if met else self.THEME['error']
                tk.Label(row, text=f"{icon_text}  {cond}", font=("Segoe UI", 10),
                        bg=self.THEME['panel'], fg=color, anchor='w').pack(fill=tk.X)

        StyledButton(dialog, "Close", dialog.destroy,
                    bg_color=player_color, hover_color=self.player_dark_colors[player_idx],
                    fg_color="white", font_size=11, padx=25, pady=8).pack(pady=14)

    
    def end_turn(self):
        # No hard turn limit
        
        self.current_player = 1 - self.current_player
        self.turn_count += 1
        self.selected_room = None
        self.selected_slot = None
        self.action_taken_this_turn = False  # Reset for new turn
        self.last_action = None
        
        # Show turn transition with animation
        transition = tk.Toplevel(self.root)
        transition.overrideredirect(True)
        transition.geometry("450x220")
        transition.configure(bg=self.player_colors[self.current_player])
        self.center_window(transition, 450, 220)
        transition.attributes('-topmost', True)
        
        player_emoji = "🔴" if self.current_player == 0 else "🔵"
        
        round_count = (self.turn_count // 2) + 1
        tk.Label(transition, text=f"Round {round_count}",
                font=("Segoe UI", 16), bg=self.player_colors[self.current_player],
                fg='white').pack(pady=(35,10))
        tk.Label(transition, text=f"{player_emoji} {self.player_names[self.current_player]}'s Turn",
                font=("Georgia", 28, "bold"), bg=self.player_colors[self.current_player],
                fg='white').pack()
        
        tk.Label(transition, text=f"(Actions taken: {self.turn_count})",
                font=("Segoe UI", 11), bg=self.player_colors[self.current_player],
                fg='white').pack(pady=15)
        
        self.root.after(1800, lambda: [transition.destroy(), self.build_game_ui()])
    
    def show_game_over(self):
        """Show game over screen when turns run out"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Game Over")
        dialog.geometry("550x500")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 550, 500)
        
        # Check final status
        all_met = all(c.check(self.house) for i in range(2) for c in self.player_conditions[i])
        
        if all_met:
            tk.Label(dialog, text="🎉🏆🎉", font=("Segoe UI", 56),
                    bg=self.THEME['bg'], fg=self.THEME['accent_gold']).pack(pady=25)
            tk.Label(dialog, text="VICTORY!", font=("Georgia", 32, "bold"),
                    bg=self.THEME['bg'], fg=self.THEME['accent_gold']).pack()
            tk.Label(dialog, text="You completed all conditions!", font=("Segoe UI", 14),
                    bg=self.THEME['bg'], fg=self.THEME['text_dark']).pack(pady=10)
        else:
            tk.Label(dialog, text="⏰", font=("Segoe UI", 56),
                    bg=self.THEME['bg'], fg=self.THEME['error']).pack(pady=25)
            tk.Label(dialog, text="Time's Up!", font=("Georgia", 32, "bold"),
                    bg=self.THEME['bg'], fg=self.THEME['error']).pack()
            tk.Label(dialog, text="You ran out of turns before completing all conditions.",
                    font=("Segoe UI", 12), bg=self.THEME['bg'],
                    fg=self.THEME['text_medium']).pack(pady=10)
        
        # Final status
        met_count = sum(1 for i in range(2) for c in self.player_conditions[i] if c.check(self.house))
        total_count = sum(len(self.player_conditions[i]) for i in range(2))
        
        tk.Label(dialog, text=f"Final Score: {met_count}/{total_count} conditions met",
                font=("Segoe UI", 14, "bold"), bg=self.THEME['bg'],
                fg=self.THEME['text_dark']).pack(pady=20)
        
        StyledButton(dialog, "View Final Results", lambda: [dialog.destroy(), self.check_win()],
                    bg_color=self.THEME['accent_lavender'], hover_color="#9575CD",
                    fg_color="white", font_size=12, padx=25, pady=12).pack(pady=10)
    
    def show_fancy_message(self, title, message, msg_type="info"):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("420x280")
        dialog.configure(bg=self.THEME['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 420, 280)
        
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
        colors = {"info": self.THEME['accent_lavender'], "warning": self.THEME['warning'],
                 "error": self.THEME['error'], "success": self.THEME['success']}
        
        tk.Label(dialog, text=icons.get(msg_type, "ℹ️"), font=("Segoe UI", 42),
                bg=self.THEME['bg'], fg=colors.get(msg_type, self.THEME['text_dark'])).pack(pady=25)
        
        tk.Label(dialog, text=title, font=("Georgia", 18, "bold"),
                bg=self.THEME['bg'], fg=self.THEME['text_dark']).pack()
        
        tk.Label(dialog, text=message, font=("Segoe UI", 11),
                bg=self.THEME['bg'], fg=self.THEME['text_medium'],
                wraplength=360, justify='center').pack(pady=18)
        
        StyledButton(dialog, "OK", dialog.destroy,
                    bg_color=colors.get(msg_type, self.THEME['accent_lavender']),
                    hover_color=self.THEME['text_light'],
                    fg_color="white", font_size=10, padx=25, pady=8).pack(pady=10)

def main():
    root = tk.Tk()
    root.withdraw()  # Hide during setup
    game = DecorumGame(root)
    root.deiconify()  # Show after setup
    root.mainloop()

if __name__ == "__main__":
    main()
