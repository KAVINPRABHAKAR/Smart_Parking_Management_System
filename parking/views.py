import json
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required  # Added for security

# Advanced PDF Libraries
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A6, letter
from reportlab.lib.units import mm

from .models import ParkingSlot, ParkingTransaction
from .utils.billing_engine import calculate_parking_fee
from .utils.analytics import get_daily_analytics

# --- DASHBOARD VIEW ---
@login_required
def dashboard(request):
    """Updates Live Status and Analytics metrics."""
    slots = ParkingSlot.objects.all().order_by('slot_number')
    stats = get_daily_analytics()
    
    if not stats:
        stats = {
            'total_revenue': 0.00, 
            'total_vehicles': 0, 
            'avg_revenue': 0.00,
            'max_single_fee': 0.00,
            'type_distribution': {}
        }

    context = {
        'slots': slots,
        'analytics': stats,
        'total_slots': slots.count(),
        'available_slots': slots.filter(is_available=True).count(),
    }
    return render(request, 'parking/dashboard.html', context)

# --- ENTRY VIEW ---
@login_required
def vehicle_entry(request):
    """Assigns slot based on zone selection and specific vehicle type."""
    if request.method == "POST":
        v_number = request.POST.get('vehicle_number', '').upper()
        v_type = request.POST.get('vehicle_type')
        cust_name = request.POST.get('customer_name', 'Guest')
        zone_choice = request.POST.get('parking_zone') 

        if not zone_choice:
            messages.error(request, "Selection Required: Please choose a Parking Zone.")
            return redirect('vehicle_entry')
        
        slot = ParkingSlot.objects.filter(
            vehicle_type=v_type, 
            is_available=True,
            is_vip=(zone_choice == 'vip')
        ).first()
        
        if slot:
            ParkingTransaction.objects.create(
                slot=slot,
                vehicle_number=v_number,
                customer_name=cust_name,
                entry_time=timezone.now(),
                is_active=True
            )
            slot.is_available = False
            slot.save()
            
            messages.success(request, f"Entry Confirmed: {v_number} assigned to {slot.slot_number}")
            return redirect('dashboard')
        else:
            messages.error(request, f"Allocation Failed: No available {v_type} slots in {zone_choice.upper()} zone.")
            
    return render(request, 'parking/entry.html')

# --- EXIT VIEW ---
@login_required
def vehicle_exit(request):
    """Processes payment and ensures the fee is committed to DB before receipt."""
    transaction = None
    fee = 0
    show_receipt = False
    active_customers = ParkingTransaction.objects.filter(is_active=True).order_by('customer_name')

    if request.method == "POST":
        v_number = request.POST.get('vehicle_number')
        action = request.POST.get('action')
        transaction = ParkingTransaction.objects.filter(vehicle_number=v_number, is_active=True).first()
        
        if transaction:
            fee = calculate_parking_fee(
                transaction.entry_time, 
                timezone.now(), 
                transaction.slot.vehicle_type,
                transaction.slot.is_vip
            )

            if action == "process_payment":
                transaction.exit_time = timezone.now()
                transaction.fee_charged = fee
                transaction.is_active = False
                transaction.save() 
                
                slot = transaction.slot
                slot.is_available = True
                slot.save()
                
                transaction.refresh_from_db()
                
                messages.success(request, f"Payment Processed: ₹{transaction.fee_charged:.2f}")
                show_receipt = True 
        else:
            messages.error(request, "Error: No active record found.")
            
    return render(request, 'parking/exit.html', {
        'transaction': transaction, 
        'fee': fee, 
        'active_customers': active_customers, 
        'show_receipt': show_receipt
    })

# --- PDF GENERATORS ---
@login_required
def generate_receipt_pdf(request, transaction_id):
    tx = get_object_or_404(ParkingTransaction, id=transaction_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{tx.vehicle_number}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=(105 * mm, 148 * mm), topMargin=5*mm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("SMART PARKING PRO", ParagraphStyle('Title', fontSize=14, alignment=1, textColor=colors.dodgerblue)))
    elements.append(Spacer(1, 5*mm))

    data = [
        ["Customer:", tx.customer_name],
        ["Vehicle:", tx.vehicle_number],
        ["Type:", tx.slot.vehicle_type],
        ["Entry:", tx.entry_time.strftime("%d/%m %H:%M")],
        ["Exit:", tx.exit_time.strftime("%d/%m %H:%M") if tx.exit_time else "N/A"],
        ["TOTAL PAID:", f"₹{tx.fee_charged:.2f}"]
    ]
    
    t = Table(data, colWidths=[30*mm, 50*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,5), (-1,5), colors.darkgreen),
        ('LINEABOVE', (0,5), (-1,5), 1, colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return response

@login_required
def export_pdf_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Parking_Revenue_Report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Detailed Revenue & Customer Log", styles['Title']))
    elements.append(Spacer(1, 10*mm))
    
    data = [["Vehicle", "Customer", "Zone", "Type", "Entry", "Exit", "Fee"]]
    transactions = ParkingTransaction.objects.filter(is_active=False).order_by('-exit_time')
    
    for tx in transactions:
        data.append([
            tx.vehicle_number,
            tx.customer_name, 
            "VIP" if tx.slot.is_vip else "STD",
            tx.slot.vehicle_type,
            tx.entry_time.strftime("%d/%m %H:%M"),
            tx.exit_time.strftime("%d/%m %H:%M") if tx.exit_time else "N/A",
            f"₹{tx.fee_charged:.2f}"
        ])
    
    table = Table(data, colWidths=[80, 100, 40, 60, 90, 90, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.dodgerblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    
    elements.append(table)
    doc.build(elements)
    return response

@login_required
def revenue_report_page(request):
    analytics_data = get_daily_analytics()
    all_transactions = ParkingTransaction.objects.all().order_by('-entry_time')
    
    exited_txs = ParkingTransaction.objects.filter(is_active=False).order_by('-exit_time')[:10]
    chart_labels = [tx.exit_time.strftime("%H:%M") for tx in exited_txs][::-1]
    chart_data = [float(tx.fee_charged) for tx in exited_txs][::-1]

    return render(request, 'parking/reports.html', {
        'analytics': analytics_data,
        'transactions': all_transactions,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })