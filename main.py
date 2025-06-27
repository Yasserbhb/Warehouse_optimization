#!/usr/bin/env python3
"""
Main Orchestration Layer for Warehouse Optimization Simulation
Coordinates all components: warehouse, items, orders, agents, and optimization
"""

import os
import sys
import time
import random
import json
from typing import List, Dict, Any

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import all components
from warehouse.structure import LargeWarehouse
from utils.data_generator import WarehouseDataGenerator, WarehouseItem
from agents.picker_swarm import PickerSwarmManager, PickOrder, OrderItem, PickerState
from shared_enums import ItemSize, WeightClass, CellType, SeasonalPattern

class WarehouseSimulation:
    """Main simulation orchestrator"""
    
    def __init__(self, 
                 warehouse_width: int = 30,
                 warehouse_depth: int = 30, 
                 warehouse_levels: int = 3,
                 num_items: int = 50,
                 num_pickers: int = 4):
        
        self.config = {
            'warehouse_width': warehouse_width,
            'warehouse_depth': warehouse_depth,
            'warehouse_levels': warehouse_levels,
            'num_items': num_items,
            'num_pickers': num_pickers
        }
        
        # Components (initialized in setup)
        self.warehouse = None
        self.items = None
        self.item_locations = {}  # item_id -> (x, y, level)
        self.picker_swarm = None
        
        # Simulation state
        self.current_time = 0.0
        self.orders_processed = 0
        self.simulation_results = {}
        
        print(f"Initialized warehouse simulation with config: {self.config}")
    
    def setup_warehouse(self) -> LargeWarehouse:
        """Create and configure warehouse infrastructure"""
        print(f"\n{'='*50}")
        print("STEP 1: CREATING WAREHOUSE INFRASTRUCTURE")
        print(f"{'='*50}")
        
        self.warehouse = LargeWarehouse(
            width=self.config['warehouse_width'],
            depth=self.config['warehouse_depth'], 
            levels=self.config['warehouse_levels']
        )
        
        # Print warehouse statistics
        stats = self.warehouse.get_warehouse_stats()
        print(f"Warehouse created:")
        print(f"  Dimensions: {stats['dimensions']}")
        print(f"  Storage locations: {stats['storage_locations']}")
        print(f"  Storage capacity: {stats['total_storage_capacity']} items")
        print(f"  Entrances: {stats['entrances']}")
        
        return self.warehouse
    
    def generate_items(self) -> List[WarehouseItem]:
        """Generate item catalog"""
        print(f"\n{'='*50}")
        print("STEP 2: GENERATING ITEM CATALOG")
        print(f"{'='*50}")
        
        generator = WarehouseDataGenerator(random_seed=42)
        self.items = generator.generate_items(self.config['num_items'])
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save items for reference
        generator.save_items_to_json("data/warehouse_items.json")
        generator.save_items_to_csv("data/warehouse_items.csv")
        
        # Print concise summary
        print(f"\nItem catalog summary:")
        categories = {}
        sizes = {}
        for item in self.items:
            categories[item.category] = categories.get(item.category, 0) + 1
            size_str = item.size.value if hasattr(item.size, 'value') else str(item.size)
            sizes[size_str] = sizes.get(size_str, 0) + 1
        
        print(f"  Categories: {dict(sorted(categories.items()))}")
        print(f"  Sizes: {dict(sorted(sizes.items()))}")
        
        frequencies = [item.base_daily_picks for item in self.items]
        print(f"  Pick frequency: {min(frequencies):.1f} - {max(frequencies):.1f} picks/day (avg: {sum(frequencies)/len(frequencies):.1f})")
        
        # Show top 5 items
        sorted_items = sorted(self.items, key=lambda x: x.base_daily_picks, reverse=True)
        print(f"  Top items: {', '.join([item.name for item in sorted_items[:5]])}")
        
        return self.items
        
        return self.items
    
    def place_items_in_warehouse(self, placement_strategy: str = "random") -> Dict[str, tuple]:
        """Place items in warehouse storage locations"""
        print(f"\n{'='*50}")
        print("STEP 3: PLACING ITEMS IN WAREHOUSE")
        print(f"{'='*50}")
        
        self.item_locations = {}
        placement_attempts = 0
        successful_placements = 0
        
        # Get all available shelf positions
        shelf_positions = []
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.get_cell_type(x, y) == CellType.SHELF:
                    shelf_positions.append((x, y))
        
        print(f"Found {len(shelf_positions)} shelf positions")
        print(f"Placing {len(self.items)} items using '{placement_strategy}' strategy...")
        
        if placement_strategy == "random":
            successful_placements = self._place_items_randomly(shelf_positions)
        elif placement_strategy == "frequency_based":
            successful_placements = self._place_items_by_frequency(shelf_positions)
        else:
            raise ValueError(f"Unknown placement strategy: {placement_strategy}")
        
        print(f"Successfully placed {successful_placements}/{len(self.items)} items")
        print(f"Item placement locations saved to item_locations dictionary")
        
        return self.item_locations
    
    def _place_items_randomly(self, shelf_positions: List[tuple]) -> int:
        """Random item placement strategy"""
        successful_placements = 0
        
        for item in self.items:
            placed = False
            attempts = 0
            max_attempts = 100
            
            while not placed and attempts < max_attempts:
                # Random position
                pos = random.choice(shelf_positions)
                x, y = pos
                
                # Choose appropriate level based on weight
                max_level = self._get_max_level_for_item(item)
                level = random.randint(1, max_level)
                
                # Try to place item
                if self.warehouse.place_item(item, x, y, level):
                    self.item_locations[item.id] = (x, y, level)
                    successful_placements += 1
                    placed = True
                
                attempts += 1
            
            if not placed:
                print(f"Warning: Could not place item {item.id}")
        
        return successful_placements
    
    def _place_items_by_frequency(self, shelf_positions: List[tuple]) -> int:
        """Frequency-based placement (high-frequency items near entrance)"""
        successful_placements = 0
        entrance = self.warehouse.entrances[0]
        
        # Sort items by frequency (high to low)
        sorted_items = sorted(self.items, key=lambda x: x.base_daily_picks, reverse=True)
        
        # Sort positions by distance from entrance (closest first)
        sorted_positions = sorted(shelf_positions, 
                                key=lambda pos: abs(pos[0] - entrance[0]) + abs(pos[1] - entrance[1]))
        
        position_index = 0
        
        for item in sorted_items:
            placed = False
            
            # Try positions starting from closest to entrance
            while position_index < len(sorted_positions) and not placed:
                pos = sorted_positions[position_index]
                x, y = pos
                
                # Choose appropriate level
                max_level = self._get_max_level_for_item(item)
                
                # Try each level
                for level in range(1, max_level + 1):
                    if self.warehouse.place_item(item, x, y, level):
                        self.item_locations[item.id] = (x, y, level)
                        successful_placements += 1
                        placed = True
                        break
                
                if not placed:
                    position_index += 1
        
        return successful_placements
    
    def _get_max_level_for_item(self, item: WarehouseItem) -> int:
        """Get maximum storage level based on item weight"""
        if item.weight_class == WeightClass.HEAVY:
            return 1
        elif item.weight_class == WeightClass.MEDIUM:
            return 2
        else:  # LIGHT
            return self.warehouse.levels
    
    def create_sample_orders(self, num_orders: int = 20) -> List[PickOrder]:
        """Create realistic sample orders from placed items"""
        print(f"\n{'='*50}")
        print("STEP 4: GENERATING SAMPLE ORDERS")
        print(f"{'='*50}")
        
        orders = []
        
        # Create order items from placed items
        available_order_items = []
        for item in self.items:
            if item.id in self.item_locations:
                location = self.item_locations[item.id]
                order_item = OrderItem(
                    item_id=item.id,
                    item_name=item.name,
                    size=item.size,
                    location=location,
                    pick_time=random.uniform(15, 45)  # 15-45 seconds
                )
                available_order_items.append(order_item)
        
        print(f"Created {len(available_order_items)} available order items from placed inventory")
        
        # Generate orders with realistic load constraints
        for i in range(num_orders):
            order_items = self._create_realistic_order(available_order_items)
            
            if order_items:
                order = PickOrder(
                    order_id=f"ORD_{i+1:03d}",
                    items=order_items,
                    priority=random.choices([1, 2, 3], weights=[70, 25, 5])[0]  # Most orders normal priority
                )
                orders.append(order)
        
        print(f"Generated {len(orders)} realistic orders")
        
        # Print order statistics
        total_items = sum(len(order.items) for order in orders)
        avg_items = total_items / len(orders) if orders else 0
        print(f"  Average items per order: {avg_items:.1f}")
        print(f"  Total items to pick: {total_items}")
        
        return orders
    
    def _create_realistic_order(self, available_items: List[OrderItem]) -> List[OrderItem]:
        """Create realistic order respecting load constraints"""
        order_items = []
        total_points = 0
        max_points = 4
        
        # Select 1-5 items for order
        target_items = random.randint(1, 5)
        attempts = 0
        max_attempts = 20
        
        while len(order_items) < target_items and total_points < max_points and attempts < max_attempts:
            item = random.choice(available_items)
            attempts += 1
            
            # Get item points using enum
            item_points = {ItemSize.SMALL: 1, ItemSize.MEDIUM: 2, ItemSize.LARGE: 4}[item.size]
            
            # Check if item fits and isn't already in order
            if (total_points + item_points <= max_points and 
                item.item_id not in [oi.item_id for oi in order_items]):
                order_items.append(item)
                total_points += item_points
        
        return order_items
    
    def setup_picker_swarm(self) -> PickerSwarmManager:
        """Initialize picker agents"""
        print(f"\n{'='*50}")
        print("STEP 5: CREATING PICKER SWARM")
        print(f"{'='*50}")
        
        self.picker_swarm = PickerSwarmManager(
            warehouse=self.warehouse,
            num_pickers=self.config['num_pickers']
        )
        
        print(f"Created swarm with {self.config['num_pickers']} picker agents")
        return self.picker_swarm
    
    def run_simulation(self, orders: List[PickOrder], duration: float = 3600.0) -> Dict[str, Any]:
        """Run complete warehouse simulation"""
        print(f"\n{'='*50}")
        print("STEP 6: RUNNING WAREHOUSE SIMULATION")
        print(f"{'='*50}")
        
        print(f"Starting simulation with {len(orders)} orders for {duration/60:.1f} minutes...")
        
        # Add all orders to swarm
        for order in orders:
            self.picker_swarm.add_order(order)
        
        # Run simulation
        start_time = time.time()
        self.picker_swarm.run_simulation(duration=duration, time_step=0.1, verbose=True)
        real_time = time.time() - start_time
        
        # Collect results
        results = {
            'simulation_duration': duration,
            'real_execution_time': real_time,
            'orders_processed': sum(p.orders_completed for p in self.picker_swarm.pickers),
            'total_distance': sum(p.total_distance for p in self.picker_swarm.pickers),
            'total_wait_time': sum(p.total_wait_time for p in self.picker_swarm.pickers),
            'picker_performance': []
        }
        
        # Individual picker performance
        for picker in self.picker_swarm.pickers:
            performance = {
                'picker_id': picker.picker_id,
                'orders_completed': picker.orders_completed,
                'distance_traveled': picker.total_distance,
                'wait_time': picker.total_wait_time,
                'efficiency': (picker.orders_completed / (duration / 3600)) if duration > 0 else 0  # orders per hour
            }
            results['picker_performance'].append(performance)
        
        self.simulation_results = results
        return results
    
    def print_simulation_summary(self):
        """Print comprehensive simulation results"""
        if not self.simulation_results:
            print("No simulation results to display")
            return
        
        results = self.simulation_results
        
        print(f"\n{'='*60}")
        print("WAREHOUSE SIMULATION SUMMARY")
        print(f"{'='*60}")
        
        print(f"Configuration:")
        print(f"  Warehouse: {self.config['warehouse_width']}x{self.config['warehouse_depth']}x{self.config['warehouse_levels']}")
        print(f"  Items: {self.config['num_items']}")
        print(f"  Pickers: {self.config['num_pickers']}")
        
        print(f"\nPerformance Results:")
        print(f"  Simulation time: {results['simulation_duration']/60:.1f} minutes")
        print(f"  Orders completed: {results['orders_processed']}")
        print(f"  Total distance: {results['total_distance']} cells")
        print(f"  Total wait time: {results['total_wait_time']:.1f} seconds")
        
        if results['orders_processed'] > 0:
            avg_time = results['simulation_duration'] / results['orders_processed']
            print(f"  Average order time: {avg_time:.1f} seconds")
            print(f"  Orders per hour: {results['orders_processed'] / (results['simulation_duration'] / 3600):.1f}")
        
        print(f"\nPicker Performance:")
        for perf in results['picker_performance']:
            print(f"  {perf['picker_id']}: {perf['orders_completed']} orders, "
                  f"{perf['distance_traveled']} cells, {perf['efficiency']:.1f} orders/hour")
        
        print(f"\nExecution time: {results['real_execution_time']:.2f} seconds")
    
    def save_results(self, filename: str = "simulation_results.json"):
        """Save simulation results to file"""
        if self.simulation_results:
            # Add configuration to results
            save_data = {
                'configuration': self.config,
                'item_locations': self.item_locations,
                'simulation_results': self.simulation_results
            }
            
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            
            print(f"Results saved to {filepath}")


def run_basic_simulation():
    """Run a basic warehouse simulation"""
    print("="*70)
    print("WAREHOUSE OPTIMIZATION SIMULATION - BASIC DEMO")
    print("="*70)
    
    # Create simulation
    sim = WarehouseSimulation(
        warehouse_width=25,
        warehouse_depth=25,
        warehouse_levels=2,
        num_items=30,
        num_pickers=3
    )
    
    # Setup all components
    sim.setup_warehouse()
    sim.generate_items()
    sim.place_items_in_warehouse(placement_strategy="frequency_based")
    sim.setup_picker_swarm()
    
    # Create and run orders
    orders = sim.create_sample_orders(num_orders=15)
    results = sim.run_simulation(orders, duration=600.0)  # 10 minute simulation
    
    # Display results
    sim.print_simulation_summary()
    sim.save_results("basic_simulation_results.json")
    
    print(f"\n✅ Basic simulation complete!")
    return sim


def run_comparison_simulation():
    """Run comparison between different placement strategies"""
    print("="*70)
    print("WAREHOUSE OPTIMIZATION SIMULATION - STRATEGY COMPARISON")
    print("="*70)
    
    strategies = ["random", "frequency_based"]
    results_comparison = {}
    
    for strategy in strategies:
        print(f"\n🔄 Testing placement strategy: {strategy.upper()}")
        
        sim = WarehouseSimulation(
            warehouse_width=20,
            warehouse_depth=20,
            warehouse_levels=2,
            num_items=25,
            num_pickers=3
        )
        
        # Setup
        sim.setup_warehouse()
        sim.generate_items()
        sim.place_items_in_warehouse(placement_strategy=strategy)
        sim.setup_picker_swarm()
        
        # Run same orders for fair comparison
        random.seed(42)  # Consistent orders
        orders = sim.create_sample_orders(num_orders=12)
        results = sim.run_simulation(orders, duration=480.0)  # 8 minute simulation
        
        # Store results
        results_comparison[strategy] = {
            'orders_completed': results['orders_processed'],
            'total_distance': results['total_distance'],
            'avg_order_time': results['simulation_duration'] / results['orders_processed'] if results['orders_processed'] > 0 else 0
        }
        
        print(f"✅ {strategy} completed: {results['orders_processed']} orders, {results['total_distance']} cells")
    
    # Print comparison
    print(f"\n{'='*60}")
    print("PLACEMENT STRATEGY COMPARISON")
    print(f"{'='*60}")
    
    for strategy, results in results_comparison.items():
        print(f"{strategy.capitalize():15s}: {results['orders_completed']:2d} orders, "
              f"{results['total_distance']:4d} cells, {results['avg_order_time']:5.1f}s avg")
    
    # Calculate improvement
    if len(results_comparison) == 2:
        random_results = results_comparison['random']
        freq_results = results_comparison['frequency_based']
        
        if random_results['total_distance'] > 0:
            distance_improvement = (random_results['total_distance'] - freq_results['total_distance']) / random_results['total_distance'] * 100
            print(f"\nFrequency-based placement improved distance by {distance_improvement:.1f}%")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Warehouse Optimization Simulation')
    parser.add_argument('--mode', choices=['basic', 'comparison'], default='basic',
                       help='Simulation mode to run')
    parser.add_argument('--width', type=int, default=25, help='Warehouse width')
    parser.add_argument('--depth', type=int, default=25, help='Warehouse depth')
    parser.add_argument('--levels', type=int, default=2, help='Warehouse levels')
    parser.add_argument('--items', type=int, default=30, help='Number of items')
    parser.add_argument('--pickers', type=int, default=3, help='Number of pickers')
    parser.add_argument('--orders', type=int, default=15, help='Number of orders')
    parser.add_argument('--duration', type=float, default=600.0, help='Simulation duration (seconds)')
    
    args = parser.parse_args()
    
    if args.mode == 'basic':
        sim = WarehouseSimulation(
            warehouse_width=args.width,
            warehouse_depth=args.depth,
            warehouse_levels=args.levels,
            num_items=args.items,
            num_pickers=args.pickers
        )
        
        sim.setup_warehouse()
        sim.generate_items()
        sim.place_items_in_warehouse(placement_strategy="frequency_based")
        sim.setup_picker_swarm()
        
        orders = sim.create_sample_orders(num_orders=args.orders)
        sim.run_simulation(orders, duration=args.duration)
        sim.print_simulation_summary()
        sim.save_results()
        
    elif args.mode == 'comparison':
        run_comparison_simulation()


if __name__ == "__main__":
    # Run basic simulation if no arguments provided
    if len(sys.argv) == 1:
        run_basic_simulation()
    else:
        main()