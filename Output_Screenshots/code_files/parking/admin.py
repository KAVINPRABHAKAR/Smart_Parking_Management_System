from django.contrib import admin
from .models import ParkingSlot, ParkingTransaction

@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    # Professional list view for managing slots [cite: 6, 10]
    list_display = ('slot_number', 'vehicle_type', 'is_vip', 'is_available')
    list_filter = ('vehicle_type', 'is_available', 'is_vip')
    search_fields = ('slot_number',)

@admin.register(ParkingTransaction)
class ParkingTransactionAdmin(admin.ModelAdmin):
    # Track vehicle entry, exit, and billing 
    list_display = ('vehicle_number', 'slot', 'entry_time', 'exit_time', 'fee_charged', 'is_active')
    list_filter = ('is_active', 'entry_time')
    search_fields = ('vehicle_number',)