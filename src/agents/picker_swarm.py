#!/usr/bin/env python3
"""
Warehouse Picker Swarm System
Multi-agent picker simulation with A* pathfinding, collision avoidance, and realistic movement
"""

import heapq
import time
import random
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import math

# Import warehouse components - using proper relative imports
try:
    # Try relative imports first (when run as module)
    from ..warehouse.structure import LargeWarehouse
    from ..utils.data_generator import WarehouseItem
    from ..shared_enums import CellType, ItemSize, WeightClass, PickerState, Direction
except ImportError:
    # Fallback for direct execution - add parent directories to path
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(parent_dir, 'warehouse'))
    sys.path.insert(0, os.path.join(parent_dir, 'utils'))
    sys.path.insert(0, parent_dir)
    
    from structure import LargeWarehouse
    from data_generator import WarehouseItem
    from shared_enums import CellType, ItemSize, WeightClass, PickerState, Direction

# Remove duplicate enum definitions since we now import from shared_enums

@dataclass
class OrderItem:
    """Single item in an order"""
    item_id: str
    item_name: str
    size: ItemSize
    location: Tuple[int, int, int]  # (x, y, level)
    pick_time: float  # Seconds to pick this item

@dataclass
class PickOrder:
    """Complete picking order"""
    order_id: str
    items: List[OrderItem]
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    created_time: float = 0.0

@dataclass
class LoadCapacity:
    """Picker's current load"""
    items_carried: List[OrderItem] = field(default_factory=list)
    load_points: int = 0  # Small=1, Medium=2, Large=4
    max_points: int = 4
    
    def can_carry(self, item: OrderItem) -> bool:
        """Check if picker can carry this item"""
        item_points = {ItemSize.SMALL: 1, ItemSize.MEDIUM: 2, ItemSize.LARGE: 4}[item.size]
        return self.load_points + item_points <= self.max_points
    
    def add_item(self, item: OrderItem) -> bool:
        """Add item to load if possible"""
        if self.can_carry(item):
            item_points = {ItemSize.SMALL: 1, ItemSize.MEDIUM: 2, ItemSize.LARGE: 4}[item.size]
            self.items_carried.append(item)
            self.load_points += item_points
            return True
        return False
    
    def get_movement_penalty(self) -> float:
        """Get movement speed penalty based on load"""
        return self.load_points * 0.1  # 0.1 seconds per load point

class AStar:
    """A* pathfinding for warehouse navigation"""
    
    def __init__(self, warehouse: LargeWarehouse):
        self.warehouse = warehouse
    
    def heuristic(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Manhattan distance heuristic"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions"""
        x, y = pos
        neighbors = []
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # N, S, E, W
            nx, ny = x + dx, y + dy
            if self.warehouse.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                  blocked_positions: Set[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        """
        Find shortest path from start to goal avoiding blocked positions
        Returns list of positions including start and goal
        """
        if blocked_positions is None:
            blocked_positions = set()
        
        if start == goal:
            return [start]
        
        # A* algorithm
        open_set = []
        heapq.heappush(open_set, (0, start))
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            for neighbor in self.get_neighbors(current):
                if neighbor in blocked_positions:
                    continue
                
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found

class WarehousePicker:
    """Individual picker agent"""
    
    def __init__(self, picker_id: str, warehouse: LargeWarehouse, pathfinder: AStar):
        self.picker_id = picker_id
        self.warehouse = warehouse
        self.pathfinder = pathfinder
        
        # Position and movement
        self.position = self.warehouse.entrances[0]  # Start at entrance
        self.target_position = None
        self.current_path = []
        self.path_index = 0
        
        # State management
        self.state = PickerState.IDLE
        self.load = LoadCapacity()
        self.current_order = None
        self.current_item_index = 0
        
        # Timing
        self.last_move_time = 0.0
        self.pick_start_time = 0.0
        self.wait_start_time = 0.0
        
        # Statistics
        self.total_distance = 0
        self.total_pick_time = 0.0
        self.total_wait_time = 0.0
        self.orders_completed = 0
    
    def assign_order(self, order: PickOrder) -> bool:
        """Assign new order to picker if idle"""
        if self.state == PickerState.IDLE and self.current_order is None:
            self.current_order = order
            self.current_item_index = 0
            self.load = LoadCapacity()  # Reset load
            self._plan_next_item()
            return True
        return False
    
    def _plan_next_item(self):
        """Plan path to next item in current order"""
        if not self.current_order or self.current_item_index >= len(self.current_order.items):
            # Order complete, go to exit
            self._plan_path_to_exit()
            return
        
        next_item = self.current_order.items[self.current_item_index]
        
        # Check if we can carry this item
        if not self.load.can_carry(next_item):
            # Go to exit first to drop off items
            self._plan_path_to_exit()
            return
        
        # Plan path to item location
        target_pos = (next_item.location[0], next_item.location[1])
        self.target_position = target_pos
        self.state = PickerState.MOVING_TO_ITEM
    
    def _plan_path_to_exit(self):
        """Plan path to warehouse exit"""
        exit_pos = self.warehouse.exit
        self.target_position = exit_pos
        self.state = PickerState.MOVING_TO_EXIT
    
    def update(self, current_time: float, other_pickers: List['WarehousePicker']) -> bool:
        """
        Update picker state and position
        Returns True if picker completed their order
        """
        if self.state == PickerState.IDLE:
            return False
        
        elif self.state == PickerState.MOVING_TO_ITEM:
            return self._update_movement(current_time, other_pickers)
        
        elif self.state == PickerState.PICKING:
            return self._update_picking(current_time)
        
        elif self.state == PickerState.MOVING_TO_EXIT:
            return self._update_movement(current_time, other_pickers)
        
        elif self.state == PickerState.WAITING:
            return self._update_waiting(current_time, other_pickers)
        
        elif self.state == PickerState.EXITING:
            return self._update_exiting(current_time)
        
        return False
    
    def _update_movement(self, current_time: float, other_pickers: List['WarehousePicker']) -> bool:
        """Update movement towards target"""
        if not self.target_position:
            return False
        
        # Check if we need to replan path
        if not self.current_path or self.path_index >= len(self.current_path):
            self._replan_path(other_pickers)
        
        # Check if movement time has elapsed
        move_delay = 1.0 + self.load.get_movement_penalty()  # Base 1 second + load penalty
        
        if current_time - self.last_move_time < move_delay:
            return False
        
        # Check for collisions before moving
        if self._check_for_collisions(other_pickers):
            self.state = PickerState.WAITING
            self.wait_start_time = current_time
            return False
        
        # Move to next position in path
        if self.path_index < len(self.current_path):
            new_position = self.current_path[self.path_index]
            self.position = new_position
            self.path_index += 1
            self.last_move_time = current_time
            self.total_distance += 1
        
        # Check if reached target
        if self.position == self.target_position:
            if self.state == PickerState.MOVING_TO_ITEM:
                self._start_picking(current_time)
            elif self.state == PickerState.MOVING_TO_EXIT:
                self._start_exiting(current_time)
        
        return False
    
    def _update_picking(self, current_time: float) -> bool:
        """Update picking process"""
        if not self.current_order:
            return False
        
        current_item = self.current_order.items[self.current_item_index]
        
        if current_time - self.pick_start_time >= current_item.pick_time:
            # Picking complete
            self.load.add_item(current_item)
            self.total_pick_time += current_item.pick_time
            self.current_item_index += 1
            
            # Plan next action
            self._plan_next_item()
        
        return False
    
    def _update_waiting(self, current_time: float, other_pickers: List['WarehousePicker']) -> bool:
        """Update waiting state (collision avoidance)"""
        # Check if path is clear now
        if not self._check_for_collisions(other_pickers):
            self.total_wait_time += current_time - self.wait_start_time
            self.state = PickerState.MOVING_TO_ITEM if self.target_position else PickerState.IDLE
        
        # Timeout: replan path if waiting too long
        elif current_time - self.wait_start_time > 5.0:  # 5 second timeout
            self._replan_path(other_pickers, avoid_congestion=True)
            self.state = PickerState.MOVING_TO_ITEM if self.target_position else PickerState.IDLE
        
        return False
    
    def _update_exiting(self, current_time: float) -> bool:
        """Update exit process"""
        # Simple exit: wait 2 seconds then complete order
        if current_time - self.pick_start_time >= 2.0:
            self.orders_completed += 1
            self.current_order = None
            self.current_item_index = 0
            self.load = LoadCapacity()
            self.state = PickerState.IDLE
            self.position = self.warehouse.entrances[0]  # Return to entrance
            return True
        
        return False
    
    def _start_picking(self, current_time: float):
        """Start picking current item"""
        self.state = PickerState.PICKING
        self.pick_start_time = current_time
    
    def _start_exiting(self, current_time: float):
        """Start exit process"""
        self.state = PickerState.EXITING
        self.pick_start_time = current_time
    
    def _replan_path(self, other_pickers: List['WarehousePicker'], avoid_congestion: bool = False):
        """Replan path to target avoiding other pickers"""
        if not self.target_position:
            return
        
        # Get positions of other pickers
        blocked_positions = set()
        for picker in other_pickers:
            if picker.picker_id != self.picker_id:
                blocked_positions.add(picker.position)
                # Also block next few positions in their path for congestion avoidance
                if avoid_congestion and hasattr(picker, 'current_path'):
                    for i in range(picker.path_index, min(picker.path_index + 3, len(picker.current_path))):
                        blocked_positions.add(picker.current_path[i])
        
        # Find new path
        new_path = self.pathfinder.find_path(self.position, self.target_position, blocked_positions)
        
        if new_path:
            self.current_path = new_path[1:]  # Exclude current position
            self.path_index = 0
        else:
            # No path found, try without avoiding other pickers
            self.current_path = self.pathfinder.find_path(self.position, self.target_position)
            self.path_index = 0
    
    def _check_for_collisions(self, other_pickers: List['WarehousePicker']) -> bool:
        """Check if next move would cause collision"""
        if self.path_index >= len(self.current_path):
            return False
        
        next_position = self.current_path[self.path_index]
        
        # Check if any other picker is at or moving to this position
        for picker in other_pickers:
            if picker.picker_id == self.picker_id:
                continue
            
            # Direct collision
            if picker.position == next_position:
                return True
            
            # Head-on collision (both moving towards each other)
            if (hasattr(picker, 'current_path') and 
                picker.path_index < len(picker.current_path) and
                picker.current_path[picker.path_index] == self.position and
                self.current_path[self.path_index] == picker.position):
                return True
        
        return False
    
    def get_status(self) -> Dict:
        """Get picker status for monitoring"""
        return {
            'id': self.picker_id,
            'position': self.position,
            'state': self.state.value,
            'load_points': self.load.load_points,
            'items_carried': len(self.load.items_carried),
            'current_order': self.current_order.order_id if self.current_order else None,
            'total_distance': self.total_distance,
            'orders_completed': self.orders_completed,
            'total_wait_time': self.total_wait_time
        }

class PickerSwarmManager:
    """Manages multiple pickers and order distribution"""
    
    def __init__(self, warehouse: LargeWarehouse, num_pickers: int = 3):
        self.warehouse = warehouse
        self.pathfinder = AStar(warehouse)
        
        # Create pickers
        self.pickers = []
        for i in range(num_pickers):
            picker = WarehousePicker(f"PICKER_{i+1:02d}", warehouse, self.pathfinder)
            self.pickers.append(picker)
        
        # Order management
        self.pending_orders = deque()
        self.completed_orders = []
        
        # Simulation state
        self.current_time = 0.0
        self.simulation_running = False
        
        print(f"Created picker swarm with {num_pickers} pickers")
    
    def add_order(self, order: PickOrder):
        """Add order to processing queue"""
        order.created_time = self.current_time
        self.pending_orders.append(order)
    
    def assign_orders(self):
        """Assign pending orders to available pickers"""
        available_pickers = [p for p in self.pickers if p.state == PickerState.IDLE]
        
        while self.pending_orders and available_pickers:
            order = self.pending_orders.popleft()
            picker = available_pickers.pop(0)
            
            if picker.assign_order(order):
                print(f"Assigned order {order.order_id} to {picker.picker_id}")
    
    def update_simulation(self, time_step: float = 0.1) -> Dict:
        """Update simulation by one time step"""
        self.current_time += time_step
        
        # Update all pickers
        completed_orders = 0
        for picker in self.pickers:
            if picker.update(self.current_time, self.pickers):
                completed_orders += 1
                print(f"{picker.picker_id} completed order at time {self.current_time:.1f}")
        
        # Assign new orders
        self.assign_orders()
        
        # Return simulation status
        return {
            'current_time': self.current_time,
            'pending_orders': len(self.pending_orders),
            'active_pickers': len([p for p in self.pickers if p.state != PickerState.IDLE]),
            'completed_orders': completed_orders,
            'picker_statuses': [p.get_status() for p in self.pickers]
        }
    
    def run_simulation(self, duration: float = 3600.0, time_step: float = 0.1, verbose: bool = True):
        """Run complete simulation for specified duration"""
        print(f"Starting simulation for {duration} seconds...")
        
        start_time = time.time()
        self.simulation_running = True
        
        while self.current_time < duration and self.simulation_running:
            status = self.update_simulation(time_step)
            
            if verbose and int(self.current_time) % 60 == 0:  # Print every minute
                active_pickers = status['active_pickers']
                pending = status['pending_orders']
                print(f"Time {self.current_time/60:.0f}min: {active_pickers} active pickers, {pending} pending orders")
        
        # Final statistics
        self.print_simulation_results()
        
        real_time = time.time() - start_time
        print(f"Simulation completed in {real_time:.2f} real seconds")
    
    def print_simulation_results(self):
        """Print detailed simulation results"""
        print(f"\n{'='*60}")
        print("PICKER SWARM SIMULATION RESULTS")
        print(f"{'='*60}")
        
        total_orders = sum(p.orders_completed for p in self.pickers)
        total_distance = sum(p.total_distance for p in self.pickers)
        total_wait_time = sum(p.total_wait_time for p in self.pickers)
        
        print(f"Simulation time: {self.current_time:.1f} seconds ({self.current_time/60:.1f} minutes)")
        print(f"Total orders completed: {total_orders}")
        print(f"Average order completion time: {self.current_time/total_orders:.1f} seconds" if total_orders > 0 else "No orders completed")
        print(f"Total distance traveled: {total_distance} cells")
        print(f"Total wait time (collisions): {total_wait_time:.1f} seconds")
        
        print(f"\nPicker Performance:")
        for picker in self.pickers:
            efficiency = (picker.orders_completed / (self.current_time / 60)) * 60  # Orders per hour
            print(f"  {picker.picker_id}: {picker.orders_completed} orders, {picker.total_distance} cells, {efficiency:.1f} orders/hour")
    
    def get_warehouse_occupancy_map(self) -> Dict[Tuple[int, int], str]:
        """Get current positions of all pickers for visualization"""
        occupancy = {}
        for picker in self.pickers:
            occupancy[picker.position] = picker.picker_id
        return occupancy


# Remove the demo and sample order creation - this will be handled by main.py
if __name__ == "__main__":
    print("Picker Swarm Module - Use main.py to run simulations")
    print("This module contains pure agent logic:")
    print("- WarehousePicker: Individual picker agent")
    print("- PickerSwarmManager: Multi-agent coordination")
    print("- AStar: Pathfinding algorithm")
    print("- LoadCapacity: Load management system")