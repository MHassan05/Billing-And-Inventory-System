import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QGroupBox, QMessageBox, QTextEdit,
    QSpinBox, QFormLayout, QLineEdit, QApplication
)
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument
import sys

try:
    from escpos.printer import Usb, Serial, Network, File
    from escpos import printer
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
    
class PrintReceiptDialog(QDialog):
    def __init__(self, shop_data, cart_data, shop_folder, parent=None):
        super().__init__(parent)
        self.shop_data = shop_data
        self.cart_data = cart_data
        self.shop_folder = shop_folder
        self.setMaximumSize(self.maximumSize())
        self.setMinimumSize(self.maximumSize())
        
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
        
        # Orientation
        self.orientation_label = QLabel("Orientation:")
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Portrait", "Landscape"])
        
        print_layout.addWidget(self.orientation_label)
        print_layout.addWidget(self.orientation_combo)
        
        # Copies
        copies_label = QLabel("Number of Copies:")
        self.copies_spinbox = QSpinBox()
        self.copies_spinbox.setRange(1, 10)
        self.copies_spinbox.setValue(1)
        
        print_layout.addWidget(copies_label)
        print_layout.addWidget(self.copies_spinbox)
        
        print_group.setLayout(print_layout)
        layout.addWidget(print_group)
        
        # Thermal Printer Settings (initially hidden)
        self.thermal_group = QGroupBox("Thermal Printer Settings")
        thermal_layout = QFormLayout()
        
        self.printer_type_combo = QComboBox()
        self.printer_type_combo.addItems(["USB", "Serial", "Network"])
        thermal_layout.addRow("Connection Type:", self.printer_type_combo)
        
        self.printer_path_input = QLineEdit()
        self.printer_path_input.setPlaceholderText("e.g., /dev/ttyUSB0 or 192.168.1.100")
        thermal_layout.addRow("Printer Path/IP:", self.printer_path_input)
        
        self.thermal_group.setLayout(thermal_layout)
        self.thermal_group.setVisible(False)
        layout.addWidget(self.thermal_group)
        
        # Connect signals
        self.printer_combo.currentTextChanged.connect(self.on_printer_type_changed)
        
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
            
            # Only show success message for thermal and regular printing
            # PDF and text file saving show their own success messages
            if "Thermal" in printer_type or printer_type == "Regular Printer":
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
        # Set default filename and location
        default_filename = f"{receipt_no}.pdf"
        default_path = os.path.join(self.bills_dir, default_filename)
        
        # Show save dialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Receipt As PDF",
            default_path,
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        # If user cancelled the dialog
        if not filename:
            return
        
        # Create PDF
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=16,
            spaceAfter=12
        )
        
        center_style = ParagraphStyle(
            'CustomCenter',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10,
            spaceAfter=6
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4
        )
        
        # Build PDF content
        story.append(Paragraph("RECEIPT", title_style))
        story.append(Spacer(1, 12))
        
        # Shop info
        shop_name = self.shop_data.get('shop_name', 'Unknown Shop')
        story.append(Paragraph(shop_name, center_style))
        
        owner_name = self.shop_data.get('owner_name', '')
        if owner_name:
            story.append(Paragraph(f"Owner: {owner_name}", center_style))
        
        address = self.shop_data.get('address', '')
        if address:
            story.append(Paragraph(address, center_style))
        
        mobile_numbers = self.shop_data.get('mobile_numbers', [])
        if mobile_numbers:
            mobile_text = " | ".join(mobile_numbers)
            story.append(Paragraph(mobile_text, center_style))
        
        story.append(Spacer(1, 12))
        
        # Date and receipt info
        now = datetime.now()
        story.append(Paragraph(f"Date: {now.strftime('%d-%m-%Y')}", normal_style))
        story.append(Paragraph(f"Time: {now.strftime('%I:%M %p')}", normal_style))
        story.append(Paragraph(f"Receipt#: {receipt_no}", normal_style))
        
        story.append(Spacer(1, 12))
        
        # Items table
        table_data = [['Qty', 'Item', 'Unit Price', 'Total']]
        
        # Fixed: cart_data is a list, not a dict with 'items' key
        for item in self.cart_data:
            table_data.append([
                str(item['quantity']),
                item['name'],
                f"Rs {item['unit_price']:.2f}",
                f"Rs {item['total_price']:.2f}"
            ])
        
        # Calculate total from cart data
        total_amount = sum(item['total_price'] for item in self.cart_data)
        table_data.append(['', '', 'TOTAL:', f"Rs {total_amount:.2f}"])
        
        # Check if cart_data has payment info (if it's a dict structure)
        if isinstance(self.cart_data, dict):
            if self.cart_data.get('cash_received', 0) > 0:
                table_data.append(['', '', 'CASH:', f"Rs {self.cart_data['cash_received']:.2f}"])
                table_data.append(['', '', 'CHANGE:', f"Rs {self.cart_data['change']:.2f}"])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 24))
        story.append(Paragraph("THANK YOU!", center_style))
        
        # Build PDF
        doc.build(story)

        QMessageBox.information(
            self, 
            "PDF Saved Successfully", 
            f"Receipt saved successfully!\n\nLocation: {filename}"
        )      
    
    def save_as_text_file(self):
        """Fallback: Save as text file when reportlab is not available"""
        receipt_no = self.get_next_receipt_number()
        
        # Set default filename and location
        default_filename = f"{receipt_no}.txt"
        default_path = os.path.join(self.bills_dir, default_filename)
        
        # Show save dialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Receipt As Text File",
            default_path,
            "Text Files (*.txt);;All Files (*)"
        )
        
        # If user cancelled the dialog
        if not filename:
            return
        
        receipt_text = self.generate_receipt_text()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(receipt_text)
            
            # Show success message with file location
            QMessageBox.information(
                self, 
                "Text File Saved Successfully", 
                f"Receipt saved successfully!\n\nLocation: {filename}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error Saving File", 
                f"Failed to save receipt:\n{str(e)}"
            )
    
    def print_thermal(self):
        """Print using thermal printer"""
        if not ESCPOS_AVAILABLE:
            QMessageBox.warning(self, "Not Available", 
                              "ESC/POS library not installed. Please install python-escpos.")
            return
        
        # This is a placeholder - actual implementation would depend on your thermal printer setup
        QMessageBox.information(self, "Thermal Print", 
                              "Thermal printing feature is ready but requires specific printer configuration.")
    
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