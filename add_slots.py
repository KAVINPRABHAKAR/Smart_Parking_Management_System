import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from parking.models import ParkingSlot

def populate_parking():
    # Define vehicle types to match your registration form exactly
    # These strings must match the 'value' in your entry.html <option> tags
    types = ['CAR', 'BIKE', 'EV', 'HEAVY']

    # --- CREATE VIP SLOTS (30 Slots) ---
    print("Syncing VIP Zones (30 Slots)...")
    for i in range(1, 31):
        # This logic distributes types evenly: VIP-101 (BIKE), VIP-102 (EV), etc.
        v_type = types[i % len(types)] 
        slot_id = f"VIP-{100+i}"
        
        # Using update_or_create ensures that even if the slot exists, 
        # it gets the correct vehicle_type and VIP status.
        ParkingSlot.objects.update_or_create(
            slot_number=slot_id,
            defaults={
                'vehicle_type': v_type,
                'is_vip': True,
                'is_available': True
            }
        )

    # --- CREATE STANDARD SLOTS (40 Slots) ---
    print("Syncing Standard Zones (40 Slots)...")
    for i in range(1, 41):
        v_type = types[i % len(types)]
        slot_id = f"STD-{200+i}"
        
        ParkingSlot.objects.update_or_create(
            slot_number=slot_id,
            defaults={
                'vehicle_type': v_type,
                'is_vip': False,
                'is_available': True
            }
        )

    print(f"\nSeeding complete! Total slots in DB: {ParkingSlot.objects.count()}")
    print("Database is now fully synced with VIP and Standard vehicle distributions.")

if __name__ == '__main__':
    populate_parking()