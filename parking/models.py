from django.db import models
from django.utils import timezone

class ParkingSlot(models.Model):
    """
    Represents the 'Slot Dictionary'.
    Stores location, vehicle capability, and availability status.
    """
    SLOT_TYPES = [
        ('BIKE', 'Bike'),
        ('CAR', 'Car'),
        ('EV', 'EV'),
        ('HEAVY', 'Heavy Vehicle')
    ]
    
    slot_number = models.CharField(max_length=10, unique=True)
    vehicle_type = models.CharField(max_length=10, choices=SLOT_TYPES, default='CAR')
    is_vip = models.BooleanField(default=False)  # Feature: VIP reserved slots
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Slot {self.slot_number} ({self.vehicle_type})"

class ParkingTransaction(models.Model):
    """
    Represents 'Vehicle Entry' and 'Time Logger'.
    Updated to include Customer Name for reporting.
    """
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    vehicle_number = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100, default="Guest") # Added field
    entry_time = models.DateTimeField(default=timezone.now)
    exit_time = models.DateTimeField(null=True, blank=True)
    fee_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        status = "Active" if self.is_active else "Completed"
        return f"{self.vehicle_number} ({self.customer_name}) - {status}"