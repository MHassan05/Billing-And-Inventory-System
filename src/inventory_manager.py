from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox, QHeaderView, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QGroupBox, QListWidget,
    QListWidgetItem, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os
import json
import sys
from datetime import datetime
import pandas as pd
from carted_items import CartDialog
from path_utilis import get_base_path

# Import the print receipt functionality
try:
    from print_receipt import show_print_receipt_dialog
    PRINT_RECEIPT_AVAILABLE = True
except ImportError:
    PRINT_RECEIPT_AVAILABLE = False
    print("Warning: print_receipt.py not found. Print functionality will be limited.")

# Get the directory paths
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# def get_base_path():
#     if getattr(sys, 'frozen', False):
#         # Running in a PyInstaller bundle
#         return sys._MEIPASS
#     # Running as a .py script
#     return os.path.dirname(os.path.abspath(__file__))

# DATA_DIR = os.path.join(get_base_path(), 'data')
DATA_DIR = os.path.join(get_base_path(), 'data')

class CategorySelectionWidget(QWidget):
    """Custom widget for selecting multiple categories"""

    def __init__(self, existing_categories=None, selected_categories=None):
        super().__init__()
        self.existing_categories = existing_categories or []
        self.selected_categories = selected_categories or []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Add new category section
        add_category_layout = QHBoxLayout()
        self.new_category_input = QLineEdit()
        self.new_category_input.setPlaceholderText("Enter new category name...")
        add_category_btn = QPushButton("Add Category")
        add_category_btn.clicked.connect(self.add_new_category)

        add_category_layout.addWidget(QLabel("New Category:"))
        add_category_layout.addWidget(self.new_category_input)
        add_category_layout.addWidget(add_category_btn)

        layout.addLayout(add_category_layout)

        # Available categories list
        layout.addWidget(QLabel("Select Categories:"))
        self.category_list = QListWidget()
        self.category_list.setMaximumHeight(150)
        self.populate_category_list()

        layout.addWidget(self.category_list)

        # Selected categories display
        layout.addWidget(QLabel("Selected Categories:"))
        self.selected_label = QLabel("None selected")
        self.selected_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        layout.addWidget(self.selected_label)

        self.setLayout(layout)
        self.update_selected_display()

    def populate_category_list(self):
        """Populate the category list with checkboxes"""
        self.category_list.clear()
        all_categories = sorted(set(self.existing_categories))

        for category in all_categories:
            item = QListWidgetItem()
            checkbox = QCheckBox(category)
            checkbox.setChecked(category in self.selected_categories)
            checkbox.stateChanged.connect(self.on_category_changed)

            self.category_list.addItem(item)
            self.category_list.setItemWidget(item, checkbox)

    def add_new_category(self):
        """Add a new category"""
        new_category = self.new_category_input.text().strip()
        if not new_category:
            QMessageBox.warning(self, "Invalid Input", "Please enter a category name.")
            return

        if new_category in self.existing_categories:
            QMessageBox.information(self, "Category Exists", "This category already exists.")
            return

        self.existing_categories.append(new_category)
        self.selected_categories.append(new_category)
        self.new_category_input.clear()
        self.populate_category_list()
        self.update_selected_display()

    def on_category_changed(self, state):
        """Handle category selection change"""
        sender = self.sender()
        category = sender.text()

        if state == Qt.Checked:
            if category not in self.selected_categories:
                self.selected_categories.append(category)
        else:
            if category in self.selected_categories:
                self.selected_categories.remove(category)

        self.update_selected_display()

    def update_selected_display(self):
        """Update the selected categories display"""
        if self.selected_categories:
            display_text = ", ".join(sorted(self.selected_categories))
        else:
            display_text = "None selected"
        self.selected_label.setText(display_text)

    def get_selected_categories(self):
        """Get the list of selected categories"""
        return self.selected_categories.copy()

    def set_selected_categories(self, categories):
        """Set the selected categories"""
        self.selected_categories = categories.copy() if categories else []
        self.populate_category_list()
        self.update_selected_display()

class AddItemDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, item_data=None, existing_categories=None):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.item_data = item_data or {}
        self.existing_categories = existing_categories or []

        self.setWindowTitle("Edit Item" if edit_mode else "Add New Item")
        self.setMinimumSize(500, 400)
        self.setup_ui()

        if edit_mode and item_data:
            self.load_item_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Form layout for item details
        form_layout = QFormLayout()

        # Item Name
        self.name_input = QLineEdit()
        form_layout.addRow("Item Name:", self.name_input)

        # Category Selection Widget
        current_categories = self.item_data.get('categories', []) if self.edit_mode else []
        self.category_widget = CategorySelectionWidget(
            existing_categories=self.existing_categories,
            selected_categories=current_categories
        )

        category_group = QGroupBox("Categories")
        category_layout = QVBoxLayout()
        category_layout.addWidget(self.category_widget)
        category_group.setLayout(category_layout)

        layout.addWidget(category_group)

        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 999999)
        form_layout.addRow("Quantity:", self.quantity_input)

        # Unit Price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.00, 999999.99)
        self.price_input.setDecimals(2)
        form_layout.addRow("Unit Price:", self.price_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_item_data(self):
        """Load existing item data for editing"""
        self.name_input.setText(self.item_data.get('name', ''))
        self.quantity_input.setValue(self.item_data.get('quantity', 0))
        self.price_input.setValue(self.item_data.get('price', 0.0))

        # Load categories
        categories = self.item_data.get('categories', [])
        # Handle backward compatibility - convert single category to list
        if isinstance(self.item_data.get('category'), str):
            categories = [self.item_data.get('category')]

        self.category_widget.set_selected_categories(categories)

    def get_item_data(self):
        """Get the item data from the form"""
        return {
            'name': self.name_input.text().strip(),
            'categories': self.category_widget.get_selected_categories(),
            'quantity': self.quantity_input.value(),
            'price': self.price_input.value()
        }

    def accept(self):
        """Override accept method to validate before accepting"""
        if not self.validate_data():
            return  # Don't call super().accept() if validation fails

        super().accept()  # Close dialog only if validation passes

    def validate_data(self):
        """Validate the form data"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Item name is required.")
            return False
        if not self.category_widget.get_selected_categories():
            QMessageBox.warning(self, "Validation Error", "At least one category must be selected.")
            return False
        return True

    def get_all_categories(self):
        """Get all categories including newly added ones"""
        return self.category_widget.existing_categories


class InventoryManager(QMainWindow):
    def __init__(self, shop_folder,previous_window=None):
        super().__init__()
        self.shop_folder = shop_folder
        self.previous_window = previous_window
        self.shop_path = os.path.join(DATA_DIR, shop_folder)
        self.inventory_file = os.path.join(self.shop_path, "inventory.json")
        self.inventory_data = []
        self.cart_items = []

        self.load_shop_info()
        self.load_inventory_data()
        self.setup_ui()
        self.populate_table()

    def load_shop_info(self):
        """Load shop information"""
        info_path = os.path.join(self.shop_path, "shop_info.json")
        try:
            with open(info_path, 'r') as f:
                self.shop_info = json.load(f)
        except:
            self.shop_info = {"shop_name": self.shop_folder}

    def load_inventory_data(self):
        """Load inventory data from JSON file"""
        try:
            if os.path.exists(self.inventory_file):
                with open(self.inventory_file, 'r') as f:
                    self.inventory_data = json.load(f)

                # Convert old format to new format (backward compatibility)
                for item in self.inventory_data:
                    if 'category' in item and 'categories' not in item:
                        item['categories'] = [item['category']] if item['category'] else []
                        del item['category']
                    elif 'categories' not in item:
                        item['categories'] = []
            else:
                self.inventory_data = []
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load inventory data: {str(e)}")
            self.inventory_data = []

    def save_inventory_data(self):
        """Save inventory data to JSON file"""
        try:
            with open(self.inventory_file, 'w') as f:
                json.dump(self.inventory_data, f, indent=4)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save inventory data: {str(e)}")
            return False

    def get_all_categories(self):
        """Get all unique categories from inventory"""
        categories = set()
        for item in self.inventory_data:
            item_categories = item.get('categories', [])
            categories.update(item_categories)
        return list(categories)

    def setup_ui(self):
        self.setWindowTitle(f"Inventory Management - {self.shop_info.get('shop_name', 'Unknown Shop')}")
        self.showMaximized()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Header section
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # Search and filter section
        search_layout = self.create_search_section()
        main_layout.addLayout(search_layout)

        # Buttons section
        buttons_layout = self.create_buttons_section()
        main_layout.addLayout(buttons_layout)

        # Table section
        self.create_table()
        main_layout.addWidget(self.table)

        # Status section
        status_layout = self.create_status_section()
        main_layout.addLayout(status_layout)

    def create_header(self):
        """Create header section with shop info"""
        layout = QHBoxLayout()

        # Shop info
        shop_info_layout = QVBoxLayout()
        shop_name = QLabel(f"Shop: {self.shop_info.get('shop_name', 'Unknown')}")
        shop_name.setFont(QFont("Arial", 16, QFont.Bold))
        owner_name = QLabel(f"Owner: {self.shop_info.get('owner_name', 'Unknown')}")
        owner_name.setFont(QFont("Arial", 12))

        shop_info_layout.addWidget(shop_name)
        shop_info_layout.addWidget(owner_name)

        layout.addLayout(shop_info_layout)
        layout.addStretch()

        # Back button
        back_btn = QPushButton("← Back to Shop Selection")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)

        return layout

    def create_search_section(self):
        """Create search and filter section"""
        layout = QHBoxLayout()

        # Search box
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by item name, category, or supplier...")
        self.search_input.textChanged.connect(self.filter_table)

        # Category filter
        category_label = QLabel("Category:")
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.filter_table)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input, 2)
        layout.addWidget(category_label)
        layout.addWidget(self.category_filter, 1)

        return layout

    def create_buttons_section(self):
        """Create action buttons section"""
        layout = QHBoxLayout()

        # Add Item button
        add_btn = QPushButton("+ Add New Item")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(self.add_item)

        # Edit Item button
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        edit_btn.clicked.connect(self.edit_item)

        # Delete Item button
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(self.delete_item)

        # Print Receipt button
        print_btn = QPushButton("🖨️ Print Receipt")
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        print_btn.clicked.connect(self.print_receipt)

        # View Cart button
        cart_btn = QPushButton("🛒 View Cart")
        cart_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        cart_btn.clicked.connect(self.show_cart)

        # Export button
        export_btn = QPushButton("📊 Export to Excel")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #198754;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #146c43;
            }
        """)
        export_btn.clicked.connect(self.export_to_excel)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)

        layout.addWidget(add_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        layout.addWidget(print_btn)
        layout.addStretch()
        layout.addWidget(cart_btn)
        layout.addWidget(export_btn)
        layout.addWidget(refresh_btn)

        return layout

    def create_table(self):
        """Create the inventory table"""
        self.table = QTableWidget()

        self.table.setColumnCount(6)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setHorizontalHeaderLabels([
            "Item Name", "Categories", "Quantity", "Price (Rs)" , "Select Qty", "Add to Cart"
        ])

        # Table settings
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Item Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Categories
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Quantity
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unit Price
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Select Quantity
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Add to Cart

        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

    def create_status_section(self):
        """Create status section showing summary info"""
        layout = QHBoxLayout()

        self.total_items_label = QLabel("Total Items: 0")
        self.total_value_label = QLabel("Total Value: Rs 0.00")

        # Style the status labels
        for label in [self.total_items_label, self.total_value_label]:
            label.setStyleSheet("""
                QLabel {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        layout.addWidget(self.total_items_label)
        layout.addWidget(self.total_value_label)
        layout.addStretch()

        return layout

    def populate_table(self):
        """Populate the table with inventory data"""
        self.table.setRowCount(len(self.inventory_data))

        all_categories = set()

        for row, item in enumerate(self.inventory_data):
            # Item Name
            self.table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))

            # Categories
            categories = item.get('categories', [])
            all_categories.update(categories)
            categories_text = ", ".join(sorted(categories)) if categories else "No Category"
            self.table.setItem(row, 1, QTableWidgetItem(categories_text))

            # Quantity
            quantity = item.get('quantity', 0)
            quantity_item = QTableWidgetItem(str(quantity))
            quantity_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, quantity_item)

            # Price (in Rs)
            price = item.get('price', 0.0)
            price_item = QTableWidgetItem(f"Rs {price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(row, 3, price_item)

             # Select Quantity Spinbox
            qty_spinbox = QSpinBox()
            qty_spinbox.setRange(0, quantity)
            qty_spinbox.setValue(0)
            self.table.setCellWidget(row, 4, qty_spinbox)

            # Add to Cart Button
            cart_button = QPushButton("Add to Cart")
            cart_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            cart_button.clicked.connect(lambda checked, r=row: self.add_to_cart(r))
            self.table.setCellWidget(row, 5, cart_button)

        # Update category filter
        self.update_category_filter(all_categories)
        self.update_status_info()

    def update_category_filter(self, categories):
        """Update the category filter dropdown"""
        current_selection = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")

        for category in sorted(categories):
            if category:  # Only add non-empty categories
                self.category_filter.addItem(category)

        # Restore previous selection if it still exists
        index = self.category_filter.findText(current_selection)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)

    def update_status_info(self):
        """Update the status information labels"""
        total_items = len(self.inventory_data)
        total_value = sum(item.get('quantity', 0) * item.get('price', 0.0) for item in self.inventory_data)

        self.total_items_label.setText(f"Total Items: {total_items}")
        self.total_value_label.setText(f"Total Inventory Value: Rs {total_value:.2f}")

    def filter_table(self):
        """Filter the table based on search criteria"""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()

        for row in range(self.table.rowCount()):
            show_row = True

            # Get item data for this row
            item_data = self.inventory_data[row] if row < len(self.inventory_data) else {}

            # Search filter
            if search_text:
                item_name = self.table.item(row, 0).text().lower() if self.table.item(row, 0) else ""
                categories = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ""

                if not (search_text in item_name or search_text in categories):
                    show_row = False

            # Category filter
            if category_filter != "All Categories":
                item_categories = item_data.get('categories', [])
                if category_filter not in item_categories:
                    show_row = False

            self.table.setRowHidden(row, not show_row)

    def add_item(self):
        """Add a new item to inventory"""
        existing_categories = self.get_all_categories()
        dialog = AddItemDialog(self, existing_categories=existing_categories)

        if dialog.exec_() == QDialog.Accepted:
            item_data = dialog.get_item_data()

            # Check for duplicates
            for existing_item in self.inventory_data:
                if existing_item['name'].lower() == item_data['name'].lower():
                    QMessageBox.warning(self, "Duplicate Item",
                                        f"An item with the name '{item_data['name']}' already exists.")
                    return

            self.inventory_data.append(item_data)
            if self.save_inventory_data():
                self.populate_table()
                QMessageBox.information(self, "Success", "Item added successfully!")

    def edit_item(self):
        """Edit the selected item"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an item to edit.")
            return

        if current_row >= len(self.inventory_data):
            QMessageBox.warning(self, "Error", "Invalid item selection.")
            return

        item_data = self.inventory_data[current_row]
        existing_categories = self.get_all_categories()
        dialog = AddItemDialog(self, edit_mode=True, item_data=item_data, existing_categories=existing_categories)

        if dialog.exec_() == QDialog.Accepted:
            if dialog.validate_data():
                updated_data = dialog.get_item_data()

                # Check for duplicate names (excluding current item)
                for i, existing_item in enumerate(self.inventory_data):
                    if i != current_row and existing_item['name'].lower() == updated_data['name'].lower():
                        QMessageBox.warning(self, "Duplicate Item",
                                          f"An item with the name '{updated_data['name']}' already exists.")
                        return

                self.inventory_data[current_row] = updated_data
                if self.save_inventory_data():
                    self.populate_table()
                    QMessageBox.information(self, "Success", "Item updated successfully!")

    def delete_item(self):
        """Delete the selected item"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")
            return

        if current_row >= len(self.inventory_data):
            QMessageBox.warning(self, "Error", "Invalid item selection.")
            return

        item_name = self.inventory_data[current_row].get('name', 'Unknown Item')

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{item_name}' from inventory?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.inventory_data[current_row]
            if self.save_inventory_data():
                self.populate_table()
                QMessageBox.information(self, "Success", "Item deleted successfully!")

    def print_receipt(self):
        """Print receipt using the new cart-based system"""
        if not self.inventory_data:
            QMessageBox.warning(self, "No Items", "No inventory items available to create a receipt.")
            return

        if PRINT_RECEIPT_AVAILABLE:
            try:
                # Use the integrated print receipt functionality
                is_receipt_successful = show_print_receipt_dialog(self, self.cart_items)

               # If receipt was successfully printed, update inventory quantities
                if is_receipt_successful == True:
                    # Update inventory data by reducing quantities
                    for cart_item in self.cart_items:
                        for inventory_item in self.inventory_data:
                            if inventory_item['name'] == cart_item['name']:
                                # Reduce the quantity in inventory
                                inventory_item['quantity'] -= cart_item['quantity']
                                # Ensure quantity doesn't go below 0
                                if inventory_item['quantity'] < 0:
                                    inventory_item['quantity'] = 0
                                break

                    # Clear the cart after successful transaction
                    self.cart_items.clear()


                # Save inventory data after printing receipt (in case of changes)
                self.save_inventory_data()
                self.populate_table()
            except Exception as e:
                QMessageBox.critical(self, "Print Error",
                                   f"An error occurred while trying to print receipt:\n{str(e)}\n\n"
                                   "Please check if print_receipt.py is properly configured.")
        else:
            # Fallback message when print_receipt module is not available
            QMessageBox.information(self, "Print Receipt",
                                  "Print receipt functionality requires the print_receipt.py module.\n\n"
                                  "Features available with print_receipt.py:\n"
                                  "• Create shopping cart from inventory\n"
                                  "• Generate professional receipts\n"
                                  "• Save as PDF or print to thermal/regular printers\n"
                                  "• Automatic receipt numbering\n"
                                  "• Payment tracking with change calculation\n\n"
                                  "Please ensure print_receipt.py is in the same directory.")

    def refresh_data(self):
        """Refresh the inventory data"""
        self.load_inventory_data()
        self.populate_table()
        QMessageBox.information(self, "Success", "Data refreshed successfully!")

    def export_to_excel(self):
        """Export inventory data to Excel file"""
        if not self.inventory_data:
            QMessageBox.warning(self, "No Data", "No inventory data to export.")
            return

        try:
            # Prepare data for export
            export_data = []
            for item in self.inventory_data:
                export_data.append({
                    'Item Name': item.get('name', ''),
                    'Categories': ', '.join(item.get('categories', [])),
                    'Quantity': item.get('quantity', 0),
                    'Unit Price (Rs)': item.get('price', 0.0),
                    'Total Value (Rs)': item.get('quantity', 0) * item.get('price', 0.0)
                })

            # Create DataFrame
            df = pd.DataFrame(export_data)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_{self.shop_folder}_{timestamp}.xlsx"
            filepath = os.path.join(self.shop_path, filename)

            # Export to Excel
            df.to_excel(filepath, index=False, sheet_name='Inventory')

            QMessageBox.information(self, "Export Successful",
                                f"Inventory data exported successfully to:\n{filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")

    def add_to_cart(self, row):
        """Add item to cart"""
        if row >= len(self.inventory_data):
            return

        item = self.inventory_data[row]
        qty_widget = self.table.cellWidget(row, 4)
        selected_qty = qty_widget.value()

        if selected_qty <= 0:
            QMessageBox.warning(self, "Invalid Quantity", "Please select a quantity greater than 0.")
            return

        if selected_qty > item.get('quantity', 0):
            QMessageBox.warning(self, "Insufficient Stock",
                            f"Only {item.get('quantity', 0)} items available in stock.")
            return

        # Check if item already in cart
        for cart_item in self.cart_items:
            if cart_item['name'] == item['name']:
                cart_item['quantity'] += selected_qty
                QMessageBox.information(self, "Updated Cart",
                                    f"Updated quantity for '{item['name']}' in cart.")
                qty_widget.setValue(0)
                total_in_cart = sum(ci['quantity'] for ci in self.cart_items if ci['name'] == item['name'])
                remaining_qty = item['quantity'] - total_in_cart
                qty_widget.setMaximum(remaining_qty)
                return

        # Add new item to cart
        cart_item = {
            'name': item['name'],
            'quantity': selected_qty,
            'unit_price': item['price'],
            'total_price': selected_qty * item['price'],
        }
        self.cart_items.append(cart_item)

        QMessageBox.information(self, "Added to Cart",
                            f"Added {selected_qty} x '{item['name']}' to cart.")
        qty_widget.setValue(0)
        total_in_cart = sum(ci['quantity'] for ci in self.cart_items if ci['name'] == item['name'])
        remaining_qty = item['quantity'] - total_in_cart
        qty_widget.setMaximum(remaining_qty)

    def show_cart(self):
        """Show the cart dialog"""
        if not self.cart_items:
            QMessageBox.information(self, "Cart Empty", "Your cart is empty.")
            return

        cart_dialog = CartDialog(self.cart_items)
        cart_dialog.setWindowTitle("Your Shopping Cart")
        cart_dialog.exec_()

    def closeEvent(self, event):
        if self.previous_window:
            self.previous_window.show()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)

    # For testing purposes, you can specify a shop folder here
    # In actual implementation, this would be passed from the shop selection window
    shop_folder = "test_shop"  # Replace with actual shop folder

    window = InventoryManager(shop_folder)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()