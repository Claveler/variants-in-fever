# Variants in Fever

A ticket selector component inspired by Fever's event ticketing interface, featuring ticket types with quantity controls and add-ons with images and **variant selection** (e.g., sizes for merchandise).

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: Astro
- **Font**: Montserrat

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

- **Ticket Selection**: Select quantities for different ticket types (Adult, Child)
- **Add-ons with Images**: Visual add-on cards with thumbnails
- **Validation**: Real-time validation for add-ons that require specific ticket types
- **Responsive Design**: Works on mobile and desktop
- **Price Calculation**: Live total calculation

## API Endpoints

- `GET /api/events/{event_id}` - Get event details with tickets and add-ons
- `GET /api/events/{event_id}/tickets` - Get ticket types for an event
- `GET /api/events/{event_id}/addons` - Get add-ons for an event
- `POST /api/events/{event_id}/validate` - Validate cart and get total
