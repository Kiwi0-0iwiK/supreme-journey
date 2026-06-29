import json
from fractions import Fraction
from pathlib import Path

RECIPES_FILE = Path(__file__).parent / "recipes.json"

def load_recipes():
    with open(RECIPES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["recipes"]

def fmt_amount(n):
    """Format a possibly-huge number. Python ints have no overflow limit."""
    if isinstance(n, Fraction):
        if n.denominator == 1:
            n = n.numerator
        else:
            return f"{float(n):.2f}"
    if n >= 1_000_000_000:
        return f"{n:,}  ({n / 1_000_000_000:.3f}B)"
    if n >= 1_000_000:
        return f"{n:,}  ({n / 1_000_000:.2f}M)"
    return f"{n:,}"

def expand(target_item, quantity, recipes, depth=0, visited=None):
    """
    Recursively expand a crafting chain.
    Returns (items_needed, fluids_needed) as dicts of {name: Fraction}.
    Uses Python's arbitrary-precision integers — no 2.1G overflow.
    """
    if visited is None:
        visited = set()

    quantity = Fraction(quantity)

    if target_item not in recipes:
        return {target_item: quantity}, {}

    if target_item in visited:
        print(f"{'  ' * depth}[WARNING] Circular dependency detected: {target_item}")
        return {target_item: quantity}, {}

    visited = visited | {target_item}
    recipe = recipes[target_item]
    recipe_output = Fraction(recipe["output"])
    multiplier = quantity / recipe_output

    total_items = {}
    total_fluids = {}

    indent = "  " * depth
    tier = recipe.get('eu_per_tick', '')
    label = f"{recipe['machine']} @ {tier}" if tier else recipe['machine']
    print(f"{indent}[{label}] {target_item} x{quantity}")

    for ingredient in recipe["items"]:
        needed = Fraction(ingredient["amount"]) * multiplier
        sub_items, sub_fluids = expand(ingredient["item"], needed, recipes, depth + 1, visited)
        for k, v in sub_items.items():
            total_items[k] = total_items.get(k, Fraction(0)) + v
        for k, v in sub_fluids.items():
            total_fluids[k] = total_fluids.get(k, Fraction(0)) + v

    for fluid in recipe["fluids"]:
        name = fluid["fluid"]
        mb = Fraction(fluid["mb"]) * multiplier
        total_fluids[name] = total_fluids.get(name, Fraction(0)) + mb

    return total_items, total_fluids

def calculate(target_item, quantity=1):
    recipes = load_recipes()

    if target_item not in recipes:
        available = "\n  ".join(recipes.keys())
        print(f"Unknown item: '{target_item}'\nAvailable items:\n  {available}")
        return

    print(f"\n{'='*60}")
    print(f"  Calculating: {target_item} x{quantity}")
    print(f"{'='*60}\n")
    print("[Crafting tree]")
    items, fluids = expand(target_item, quantity, recipes)

    print(f"\n{'='*60}")
    print("  RAW MATERIALS NEEDED (items)")
    print(f"{'='*60}")
    for name, amt in sorted(items.items()):
        print(f"  {name:<45} {fmt_amount(amt)}")

    print(f"\n{'='*60}")
    print("  RAW MATERIALS NEEDED (fluids, in mB)")
    print(f"{'='*60}")
    for name, amt in sorted(fluids.items()):
        print(f"  {name:<45} {fmt_amount(amt)} mB")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python calc.py <ItemName> [quantity]")
        print("\nAvailable items:")
        recipes = load_recipes()
        for name in recipes:
            print(f"  {name}")
        sys.exit(0)

    item = sys.argv[1]
    qty  = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    calculate(item, qty)
