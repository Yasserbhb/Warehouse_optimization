#!/usr/bin/env python3
"""
Warehouse Data Generator
Creates realistic warehouse items with seasonal patterns, frequencies, and characteristics
"""

import json
import random
import math
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
import csv
from datetime import datetime, timedelta

# Import shared enums
try:
    from ..shared_enums import ItemSize, WeightClass, SeasonalPattern
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from shared_enums import ItemSize, WeightClass, SeasonalPattern

@dataclass
class WarehouseItem:
    """Complete warehouse item definition"""
    id: str
    name: str
    category: str
    size: ItemSize
    weight_class: WeightClass
    base_daily_picks: float  # Average picks per day during normal periods
    seasonal_pattern: SeasonalPattern
    seasonal_multiplier: float  # Peak season multiplier (1.0 = no change)
    unit_cost: float  # Cost per item (for analytics)
    storage_requirements: List[str]  # Special storage needs
    popularity_rank: str  # "high", "medium", "low" frequency item
    
    def get_daily_picks_for_month(self, month: int) -> float:
        """Calculate daily picks for given month (1=Jan, 12=Dec)"""
        base_picks = self.base_daily_picks
        
        # Define seasonal multipliers by month
        seasonal_factors = {
            SeasonalPattern.ALL_YEAR: [1.0] * 12,
            SeasonalPattern.WINTER_HEAVY: [1.8, 1.9, 1.2, 0.8, 0.7, 0.6, 0.6, 0.7, 0.8, 1.0, 1.3, 1.7],
            SeasonalPattern.SPRING_HEAVY: [0.8, 0.7, 1.5, 1.8, 1.9, 1.2, 0.8, 0.7, 0.8, 1.0, 1.1, 0.9],
            SeasonalPattern.SUMMER_HEAVY: [0.7, 0.6, 0.8, 1.2, 1.5, 1.9, 1.8, 1.6, 1.0, 0.8, 0.7, 0.6],
            SeasonalPattern.AUTUMN_HEAVY: [0.8, 0.7, 0.8, 0.9, 1.0, 0.8, 0.7, 1.2, 1.8, 1.9, 1.5, 1.0],
            SeasonalPattern.HOLIDAY_PEAK: [0.9, 0.8, 0.8, 0.9, 0.9, 0.8, 0.8, 0.9, 1.0, 1.1, 1.8, 2.2],
            SeasonalPattern.BACK_TO_SCHOOL: [0.9, 0.8, 0.8, 0.9, 0.9, 1.0, 1.2, 2.0, 1.8, 1.0, 0.9, 0.8]
        }
        
        factor = seasonal_factors[self.seasonal_pattern][month - 1]
        return base_picks * factor


class WarehouseDataGenerator:
    """Generate realistic warehouse inventory and order data"""
    
    def __init__(self, random_seed: int = 42):
        """Initialize data generator with optional random seed for reproducibility"""
        random.seed(random_seed)
        self.items: List[WarehouseItem] = []
        
        # Item templates with realistic characteristics
        self.item_templates = self._create_item_templates()
    
    def _create_item_templates(self) -> List[Dict[str, Any]]:
        """Create realistic item templates for different categories"""
        return [
            # Electronics - High frequency, light/medium weight, small/medium size
            {
                "category": "electronics",
                "items": [
                    {"name": "Laptop Computer", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 12.5, "season": SeasonalPattern.BACK_TO_SCHOOL, "cost": 899.99},
                    {"name": "Smartphone", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 15.2, "season": SeasonalPattern.ALL_YEAR, "cost": 699.99},
                    {"name": "Tablet Device", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 8.3, "season": SeasonalPattern.HOLIDAY_PEAK, "cost": 329.99},
                    {"name": "Wireless Headphones", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 18.7, "season": SeasonalPattern.ALL_YEAR, "cost": 199.99},
                    {"name": "Gaming Console", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 6.4, "season": SeasonalPattern.HOLIDAY_PEAK, "cost": 499.99},
                    {"name": "Smart Watch", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 9.1, "season": SeasonalPattern.ALL_YEAR, "cost": 399.99},
                    {"name": "Bluetooth Speaker", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 11.8, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 89.99},
                    {"name": "Webcam", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 4.2, "season": SeasonalPattern.BACK_TO_SCHOOL, "cost": 79.99},
                ]
            },
            
            # Home & Garden - Seasonal patterns, various sizes
            {
                "category": "home_garden",
                "items": [
                    {"name": "Space Heater", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 3.8, "season": SeasonalPattern.WINTER_HEAVY, "cost": 149.99},
                    {"name": "Air Conditioner", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 2.1, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 299.99},
                    {"name": "Garden Hose", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 5.3, "season": SeasonalPattern.SPRING_HEAVY, "cost": 34.99},
                    {"name": "Lawn Mower", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 1.8, "season": SeasonalPattern.SPRING_HEAVY, "cost": 449.99},
                    {"name": "Christmas Lights", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 0.5, "season": SeasonalPattern.HOLIDAY_PEAK, "cost": 24.99},
                    {"name": "Patio Furniture Set", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 1.2, "season": SeasonalPattern.SPRING_HEAVY, "cost": 599.99},
                    {"name": "Snow Shovel", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 2.7, "season": SeasonalPattern.WINTER_HEAVY, "cost": 29.99},
                    {"name": "Barbecue Grill", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 1.9, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 399.99},
                ]
            },
            
            # Clothing & Fashion - Seasonal, light weight, small/medium
            {
                "category": "clothing",
                "items": [
                    {"name": "Winter Coat", "size": ItemSize.MEDIUM, "weight": WeightClass.LIGHT, "freq": 4.6, "season": SeasonalPattern.WINTER_HEAVY, "cost": 129.99},
                    {"name": "Summer Dress", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 7.2, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 59.99},
                    {"name": "Running Shoes", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 13.4, "season": SeasonalPattern.ALL_YEAR, "cost": 119.99},
                    {"name": "Jeans", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 16.8, "season": SeasonalPattern.ALL_YEAR, "cost": 79.99},
                    {"name": "Sweater", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 6.9, "season": SeasonalPattern.AUTUMN_HEAVY, "cost": 49.99},
                    {"name": "Swimwear", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 3.1, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 39.99},
                    {"name": "School Backpack", "size": ItemSize.MEDIUM, "weight": WeightClass.LIGHT, "freq": 5.7, "season": SeasonalPattern.BACK_TO_SCHOOL, "cost": 49.99},
                ]
            },
            
            # Sports & Outdoors - Seasonal, various sizes and weights
            {
                "category": "sports",
                "items": [
                    {"name": "Ski Equipment Set", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 1.4, "season": SeasonalPattern.WINTER_HEAVY, "cost": 799.99},
                    {"name": "Bicycle", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 3.6, "season": SeasonalPattern.SPRING_HEAVY, "cost": 599.99},
                    {"name": "Tennis Racket", "size": ItemSize.MEDIUM, "weight": WeightClass.LIGHT, "freq": 4.8, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 149.99},
                    {"name": "Camping Tent", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 2.9, "season": SeasonalPattern.SUMMER_HEAVY, "cost": 199.99},
                    {"name": "Yoga Mat", "size": ItemSize.MEDIUM, "weight": WeightClass.LIGHT, "freq": 8.1, "season": SeasonalPattern.ALL_YEAR, "cost": 29.99},
                    {"name": "Football", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 6.3, "season": SeasonalPattern.AUTUMN_HEAVY, "cost": 24.99},
                    {"name": "Golf Club Set", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 2.2, "season": SeasonalPattern.SPRING_HEAVY, "cost": 899.99},
                ]
            },
            
            # Books & Education - Back to school heavy, light weight
            {
                "category": "books",
                "items": [
                    {"name": "Textbook Mathematics", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 7.5, "season": SeasonalPattern.BACK_TO_SCHOOL, "cost": 199.99},
                    {"name": "Novel Fiction", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 12.3, "season": SeasonalPattern.ALL_YEAR, "cost": 14.99},
                    {"name": "Children's Book Set", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 8.7, "season": SeasonalPattern.HOLIDAY_PEAK, "cost": 39.99},
                    {"name": "Professional Manual", "size": ItemSize.MEDIUM, "weight": WeightClass.LIGHT, "freq": 3.4, "season": SeasonalPattern.ALL_YEAR, "cost": 89.99},
                    {"name": "Art Supplies Kit", "size": ItemSize.MEDIUM, "weight": WeightClass.LIGHT, "freq": 5.6, "season": SeasonalPattern.BACK_TO_SCHOOL, "cost": 79.99},
                    {"name": "Calculator Scientific", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 4.1, "season": SeasonalPattern.BACK_TO_SCHOOL, "cost": 129.99},
                ]
            },
            
            # Tools & Hardware - Medium frequency, heavy items
            {
                "category": "tools",
                "items": [
                    {"name": "Power Drill", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 6.8, "season": SeasonalPattern.SPRING_HEAVY, "cost": 199.99},
                    {"name": "Tool Box Set", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 4.2, "season": SeasonalPattern.ALL_YEAR, "cost": 299.99},
                    {"name": "Hammer", "size": ItemSize.SMALL, "weight": WeightClass.MEDIUM, "freq": 9.1, "season": SeasonalPattern.ALL_YEAR, "cost": 24.99},
                    {"name": "Screwdriver Set", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 11.6, "season": SeasonalPattern.ALL_YEAR, "cost": 39.99},
                    {"name": "Chainsaw", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 1.7, "season": SeasonalPattern.AUTUMN_HEAVY, "cost": 399.99},
                    {"name": "Work Gloves", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 14.2, "season": SeasonalPattern.ALL_YEAR, "cost": 12.99},
                ]
            },
            
            # Kitchen & Appliances - Holiday peaks, various sizes
            {
                "category": "kitchen",
                "items": [
                    {"name": "Coffee Machine", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 7.9, "season": SeasonalPattern.ALL_YEAR, "cost": 149.99},
                    {"name": "Microwave Oven", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 3.8, "season": SeasonalPattern.ALL_YEAR, "cost": 199.99},
                    {"name": "Blender", "size": ItemSize.MEDIUM, "weight": WeightClass.MEDIUM, "freq": 5.4, "season": SeasonalPattern.ALL_YEAR, "cost": 89.99},
                    {"name": "Cookie Cutters Set", "size": ItemSize.SMALL, "weight": WeightClass.LIGHT, "freq": 2.1, "season": SeasonalPattern.HOLIDAY_PEAK, "cost": 19.99},
                    {"name": "Stand Mixer", "size": ItemSize.LARGE, "weight": WeightClass.HEAVY, "freq": 2.7, "season": SeasonalPattern.HOLIDAY_PEAK, "cost": 399.99},
                ]
            }
        ]
    
    def generate_items(self, total_items: int = 50) -> List[WarehouseItem]:
        """Generate specified number of warehouse items"""
        self.items = []
        item_counter = 1
        
        # Calculate items per category
        items_per_category = total_items // len(self.item_templates)
        remaining_items = total_items % len(self.item_templates)
        
        for category_template in self.item_templates:
            category = category_template["category"]
            category_items = category_template["items"]
            
            # Determine how many items for this category
            category_count = items_per_category
            if remaining_items > 0:
                category_count += 1
                remaining_items -= 1
            
            # Generate items for this category
            for i in range(category_count):
                # Select base item (cycle through available items)
                base_item = category_items[i % len(category_items)]
                
                # Add some variation to make items unique
                variation_suffix = "" if i < len(category_items) else f" v{i // len(category_items) + 1}"
                
                # Determine popularity based on frequency
                freq = base_item["freq"]
                if freq >= 10:
                    popularity = "high"
                elif freq >= 5:
                    popularity = "medium"
                else:
                    popularity = "low"
                
                # Create storage requirements
                storage_reqs = []
                if base_item["weight"] == WeightClass.HEAVY:
                    storage_reqs.append("ground_level_only")
                if category == "electronics":
                    storage_reqs.append("climate_controlled")
                if "winter" in base_item["name"].lower() or base_item["season"] == SeasonalPattern.WINTER_HEAVY:
                    storage_reqs.append("seasonal_storage")
                
                # Generate item
                item = WarehouseItem(
                    id=f"WH_{item_counter:03d}",
                    name=base_item["name"] + variation_suffix,
                    category=category,
                    size=base_item["size"],
                    weight_class=base_item["weight"],
                    base_daily_picks=freq + random.uniform(-1.0, 1.0),  # Add some randomness
                    seasonal_pattern=base_item["season"],
                    seasonal_multiplier=self._calculate_seasonal_multiplier(base_item["season"]),
                    unit_cost=base_item["cost"] * random.uniform(0.9, 1.1),  # Price variation
                    storage_requirements=storage_reqs,
                    popularity_rank=popularity
                )
                
                self.items.append(item)
                item_counter += 1
        
        # Sort by popularity (high frequency items first)
        self.items.sort(key=lambda x: x.base_daily_picks, reverse=True)
        
        print(f"Generated {len(self.items)} warehouse items across {len(self.item_templates)} categories")
        return self.items
    
    def _calculate_seasonal_multiplier(self, pattern: SeasonalPattern) -> float:
        """Calculate the peak seasonal multiplier for a pattern"""
        multipliers = {
            SeasonalPattern.ALL_YEAR: 1.0,
            SeasonalPattern.WINTER_HEAVY: 1.9,
            SeasonalPattern.SPRING_HEAVY: 1.9,
            SeasonalPattern.SUMMER_HEAVY: 1.9,
            SeasonalPattern.AUTUMN_HEAVY: 1.9,
            SeasonalPattern.HOLIDAY_PEAK: 2.2,
            SeasonalPattern.BACK_TO_SCHOOL: 2.0
        }
        return multipliers[pattern]
    
    def save_items_to_json(self, filename: str = "warehouse_items.json") -> None:
        """Save generated items to JSON file"""
        items_data = []
        for item in self.items:
            item_dict = asdict(item)
            # Convert enums to strings for JSON serialization
            item_dict["size"] = item.size.value
            item_dict["weight_class"] = item.weight_class.value
            item_dict["seasonal_pattern"] = item.seasonal_pattern.value
            items_data.append(item_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(items_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.items)} items to {filename}")
    
    def save_items_to_csv(self, filename: str = "warehouse_items.csv") -> None:
        """Save items to CSV for easy analysis"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'ID', 'Name', 'Category', 'Size', 'Weight Class', 
                'Base Daily Picks', 'Seasonal Pattern', 'Seasonal Multiplier',
                'Unit Cost', 'Popularity Rank', 'Storage Requirements'
            ])
            
            # Data rows
            for item in self.items:
                writer.writerow([
                    item.id,
                    item.name,
                    item.category,
                    item.size.value,
                    item.weight_class.value,
                    f"{item.base_daily_picks:.2f}",
                    item.seasonal_pattern.value,
                    f"{item.seasonal_multiplier:.2f}",
                    f"${item.unit_cost:.2f}",
                    item.popularity_rank,
                    '; '.join(item.storage_requirements)
                ])
        
        print(f"Saved {len(self.items)} items to {filename}")
    
    def load_items_from_json(self, filename: str = "warehouse_items.json") -> List[WarehouseItem]:
        """Load items from JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        
        self.items = []
        for item_dict in items_data:
            # Convert string values back to enums
            item_dict["size"] = ItemSize(item_dict["size"])
            item_dict["weight_class"] = WeightClass(item_dict["weight_class"])
            item_dict["seasonal_pattern"] = SeasonalPattern(item_dict["seasonal_pattern"])
            
            item = WarehouseItem(**item_dict)
            self.items.append(item)
        
        print(f"Loaded {len(self.items)} items from {filename}")
        return self.items
    
    def get_items_by_category(self, category: str) -> List[WarehouseItem]:
        """Get all items in a specific category"""
        return [item for item in self.items if item.category == category]
    
    def get_high_frequency_items(self, threshold: float = 10.0) -> List[WarehouseItem]:
        """Get items with high pick frequency"""
        return [item for item in self.items if item.base_daily_picks >= threshold]
    
    def get_seasonal_items(self, exclude_all_year: bool = True) -> List[WarehouseItem]:
        """Get items with seasonal patterns"""
        if exclude_all_year:
            return [item for item in self.items if item.seasonal_pattern != SeasonalPattern.ALL_YEAR]
        return [item for item in self.items if item.seasonal_pattern != SeasonalPattern.ALL_YEAR]
    
    def print_items_summary(self) -> None:
        """Print summary statistics of generated items"""
        if not self.items:
            print("No items generated yet!")
            return
        
        print(f"\n{'='*60}")
        print(f"WAREHOUSE ITEMS SUMMARY ({len(self.items)} total items)")
        print(f"{'='*60}")
        
        # Category breakdown
        categories = {}
        for item in self.items:
            categories[item.category] = categories.get(item.category, 0) + 1
        
        print(f"\nItems by Category:")
        for category, count in sorted(categories.items()):
            print(f"  {category:15s}: {count:2d} items")
        
        # Size breakdown
        sizes = {}
        for item in self.items:
            sizes[item.size.value] = sizes.get(item.size.value, 0) + 1
        
        print(f"\nItems by Size:")
        for size, count in sorted(sizes.items()):
            print(f"  {size:8s}: {count:2d} items")
        
        # Weight breakdown
        weights = {}
        for item in self.items:
            weights[item.weight_class.value] = weights.get(item.weight_class.value, 0) + 1
        
        print(f"\nItems by Weight Class:")
        for weight, count in sorted(weights.items()):
            print(f"  {weight:8s}: {count:2d} items")
        
        # Frequency statistics
        frequencies = [item.base_daily_picks for item in self.items]
        print(f"\nDaily Pick Frequency:")
        print(f"  Average: {sum(frequencies)/len(frequencies):.2f} picks/day")
        print(f"  Range:   {min(frequencies):.2f} - {max(frequencies):.2f} picks/day")
        
        # Top 10 most frequent items
        print(f"\nTop 10 Most Frequently Picked Items:")
        sorted_items = sorted(self.items, key=lambda x: x.base_daily_picks, reverse=True)
        for i, item in enumerate(sorted_items[:10]):
            print(f"  {i+1:2d}. {item.name:25s} ({item.base_daily_picks:5.1f} picks/day)")
        
        # Seasonal breakdown
        seasons = {}
        for item in self.items:
            seasons[item.seasonal_pattern.value] = seasons.get(item.seasonal_pattern.value, 0) + 1
        
        print(f"\nItems by Seasonal Pattern:")
        for season, count in sorted(seasons.items()):
            print(f"  {season:15s}: {count:2d} items")


def main():
    """Demonstrate the data generator"""
    print("="*60)
    print("WAREHOUSE DATA GENERATOR DEMO")
    print("="*60)
    
    # Create generator
    generator = WarehouseDataGenerator(random_seed=42)
    
    # Generate 50 items
    items = generator.generate_items(50)
    
    # Print summary
    generator.print_items_summary()
    
    # Save to files
    print(f"\nSaving items to files...")
    generator.save_items_to_json("warehouse_items.json")
    generator.save_items_to_csv("warehouse_items.csv")
    
    # Demonstrate seasonal calculations
    print(f"\nSeasonal Demand Examples:")
    print(f"{'Item':<25s} {'Jan':<6s} {'Jun':<6s} {'Sep':<6s} {'Dec':<6s}")
    print("-" * 50)
    
    for item in items[:5]:  # Show first 5 items
        jan_picks = item.get_daily_picks_for_month(1)
        jun_picks = item.get_daily_picks_for_month(6)
        sep_picks = item.get_daily_picks_for_month(9)
        dec_picks = item.get_daily_picks_for_month(12)
        
        print(f"{item.name[:24]:<25s} {jan_picks:5.1f} {jun_picks:5.1f} {sep_picks:5.1f} {dec_picks:5.1f}")
    
    print(f"\n✅ Data generation complete! Files saved:")
    print(f"   - warehouse_items.json (for loading in applications)")
    print(f"   - warehouse_items.csv (for spreadsheet analysis)")


if __name__ == "__main__":
    main()