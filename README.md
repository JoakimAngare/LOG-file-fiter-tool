# LOGfilter Tool

This is a simple tool for filtering `.LOG` files from Scania’s log archives. It extracts key information and highlights matches/mismatches related to CAN communication protocols.

---

## 📦 Requirements

- **Python 3**  
  [Download Python](https://www.python.org/downloads/) if it's not already installed.

---

## 🗂️ Setup Instructions

1. Copy the following files from the network location:
   ```
   X:\05_General\M\MLOG\6_Programs and Plug-ins\LOG file filter\
   ├── LOGfilter_enhanced.py
   ├── LOGfilter_wrapper.ps1
   └── log_filter_config.json
   ```

2. Paste the files into a folder on your local machine, for example:
   ```
   C:\Users\janjdr\Desktop\VDA grejer\Scripting\LOGfilter
   ```

3. Copy the `.zip` files containing the `.LOG` files you want to filter into this same folder.

---

## ▶️ How to Run

1. Open **PowerShell** in the folder where your script is located.
2. Run the script:
   ```powershell
   .\LOGfilter_wrapper.ps1
   ```
3. This will generate two result files:
   - `filtered_log_results.txt` (plain text)
   - `filtered_log_results.html` (clickable and highlighted view)

4. From the command window, press **`Y`** to open the HTML result automatically.

---

## 📌 Example Usage

If your script and log files are located here:
```
C:\Users\janjdr\Desktop\VDA grejer\Scripting\LOGfilter
```

And you’ve copied `.zip` log archives from “Ciri” into the same folder, simply run:
```powershell
.\LOGfilter_wrapper.ps1
```
