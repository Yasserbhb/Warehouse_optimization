#!/usr/bin/env python3
"""
Comprehensive test suite for the Large Warehouse Structure
Tests all functionality including storage, worker placement, and pathfinding
"""

import unittest
import random
from src.warehouse.structure import (
    LargeWarehouse, Item, ItemSize, WeightClass, 
    CellType, StorageCell
)

class TestStorageCell(unittest.TestCase):
    """Test storage cell functionality"""
    
    def setUp(self):
        """Set up test storage cell"""
        self.cell = StorageCell(
            max_capacity={ItemSize.SMALL: 4, ItemSize.MEDIUM: 2, ItemSize.LARGE: 1},
            current_items=[],
            level=1,
            x=5,
            y=5
        )
    
    def test_cell_creation(self):
        """Test storage cell initialization"""
        self.assertEqual(self.cell.level, 1)
        self.assertEqual(self.cell.x, 5)
        self.assertEqual(self.cell.y, 5)
        self.assertEqual(len(self.cell.current_items), 0)
        self.assertEqual(self.cell.get_occupancy_rate(), 0.0)
    
    def test_small_item_storage(self):
        """Test storing small items (4 per cell)"""
        items = [
            Item("SMALL_01", ItemSize.SMALL, WeightClass.LIGHT, 1.0, "electronics"),
            Item("SMALL_02", ItemSize.SMALL, WeightClass.LIGHT, 2.0, "electronics"),
            Item("SMALL_03", ItemSize.SMALL, WeightClass.LIGHT, 1.5, "electronics"),
            Item("SMALL_04", ItemSize.SMALL, WeightClass.LIGHT, 0.5, "electronics")
        ]
        
        # Should be able to store all 4 small items
        for item in items:
            self.assertTrue(self.cell.can_store_item(item))
            self.assertTrue(self.cell.add_item(item))
        
        # Should be full now
        extra_item = Item("SMALL_05", ItemSize.SMALL, WeightClass.LIGHT, 1.0, "electronics")
        self.assertFalse(self.cell.can_store_item(extra_item))
        self.assertEqual(self.cell.get_occupancy_rate(), 1.0)
    
    def test_medium_item_storage(self):
        """Test storing medium items (2 per cell)"""
        items = [
            Item("MED_01", ItemSize.MEDIUM, WeightClass.MEDIUM, 5.0, "tools"),
            Item("MED_02", ItemSize.MEDIUM, WeightClass.MEDIUM, 3.0, "tools")
        ]
        
        for item in items:
            self.assertTrue(self.cell.add_item(item))
        
        # Should be full
        extra_item = Item("MED_03", ItemSize.MEDIUM, WeightClass.MEDIUM, 2.0, "tools")
        self.assertFalse(self.cell.can_store_item(extra_item))
        self.assertEqual(self.cell.get_occupancy_rate(), 1.0)
    
    def test_large_item_storage(self):
        """Test storing large items (1 per cell)"""
        large_item = Item("LARGE_01", ItemSize.LARGE, WeightClass.HEAVY, 10.0, "appliances")
        
        self.assertTrue(self.cell.add_item(large_item))
        self.assertEqual(self.cell.get_occupancy_rate(), 1.0)
        
        # Should not be able to add anything else
        small_item = Item("SMALL_01", ItemSize.SMALL, WeightClass.LIGHT, 1.0, "electronics")
        self.assertFalse(self.cell.can_store_item(small_item))
    
    def test_weight_restrictions(self):
        """Test weight class restrictions by level"""
        # Level 1 cell - should accept all weights
        level1_cell = StorageCell({}, [], 1, 0, 0)
        heavy_item = Item("HEAVY_01", ItemSize.LARGE, WeightClass.HEAVY, 15.0, "machinery")
        self.assertTrue(level1_cell.can_store_item(heavy_item))
        
        # Level 2 cell - should reject heavy items
        level2_cell = StorageCell({}, [], 2, 0, 0)
        self.assertFalse(level2_cell.can_store_item(heavy_item))
        
        # Level 3 cell - should reject heavy and medium items
        level3_cell = StorageCell({}, [], 3, 0, 0)
        medium_item = Item("MED_01", ItemSize.MEDIUM, WeightClass.MEDIUM, 5.0, "tools")
        self.assertFalse(level3_cell.can_store_item(heavy_item))
        self.assertFalse(level3_cell.can_store_item(medium_item))
        
        light_item = Item("LIGHT_01", ItemSize.SMALL, WeightClass.LIGHT, 1.0, "electronics")
        self.assertTrue(level3_cell.can_store_item(light_item))
    
    def test_mixed_item_storage(self):
        """Test storing mixed item sizes"""
        # 1 medium + 2 small = full capacity
        medium_item = Item("MED_01", ItemSize.MEDIUM, WeightClass.LIGHT, 3.0, "books")
        small_item1 = Item("SMALL_01", ItemSize.SMALL, WeightClass.LIGHT, 1.0, "electronics")
        small_item2 = Item("SMALL_02", ItemSize.SMALL, WeightClass.LIGHT, 1.5, "electronics")
        
        self.assertTrue(self.cell.add_item(medium_item))
        self.assertTrue(self.cell.add_item(small_item1))
        self.assertTrue(self.cell.add_item(small_item2))
        
        # Should be full now
        extra_small = Item("SMALL_03", ItemSize.SMALL, WeightClass.LIGHT, 1.0, "electronics")
        self.assertFalse(self.cell.can_store_item(extra_small))
        self.assertEqual(self.cell.get_occupancy_rate(), 1.0)


class TestLargeWarehouse(unittest.TestCase):
    """Test large warehouse functionality"""
    
    def setUp(self):
        """Set up test warehouse"""
        self.warehouse = LargeWarehouse(width=20, depth=20, levels=3)
    
    def test_warehouse_creation(self):
        """Test warehouse initialization"""
        self.assertEqual(self.warehouse.width, 20)
        self.assertEqual(self.warehouse.depth, 20)
        self.assertEqual(self.warehouse.levels, 3)
        self.assertEqual(len(self.warehouse.entrances), 2)
        self.assertIsNotNone(self.warehouse.exit)
        
        # Check that we have storage cells
        self.assertGreater(len(self.warehouse.storage_cells), 0)
        print(f"Created warehouse with {len(self.warehouse.storage_cells)} storage cells")
    
    def test_cell_types(self):
        """Test different cell types are created correctly"""
        cell_types_found = set()
        
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                cell_type = self.warehouse.get_cell_type(x, y)
                cell_types_found.add(cell_type)
        
        # Should have multiple cell types
        expected_types = {CellType.SHELF, CellType.AISLE, CellType.MAIN_HALLWAY}
        self.assertTrue(expected_types.issubset(cell_types_found))
        print(f"Found cell types: {[ct.name for ct in cell_types_found]}")
    
    def test_walkable_areas(self):
        """Test that walkable areas are properly identified"""
        walkable_count = 0
        
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.is_walkable(x, y):
                    walkable_count += 1
        
        self.assertGreater(walkable_count, 0)
        print(f"Found {walkable_count} walkable cells")
    
    def test_worker_placement(self):
        """Test worker placement and movement"""
        # Find a walkable position
        walkable_pos = None
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.is_walkable(x, y):
                    walkable_pos = (x, y)
                    break
            if walkable_pos:
                break
        
        self.assertIsNotNone(walkable_pos)
        
        # Place worker
        worker_id = "WORKER_01"
        self.assertTrue(self.warehouse.place_worker(walkable_pos[0], walkable_pos[1], worker_id))
        
        # Should not be able to place another worker in same position
        self.assertFalse(self.warehouse.place_worker(walkable_pos[0], walkable_pos[1], "WORKER_02"))
        
        # Remove worker
        removed_pos = self.warehouse.remove_worker(worker_id)
        self.assertEqual(removed_pos, walkable_pos)
    
    def test_item_placement_and_retrieval(self):
        """Test item storage and retrieval"""
        # Find a shelf cell
        shelf_pos = None
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.get_cell_type(x, y) == CellType.SHELF:
                    shelf_pos = (x, y)
                    break
            if shelf_pos:
                break
        
        self.assertIsNotNone(shelf_pos)
        
        # Create test item
        test_item = Item("TEST_ITEM_01", ItemSize.SMALL, WeightClass.LIGHT, 5.0, "test_category")
        
        # Place item
        self.assertTrue(self.warehouse.place_item(test_item, shelf_pos[0], shelf_pos[1], 1))
        
        # Find item
        found = self.warehouse.find_item("TEST_ITEM_01")
        self.assertIsNotNone(found)
        self.assertEqual(found[0], shelf_pos[0])  # x
        self.assertEqual(found[1], shelf_pos[1])  # y
        self.assertEqual(found[2], 1)             # level
        self.assertEqual(found[3].id, "TEST_ITEM_01")
        
        # Remove item
        removed_item = self.warehouse.remove_item("TEST_ITEM_01", shelf_pos[0], shelf_pos[1], 1)
        self.assertIsNotNone(removed_item)
        self.assertEqual(removed_item.id, "TEST_ITEM_01")
        
        # Should not find item anymore
        not_found = self.warehouse.find_item("TEST_ITEM_01")
        self.assertIsNone(not_found)
    
    def test_pathfinding_neighbors(self):
        """Test neighbor finding for pathfinding"""
        # Find an aisle position
        aisle_pos = None
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.get_cell_type(x, y) == CellType.AISLE:
                    aisle_pos = (x, y)
                    break
            if aisle_pos:
                break
        
        self.assertIsNotNone(aisle_pos)
        
        neighbors = self.warehouse.get_accessible_neighbors(aisle_pos[0], aisle_pos[1])
        self.assertGreater(len(neighbors), 0)
        
        # All neighbors should be walkable
        for nx, ny in neighbors:
            self.assertTrue(self.warehouse.is_walkable(nx, ny))
    
    def test_warehouse_statistics(self):
        """Test warehouse statistics generation"""
        stats = self.warehouse.get_warehouse_stats()
        
        required_keys = [
            'dimensions', 'total_cells', 'shelf_cells', 'aisle_cells',
            'storage_locations', 'total_storage_capacity', 'current_items',
            'occupancy_rate', 'entrances', 'workers'
        ]
        
        for key in required_keys:
            self.assertIn(key, stats)
        
        # Check reasonable values
        self.assertGreater(stats['shelf_cells'], 0)
        self.assertGreater(stats['aisle_cells'], 0)
        self.assertGreater(stats['storage_locations'], 0)
        self.assertEqual(stats['entrances'], 2)
        
        print(f"Warehouse Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


class TestWarehouseStressTest(unittest.TestCase):
    """Stress tests for large warehouse operations"""
    
    def setUp(self):
        """Set up large warehouse for stress testing"""
        self.warehouse = LargeWarehouse(width=36, depth=36, levels=3)
    
    def test_large_warehouse_creation(self):
        """Test creation of full-size warehouse"""
        self.assertEqual(self.warehouse.width, 36)
        self.assertEqual(self.warehouse.depth, 36)
        self.assertEqual(self.warehouse.levels, 3)
        
        stats = self.warehouse.get_warehouse_stats()
        print(f"\nLarge Warehouse Created:")
        print(f"  Total cells: {stats['total_cells']}")
        print(f"  Storage locations: {stats['storage_locations']}")
        print(f"  Storage capacity: {stats['total_storage_capacity']} items")
    
    def test_massive_item_placement(self):
        """Test placing many items throughout warehouse"""
        items_placed = 0
        max_items_to_place = 100
        
        # Generate test items
        test_items = []
        for i in range(max_items_to_place):
            size = random.choice(list(ItemSize))
            weight = random.choice(list(WeightClass))
            item = Item(
                id=f"STRESS_ITEM_{i:03d}",
                size=size,
                weight_class=weight,
                daily_picks=random.uniform(0.5, 20.0),
                category=random.choice(["electronics", "tools", "books", "clothing"])
            )
            test_items.append(item)
        
        # Try to place items in random valid locations
        shelf_positions = []
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.get_cell_type(x, y) == CellType.SHELF:
                    shelf_positions.append((x, y))
        
        for item in test_items:
            placed = False
            attempts = 0
            while not placed and attempts < 20:  # Try up to 20 random positions
                pos = random.choice(shelf_positions)
                level = random.randint(1, self.warehouse.levels)
                
                if self.warehouse.place_item(item, pos[0], pos[1], level):
                    items_placed += 1
                    placed = True
                attempts += 1
        
        print(f"Successfully placed {items_placed}/{max_items_to_place} items")
        self.assertGreater(items_placed, 0)
        
        # Verify we can find all placed items
        found_items = 0
        for item in test_items[:items_placed]:
            if self.warehouse.find_item(item.id) is not None:
                found_items += 1
        
        self.assertEqual(found_items, items_placed)
        print(f"Successfully found all {found_items} placed items")
    
    def test_multiple_workers(self):
        """Test placing multiple workers"""
        workers_placed = 0
        max_workers = 10
        
        # Find walkable positions
        walkable_positions = []
        for x in range(self.warehouse.width):
            for y in range(self.warehouse.depth):
                if self.warehouse.is_walkable(x, y):
                    walkable_positions.append((x, y))
        
        print(f"Found {len(walkable_positions)} walkable positions")
        
        # Place workers
        for i in range(min(max_workers, len(walkable_positions))):
            pos = walkable_positions[i]
            worker_id = f"WORKER_{i:02d}"
            if self.warehouse.place_worker(pos[0], pos[1], worker_id):
                workers_placed += 1
        
        print(f"Placed {workers_placed} workers")
        self.assertEqual(workers_placed, min(max_workers, len(walkable_positions)))
        
        # Verify worker positions
        self.assertEqual(len(self.warehouse.worker_positions), workers_placed)
    
    def test_pathfinding_connectivity(self):
        """Test that warehouse areas are properly connected"""
        # Test connectivity between entrances and various points
        entrance = self.warehouse.entrances[0]
        
        # Find positions in different zones
        test_positions = []
        zones_tested = set()
        
        for x in range(0, self.warehouse.width, 5):
            for y in range(0, self.warehouse.depth, 5):
                if self.warehouse.is_walkable(x, y):
                    zone = f"zone_{x//10}_{y//10}"
                    if zone not in zones_tested:
                        test_positions.append((x, y))
                        zones_tested.add(zone)
        
        print(f"Testing connectivity from entrance {entrance} to {len(test_positions)} positions")
        
        # For each position, check if we can find neighbors (basic connectivity test)
        connected_positions = 0
        for pos in test_positions:
            neighbors = self.warehouse.get_accessible_neighbors(pos[0], pos[1])
            if len(neighbors) > 0:
                connected_positions += 1
        
        print(f"Found {connected_positions}/{len(test_positions)} connected positions")
        self.assertGreater(connected_positions, 0)


class TestWarehouseVisualization(unittest.TestCase):
    """Test warehouse visualization and layout printing"""
    
    def test_layout_printing(self):
        """Test warehouse layout visualization"""
        warehouse = LargeWarehouse(width=20, depth=15, levels=2)
        
        print("\n" + "="*50)
        print("WAREHOUSE LAYOUT VISUALIZATION TEST")
        print("="*50)
        
        # Print layout
        warehouse.print_layout()
        
        # Place some workers and show updated layout
        walkable_pos = []
        for x in range(warehouse.width):
            for y in range(warehouse.depth):
                if warehouse.is_walkable(x, y):
                    walkable_pos.append((x, y))
                if len(walkable_pos) >= 3:
                    break
            if len(walkable_pos) >= 3:
                break
        
        # Place workers
        for i, pos in enumerate(walkable_pos[:3]):
            warehouse.place_worker(pos[0], pos[1], f"WORKER_{i}")
        
        print(f"\nLayout with {len(walkable_pos[:3])} workers placed:")
        warehouse.print_layout()
        
        # Print statistics
        stats = warehouse.get_warehouse_stats()
        print(f"\nWarehouse Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


def run_comprehensive_tests():
    """Run all tests with detailed output"""
    print("="*60)
    print("COMPREHENSIVE WAREHOUSE STRUCTURE TESTS")
    print("="*60)
    
    # Test suites
    test_suites = [
        TestStorageCell,
        TestLargeWarehouse, 
        TestWarehouseStressTest,
        TestWarehouseVisualization
    ]
    
    total_tests = 0
    total_failures = 0
    
    for test_class in test_suites:
        print(f"\n{'='*40}")
        print(f"Running {test_class.__name__}")
        print(f"{'='*40}")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures) + len(result.errors)
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS: {total_tests - total_failures}/{total_tests} tests passed")
    if total_failures == 0:
        print("🎉 ALL TESTS PASSED! Warehouse structure is ready for optimization!")
    else:
        print(f"❌ {total_failures} tests failed. Please review implementation.")
    print(f"{'='*60}")


def demo_warehouse_capabilities():
    """Demonstrate warehouse capabilities with realistic scenario"""
    print("\n" + "="*60)
    print("WAREHOUSE CAPABILITIES DEMONSTRATION")
    print("="*60)
    
    # Create large warehouse
    warehouse = LargeWarehouse(width=30, depth=30, levels=3)
    
    # Create sample items
    sample_items = [
        Item("LAPTOP_001", ItemSize.SMALL, WeightClass.LIGHT, 8.5, "electronics"),
        Item("PRINTER_002", ItemSize.MEDIUM, WeightClass.MEDIUM, 3.2, "electronics"),
        Item("SERVER_003", ItemSize.LARGE, WeightClass.HEAVY, 12.0, "electronics"),
        Item("WRENCH_004", ItemSize.SMALL, WeightClass.MEDIUM, 2.1, "tools"),
        Item("TOOLBOX_005", ItemSize.MEDIUM, WeightClass.HEAVY, 5.5, "tools"),
        Item("BOOK_006", ItemSize.SMALL, WeightClass.LIGHT, 1.5, "books"),
        Item("JACKET_007", ItemSize.MEDIUM, WeightClass.LIGHT, 4.0, "clothing")
    ]
    
    # Place items strategically
    placed_items = []
    shelf_cells = [(x, y) for x in range(warehouse.width) for y in range(warehouse.depth) 
                   if warehouse.get_cell_type(x, y) == CellType.SHELF]
    
    for item in sample_items:
        for pos in shelf_cells[:10]:  # Try first 10 shelf positions
            # Heavy items on level 1, others can go higher
            max_level = 1 if item.weight_class == WeightClass.HEAVY else warehouse.levels
            for level in range(1, max_level + 1):
                if warehouse.place_item(item, pos[0], pos[1], level):
                    placed_items.append((item, pos[0], pos[1], level))
                    break
            if item in [p[0] for p in placed_items]:
                break
    
    print(f"Placed {len(placed_items)} items in warehouse:")
    for item, x, y, level in placed_items:
        print(f"  {item.id} ({item.size.value}, {item.weight_class.value}) -> ({x},{y}) Level {level}")
    
    # Place workers
    walkable_positions = [(x, y) for x in range(warehouse.width) for y in range(warehouse.depth)
                         if warehouse.is_walkable(x, y)]
    
    workers = ["PICKER_A", "PICKER_B"]
    for i, worker_id in enumerate(workers):
        if i < len(walkable_positions):
            pos = walkable_positions[i * 10]  # Spread them out
            warehouse.place_worker(pos[0], pos[1], worker_id)
    
    # Show final statistics
    stats = warehouse.get_warehouse_stats()
    print(f"\nFinal Warehouse State:")
    print(f"  Storage utilization: {stats['occupancy_rate']:.2%}")
    print(f"  Items stored: {stats['current_items']}")
    print(f"  Workers active: {stats['workers']}")
    print(f"  Available storage: {stats['total_storage_capacity'] - stats['current_items']}")
    
    # Test item retrieval
    if placed_items:
        test_item = placed_items[0]
        item, x, y, level = test_item
        found = warehouse.find_item(item.id)
        print(f"\nItem retrieval test:")
        print(f"  Looking for: {item.id}")
        print(f"  Found at: ({found[0]},{found[1]}) Level {found[2]}")
        
        retrieved = warehouse.remove_item(item.id, x, y, level)
        print(f"  Retrieved: {retrieved.id if retrieved else 'Failed'}")


if __name__ == "__main__":
    # Run comprehensive tests
    run_comprehensive_tests()
    
    # Run demonstration
    demo_warehouse_capabilities()