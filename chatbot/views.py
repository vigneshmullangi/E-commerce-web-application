import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import google.generativeai as genai

from .actions import get_total_products, search_products, add_to_cart, view_cart, place_order

genai.configure(api_key=settings.GEMINI_API_KEY)

AVAILABLE_FUNCTIONS = {
    "get_total_products": get_total_products,
    "search_products": search_products,
    "add_to_cart": add_to_cart,
    "view_cart": view_cart,
    "place_order": place_order,
}

tools = [
    {
        "function_declarations": [
            {
                "name": "get_total_products",
                "description": "Get the total number of products available in the store",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "search_products",
                "description": "Search for products by name or category, returns available units and prices",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Product name or keyword"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_to_cart",
                "description": "Add a product to the user's cart",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string"},
                        "unit_label": {"type": "string", "description": "e.g. '250 GMS', '1 KG' - optional, uses cheapest if not given"},
                        "quantity": {"type": "integer"}
                    },
                    "required": ["product_name", "quantity"]
                }
            },
            {
                "name": "view_cart",
                "description": "Show current items in the user's cart with total",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "place_order",
                "description": "Place an order using items currently in the cart and the logged-in customer's saved details",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
    }
]

model = genai.GenerativeModel(
    model_name="gemini-3.6-flash",
    tools=tools,
    system_instruction=(
        "You are a shopping assistant for Sri Lakshmi Ganapati Kirana & General store. "
        "Use the available tools to answer questions about products, manage the cart, and place orders. "
        "If a user tries to add to cart or place an order and gets a 'please log in' error, "
        "tell them to log in first, then try again. "
        "Always show the cart and confirm with the user before calling place_order."
    )
)


from google.api_core.exceptions import ResourceExhausted
@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    user_message = data.get("message", "")

    chat = model.start_chat()

    try:
        response = chat.send_message(user_message)
    except ResourceExhausted:
        return JsonResponse({
            "reply": "I'm getting a lot of questions right now and hit my daily limit. Please try again in a few minutes, or browse products directly on the page!",
            "action": None,
            "data": None
        })

    func_name = None
    result = None

    part = response.candidates[0].content.parts[0]

    has_function_call = False
    try:
        if part.function_call and part.function_call.name:
            has_function_call = True
    except (ValueError, AttributeError):
        has_function_call = False

    if has_function_call:
        func_call = part.function_call
        func_name = func_call.name
        args = dict(func_call.args)

        if func_name in ("add_to_cart", "view_cart", "place_order"):
            args["request"] = request

        try:
            result = AVAILABLE_FUNCTIONS[func_name](**args)
        except Exception as e:
            result = {"error": f"Something went wrong running {func_name}: {str(e)}"}

        try:
            response = chat.send_message(
                genai.protos.Content(
                    parts=[genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=func_name,
                            response={"result": result}
                        )
                    )]
                )
            )
            reply = response.text
        except ResourceExhausted:
            reply = "I ran your request, but hit my daily limit forming a reply. Here's the raw result: " + json.dumps(result)
        except ValueError:
            reply = "Done!" if result and result.get("success") else "I ran into an issue completing that."
    else:
        try:
            reply = response.text
        except ValueError:
            reply = "I'm not sure how to respond to that — could you rephrase?"

    return JsonResponse({
        "reply": reply,
        "action": func_name,
        "data": result
    })