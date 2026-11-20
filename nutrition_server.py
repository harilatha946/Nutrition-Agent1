from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Nutrition Server", log_level="ERROR")

nutrition_data = {
    "chicken breast": {"calories": 165, "protein": 31},
    "banana": {"calories": 89, "protein": 1.1},
    "egg": {"calories": 155, "protein": 13},
    "oats": {"calories": 389, "protein": 16.9},
}

@mcp.tool()
def get_calories(food_item: str) -> str:
    """Get calorie information per 100g of a food item."""
    food = food_item.lower().strip()
    if food in nutrition_data:
        return f"{nutrition_data[food]['calories']} kcal"
    return f"No data available for {food_item}"

@mcp.tool()
def get_protein(food_item: str) -> str:
    """Get protein information per 100g of a food item."""
    food = food_item.lower().strip()
    if food in nutrition_data:
        return f"{nutrition_data[food]['protein']}g protein"
    return f"No data available for {food_item}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
