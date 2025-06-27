#!/usr/bin/env python3
"""
Realistic Order Generator for Warehouse Simulation
Creates daily orders with seasonal patterns, customer behavior, and realistic timing
"""

import random
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from collections import defaultdict

# Import shared enums
try:
    from ..shared_enums import ItemSize, WeightClass, SeasonalPattern
    from ..agents.picker_swarm import PickOrder, OrderItem
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, os.path.join(parent_dir, 'agents'))
    
    from shared_enums import ItemSize, WeightClass, SeasonalPattern
    from picker_swarm import PickOrder, OrderItem

class Season:
    """Current season for demand calculation"""
    WINTER = 1    # Dec, Jan, Feb
    SPRING = 2    # Mar, Apr, May  
    SUMMER = 3    # Jun, Jul, Aug
    AUTUMN = 4    # Sep, Oct, Nov

class CustomerType:
    """Different customer behavior patterns"""
    INDIVIDUAL = "individual"      # Small, frequent orders (1-3 items)
    FAMILY = "family"             # Medium orders (2-6 items)
    BUSINESS = "business"         # Larger, bulk orders (4-12 items)
    EMERGENCY = "emergency"       # Single item, high priority

@dataclass
class OrderPattern:
    """Order generation pattern definition"""
    customer_type: str
    min_items: int
    max_items: int
    frequency_weight: float  # How often this pattern occurs
    priority_distribution: List[float]  # [normal, high, urgent] probabilities
    size_preference: Dict[ItemSize, float]  # Preference for item sizes

class RealisticOrderGenerator:
    """Generate realistic warehouse orders with seasonal patterns and customer behavior"""
    
    def __init__(self, placed_items: List[Dict], random_seed: int = None):
        """
        Initialize order generator
        
        Args:
            placed_items: List of item dictionaries from warehouse simulation
            random_seed: Optional seed for reproducible results
        """
        if random_seed:
            random.seed(random_seed)
        
        self.placed_items = placed_items
        self.current_season = Season.AUTUMN  # Default season
        
        # Create order patterns for different customer types
        self.order_patterns = self._create_order_patterns()
        
        # Create item lookup for quick access
        self.items_by_category = self._group_items_by_category()
        self.items_by_frequency = self._sort_items_by_frequency()
        
        print(f"Order generator initialized with {len(placed_items)} available items")
    
    def _create_order_patterns(self) -> Dict[str, OrderPattern]:
        """Define realistic order patterns for different customer types"""
        return {
            CustomerType.INDIVIDUAL: OrderPattern(
                customer_type=CustomerType.INDIVIDUAL,
                min_items=1,
                max_items=3,
                frequency_weight=0.60,  # 60% of orders
                priority_distribution=[0.85, 0.13, 0.02],  # Mostly normal priority
                size_preference={ItemSize.SMALL: 0.7, ItemSize.MEDIUM: 0.25, ItemSize.LARGE: 0.05}
            ),
            
            CustomerType.FAMILY: OrderPattern(
                customer_type=CustomerType.FAMILY,
                min_items=2,
                max_items=6,
                frequency_weight=0.25,  # 25% of orders
                priority_distribution=[0.75, 0.20, 0.05],
                size_preference={ItemSize.SMALL: 0.5, ItemSize.MEDIUM: 0.35, ItemSize.LARGE: 0.15}
            ),
            
            CustomerType.BUSINESS: OrderPattern(
                customer_type=CustomerType.BUSINESS,
                min_items=4,
                max_items=12,
                frequency_weight=0.12,  # 12% of orders
                priority_distribution=[0.60, 0.30, 0.10],
                size_preference={ItemSize.SMALL: 0.4, ItemSize.MEDIUM: 0.4, ItemSize.LARGE: 0.2}
            ),
            
            CustomerType.EMERGENCY: OrderPattern(
                customer_type=CustomerType.EMERGENCY,
                min_items=1,
                max_items=2,
                frequency_weight=0.03,  # 3% of orders
                priority_distribution=[0.20, 0.50, 0.30],  # Often high priority
                size_preference={ItemSize.SMALL: 0.6, ItemSize.MEDIUM: 0.3, ItemSize.LARGE: 0.1}
            )
        }
    
    def _group_items_by_category(self) -> Dict[str, List[Dict]]:
        """Group items by category for realistic order composition"""
        categories = defaultdict(list)
        for item in self.placed_items:
            categories[item['category']].append(item)
        return dict(categories)
    
    def _sort_items_by_frequency(self) -> List[Dict]:
        """Sort items by daily pick frequency for popularity-based selection"""
        return sorted(self.placed_items, key=lambda x: x['daily_picks'], reverse=True)
    
    def set_season(self, season: int):
        """Set current season (1=Winter, 2=Spring, 3=Summer, 4=Autumn)"""
        self.current_season = season
        print(f"Season set to: {['Winter', 'Spring', 'Summer', 'Autumn'][season-1]}")
    
    def calculate_seasonal_demand(self, item: Dict) -> float:
        """Calculate item demand based on current season"""
        base_demand = item['daily_picks']
        seasonal_pattern = item['seasonal_pattern']
        
        # Season multipliers based on seasonal patterns
        season_multipliers = {
            SeasonalPattern.ALL_YEAR: [1.0, 1.0, 1.0, 1.0],
            SeasonalPattern.WINTER_HEAVY: [1.9, 0.8, 0.6, 1.0],
            SeasonalPattern.SPRING_HEAVY: [0.8, 1.9, 0.8, 0.9],
            SeasonalPattern.SUMMER_HEAVY: [0.6, 0.8, 1.9, 0.8],
            SeasonalPattern.AUTUMN_HEAVY: [0.8, 0.9, 0.8, 1.9],
            SeasonalPattern.HOLIDAY_PEAK: [1.8, 0.9, 0.8, 1.1],
            SeasonalPattern.BACK_TO_SCHOOL: [0.8, 1.0, 1.2, 2.0]
        }
        
        if seasonal_pattern in season_multipliers:
            multiplier = season_multipliers[seasonal_pattern][self.current_season - 1]
            return base_demand * multiplier
        
        return base_demand
    
    def generate_daily_orders(self, 
                            num_orders: int = None,
                            day_of_week: int = 1,
                            special_events: List[str] = None) -> List[PickOrder]:
        """
        Generate realistic daily orders
        
        Args:
            num_orders: Number of orders to generate (auto-calculated if None)
            day_of_week: 1=Monday, 7=Sunday (affects order patterns)
            special_events: List of special events affecting demand
            
        Returns:
            List of PickOrder objects ready for simulation
        """
        
        if num_orders is None:
            # Calculate realistic daily order volume
            num_orders = self._calculate_daily_order_volume(day_of_week, special_events)
        
        print(f"Generating {num_orders} orders for day {day_of_week} ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][day_of_week-1]})")
        
        orders = []
        
        # Generate orders throughout the day
        order_times = self._generate_order_times(num_orders, day_of_week)
        
        for i, order_time in enumerate(order_times):
            # Select customer type based on time and patterns
            customer_type = self._select_customer_type(order_time, day_of_week)
            
            # Generate order for this customer type
            order = self._generate_single_order(
                order_id=f"ORD_{i+1:03d}",
                customer_type=customer_type,
                order_time=order_time
            )
            
            if order and order.items:  # Only add non-empty orders
                orders.append(order)
        
        print(f"Generated {len(orders)} valid orders")
        self._print_order_statistics(orders)
        
        return orders
    
    def _calculate_daily_order_volume(self, day_of_week: int, special_events: List[str] = None) -> int:
        """Calculate realistic daily order volume"""
        # Base volume (weekday average)
        base_volume = 60
        
        # Day of week modifiers
        day_modifiers = {
            1: 1.0,   # Monday
            2: 1.1,   # Tuesday
            3: 1.0,   # Wednesday  
            4: 1.1,   # Thursday
            5: 1.2,   # Friday
            6: 0.8,   # Saturday
            7: 0.6    # Sunday
        }
        
        volume = base_volume * day_modifiers.get(day_of_week, 1.0)
        
        # Special event modifiers
        if special_events:
            for event in special_events:
                if event == "black_friday":
                    volume *= 2.5
                elif event == "holiday_season":
                    volume *= 1.8
                elif event == "back_to_school":
                    volume *= 1.6
                elif event == "summer_sale":
                    volume *= 1.4
        
        # Season modifier
        season_volume_modifiers = {
            Season.WINTER: 1.1,
            Season.SPRING: 1.0,
            Season.SUMMER: 0.9,
            Season.AUTUMN: 1.2  # Back to school + holiday prep
        }
        
        volume *= season_volume_modifiers.get(self.current_season, 1.0)
        
        # Add some randomness
        volume *= random.uniform(0.85, 1.15)
        
        return max(10, int(volume))  # Minimum 10 orders per day
    
    def _generate_order_times(self, num_orders: int, day_of_week: int) -> List[str]:
        """Generate realistic order times throughout the day"""
        times = []
        
        # Define peak hours (more orders during these times)
        if day_of_week <= 5:  # Weekday
            peak_hours = [(9, 11), (13, 15), (19, 21)]  # Morning, lunch, evening
        else:  # Weekend
            peak_hours = [(10, 12), (14, 18)]  # Late morning, afternoon
        
        # Generate times with higher probability during peak hours
        for _ in range(num_orders):
            if random.random() < 0.7:  # 70% chance of peak hour order
                # Select random peak period
                start_hour, end_hour = random.choice(peak_hours)
                hour = random.randint(start_hour, end_hour - 1)
            else:
                # Off-peak order (any time 8 AM - 10 PM)
                hour = random.randint(8, 21)
            
            minute = random.randint(0, 59)
            time_str = f"{hour:02d}:{minute:02d}:00"
            times.append(time_str)
        
        # Sort times chronologically
        times.sort()
        return times
    
    def _select_customer_type(self, order_time: str, day_of_week: int) -> str:
        """Select customer type based on time and day patterns"""
        hour = int(order_time.split(':')[0])
        
        # Adjust customer type probabilities based on time
        base_weights = [p.frequency_weight for p in self.order_patterns.values()]
        
        # Business orders more common during business hours
        if 9 <= hour <= 17 and day_of_week <= 5:
            # Increase business order probability
            weights = base_weights.copy()
            weights[2] *= 2.0  # Business pattern index
        # Emergency orders more common in evenings/weekends
        elif hour >= 18 or day_of_week > 5:
            weights = base_weights.copy()
            weights[3] *= 2.0  # Emergency pattern index
        else:
            weights = base_weights
        
        # Normalize weights
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        # Select customer type
        customer_types = list(self.order_patterns.keys())
        return random.choices(customer_types, weights=probabilities)[0]
    
    def _generate_single_order(self, order_id: str, customer_type: str, order_time: str) -> PickOrder:
        """Generate a single order for given customer type"""
        pattern = self.order_patterns[customer_type]
        
        # Determine number of items
        num_items = random.randint(pattern.min_items, pattern.max_items)
        
        # Select priority
        priority = random.choices([1, 2, 3], weights=pattern.priority_distribution)[0]
        
        # Select items for this order
        order_items = self._select_order_items(num_items, pattern)
        
        if not order_items:
            return None
        
        order = PickOrder(
            order_id=order_id,
            items=order_items,
            priority=priority,
            created_time=0.0  # Will be set by simulation
        )
        
        return order
    
    def _select_order_items(self, num_items: int, pattern: OrderPattern) -> List[OrderItem]:
        """Select items for an order based on customer pattern"""
        selected_items = []
        total_load_points = 0
        max_load_points = 4  # Picker capacity constraint
        
        # Track used items to avoid duplicates
        used_item_ids = set()
        
        # Create weighted item pool based on seasonal demand and size preference
        weighted_items = self._create_weighted_item_pool(pattern)
        
        attempts = 0
        max_attempts = num_items * 10
        
        while len(selected_items) < num_items and total_load_points < max_load_points and attempts < max_attempts:
            attempts += 1
            
            # Select item based on weights
            item_data = random.choices(weighted_items, weights=[w for _, w in weighted_items])[0][0]
            
            # Skip if already selected
            if item_data['item_id'] in used_item_ids:
                continue
            
            # Check load capacity
            item_points = {ItemSize.SMALL: 1, ItemSize.MEDIUM: 2, ItemSize.LARGE: 4}[item_data['size']]
            
            if total_load_points + item_points <= max_load_points:
                # Create order item
                order_item = OrderItem(
                    item_id=item_data['item_id'],
                    item_name=item_data['item_name'],
                    size=item_data['size'],
                    location=item_data['location'],
                    pick_time=item_data['pick_time']
                )
                
                selected_items.append(order_item)
                used_item_ids.add(item_data['item_id'])
                total_load_points += item_points
        
        return selected_items
    
    def _create_weighted_item_pool(self, pattern: OrderPattern) -> List[Tuple[Dict, float]]:
        """Create weighted pool of items based on pattern preferences and seasonal demand"""
        weighted_items = []
        
        for item in self.placed_items:
            # Base weight from seasonal demand
            seasonal_demand = self.calculate_seasonal_demand(item)
            base_weight = seasonal_demand
            
            # Apply size preference
            size_preference = pattern.size_preference.get(item['size'], 0.1)
            weight = base_weight * size_preference
            
            # Boost popular items
            if seasonal_demand > 10:  # High-demand items
                weight *= 1.5
            
            # Category-based adjustments for realistic combinations
            category_boosts = {
                'electronics': 1.2,  # Popular category
                'clothing': 1.1,
                'books': 0.9,
                'tools': 0.8,
                'home_garden': 0.7,
                'sports': 0.8,
                'kitchen': 1.0
            }
            
            category_boost = category_boosts.get(item['category'], 1.0)
            weight *= category_boost
            
            weighted_items.append((item, max(0.1, weight)))  # Minimum weight
        
        return weighted_items
    
    def _print_order_statistics(self, orders: List[PickOrder]):
        """Print statistics about generated orders"""
        if not orders:
            return
        
        total_items = sum(len(order.items) for order in orders)
        avg_items = total_items / len(orders)
        
        # Count by priority
        priority_counts = {1: 0, 2: 0, 3: 0}
        for order in orders:
            priority_counts[order.priority] += 1
        
        # Count by size
        size_counts = {ItemSize.SMALL: 0, ItemSize.MEDIUM: 0, ItemSize.LARGE: 0}
        for order in orders:
            for item in order.items:
                size_counts[item.size] += 1
        
        print(f"\nOrder Statistics:")
        print(f"  Total orders: {len(orders)}")
        print(f"  Total items: {total_items}")
        print(f"  Average items per order: {avg_items:.1f}")
        print(f"  Priority distribution: Normal={priority_counts[1]}, High={priority_counts[2]}, Urgent={priority_counts[3]}")
        print(f"  Size distribution: Small={size_counts[ItemSize.SMALL]}, Medium={size_counts[ItemSize.MEDIUM]}, Large={size_counts[ItemSize.LARGE]}")
    
    def generate_weekly_orders(self, special_events: List[str] = None) -> Dict[int, List[PickOrder]]:
        """Generate orders for a full week (7 days)"""
        weekly_orders = {}
        
        for day in range(1, 8):  # Monday to Sunday
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day-1]
            print(f"\nGenerating orders for {day_name}...")
            
            daily_orders = self.generate_daily_orders(
                day_of_week=day,
                special_events=special_events
            )
            weekly_orders[day] = daily_orders
        
        total_orders = sum(len(orders) for orders in weekly_orders.values())
        total_items = sum(sum(len(order.items) for order in orders) for orders in weekly_orders.values())
        
        print(f"\nWeekly Summary:")
        print(f"  Total orders: {total_orders}")
        print(f"  Total items: {total_items}")
        print(f"  Average orders per day: {total_orders/7:.1f}")
        
        return weekly_orders


def demo_order_generator():
    """Demonstrate the order generator with sample data"""
    print("="*60)
    print("REALISTIC ORDER GENERATOR DEMONSTRATION")
    print("="*60)
    
    # Create sample placed items (simulating warehouse setup)
    sample_items = []
    categories = ['electronics', 'clothing', 'books', 'tools', 'home_garden']
    
    for i in range(30):
        item = {
            'item_id': f"ITEM_{i+1:03d}",
            'item_name': f"Sample Item {i+1}",
            'size': random.choice(list(ItemSize)),
            'weight_class': random.choice(list(WeightClass)),
            'category': random.choice(categories),
            'daily_picks': random.uniform(1.0, 20.0),
            'seasonal_pattern': random.choice(list(SeasonalPattern)),
            'location': (random.randint(1, 30), random.randint(1, 30), random.randint(1, 3)),
            'pick_time': random.uniform(15, 45)
        }
        sample_items.append(item)
    
    print(f"Created {len(sample_items)} sample items for demonstration")
    
    # Create order generator
    order_gen = RealisticOrderGenerator(sample_items, random_seed=42)
    
    # Test different seasons
    seasons = [Season.WINTER, Season.SPRING, Season.SUMMER, Season.AUTUMN]
    season_names = ['Winter', 'Spring', 'Summer', 'Autumn']
    
    for season, name in zip(seasons, season_names):
        print(f"\n{'='*40}")
        print(f"TESTING {name.upper()} SEASON")
        print(f"{'='*40}")
        
        order_gen.set_season(season)
        orders = order_gen.generate_daily_orders(num_orders=20, day_of_week=3)  # Wednesday
        
        print(f"{name} generated {len(orders)} orders")
    
    # Test special events
    print(f"\n{'='*40}")
    print("TESTING BLACK FRIDAY EVENT")
    print(f"{'='*40}")
    
    order_gen.set_season(Season.AUTUMN)
    black_friday_orders = order_gen.generate_daily_orders(
        day_of_week=5,  # Friday
        special_events=["black_friday"]
    )
    
    print(f"Black Friday generated {len(black_friday_orders)} orders")
    
    print(f"\n✅ Order generator demonstration complete!")


if __name__ == "__main__":
    demo_order_generator()