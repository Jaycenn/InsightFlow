# Data import

Accepted extensions are `.csv` and `.xlsx`; the default upload limit is 5 MB (`MAX_UPLOAD_MB`). The API strips path components from filenames, bounds file bytes, parses the content, and stores only a valid, nonempty dataset. CSV is read as UTF-8 with optional BOM; XLSX uses `openpyxl`. File content is retained in PostgreSQL for repeat preview and validation.

Upload returns dataset metadata. Preview returns column names, eight sample rows, total rows, and best-effort suggested mappings. The UI lets users map each canonical field to a distinct source column. Required canonical fields are `order_id`, `date`, `product`, `quantity`, and `unit_price`; `category`, `cost`, and `customer` are optional.

Validation checks required mappings/values, unknown or duplicate source columns, ISO date syntax, finite nonnegative numeric values, positive quantities, empty rows, duplicate transaction rows within a file, and malformed file structure. An issue includes row, field, and a readable message. The API rejects imports with issues and returns details. A successful import creates/reuses products and customers and writes all sales in one database transaction. Reimporting the same dataset is blocked. Failed imports roll back, leaving the uploaded dataset available for mapping corrections.

Try `sample-data/small_sales.csv` for a valid import, `invalid_sales.csv` for row errors, and `sales_without_cost.csv` for unavailable profit metrics. The expected header mapping is Transaction Number → `order_id`, Purchase Date → `date`, Item Name → `product`, Product Category → `category`, Qty → `quantity`, Selling Price → `unit_price`, Unit Cost → `cost`, Buyer → `customer`.
