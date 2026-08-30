TOOL_SPECS: list[dict] = [
    {
        "name": "get_user",
        "description": "Retrieves user profile information: wallet balance, saved payment methods, age verification status, address, and district.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "get_cart",
        "description": "Retrieves the user's active shopping cart (including restaurant ID and items).",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "search_restaurants",
        "description": "Searches for restaurants. Use 'q' for free-text search (name/menu). If 'near_district' is provided, filters for restaurants that deliver to that specific district.",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Free-text search term (optional)"},
                "cuisine": {"type": "string", "description": "Cuisine type (optional, e.g., Italian, Turkish)"},
                "near_district": {"type": "string", "description": "Deliverable district filter (optional)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_menu",
        "description": "Retrieves the menu for a specific restaurant, including items, prices, availability, and age restrictions.",
        "input_schema": {
            "type": "object",
            "properties": {"restaurant_id": {"type": "string"}},
            "required": ["restaurant_id"],
        },
    },
    {
        "name": "quote_checkout",
        "description": "Calculates pricing details for an order (subtotal, delivery fee, total, minimum order check). This is the SINGLE source of truth for pricing calculations -- always call this whenever presenting a cart or order summary; never calculate it yourself.",
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "qty": {"type": "integer"},
                        },
                        "required": ["item_id", "qty"],
                    },
                },
            },
            "required": ["restaurant_id", "items"],
        },
    },
    {
        "name": "list_orders",
        "description": "Lists the user's past and active orders.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Searches policies, FAQs, how-to, and support documents. MUST be called for informational queries regarding pricing policies, cancellation rules, or age restrictions -- never guess or answer from memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "description": "Default is 5"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "place_order",
        "description": "SENSITIVE. Places an order. If confirm_token is omitted, it performs NO mutations, returning only a confirmation prompt (confirm_token and summary) -- place this into a confirmation_prompt block and ask the user for approval. When the user confirms, call the EXACT same tool again passing the confirm_token received in the prompt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "restaurant_id": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "qty": {"type": "integer"},
                        },
                        "required": ["item_id", "qty"],
                    },
                },
                "confirm_token": {"type": "string", "description": "Provide only during the confirmation turn"},
            },
            "required": ["user_id", "restaurant_id", "items"],
        },
    },
    {
        "name": "cancel_order",
        "description": "SENSITIVE. Cancels an order. Follows the same two-step confirmation rule as place_order: if confirm_token is missing, request confirmation without executing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "order_id": {"type": "string"},
                "confirm_token": {"type": "string"},
            },
            "required": ["user_id", "order_id"],
        },
    },
    {
        "name": "add_tip",
        "description": "SENSITIVE. Adds a tip to an order. Tips are cumulative -- a second call does not overwrite the previous one, it counts as an additional tip. The two-step confirmation rule applies here as well.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "order_id": {"type": "string"},
                "amount_try": {"type": "number"},
                "confirm_token": {"type": "string"},
            },
            "required": ["user_id", "order_id", "amount_try"],
        },
    },
]