# Billing-And-Inventory-System

A simple Inventory Management System built with Python. This application allows users to manage products, update stock, generate receipts, and more — all through a user-friendly interface.

## Features

- Add, update, and delete inventory items
- Track stock levels
- Generate and print receipts
- Store data using JSON
- Export data to `.XLSX` ( excel file)
- User-friendly GUI `PyQt5`
- Packaged as a standalone `.exe` using PyInstaller ( to be implemented )

## Project Structure
```
inventory_system/
├── src/                              # Source code and data
│   ├── main.py                       # Entry point for the app
│   ├── carted_items.py
│   ├── create_new_shop.py
│   ├── inventory_manager.py
│   ├── print_receipt.py
│   ├── data/                         # Data folder now inside src/
│   │   ├── inventory.json
│   │   ├── shop_info.json
│   │   ├── shop_name/
│   │   │   └── bills/
│   │   └── exported_files/           # .XLSX files / but you can save this on your choosen location as well
│   └── __pycache__/                  # Ignore
├── requirements.txt
└── README.md
```

## After Running Pyinstaller data location 
```
    C:\Users\<YourUsername>\AppData\Local\InventoryManager\data\
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MHassan05/Billing-And-Inventory-System.git
   cd Billing-And-Inventory-System
   ```

2. **Set up virtual environment**
  ```bash
python -m venv venv
source venv/bin/activate        # On Linux/macOS
venv\Scripts\activate           # On Windows
  ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
5. **Ready To Run**
   Finally, type `python3 main.py`.

## Printing Receipts

The system is compatible with standard receipt printers. Make sure your printer is configured correctly before use.

---

## License

This project is licensed under the MIT License.

---

## Contributing

Contributions are welcome! Feel free to **fork the repository** and submit a **pull request** with your changes.

---

## Contact

**Muhammad Hassan**  
📧 [mh873030@gmail.com]  
🔗 [My GitHub Profile](https://github.com/MHassan05)




   
