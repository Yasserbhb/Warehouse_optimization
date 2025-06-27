#!/usr/bin/env python3
"""
Shared Enums for Warehouse Optimization System
Single source of truth for all enum definitions
"""

from enum import Enum

class CellType(Enum):
    """Different types of warehouse cells"""
    AISLE = 0           # Regular aisle (walkable)
    SHELF = 1           # Storage shelf
    MAIN_HALLWAY = 2    # Main corridor (wider)
    ENTRANCE = 3        # Entry points
    EXIT = 4            # Exit point
    CROSS_AISLE = 5     # Cross-connecting aisles
    WALL = 6            # Walls/blocked areas

class ItemSize(Enum):
    """Item size categories"""
    SMALL = "small"     # 4 items per cell
    MEDIUM = "medium"   # 2 items per cell  
    LARGE = "large"     # 1 item per cell

class WeightClass(Enum):
    """Weight classifications"""
    LIGHT = "light"     # Can go on any level (1-3)
    MEDIUM = "medium"   # Levels 1-2 only
    HEAVY = "heavy"     # Level 1 only

class SeasonalPattern(Enum):
    """Seasonal demand patterns"""
    ALL_YEAR = "all_year"          # Consistent demand year-round
    WINTER_HEAVY = "winter_heavy"  # Peak in Dec-Feb
    SPRING_HEAVY = "spring_heavy"  # Peak in Mar-May
    SUMMER_HEAVY = "summer_heavy"  # Peak in Jun-Aug
    AUTUMN_HEAVY = "autumn_heavy"  # Peak in Sep-Nov
    HOLIDAY_PEAK = "holiday_peak"  # Spike in Nov-Dec only
    BACK_TO_SCHOOL = "back_to_school"  # Spike in Aug-Sep

class PickerState(Enum):
    """Picker current state"""
    IDLE = "idle"                    # Waiting for orders at entrance
    MOVING_TO_ITEM = "moving_to_item"  # Traveling to pick up item
    PICKING = "picking"              # Picking up item (takes time)
    MOVING_TO_EXIT = "moving_to_exit"  # Returning to exit
    WAITING = "waiting"              # Blocked by another picker
    EXITING = "exiting"              # In exit queue

class Direction(Enum):
    """Movement directions"""
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    STAY = (0, 0)