"""
DECORUM - A Two-Player Cooperative House Decorating Game
=========================================================
Players must decorate a shared house while satisfying their secret conditions.
Each player takes turns placing, removing, or swapping objects in the rooms.
The game is won when ALL conditions from both players are satisfied!

Controls:
- Enter room number (1-4) and action to modify the house
- 'check' to see if all conditions are met
- 'quit' to exit the game
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Color(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    
    def __str__(self):
        return self.value

class ObjectType(Enum):
    LAMP = "lamp"
    PAINTING = "painting"
    PLANT = "plant"
    CUSHION = "cushion"
    
    def __str__(self):
        return self.value

class WallColor(Enum):
    WHITE = "white"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    
    def __str__(self):
        return self.value

@dataclass
class GameObject:
    obj_type: ObjectType
    color: Color
    
    def __str__(self):
        return f"{self.color} {self.obj_type}"

@dataclass 
class Room:
    name: str
    wall_color: WallColor
    objects: list  # List of GameObjects, max 3
    
    def __str__(self):
        obj_str = ", ".join(str(o) for o in self.objects) if self.objects else "empty"
        return f"{self.name} (walls: {self.wall_color}): [{obj_str}]"
    
    def add_object(self, obj: GameObject) -> bool:
        if len(self.objects) < 3:
            self.objects.append(obj)
            return True
        return False
    
    def remove_object(self, index: int) -> Optional[GameObject]:
        if 0 <= index < len(self.objects):
            return self.objects.pop(index)
        return None

class House:
    def __init__(self):
        self.rooms = [
            Room("Bathroom", WallColor.WHITE, []),
            Room("Bedroom", WallColor.WHITE, []),
            Room("Living Room", WallColor.WHITE, []),
            Room("Kitchen", WallColor.WHITE, [])
        ]
    
    def display(self):
        print("\n" + "="*60)
        print("                    THE HOUSE")
        print("="*60)
        for i, room in enumerate(self.rooms, 1):
            print(f"  Room {i}: {room}")
        print("="*60)
    
    def get_all_objects(self) -> list:
        all_objs = []
        for room in self.rooms:
            all_objs.extend(room.objects)
        return all_objs
    
    def count_objects_by_color(self, color: Color) -> int:
        return sum(1 for obj in self.get_all_objects() if obj.color == color)
    
    def count_objects_by_type(self, obj_type: ObjectType) -> int:
        return sum(1 for obj in self.get_all_objects() if obj.obj_type == obj_type)
    
    def count_objects_in_room(self, room_index: int) -> int:
        return len(self.rooms[room_index].objects)
    
    def room_has_object_type(self, room_index: int, obj_type: ObjectType) -> bool:
        return any(obj.obj_type == obj_type for obj in self.rooms[room_index].objects)
    
    def room_has_color(self, room_index: int, color: Color) -> bool:
        return any(obj.color == color for obj in self.rooms[room_index].objects)


class Condition:
    """Base class for win conditions"""
    def check(self, house: House) -> bool:
        raise NotImplementedError
    
    def __str__(self):
        raise NotImplementedError

class MinObjectsOfColor(Condition):
    def __init__(self, color: Color, min_count: int):
        self.color = color
        self.min_count = min_count
    
    def check(self, house: House) -> bool:
        return house.count_objects_by_color(self.color) >= self.min_count
    
    def __str__(self):
        return f"At least {self.min_count} {self.color} object(s) in the house"

class MaxObjectsOfColor(Condition):
    def __init__(self, color: Color, max_count: int):
        self.color = color
        self.max_count = max_count
    
    def check(self, house: House) -> bool:
        return house.count_objects_by_color(self.color) <= self.max_count
    
    def __str__(self):
        return f"At most {self.max_count} {self.color} object(s) in the house"

class MinObjectsOfType(Condition):
    def __init__(self, obj_type: ObjectType, min_count: int):
        self.obj_type = obj_type
        self.min_count = min_count
    
    def check(self, house: House) -> bool:
        return house.count_objects_by_type(self.obj_type) >= self.min_count
    
    def __str__(self):
        return f"At least {self.min_count} {self.obj_type}(s) in the house"

class RoomMustHaveType(Condition):
    def __init__(self, room_index: int, room_name: str, obj_type: ObjectType):
        self.room_index = room_index
        self.room_name = room_name
        self.obj_type = obj_type
    
    def check(self, house: House) -> bool:
        return house.room_has_object_type(self.room_index, self.obj_type)
    
    def __str__(self):
        return f"The {self.room_name} must have a {self.obj_type}"

class RoomMustHaveColor(Condition):
    def __init__(self, room_index: int, room_name: str, color: Color):
        self.room_index = room_index
        self.room_name = room_name
        self.color = color
    
    def check(self, house: House) -> bool:
        return house.room_has_color(self.room_index, self.color)
    
    def __str__(self):
        return f"The {self.room_name} must have a {self.color} object"

class RoomMustNotHaveColor(Condition):
    def __init__(self, room_index: int, room_name: str, color: Color):
        self.room_index = room_index
        self.room_name = room_name
        self.color = color
    
    def check(self, house: House) -> bool:
        return not house.room_has_color(self.room_index, self.color)
    
    def __str__(self):
        return f"The {self.room_name} must NOT have any {self.color} objects"

class RoomMinObjects(Condition):
    def __init__(self, room_index: int, room_name: str, min_count: int):
        self.room_index = room_index
        self.room_name = room_name
        self.min_count = min_count
    
    def check(self, house: House) -> bool:
        return house.count_objects_in_room(self.room_index) >= self.min_count
    
    def __str__(self):
        return f"The {self.room_name} must have at least {self.min_count} object(s)"

class RoomMaxObjects(Condition):
    def __init__(self, room_index: int, room_name: str, max_count: int):
        self.room_index = room_index
        self.room_name = room_name
        self.max_count = max_count
    
    def check(self, house: House) -> bool:
        return house.count_objects_in_room(self.room_index) <= self.max_count
    
    def __str__(self):
        return f"The {self.room_name} must have at most {self.max_count} object(s)"


class Player:
    def __init__(self, name: str, conditions: list):
        self.name = name
        self.conditions = conditions
    
    def show_conditions(self):
        print(f"\n{self.name}'s SECRET Conditions:")
        print("-" * 40)
        for i, cond in enumerate(self.conditions, 1):
            print(f"  {i}. {cond}")
        print("-" * 40)
    
    def check_conditions(self, house: House) -> tuple:
        results = [(cond, cond.check(house)) for cond in self.conditions]
        return results


def generate_conditions(house: House):
    """Generate random conditions for two players"""
    room_names = ["Bathroom", "Bedroom", "Living Room", "Kitchen"]
    all_conditions = []
    
    # Generate a pool of possible conditions
    for color in Color:
        all_conditions.append(MinObjectsOfColor(color, random.randint(1, 3)))
        all_conditions.append(MaxObjectsOfColor(color, random.randint(1, 2)))
    
    for obj_type in ObjectType:
        all_conditions.append(MinObjectsOfType(obj_type, random.randint(1, 2)))
    
    for i, room_name in enumerate(room_names):
        for obj_type in ObjectType:
            all_conditions.append(RoomMustHaveType(i, room_name, obj_type))
        for color in Color:
            all_conditions.append(RoomMustHaveColor(i, room_name, color))
            all_conditions.append(RoomMustNotHaveColor(i, room_name, color))
        all_conditions.append(RoomMinObjects(i, room_name, random.randint(1, 2)))
        all_conditions.append(RoomMaxObjects(i, room_name, random.randint(1, 2)))
    
    random.shuffle(all_conditions)
    
    # Give 3 conditions to each player
    player1_conditions = all_conditions[:3]
    player2_conditions = all_conditions[3:6]
    
    return player1_conditions, player2_conditions


def create_object_menu():
    """Create object selection menu"""
    print("\n  Object Types:")
    for i, obj_type in enumerate(ObjectType, 1):
        print(f"    {i}. {obj_type}")
    print("\n  Colors:")
    for i, color in enumerate(Color, 1):
        print(f"    {i}. {color}")


def get_object_choice() -> Optional[GameObject]:
    """Get player's choice for a new object"""
    create_object_menu()
    
    try:
        type_choice = int(input("  Choose object type (1-4): ")) - 1
        if not (0 <= type_choice < 4):
            print("Invalid choice!")
            return None
        obj_type = list(ObjectType)[type_choice]
        
        color_choice = int(input("  Choose color (1-4): ")) - 1
        if not (0 <= color_choice < 4):
            print("Invalid choice!")
            return None
        color = list(Color)[color_choice]
        
        return GameObject(obj_type, color)
    except ValueError:
        print("Invalid input!")
        return None


def play_turn(house: House, player: Player):
    """Execute a single player turn"""
    print(f"\n>>> {player.name}'s Turn <<<")
    house.display()
    
    print("\nActions:")
    print("  1. Add object to a room")
    print("  2. Remove object from a room")
    print("  3. Change wall color")
    print("  4. View my conditions")
    print("  5. Check if we won")
    print("  6. Pass (do nothing)")
    
    try:
        action = input("\nChoose action (1-6): ").strip()
        
        if action == "1":
            room_num = int(input("Which room? (1-4): ")) - 1
            if not (0 <= room_num < 4):
                print("Invalid room!")
                return False
            
            obj = get_object_choice()
            if obj:
                if house.rooms[room_num].add_object(obj):
                    print(f"Added {obj} to {house.rooms[room_num].name}")
                else:
                    print("Room is full! (max 3 objects)")
        
        elif action == "2":
            room_num = int(input("Which room? (1-4): ")) - 1
            if not (0 <= room_num < 4):
                print("Invalid room!")
                return False
            
            room = house.rooms[room_num]
            if not room.objects:
                print("Room is empty!")
                return False
            
            print(f"Objects in {room.name}:")
            for i, obj in enumerate(room.objects, 1):
                print(f"  {i}. {obj}")
            
            obj_num = int(input("Remove which object? ")) - 1
            removed = room.remove_object(obj_num)
            if removed:
                print(f"Removed {removed}")
            else:
                print("Invalid selection!")
        
        elif action == "3":
            room_num = int(input("Which room? (1-4): ")) - 1
            if not (0 <= room_num < 4):
                print("Invalid room!")
                return False
            
            print("Wall colors:")
            for i, wc in enumerate(WallColor, 1):
                print(f"  {i}. {wc}")
            
            color_choice = int(input("Choose wall color (1-5): ")) - 1
            if 0 <= color_choice < 5:
                house.rooms[room_num].wall_color = list(WallColor)[color_choice]
                print(f"Changed {house.rooms[room_num].name} walls to {house.rooms[room_num].wall_color}")
            else:
                print("Invalid color!")
        
        elif action == "4":
            player.show_conditions()
            input("Press Enter to continue...")
            return False  # Don't count as a turn
        
        elif action == "5":
            return True  # Signal to check win condition
        
        elif action == "6":
            print("Passing turn...")
        
        else:
            print("Invalid action!")
            return False
            
    except ValueError:
        print("Invalid input!")
        return False
    
    return False


def check_victory(house: House, player1: Player, player2: Player) -> bool:
    """Check if all conditions are satisfied"""
    print("\n" + "="*60)
    print("           CHECKING WIN CONDITIONS")
    print("="*60)
    
    all_met = True
    
    for player in [player1, player2]:
        print(f"\n{player.name}'s Conditions:")
        results = player.check_conditions(house)
        for cond, met in results:
            status = "✓ MET" if met else "✗ NOT MET"
            print(f"  [{status}] {cond}")
            if not met:
                all_met = False
    
    print("\n" + "="*60)
    
    if all_met:
        print("🎉 CONGRATULATIONS! ALL CONDITIONS MET! YOU WIN! 🎉")
        return True
    else:
        print("Not all conditions are met yet. Keep decorating!")
        return False


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                      D E C O R U M                        ║
    ║           A Two-Player Cooperative Decorating Game        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Work together to decorate the house!                     ║
    ║  Each player has SECRET conditions that must be met.      ║
    ║  Communicate and cooperate to satisfy everyone!           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Setup
    house = House()
    p1_conds, p2_conds = generate_conditions(house)
    
    player1_name = input("Enter Player 1 name: ").strip() or "Player 1"
    player2_name = input("Enter Player 2 name: ").strip() or "Player 2"
    
    player1 = Player(player1_name, p1_conds)
    player2 = Player(player2_name, p2_conds)
    
    # Show conditions privately
    input(f"\n{player1_name}, press Enter to view your SECRET conditions...")
    player1.show_conditions()
    input("Press Enter when done (clear screen for next player)...")
    print("\n" * 50)  # Clear screen
    
    input(f"\n{player2_name}, press Enter to view your SECRET conditions...")
    player2.show_conditions()
    input("Press Enter to start the game...")
    print("\n" * 50)  # Clear screen
    
    # Game loop
    current_player_idx = 0
    players = [player1, player2]
    turn_count = 0
    max_turns = 30
    
    while turn_count < max_turns:
        current_player = players[current_player_idx]
        
        check_win = play_turn(house, current_player)
        
        if check_win:
            if check_victory(house, player1, player2):
                print(f"\nGame completed in {turn_count} turns!")
                break
            input("Press Enter to continue...")
        
        # Alternate players
        current_player_idx = 1 - current_player_idx
        turn_count += 1
        
        # Check for quit
        cont = input("\nPress Enter to continue (or 'q' to quit): ").strip().lower()
        if cont == 'q':
            print("\nThanks for playing!")
            check_victory(house, player1, player2)
            break
    
    if turn_count >= max_turns:
        print(f"\nGame ended after {max_turns} turns!")
        check_victory(house, player1, player2)


if __name__ == "__main__":
    main()
