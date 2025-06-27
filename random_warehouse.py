from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import time
import math
import random

class WarehouseEnvironment:
    """
    A realistic 3D warehouse environment for swarm algorithm simulation using Ursina Engine.
    """
    
    def __init__(self, grid_size=12):
        """
        Initialize the warehouse environment.
        
        Args:
            grid_size (int): Size of the square warehouse grid (default: 12x12)
        """
        self.grid_size = grid_size
        self.floor_tiles = []
        self.shelves = []
        self.shelf_levels = []
        self.pickers = []
        
        # Initialize Ursina
        self.app = Ursina()
        
        # Set up the scene
        self.setup_camera()
        self.create_warehouse_floor()
        self.create_warehouse_walls()
        self.create_realistic_shelving_system()
        self.create_pickers()
        
        # Enable proper lighting
        DirectionalLight(direction=Vec3(1, -1, -1), color=color.white)
        AmbientLight(color=color.white * 0.4)
        
        # Simple sky
        Sky(color=color.gray)
        
    def setup_camera(self):
        """Set up camera for better warehouse view."""
        # Position camera to get a good overview of the warehouse
        camera.position = (6, 18, -8)
        camera.rotation_x = 55
        camera.rotation_y = 15
        
        # Uncomment for manual camera control
        # self.player = FirstPersonController()
        
    def create_warehouse_floor(self):
        """Create realistic warehouse floor with concrete texture effect."""
        print("Creating warehouse floor...")
        
        # Main floor base
        main_floor = Entity(
            model='cube',
            color=color.light_gray,
            position=(self.grid_size/2 - 0.5, -0.1, self.grid_size/2 - 0.5),
            scale=(self.grid_size, 0.2, self.grid_size)
        )
        self.floor_tiles.append(main_floor)
        
        # Add floor grid lines for realism
        for i in range(self.grid_size + 1):
            # Vertical lines
            line_v = Entity(
                model='cube',
                color=color.dark_gray,
                position=(i - 0.5, 0.01, self.grid_size/2 - 0.5),
                scale=(0.02, 0.02, self.grid_size)
            )
            # Horizontal lines  
            line_h = Entity(
                model='cube',
                color=color.dark_gray,
                position=(self.grid_size/2 - 0.5, 0.01, i - 0.5),
                scale=(self.grid_size, 0.02, 0.02)
            )
            self.floor_tiles.extend([line_v, line_h])
        
        print(f"Created warehouse floor with grid lines")
    
    def create_warehouse_walls(self):
        """Create warehouse perimeter walls."""
        wall_height = 4
        wall_color = color.white
        
        # North wall
        Entity(
            model='cube',
            color=wall_color,
            position=(self.grid_size/2 - 0.5, wall_height/2, -0.5),
            scale=(self.grid_size + 1, wall_height, 0.2)
        )
        
        # South wall
        Entity(
            model='cube',
            color=wall_color,
            position=(self.grid_size/2 - 0.5, wall_height/2, self.grid_size - 0.5),
            scale=(self.grid_size + 1, wall_height, 0.2)
        )
        
        # West wall
        Entity(
            model='cube',
            color=wall_color,
            position=(-0.5, wall_height/2, self.grid_size/2 - 0.5),
            scale=(0.2, wall_height, self.grid_size)
        )
        
        # East wall
        Entity(
            model='cube',
            color=wall_color,
            position=(self.grid_size - 0.5, wall_height/2, self.grid_size/2 - 0.5),
            scale=(0.2, wall_height, self.grid_size)
        )
    
    def create_realistic_shelving_system(self):
        """Create a realistic warehouse shelving system with aisles and multi-level shelves."""
        print("Creating realistic shelving system...")
        
        # Define shelf rows and aisles (realistic warehouse layout)
        # Aisles run north-south, shelves run east-west
        shelf_areas = [
            # Format: (start_x, end_x, start_z, end_z, is_shelf_area)
            (1, 2, 1, 10, True),    # Shelf row 1
            (3, 3, 1, 10, False),   # Aisle 1
            (4, 5, 1, 10, True),    # Shelf row 2  
            (6, 6, 1, 10, False),   # Aisle 2
            (7, 8, 1, 10, True),    # Shelf row 3
            (9, 9, 1, 10, False),   # Aisle 3
            (10, 10, 1, 10, True),  # Shelf row 4
        ]
        
        shelf_count = 0
        
        for start_x, end_x, start_z, end_z, is_shelf_area in shelf_areas:
            if is_shelf_area:
                for x in range(start_x, end_x + 1):
                    for z in range(start_z, end_z + 1):
                        # Skip some positions for cross-aisles
                        if z in [3, 6, 8]:  # Cross-aisle breaks
                            continue
                            
                        self.create_multi_level_shelf(x, z)
                        shelf_count += 1
        
        print(f"Created {shelf_count} multi-level shelf units")
    
    def create_multi_level_shelf(self, x, z):
        """Create a realistic multi-level shelf unit at given position."""
        # Industrial shelf colors - using simple color names
        frame_color = color.gray
        shelf_color = color.brown
        
        # Vertical frame posts
        post_positions = [
            (x - 0.4, z - 0.4), (x + 0.4, z - 0.4),
            (x - 0.4, z + 0.4), (x + 0.4, z + 0.4)
        ]
        
        for post_x, post_z in post_positions:
            post = Entity(
                model='cube',
                color=frame_color,
                position=(post_x, 1.5, post_z),
                scale=(0.08, 3, 0.08)
            )
            self.shelves.append(post)
        
        # Horizontal shelf levels
        shelf_heights = [0.3, 1.0, 1.7, 2.4]  # Multiple levels
        
        for height in shelf_heights:
            # Main shelf platform
            shelf = Entity(
                model='cube',
                color=shelf_color,
                position=(x, height, z),
                scale=(0.9, 0.08, 0.9)
            )
            self.shelf_levels.append(shelf)
            
            # Support beams
            for beam_x in [x - 0.4, x + 0.4]:
                beam = Entity(
                    model='cube',
                    color=frame_color,
                    position=(beam_x, height, z),
                    scale=(0.06, 0.06, 0.9)
                )
                self.shelves.append(beam)
        
        # Back panel for realism
        back_panel = Entity(
            model='cube',
            color=color.dark_gray,
            position=(x, 1.5, z + 0.45),
            scale=(0.9, 3, 0.05)
        )
        self.shelves.append(back_panel)
        
        # Add some "inventory" boxes on shelves randomly
        if random.random() > 0.3:  # 70% chance of having boxes
            box_height = random.choice(shelf_heights[1:])  # Not on floor level
            box_colors = [color.red, color.blue, color.yellow, color.green, color.orange]
            box = Entity(
                model='cube',
                color=random.choice(box_colors),
                position=(
                    x + random.uniform(-0.3, 0.3),
                    box_height + 0.15,
                    z + random.uniform(-0.3, 0.3)
                ),
                scale=(
                    random.uniform(0.2, 0.4),
                    random.uniform(0.2, 0.4),
                    random.uniform(0.2, 0.4)
                )
            )
            self.shelves.append(box)
    
    def create_pickers(self):
        """Create picker robots as realistic warehouse vehicles."""
        print("Creating picker robots...")
        
        # Create the main picker at starting position (0, 3) - in an aisle
        picker = Picker(
            position=(0, 3),
            warehouse_env=self
        )
        self.pickers.append(picker)
        
        print(f"Created {len(self.pickers)} picker(s)")
    
    def grid_to_world_pos(self, grid_x, grid_z):
        """Convert grid coordinates to world position."""
        return (grid_x, 0.3, grid_z)  # Y=0.3 to place picker above floor
    
    def run(self):
        """Start the simulation."""
        print("Starting realistic warehouse simulation...")
        self.app.run()


class Picker:
    """
    A realistic picker robot that navigates warehouse aisles.
    """
    
    def __init__(self, position, warehouse_env):
        """Initialize a picker robot."""
        self.warehouse_env = warehouse_env
        self.grid_x, self.grid_z = position
        self.current_path_index = 0
        self.is_moving = False
        self.movement_complete = False
        
        # Realistic path through warehouse aisles
        self.path = [
            (0, 3),   # Start in aisle
            (3, 3),   # Move to main aisle 1
            (3, 1),   # Go to beginning of aisle 1
            (3, 5),   # Travel down aisle 1
            (3, 7),   # Continue in aisle 1
            (3, 10),  # End of aisle 1
            (6, 10),  # Move to aisle 2
            (6, 7),   # Travel in aisle 2
            (6, 4),   # Continue in aisle 2
            (6, 2),   # Continue in aisle 2
            (9, 2),   # Move to aisle 3
            (9, 5),   # Travel in aisle 3
            (9, 8),   # Continue in aisle 3
            (9, 10),  # End of aisle 3
            (11, 10), # Exit area
        ]
        
        # Movement parameters
        self.movement_speed = 1.5  # Realistic warehouse speed
        self.movement_start_time = 0
        self.start_pos = None
        self.target_pos = None
        
        # Create realistic picker vehicle
        self.create_picker_vehicle()
        
        # Start movement after delay
        invoke(self.start_next_movement, delay=2.0)
    
    def create_picker_vehicle(self):
        """Create a realistic warehouse picker vehicle."""
        base_pos = self.warehouse_env.grid_to_world_pos(self.grid_x, self.grid_z)
        
        # Main body (orange industrial color)
        self.entity = Entity(
            model='cube',
            color=color.orange,
            position=base_pos,
            scale=(0.4, 0.3, 0.6)
        )
        
        # Operator platform
        platform = Entity(
            model='cube',
            color=color.light_gray,
            position=(base_pos[0], base_pos[1] + 0.4, base_pos[2] - 0.1),
            scale=(0.3, 0.1, 0.2),
            parent=self.entity
        )
        
        # Mast (vertical lifting mechanism)
        mast = Entity(
            model='cube',
            color=color.gray,
            position=(0, 0.8, 0.2),
            scale=(0.1, 1.2, 0.1),
            parent=self.entity
        )
        
        # Forks
        fork1 = Entity(
            model='cube',
            color=color.dark_gray,
            position=(-0.1, 0.2, 0.35),
            scale=(0.03, 0.03, 0.3),
            parent=self.entity
        )
        
        fork2 = Entity(
            model='cube',
            color=color.dark_gray,
            position=(0.1, 0.2, 0.35),
            scale=(0.03, 0.03, 0.3),
            parent=self.entity
        )
        
        # Warning light
        warning_light = Entity(
            model='sphere',
            color=color.red,
            position=(0, 0.6, -0.2),
            scale=0.08,
            parent=self.entity
        )
    
    def start_next_movement(self):
        """Start moving to the next position in the path."""
        if self.movement_complete:
            return
            
        if self.current_path_index >= len(self.path) - 1:
            print("Picker completed warehouse route!")
            self.movement_complete = True
            return
        
        # Get next target position
        self.current_path_index += 1
        target_grid_pos = self.path[self.current_path_index]
        
        # Set up movement parameters
        self.start_pos = Vec3(self.entity.position)
        self.target_pos = Vec3(self.warehouse_env.grid_to_world_pos(
            target_grid_pos[0], target_grid_pos[1]
        ))
        
        self.movement_start_time = time.time()
        self.is_moving = True
        
        print(f"Picker navigating to grid position {target_grid_pos}")
    
    def update_movement(self):
        """Update the picker's position during movement."""
        if not self.is_moving or self.movement_complete:
            return
        
        # Calculate movement progress
        elapsed_time = time.time() - self.movement_start_time
        distance = (self.target_pos - self.start_pos).length()
        movement_duration = distance / self.movement_speed
        progress = min(elapsed_time / movement_duration, 1.0)
        
        # Smooth interpolation with easing
        # Create smooth acceleration/deceleration curve
        eased_progress = progress * progress * (3.0 - 2.0 * progress)  # Smoothstep formula
        current_pos = lerp(self.start_pos, self.target_pos, eased_progress)
        self.entity.position = current_pos
        
        # Rotate picker to face movement direction
        if distance > 0.1:
            direction = (self.target_pos - self.start_pos).normalized()
            target_rotation_y = math.degrees(math.atan2(direction.x, direction.z))
            # Use simple interpolation for rotation
            rotation_diff = target_rotation_y - self.entity.rotation_y
            # Handle angle wrapping
            if rotation_diff > 180:
                rotation_diff -= 360
            elif rotation_diff < -180:
                rotation_diff += 360
            self.entity.rotation_y += rotation_diff * time.dt * 3
        
        # Check if movement is complete
        if progress >= 1.0:
            self.is_moving = False
            self.grid_x, self.grid_z = self.path[self.current_path_index]
            
            # Schedule next movement
            invoke(self.start_next_movement, delay=0.8)


def update():
    """Global update function called every frame by Ursina."""
    # Update all pickers
    if hasattr(warehouse, 'pickers'):
        for picker in warehouse.pickers:
            picker.update_movement()


def main():
    """Main function to run the realistic warehouse simulation."""
    global warehouse
    
    print("=== Realistic 3D Warehouse Simulation ===")
    print("Multi-level shelving system with industrial design")
    print()
    
    # Create and run the warehouse environment
    warehouse = WarehouseEnvironment(grid_size=12)
    
    print()
    print("Features:")
    print("- Realistic multi-level shelving with inventory boxes")
    print("- Industrial color scheme and materials")
    print("- Proper aisles for navigation")
    print("- Realistic picker vehicle design")
    print("- Warehouse walls and concrete flooring")
    print()
    
    # Start the simulation
    warehouse.run()


if __name__ == "__main__":
    main()