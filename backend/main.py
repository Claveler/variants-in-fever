from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Fever Ticket Selector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TicketType(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    min_quantity: int = 0
    max_quantity: int = 10


class Variant(BaseModel):
    id: str
    name: str
    price_modifier: float = 0.0  # Additional cost for this variant (can be negative for discounts)
    available: bool = True


class AddOn(BaseModel):
    id: str
    name: str
    description: str
    price: float
    image_url: str
    requires_ticket_type: Optional[str] = None
    min_required_tickets: int = 0
    variants: Optional[list[Variant]] = None  # If present, user must select a variant


class Event(BaseModel):
    id: str
    name: str
    venue: str
    image_url: str
    ticket_types: list[TicketType]
    add_ons: list[AddOn]


# Sample data based on ARTE MUSEUM event
EVENTS = {
    "arte-museum-ny": Event(
        id="arte-museum-ny",
        name="ARTE MUSEUM: An Immersive Media Art Exhibition",
        venue="Arte Museum New York",
        image_url="https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=800",
        ticket_types=[
            TicketType(
                id="adult",
                name="Adult (13+)",
                description="Entry ticket for guests aged 13 and above. Includes access to ARTE MUSEUM and ARTE CAFE with one complimentary drink.",
                price=20.40,
                min_quantity=0,
                max_quantity=10,
            ),
            TicketType(
                id="child",
                name="Child (3-12)",
                description="Entry ticket for children aged 3-12. Children under 3 enter free. Includes access to ARTE MUSEUM and ARTE CAFE.",
                price=20.40,
                min_quantity=0,
                max_quantity=10,
            ),
        ],
        add_ons=[
            AddOn(
                id="parking",
                name="Parking",
                description="Save time and stress by securing a parking spot at or near the event venue. This is a long description that shows how the text gets truncated when it exceeds a certain length to maintain a clean card layout.",
                price=20.00,
                image_url="https://images.unsplash.com/photo-1545558014-8692077e9b5c?w=400",
                requires_ticket_type="adult",
                min_required_tickets=1,
                variants=None,
            ),
            AddOn(
                id="tshirt",
                name="Event T-Shirt",
                description="Take home a piece of the experience with our exclusive ARTE MUSEUM t-shirt. Premium cotton, available in multiple sizes.",
                price=35.00,
                image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
                requires_ticket_type=None,
                min_required_tickets=0,
                variants=[
                    Variant(id="xs", name="XS", price_modifier=0.0),
                    Variant(id="s", name="S", price_modifier=0.0),
                    Variant(id="m", name="M", price_modifier=0.0),
                    Variant(id="l", name="L", price_modifier=0.0),
                    Variant(id="xl", name="XL", price_modifier=0.0),
                    Variant(id="xxl", name="XXL", price_modifier=5.00),
                ],
            ),
            AddOn(
                id="photobook",
                name="Photo Book",
                description="A beautiful hardcover photo book featuring the best artworks from the exhibition. Choose your preferred edition.",
                price=45.00,
                image_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
                requires_ticket_type=None,
                min_required_tickets=0,
                variants=[
                    Variant(id="standard", name="Standard Edition", price_modifier=0.0),
                    Variant(id="deluxe", name="Deluxe Edition", price_modifier=25.00),
                    Variant(id="collectors", name="Collector's Edition", price_modifier=55.00),
                ],
            ),
        ],
    )
}


@app.get("/")
def read_root():
    return {"message": "Fever Ticket Selector API", "version": "1.0.0"}


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    if event_id in EVENTS:
        return EVENTS[event_id]
    return {"error": "Event not found"}, 404


@app.get("/api/events/{event_id}/tickets")
def get_tickets(event_id: str):
    if event_id in EVENTS:
        return {"tickets": EVENTS[event_id].ticket_types}
    return {"error": "Event not found"}, 404


@app.get("/api/events/{event_id}/addons")
def get_addons(event_id: str):
    if event_id in EVENTS:
        return {"addons": EVENTS[event_id].add_ons}
    return {"error": "Event not found"}, 404


class CartAddonItem(BaseModel):
    quantity: int
    variant_id: Optional[str] = None


class CartValidation(BaseModel):
    tickets: dict[str, int]  # ticket_id -> quantity
    addons: dict[str, CartAddonItem]  # addon_id -> {quantity, variant_id}


@app.post("/api/events/{event_id}/validate")
def validate_cart(event_id: str, cart: CartValidation):
    if event_id not in EVENTS:
        return {"error": "Event not found"}, 404
    
    event = EVENTS[event_id]
    errors = []
    warnings = []
    
    # Check add-on requirements
    for addon in event.add_ons:
        addon_item = cart.addons.get(addon.id)
        addon_qty = addon_item.quantity if addon_item else 0
        
        if addon_qty > 0:
            # Check ticket requirement
            if addon.requires_ticket_type:
                required_ticket_qty = cart.tickets.get(addon.requires_ticket_type, 0)
                if required_ticket_qty < addon.min_required_tickets:
                    errors.append({
                        "addon_id": addon.id,
                        "message": f"To purchase the {addon.name} add-on, you need to select at least {addon.min_required_tickets} {addon.requires_ticket_type.title()} ticket. Please adjust your selection to proceed."
                    })
            
            # Check variant requirement
            if addon.variants and (not addon_item or not addon_item.variant_id):
                errors.append({
                    "addon_id": addon.id,
                    "message": f"Please select a variant for {addon.name}."
                })
    
    # Calculate total
    total = 0.0
    for ticket in event.ticket_types:
        qty = cart.tickets.get(ticket.id, 0)
        total += ticket.price * qty
    
    for addon in event.add_ons:
        addon_item = cart.addons.get(addon.id)
        if addon_item and addon_item.quantity > 0:
            addon_price = addon.price
            # Add variant price modifier
            if addon.variants and addon_item.variant_id:
                variant = next((v for v in addon.variants if v.id == addon_item.variant_id), None)
                if variant:
                    addon_price += variant.price_modifier
            total += addon_price * addon_item.quantity
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total": round(total, 2)
    }
