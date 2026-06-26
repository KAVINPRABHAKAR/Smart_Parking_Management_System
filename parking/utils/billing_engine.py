import math
from decimal import Decimal

def calculate_parking_fee(entry_time, exit_time, vehicle_type='CAR', is_vip=False):
    """
    Calculates charges based on total duration and vehicle type.
    Fulfills 'Variable Pricing' requirement: First 2 hours fixed, then hourly.
    """
    # 1. Calculate duration in hours (Always round up to the next hour)
    duration = exit_time - entry_time
    total_seconds = duration.total_seconds()
    
    # math.ceil ensures 1 min = 1 hour, 61 mins = 2 hours
    hours = math.ceil(total_seconds / 3600)
    
    # Safety check: if exit is processed immediately, charge for 1 hour minimum
    if hours <= 0:
        hours = 1

    # 2. Pricing rates based on vehicle type 
    # 'base' covers the first 2 hours total, 'hourly' is for every hour after that
    rates = {
        'BIKE': {'base': 10, 'hourly': 5},
        'CAR': {'base': 20, 'hourly': 10},
        'EV': {'base': 15, 'hourly': 7},
        'HEAVY': {'base': 50, 'hourly': 25},
    }

    config = rates.get(vehicle_type, rates['CAR'])
    
    # 3. Variable Pricing Logic: First 2 hours fixed, then per-hour 
    if hours <= 2:
        fee = Decimal(config['base'])
    else:
        fee = Decimal(config['base']) + (Decimal(hours) - 2) * Decimal(config['hourly'])

    # 4. VIP Discount: Premium Add-on (20% discount)
    if is_vip:
        fee = fee * Decimal('0.80')

    # Return as Decimal for precision with MySQL/Django DecimalFields
    return fee.quantize(Decimal('0.01'))