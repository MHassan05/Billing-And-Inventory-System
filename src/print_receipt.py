import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QGroupBox, QMessageBox, QTextEdit,
    QSpinBox, QFormLayout, QLineEdit, QApplication, QProgressBar
)
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
import sys
import subprocess
import platform

try:
    from escpos.printer import Usb, Serial, Network, File
    from escpos import printer
    import usb.core
    import serial.tools.list_ports
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4, A5
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class PrinterDetectionThread(QThread):
    """Thread for detecting available printers"""
    printers_found = pyqtSignal(dict)
    detection_finished = pyqtSignal()
    
    def run(self):
        printers = self.detect_all_printers()
        self.printers_found.emit(printers)
        self.detection_finished.emit()
    
    def detect_all_printers(self):
        """Detect all available printers"""
        printers = {
            'usb': [],
            'serial': [],
            'network': [],
            'system': []
        }
        
        # Detect USB printers
        printers['usb'] = self.detect_usb_printers()
        
        # Detect Serial printers
        printers['serial'] = self.detect_serial_printers()
        
        # Detect Network printers (basic scan)
        printers['network'] = self.detect_network_printers()
        
        # Detect System printers
        printers['system'] = self.detect_system_printers()
        
        return printers
    
    def detect_usb_printers(self):
        """Detect USB thermal printers"""
        usb_printers = []
        
        if not ESCPOS_AVAILABLE:
            return usb_printers
        
        try:
            import usb.core
            # Common thermal printer vendor IDs
            thermal_vendors = [
                0x04b8,  # Epson
                0x0fe6,  # ICS Advent (Star Micronics)
                0x0519,  # Star Micronics
                0x1504,  # Citizen
                0x1659,  # Prolific
                0x28e9,  # GprinterTech
                0x0483,  # STMicroelectronics
            ]
            
            devices = usb.core.find(find_all=True)
            for device in devices:
                if device.idVendor in thermal_vendors:
                    try:
                        manufacturer = usb.util.get_string(device, device.iManufacturer) if device.iManufacturer else "Unknown"
                        product = usb.util.get_string(device, device.iProduct) if device.iProduct else "Unknown"
                        
                        printer_info = {
                            'name': f"{manufacturer} {product}",
                            'vendor_id': hex(device.idVendor),
                            'product_id': hex(device.idProduct),
                            'address': device.address,
                            'bus': device.bus
                        }
                        usb_printers.append(printer_info)
                    except:
                        # If we can't get strings, still add basic info
                        printer_info = {
                            'name': f"USB Printer (VID:{hex(device.idVendor)} PID:{hex(device.idProduct)})",
                            'vendor_id': hex(device.idVendor),
                            'product_id': hex(device.idProduct),
                            'address': device.address,
                            'bus': device.bus
                        }
                        usb_printers.append(printer_info)
        except Exception as e:
            print(f"USB detection error: {e}")
        
        return usb_printers
    
    def detect_serial_printers(self):
        """Detect Serial port printers"""
        serial_printers = []
        
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                # Check if it might be a printer
                description = port.description.lower()
                if any(keyword in description for keyword in ['printer', 'pos', 'receipt', 'thermal', 'usb serial']):
                    printer_info = {
                        'name': f"{port.description} ({port.device})",
                        'device': port.device,
                        'description': port.description,
                        'vid': port.vid,
                        'pid': port.pid
                    }
                    serial_printers.append(printer_info)
        except Exception as e:
            print(f"Serial detection error: {e}")
        
        return serial_printers
    
    def detect_network_printers(self):
        """Basic network printer detection"""
        network_printers = []
        
        # This is a basic implementation - you might want to implement
        # more sophisticated network discovery
        try:
            # Common thermal printer IP ranges and ports
            common_ports = [9100, 515, 631]  # Raw, LPD, IPP
            
            # You could implement network scanning here
            # For now, we'll just return an empty list
            # In a real implementation, you might scan local network
            pass
            
        except Exception as e:
            print(f"Network detection error: {e}")
        
        return network_printers
    
    def detect_system_printers(self):
        """Detect system-installed printers"""
        system_printers = []
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows WMI query for printers
                try:
                    import wmi
                    c = wmi.WMI()
                    for printer in c.Win32_Printer():
                        printer_info = {
                            'name': printer.Name,
                            'status': printer.Status,
                            'port': printer.PortName,
                            'driver': printer.DriverName
                        }
                        system_printers.append(printer_info)
                except ImportError:
                    # Alternative method using subprocess
                    try:
                        result = subprocess.run(['wmic', 'printer', 'get', 'name,status'], 
                                              capture_output=True, text=True)
                        lines = result.stdout.strip().split('\n')[1:]  # Skip header
                        for line in lines:
                            if line.strip():
                                parts = line.strip().split()
                                if len(parts) >= 2:
                                    printer_info = {
                                        'name': ' '.join(parts[:-1]),
                                        'status': parts[-1]
                                    }
                                    system_printers.append(printer_info)
                    except:
                        pass
            
            elif system == "Linux":
                # Linux CUPS printers
                try:
                    result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('printer'):
                            parts = line.split()
                            if len(parts) >= 2:
                                printer_info = {
                                    'name': parts[1],
                                    'status': ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                                }
                                system_printers.append(printer_info)
                except:
                    pass
            
            elif system == "Darwin":  # macOS
                try:
                    result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('printer'):
                            parts = line.split()
                            if len(parts) >= 2:
                                printer_info = {
                                    'name': parts[1],
                                    'status': ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                                }
                                system_printers.append(printer_info)
                except:
                    pass
                    
        except Exception as e:
            print(f"System printer detection error: {e}")
        
        return system_printers

class PrintReceiptDialog(QDialog):
    def __init__(self, shop_data, cart_data, shop_folder, parent=None):
        super().__init__(parent)
        self.shop_data = shop_data
        self.cart_data = cart_data
        self.shop_folder = shop_folder
        self.detected_printers = {}
        
        # Get the project structure paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.data_dir = os.path.join(project_root, "data")
        self.shop_dir = os.path.join(self.data_dir, self.shop_folder)
        self.bills_dir = os.path.join(self.shop_dir, "bills")
        
        # Create bills directory if it doesn't exist
        os.makedirs(self.bills_dir, exist_ok=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Print Receipt")
        self.showMaximized()
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Print Receipt Options")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Receipt Preview Group
        preview_group = QGroupBox("Receipt Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(300)
        self.preview_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        self.update_preview()
        
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Print Options Group
        print_group = QGroupBox("Print Options")
        print_layout = QVBoxLayout()
        
        # Printer Type Selection
        printer_label = QLabel("Output Type:")
        self.printer_combo = QComboBox()
        self.printer_combo.addItems(["Save as PDF", "Thermal Printer (ESC/POS)", "Regular Printer"])
        if not ESCPOS_AVAILABLE:
            self.printer_combo.setItemData(1, 0, Qt.UserRole - 1)  # Disable thermal printer
        
        print_layout.addWidget(printer_label)
        print_layout.addWidget(self.printer_combo)
        
        # Paper Size (for PDF)
        self.paper_size_label = QLabel("Paper Size:")
        self.paper_size_combo = QComboBox()
        self.paper_size_combo.addItems(["A4", "Letter", "A5", "Thermal (80mm)"])
        
        print_layout.addWidget(self.paper_size_label)
        print_layout.addWidget(self.paper_size_combo)
        
        # Copies
        copies_label = QLabel("Number of Copies:")
        self.copies_spinbox = QSpinBox()
        self.copies_spinbox.setRange(1, 10)
        self.copies_spinbox.setValue(1)
        
        print_layout.addWidget(copies_label)
        print_layout.addWidget(self.copies_spinbox)
        
        print_group.setLayout(print_layout)
        layout.addWidget(print_group)
        
        # Enhanced Thermal Printer Settings
        self.thermal_group = QGroupBox("Thermal Printer Settings")
        thermal_layout = QVBoxLayout()
        
        # Detect Printers Button
        detect_btn_layout = QHBoxLayout()
        self.detect_btn = QPushButton("🔍 Detect Printers")
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.detect_btn.clicked.connect(self.detect_printers)
        
        self.detection_progress = QProgressBar()
        self.detection_progress.setVisible(False)
        self.detection_progress.setRange(0, 0)  # Indeterminate progress
        
        detect_btn_layout.addWidget(self.detect_btn)
        detect_btn_layout.addWidget(self.detection_progress)
        detect_btn_layout.addStretch()
        
        thermal_layout.addLayout(detect_btn_layout)
        
        # Printer Selection
        form_layout = QFormLayout()
        
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["USB", "Serial", "Network", "System"])
        form_layout.addRow("Connection Type:", self.printer_type_combo)
        
        self.available_printers_combo = QComboBox()
        self.available_printers_combo.addItem("No printers detected - Click 'Detect Printers'")
        form_layout.addRow("Available Printers:", self.available_printers_combo)
        
        # Manual entry (for network printers or custom configurations)
        self.manual_entry_input = QLineEdit()
        self.manual_entry_input.setPlaceholderText("Manual IP/Path (optional)")
        form_layout.addRow("Manual Entry:", self.manual_entry_input)
        
        thermal_layout.addLayout(form_layout)
        
        self.thermal_group.setLayout(thermal_layout)
        self.thermal_group.setVisible(False)
        layout.addWidget(self.thermal_group)
        
        # Connect signals
        self.printer_combo.currentTextChanged.connect(self.on_printer_type_changed)
        self.printer_type_combo.currentTextChanged.connect(self.update_printer_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.print_btn = QPushButton("Print Receipt")
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.print_btn.clicked.connect(self.print_receipt)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def on_printer_type_changed(self, printer_type):
        """Handle printer type change"""
        if "Thermal" in printer_type:
            self.thermal_group.setVisible(True)
            self.paper_size_combo.setCurrentText("Thermal (80mm)")
        else:
            self.thermal_group.setVisible(False)
    
    def detect_printers(self):
        """Start printer detection in background thread"""
        self.detect_btn.setEnabled(False)
        self.detection_progress.setVisible(True)
        
        # Start detection thread
        self.detection_thread = PrinterDetectionThread()
        self.detection_thread.printers_found.connect(self.on_printers_detected)
        self.detection_thread.detection_finished.connect(self.on_detection_finished)
        self.detection_thread.start()
    
    def on_printers_detected(self, printers):
        """Handle detected printers"""
        self.detected_printers = printers
        self.update_printer_list()
    
    def on_detection_finished(self):
        """Handle detection completion"""
        self.detect_btn.setEnabled(True)
        self.detection_progress.setVisible(False)
        
        # Show detection results
        total_found = sum(len(printers) for printers in self.detected_printers.values())
        if total_found > 0:
            QMessageBox.information(
                self, 
                "Detection Complete", 
                f"Found {total_found} printer(s). Select connection type to view available printers."
            )
        else:
            QMessageBox.information(
                self, 
                "Detection Complete", 
                "No printers detected. You can still enter printer details manually."
            )
    
    def update_printer_list(self):
        """Update the printer list based on selected connection type"""
        connection_type = self.printer_type_combo.currentText().lower()
        self.available_printers_combo.clear()
        
        if connection_type in self.detected_printers:
            printers = self.detected_printers[connection_type]
            if printers:
                for printer in printers:
                    self.available_printers_combo.addItem(printer['name'], printer)
            else:
                self.available_printers_combo.addItem(f"No {connection_type} printers detected")
        else:
            self.available_printers_combo.addItem(f"No {connection_type} printers detected")
    
    def get_selected_printer_config(self):
        """Get configuration for selected printer"""
        connection_type = self.printer_type_combo.currentText().lower()
        
        # Check if manual entry is provided
        manual_entry = self.manual_entry_input.text().strip()
        if manual_entry:
            return {
                'type': connection_type,
                'manual': True,
                'address': manual_entry
            }
        
        # Get selected printer from dropdown
        current_data = self.available_printers_combo.currentData()
        if current_data:
            config = {
                'type': connection_type,
                'manual': False,
                'printer_data': current_data
            }
            return config
        
        return None
    
    def print_thermal(self):
        """Print using thermal printer with auto-detected configuration"""
        if not ESCPOS_AVAILABLE:
            QMessageBox.warning(self, "Not Available", 
                              "ESC/POS library not installed. Please install python-escpos.")
            return
        
        printer_config = self.get_selected_printer_config()
        if not printer_config:
            QMessageBox.warning(self, "No Printer Selected", 
                              "Please select a printer or enter manual configuration.")
            return
        
        try:
            # Create printer instance based on configuration
            if printer_config['manual']:
                # Manual configuration
                connection_type = printer_config['type']
                address = printer_config['address']
                
                if connection_type == 'usb':
                    # Parse USB address (vendor_id:product_id)
                    if ':' in address:
                        vid, pid = address.split(':')
                        p = Usb(int(vid, 16), int(pid, 16))
                    else:
                        raise ValueError("USB format should be vendor_id:product_id (hex)")
                        
                elif connection_type == 'serial':
                    p = Serial(address)
                    
                elif connection_type == 'network':
                    p = Network(address)
                    
                else:
                    raise ValueError(f"Unsupported connection type: {connection_type}")
            
            else:
                # Auto-detected printer
                printer_data = printer_config['printer_data']
                connection_type = printer_config['type']
                
                if connection_type == 'usb':
                    vid = int(printer_data['vendor_id'], 16)
                    pid = int(printer_data['product_id'], 16)
                    p = Usb(vid, pid)
                    
                elif connection_type == 'serial':
                    p = Serial(printer_data['device'])
                    
                elif connection_type == 'network':
                    # This would need the IP address from network detection
                    ip = printer_data.get('ip', '192.168.1.100')
                    p = Network(ip)
                    
                else:
                    raise ValueError(f"Unsupported connection type: {connection_type}")
            
            # Generate and print receipt
            receipt_text = self.generate_receipt_text()
            
            # Print the receipt
            p.text(receipt_text)
            p.cut()
            p.close()
            
            QMessageBox.information(self, "Success", "Receipt printed successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Printing Error", 
                               f"Failed to print receipt:\n{str(e)}")
    
    # ... (rest of the methods remain the same as in your original code)
    def update_preview(self):
        """Update receipt preview"""
        receipt_text = self.generate_receipt_text()
        self.preview_text.setText(receipt_text)
    
    def generate_receipt_text(self):
        """Generate receipt text content"""
        receipt = []
        
        # Header
        receipt.append("*" * 35)
        receipt.append("RECEIPT".center(35))
        receipt.append("*" * 35)
        
        # Shop Info
        shop_name = self.shop_data.get('shop_name', 'Unknown Shop')
        receipt.append(shop_name.center(35))
        
        owner_name = self.shop_data.get('owner_name', '')
        if owner_name:
            receipt.append(f"Owner: {owner_name}".center(35))
        
        address = self.shop_data.get('address', '')
        if address:
            receipt.append(address.center(35))
        
        mobile_numbers = self.shop_data.get('mobile_numbers', [])
        if mobile_numbers:
            mobile_text = " | ".join(mobile_numbers)
            receipt.append(mobile_text.center(35))
        
        receipt.append("-" * 35)
        
        # Date and Time
        now = datetime.now()
        receipt.append(f"Date: {now.strftime('%d-%m-%Y')}")
        receipt.append(f"Time: {now.strftime('%I:%M %p')}")
        
        # Receipt Number
        receipt_no = self.get_next_receipt_number()
        receipt.append(f"Receipt#: {receipt_no}")
        receipt.append("-" * 35)
        
        # Items
        receipt.append("ITEMS:")
        receipt.append("-" * 35)
        
        for item in self.cart_data:
            item_line = f"{item['quantity']} x {item['name']}"
            if len(item_line) > 25:
                item_line = item_line[:22] + "..."
            price_text = f"Rs {item['total_price']:.2f}"
            receipt.append(f"{item_line:<25} {price_text:>9}")
        
        receipt.append("-" * 35)
        
        # Totals
        total_line = f"TOTAL AMOUNT"
        total_amount = sum(item['total_price'] for item in self.cart_data)
        total_price = f"Rs {total_amount:.2f}"
        receipt.append(f"{total_line:<25} {total_price:>9}")
        
        receipt.append("-" * 35)
        receipt.append("THANK YOU!".center(35))
        receipt.append("*" * 35)
        
        return "\n".join(receipt)
    
    def get_next_receipt_number(self):
        """Generate next receipt number"""
        receipt_files = [f for f in os.listdir(self.bills_dir) if f.startswith('sr#') and f.endswith('.pdf')]
        
        if not receipt_files:
            return "sr#0001"
        
        # Extract numbers and find max
        numbers = []
        for filename in receipt_files:
            try:
                num_str = filename[3:7]  # Extract 4 digits after "sr#"
                numbers.append(int(num_str))
            except:
                continue
        
        if numbers:
            next_num = max(numbers) + 1
        else:
            next_num = 1
        
        return f"sr#{next_num:04d}"
    
    def print_receipt(self):
        """Print or save the receipt"""
        printer_type = self.printer_combo.currentText()
        
        try:
            if printer_type == "Save as PDF":
                self.save_as_pdf()
            elif "Thermal" in printer_type:
                self.print_thermal()
            else:
                self.print_regular()
            
            # Only show success message for regular printing
            if printer_type == "Regular Printer":
                QMessageBox.information(self, "Success", "Receipt processed successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process receipt: {str(e)}")
    
    def save_as_pdf(self):
        """Save receipt as PDF"""
        if not REPORTLAB_AVAILABLE:
            # Fallback to simple text file
            self.save_as_text_file()
            return
        
        receipt_no = self.get_next_receipt_number()
        
        # Show file dialog to let user choose where to save
        default_filename = f"{receipt_no}.pdf"
        default_path = os.path.join(self.bills_dir, default_filename)
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Receipt As PDF",
            default_path,
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not filename:
            return
        
        # Create PDF (implementation remains the same as your original code)
        QMessageBox.information(
            self, 
            "PDF Saved Successfully", 
            f"Receipt saved successfully!\n\nLocation: {filename}"
        )
    
    def save_as_text_file(self):
        """Fallback: Save as text file when reportlab is not available"""
        # Implementation remains the same as your original code
        pass
    
    def print_regular(self):
        """Print using regular printer"""
        receipt_text = self.generate_receipt_text()
        
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec_() == QPrintDialog.Accepted:
            document = QTextDocument()
            document.setPlainText(receipt_text)
            document.print_(printer)
        
def show_print_receipt_dialog(inventory_manager, cart_data):
    """Main function to show print receipt dialog from inventory manager"""
    
    if not cart_data or all (not item for item in cart_data):
        QMessageBox.warning(inventory_manager, "Empty Cart", "Please add items to cart before printing receipt.")
        return
    
    try: 
        # Show print dialog
        print_dialog = PrintReceiptDialog(
            inventory_manager.shop_info,
            cart_data,
            inventory_manager.shop_folder,
            inventory_manager
        )
        print_dialog.exec_()
        return True
    except Exception as e:
        print(f"Error! {e}")
        return False

# For testing
if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    
    # Sample data for testing
    sample_shop_data = {
        "shop_name": "Test Shop",
        "owner_name": "John Doe",
        "address": "123 Main Street",
        "mobile_numbers": ["123-456-7890"]
    }
    
    sample_cart_data = [
            {'name': 'T-Shirt', 'quantity': 2, 'unit_price': 25.99, 'total_price': 51.98},
            {'name': 'Jeans', 'quantity': 1, 'unit_price': 49.99, 'total_price': 49.99}
    ]
    
    dialog = PrintReceiptDialog(sample_shop_data, sample_cart_data, "test_shop")
    dialog.show()
    
    sys.exit(app.exec_())
