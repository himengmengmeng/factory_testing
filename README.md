<p align="right">
  <strong>English</strong> | <a href="README_zh.md">中文</a>
</p>

# Factory Testing Tool — Client End

A Django-based web client for the Instavision ODM factory testing platform. It provides a dark-themed UI for managing seller accounts, viewing product variants, and binding/updating floating Device IDs (DIDs) to product variants via the Instavision backend API.

---

## Features

### Authentication
- Seller login with email/password via JWT tokens
- Automatic token refresh with session lifecycle management
- Environment switching (Production / Staging)

### Sellers & Products Dashboard
- View primary seller's product variants (name, variant ID, OEM model ID, OEM model name)
- View all sub-sellers and their product variants
- **Unified search** across all sellers by variant name, variant ID, model name, or model ID
- One-click copy for variant name, variant ID, model name, and model ID
- Long text truncated with ellipsis; hover for full content

### DID Binding Operations
- **Single DID**: Query a DID's current status, then auto-detect and perform assign or update
- **Batch CSV**: Upload a CSV file (`Device Id`, `Access Key`) to process multiple DIDs
  - Real-time progress bar and operation log
  - Pause / Resume controls
  - Retry mechanism for failed items
  - Export outcome as CSV
- Supports both primary seller and sub-seller operations
- Navigation guard warns before leaving during an active batch

### UI / UX
- Dark theme with frosted glass sidebar and top navigation
- Tailwind CSS via CDN
- Searchable variant picker
- Responsive layout

---

## Project Structure

```
factory_testing/
├── manage.py
├── requirements.txt
├── root_directory/            # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── token_based_factory_tool/  # Main app
    ├── views.py               # Backend logic & API proxy
    ├── urls.py                # URL routing
    └── templates/token_based_factory_tool/
        ├── base.html          # Base template (Tailwind config, global styles)
        ├── _sidebar.html      # Sidebar navigation partial
        ├── _topbar.html       # Top navigation bar partial
        ├── login.html         # Login page
        ├── dashboard.html     # Sellers & Products page
        └── operations.html    # DID binding operations page
```

## Quick Start

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install django requests PyJWT

# 3. Run migrations (session table)
python manage.py migrate

# 4. Start dev server
python manage.py runserver 9000
```

Open http://localhost:9000/factory-tool/login/ and sign in with your seller account.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/factory-tool/login/` | Login page |
| GET | `/factory-tool/logout/` | Logout and clear session |
| GET | `/factory-tool/dashboard/` | Sellers & Products page |
| GET | `/factory-tool/operations/` | DID operations page |
| GET | `/factory-tool/api/variants/` | Fetch primary seller variants |
| GET | `/factory-tool/api/sub-sellers/` | Fetch sub-sellers list |
| GET | `/factory-tool/api/sub-sellers/<id>/variants/` | Fetch sub-seller variants |
| GET | `/factory-tool/api/query-did/?device_id=<did>` | Query DID status |
| POST | `/factory-tool/api/bind-did/` | Assign or update a single DID |
| POST | `/factory-tool/api/batch-bind/` | Server-side batch processing |

## CSV Format

```csv
Device Id,Access Key
ABC123,key123
DEF456,key456
```
