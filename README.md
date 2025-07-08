#  WhatsApp Invoice PDF Downloader Automation

This Python automation script uses **Selenium WebDriver** to interact with **Treebo Club Support's** WhatsApp bot, send a list of booking IDs, and automatically download invoice PDFs for each one.

---

##  Features

-  Automated login and session persistence for WhatsApp Web
-  Finds and opens chat with Treebo bot via name or number
-  Sends messages step-by-step to request invoices
-  Detects and downloads PDF invoices automatically
-  Renames downloaded files using the booking ID
-  Logs failed bookings in `failed_bookings.txt`

