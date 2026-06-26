import pandas as pd
import numpy as np
from django.utils import timezone
from datetime import datetime, time
from ..models import ParkingTransaction

def get_daily_analytics():
    """
    Summarizes today's revenue and vehicle volume.
    Volume: Count of all vehicles currently active or entered today.
    Revenue: Stats of all payments collected specifically between 00:00 and 23:59 today.
    """
    now = timezone.now()
    # Create timezone-aware start and end of the current day
    start_of_day = timezone.make_aware(datetime.combine(now.date(), time.min))
    end_of_day = timezone.make_aware(datetime.combine(now.date(), time.max))
    
    # 1. Fetch Data
    # VOLUME: Any vehicle that entered today OR is still parked
    volume_qs = ParkingTransaction.objects.filter(
        entry_time__lte=end_of_day,
        is_active=True
    ).values('id', 'slot__vehicle_type')
    
    # REVENUE: Any payment collected between 12:00 AM and 11:59 PM today
    # This captures long-term stayers (like KL 70 1678) who pay upon exit today
    revenue_qs = ParkingTransaction.objects.filter(
        exit_time__range=(start_of_day, end_of_day), 
        is_active=False
    ).values('fee_charged')

    stats = {
        'total_revenue': 0.00,
        'max_single_fee': 0.00,
        'avg_revenue': 0.00,
        'total_vehicles': 0,
        'type_distribution': {}
    }

    # 2. Process Volume with Pandas
    if volume_qs.exists():
        df_volume = pd.DataFrame(list(volume_qs))
        stats['total_vehicles'] = int(len(df_volume))
        stats['type_distribution'] = df_volume['slot__vehicle_type'].value_counts().to_dict()

    # 3. Process Revenue with NumPy (handling Decimal to Float conversion)
    if revenue_qs.exists():
        df_rev = pd.DataFrame(list(revenue_qs))
        # Use to_numeric to safely handle Decimal objects and prevent NaN errors
        revenues = pd.to_numeric(df_rev['fee_charged'], errors='coerce').fillna(0).to_numpy()
        
        if revenues.size > 0:
            stats['total_revenue'] = round(float(np.sum(revenues)), 2)
            stats['max_single_fee'] = round(float(np.max(revenues)), 2)
            stats['avg_revenue'] = round(float(np.mean(revenues)), 2)

    return stats

def generate_revenue_report():
    """
    Historical summary logic for all-time data.
    """
    data = ParkingTransaction.objects.filter(is_active=False).values('fee_charged')
    
    if not data.exists():
        return {'total_revenue': 0.00, 'avg_fee': 0.00, 'vehicle_count': 0}
        
    df = pd.DataFrame(list(data))
    fees = pd.to_numeric(df['fee_charged'], errors='coerce').fillna(0).to_numpy()
    
    return {
        'total_revenue': round(float(np.sum(fees)), 2),
        'avg_fee': round(float(np.mean(fees)), 2),
        'vehicle_count': int(len(df))
    }