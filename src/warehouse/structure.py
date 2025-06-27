import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# Import shared enums
try:
    from ..shared_enums import CellType, ItemSize, WeightClass
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from shared_enums import CellType, ItemSize, WeightClass

@dataclass
class Item:
    """Warehouse item definition"""
    id: str
    size: ItemSize
    weight_class: WeightClass
    daily_picks: float
    category: str
    orientation: Tuple[int, int] = (1, 1)  # (width, depth) in cells

@dataclass
class StorageCell:
    """Individual storage cell that can hold multiple items"""
    max_capacity: Dict[ItemSize, int]
    current_items: List[Item]
    level: int
    x: int
    y: int
    
    def __post_init__(self):
        if not hasattr(self, 'max_capacity') or not self.max_capacity:
            self.max_capacity = {
                ItemSize.SMALL: 4,
                ItemSize.MEDIUM: 2, 
                ItemSize.LARGE: 1
            }
        if not hasattr(self, 'current_items'):
            self.current_items = []
    
    def can_store_item(self, item: Item) -> bool:
        """Check if this cell can store the given item"""
        # Check weight restrictions
        if item.weight_class == WeightClass.HEAVY and self.level > 1:
            return False
        if item.weight_class == WeightClass.MEDIUM and self.level > 2:
            return False
        
        # Count current items by size
        current_count = {size: 0 for size in ItemSize}
        for current_item in self.current_items:
            current_count[current_item.size] += 1
        
        # Calculate space used (in "small item units")
        space_used = (current_count[ItemSize.LARGE] * 4 + 
                     current_count[ItemSize.MEDIUM] * 2 + 
                     current_count[ItemSize.SMALL])
        
        # Calculate space needed for new item - handle both enum and string
        if hasattr(item.size, 'value'):
            size_str = item.size.value
        else:
            size_str = str(item.size)
        
        space_needed_map = {'small': 1, 'medium': 2, 'large': 4}
        space_needed = space_needed_map.get(size_str, 1)
        
        return space_used + space_needed <= 4
    
    def add_item(self, item: Item) -> bool:
        """Add item to this cell if possible"""
        if self.can_store_item(item):
            self.current_items.append(item)
            return True
        return False
    
    def remove_item(self, item_id: str) -> Optional[Item]:
        """Remove item by ID and return it"""
        for i, item in enumerate(self.current_items):
            if item.id == item_id:
                return self.current_items.pop(i)
        return None
    
    def get_occupancy_rate(self) -> float:
        """Get current occupancy as percentage (0.0 to 1.0)"""
        if not self.current_items:
            return 0.0
        
        # Count space used by checking each item's size
        space_used = 0
        for item in self.current_items:
            if hasattr(item.size, 'value'):
                size_str = item.size.value
            else:
                size_str = str(item.size)
            
            size_points = {'small': 1, 'medium': 2, 'large': 4}
            space_used += size_points.get(size_str, 1)
        
        return space_used / 4.0

class LargeWarehouse:
    """Large-scale warehouse with multiple levels and realistic layout"""
    
    def __init__(self, width=36, depth=36, levels=3):
        """
        Initialize large warehouse
        
        Args:
            width: Warehouse width (default 36)
            depth: Warehouse depth (default 36) 
            levels: Number of storage levels (default 3)
        """
        self.width = width
        self.depth = depth
        self.levels = levels
        
        # Grid: 0=cell_type, storage handled separately
        self.layout_grid = np.zeros((width, depth), dtype=int)
        
        # Storage cells for each shelf location and level
        self.storage_cells: Dict[Tuple[int, int, int], StorageCell] = {}
        
        # Worker positions (can only have 1 worker per cell)
        self.worker_positions: Dict[Tuple[int, int], str] = {}
        
        # Important locations
        self.entrances = []
        self.exit = None
        self.main_hallway_cells = []
        
        # Generate warehouse layout
        self._create_warehouse_layout()
        self._initialize_storage_cells()
        
        print(f"Created large warehouse: {width}x{depth} with {levels} levels")
        print(f"Total storage cells: {len(self.storage_cells)}")
        print(f"Entrances: {len(self.entrances)}, Exit: {self.exit}")
    
    def _create_warehouse_layout(self):
        """Create the warehouse floor plan"""
        # Fill with walls initially
        self.layout_grid.fill(CellType.WALL.value)
        
        # Create main hallway (horizontal through middle)
        main_hallway_y = self.depth // 2
        for x in range(2, self.width - 2):
            for y in range(main_hallway_y - 1, main_hallway_y + 2):  # 3 cells wide
                self.layout_grid[x, y] = CellType.MAIN_HALLWAY.value
                self.main_hallway_cells.append((x, y))
        
        # Create storage zones with aisles
        self._create_storage_zones()
        
        # Create entrances and exit
        self._create_entry_exit_points()
        
        # Add cross-aisles for connectivity
        self._create_cross_aisles()
    
    def _create_storage_zones(self):
        """Create storage areas with shelves and aisles"""
        # Zone 1: Upper area (above main hallway)
        self._create_zone(
            start_x=3, end_x=self.width-3,
            start_y=3, end_y=self.depth//2 - 2,
            zone_id="upper"
        )
        
        # Zone 2: Lower area (below main hallway) 
        self._create_zone(
            start_x=3, end_x=self.width-3,
            start_y=self.depth//2 + 3, end_y=self.depth-3,
            zone_id="lower"
        )
    
    def _create_zone(self, start_x, end_x, start_y, end_y, zone_id):
        """Create a storage zone with alternating shelves and aisles"""
        current_x = start_x
        
        while current_x < end_x:
            # Determine if this should be shelf or aisle
            if (current_x - start_x) % 4 == 0 or (current_x - start_x) % 4 == 1:
                # Create shelf rows (2 cells wide)
                for x in range(current_x, min(current_x + 2, end_x)):
                    for y in range(start_y, end_y):
                        if x < self.width and y < self.depth:
                            self.layout_grid[x, y] = CellType.SHELF.value
                current_x += 2
            else:
                # Create aisle (2 cells wide for bidirectional traffic)
                for x in range(current_x, min(current_x + 2, end_x)):
                    for y in range(start_y, end_y):
                        if x < self.width and y < self.depth:
                            self.layout_grid[x, y] = CellType.AISLE.value
                current_x += 2
    
    def _create_entry_exit_points(self):
        """Create entrance and exit points"""
        # Entrance 1: Left side of main hallway
        entrance1 = (0, self.depth // 2)
        self.layout_grid[0, self.depth // 2] = CellType.ENTRANCE.value
        self.layout_grid[1, self.depth // 2] = CellType.ENTRANCE.value
        self.entrances.append(entrance1)
        
        # Entrance 2: Right side of main hallway  
        entrance2 = (0, self.depth // 2 + 1)
        self.layout_grid[0, self.depth // 2 + 1] = CellType.ENTRANCE.value
        self.layout_grid[1, self.depth // 2 + 1] = CellType.ENTRANCE.value
        self.entrances.append(entrance2)
        
        # Exit: Opposite side
        exit_point = (self.width - 1, self.depth // 2)
        self.layout_grid[self.width - 1, self.depth // 2] = CellType.EXIT.value
        self.layout_grid[self.width - 2, self.depth // 2] = CellType.EXIT.value
        self.exit = exit_point
    
    def _create_cross_aisles(self):
        """Create cross-aisles for zone connectivity"""
        # Vertical cross-aisles every 8 cells
        for x in range(8, self.width - 2, 8):
            # Upper zone cross-aisle
            for y in range(3, self.depth // 2 - 2):
                if self.layout_grid[x, y] == CellType.SHELF.value:
                    self.layout_grid[x, y] = CellType.CROSS_AISLE.value
            
            # Lower zone cross-aisle
            for y in range(self.depth // 2 + 3, self.depth - 3):
                if self.layout_grid[x, y] == CellType.SHELF.value:
                    self.layout_grid[x, y] = CellType.CROSS_AISLE.value
    
    def _initialize_storage_cells(self):
        """Initialize storage cells for all shelf locations"""
        for x in range(self.width):
            for y in range(self.depth):
                if self.layout_grid[x, y] == CellType.SHELF.value:
                    # Create storage cell for each level
                    for level in range(1, self.levels + 1):
                        cell = StorageCell(
                            max_capacity={
                                ItemSize.SMALL: 4,
                                ItemSize.MEDIUM: 2,
                                ItemSize.LARGE: 1
                            },
                            current_items=[],
                            level=level,
                            x=x,
                            y=y
                        )
                        self.storage_cells[(x, y, level)] = cell
    
    def get_cell_type(self, x: int, y: int) -> CellType:
        """Get the type of cell at given coordinates"""
        if 0 <= x < self.width and 0 <= y < self.depth:
            return CellType(self.layout_grid[x, y])
        return CellType.WALL
    
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a cell is walkable for workers"""
        cell_type = self.get_cell_type(x, y)
        walkable_types = {
            CellType.AISLE, 
            CellType.MAIN_HALLWAY, 
            CellType.CROSS_AISLE,
            CellType.ENTRANCE,
            CellType.EXIT
        }
        return cell_type in walkable_types
    
    def can_place_worker(self, x: int, y: int, worker_id: str) -> bool:
        """Check if a worker can be placed at given position"""
        return (self.is_walkable(x, y) and 
                (x, y) not in self.worker_positions)
    
    def place_worker(self, x: int, y: int, worker_id: str) -> bool:
        """Place a worker at given position"""
        if self.can_place_worker(x, y, worker_id):
            self.worker_positions[(x, y)] = worker_id
            return True
        return False
    
    def remove_worker(self, worker_id: str) -> Optional[Tuple[int, int]]:
        """Remove worker and return their position"""
        for pos, wid in self.worker_positions.items():
            if wid == worker_id:
                del self.worker_positions[pos]
                return pos
        return None
    
    def get_storage_cell(self, x: int, y: int, level: int) -> Optional[StorageCell]:
        """Get storage cell at given coordinates and level"""
        return self.storage_cells.get((x, y, level))
    
    def place_item(self, item: Item, x: int, y: int, level: int) -> bool:
        """Place an item in a storage cell"""
        cell = self.get_storage_cell(x, y, level)
        if cell and cell.can_store_item(item):
            return cell.add_item(item)
        return False
    
    def remove_item(self, item_id: str, x: int, y: int, level: int) -> Optional[Item]:
        """Remove an item from a storage cell"""
        cell = self.get_storage_cell(x, y, level)
        if cell:
            return cell.remove_item(item_id)
        return None
    
    def find_item(self, item_id: str) -> Optional[Tuple[int, int, int, Item]]:
        """Find an item in the warehouse and return its location"""
        for (x, y, level), cell in self.storage_cells.items():
            for item in cell.current_items:
                if item.id == item_id:
                    return (x, y, level, item)
        return None
    
    def get_accessible_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get walkable neighboring cells for pathfinding"""
        neighbors = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # N, S, E, W
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_warehouse_stats(self) -> Dict:
        """Get comprehensive warehouse statistics"""
        total_shelf_cells = sum(1 for cell_type in self.layout_grid.flat 
                               if cell_type == CellType.SHELF.value)
        total_aisle_cells = sum(1 for cell_type in self.layout_grid.flat 
                               if cell_type in [CellType.AISLE.value, 
                                              CellType.MAIN_HALLWAY.value,
                                              CellType.CROSS_AISLE.value])
        
        total_storage_capacity = len(self.storage_cells) * 4  # 4 small items per cell
        current_items = sum(len(cell.current_items) for cell in self.storage_cells.values())
        
        stats = {
            'dimensions': f"{self.width}x{self.depth}x{self.levels}",
            'total_cells': self.width * self.depth,
            'shelf_cells': total_shelf_cells,
            'aisle_cells': total_aisle_cells, 
            'storage_locations': len(self.storage_cells),
            'total_storage_capacity': total_storage_capacity,
            'current_items': current_items,
            'occupancy_rate': current_items / total_storage_capacity if total_storage_capacity > 0 else 0,
            'entrances': len(self.entrances),
            'workers': len(self.worker_positions)
        }
        
        return stats
    
    def print_layout(self, level: Optional[int] = None):
        """Print a visual representation of the warehouse layout"""
        symbols = {
            CellType.WALL: '█',
            CellType.SHELF: '▢',
            CellType.AISLE: '·',
            CellType.MAIN_HALLWAY: '═',
            CellType.CROSS_AISLE: '┼',
            CellType.ENTRANCE: 'E',
            CellType.EXIT: 'X'
        }
        
        print(f"\nWarehouse Layout ({self.width}x{self.depth}):")
        print("═" * (self.width + 2))
        
        for y in range(self.depth):
            row = "║"
            for x in range(self.width):
                cell_type = CellType(self.layout_grid[x, y])
                symbol = symbols.get(cell_type, '?')
                
                # Show workers
                if (x, y) in self.worker_positions:
                    symbol = '◉'
                
                row += symbol
            row += "║"
            print(row)
        
        print("═" * (self.width + 2))
        print("Legend: ▢=Shelf, ·=Aisle, ═=Main Hallway, ┼=Cross-aisle, E=Entrance, X=Exit, ◉=Worker")