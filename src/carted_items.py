from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QGroupBox, QHBoxLayout,
    QTextEdit, QPushButton, QMessageBox
)
import sys

class CartDialog(QDialog):
    """Dialog for showing only cart summary and clear cart button"""
    def __init__(self, cart_items, parent=None):
        super().__init__(parent)
        self.cart_items = cart_items if cart_items else []
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Cart Summary")
        self.resize(600, 400)
        layout = QVBoxLayout()

        # Cart Summary
        cart_group = QGroupBox("Cart Summary")
        cart_layout = QVBoxLayout()
        self.cart_text = QTextEdit()
        self.cart_text.setReadOnly(True)
        self.cart_text.setMaximumHeight(200)
        cart_layout.addWidget(self.cart_text)
        cart_group.setLayout(cart_layout)
        layout.addWidget(cart_group)

        # Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.update_cart_summary()

    def clear_cart(self):
        """Clear the cart"""
        if not self.cart_items:
            QMessageBox.information(self, "Cart Empty", "Cart is already empty.")
            return
        reply = QMessageBox.question(
            self, "Clear Cart", 
            "Are you sure you want to clear all items from the cart?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.cart_items = []
            self.update_cart_summary()
            QMessageBox.information(self, "Cart Cleared", "All items have been removed from the cart.")

    def update_cart_summary(self):
        """Update cart summary display"""
        if not self.cart_items:
            self.cart_text.setText("🛒 Cart is empty\n\nStart adding items to see your cart summary here.")
            return
        
        summary = "🛒 CART SUMMARY\n"
        summary += "=" * 60 + "\n"
        total_amount = 0
        total_items = 0
        for item in self.cart_items:
            item_total = item['total_price']
            total_amount += item_total
            total_items += item['quantity']
            summary += f"{item['quantity']:>2} x {item['name']:<25} "
            summary += f"@ Rs {item['unit_price']:>6.2f} = Rs {item_total:>8.2f}\n"
        summary += "=" * 60 + "\n"
        summary += f"{'Total Items:':<35} {total_items:>3}\n"
        summary += f"{'TOTAL AMOUNT:':<35} Rs {total_amount:>8.2f}\n"
        self.cart_text.setText(summary)

    def get_cart_data(self):
        """Get cart data for receipt printing"""
        total_amount = sum(item['total_price'] for item in self.cart_items)
        return {
            'items': self.cart_items,
            'total_amount': total_amount
        }


def main():
    app = QApplication(sys.argv)
        
    cart_items = [
        {'name': 'Item A', 'quantity': 2, 'unit_price': 50.00, 'total_price': 100.00},
        {'name': 'Item B', 'quantity': 1, 'unit_price': 30.00, 'total_price': 30.00}
    ]  # Example cart items, replace with actual data
        
    dialog = CartDialog(cart_items)
    if dialog.exec_() == QDialog.Accepted:
        print("Cart Data:", dialog.get_cart_data())
   
if __name__ == "__main__":
    main()
