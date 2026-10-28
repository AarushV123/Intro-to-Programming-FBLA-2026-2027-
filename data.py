"""
data.py - all the vendors and products live here.

Keeping the data in its own file means app.py only has logic in it.
To add a product, copy one line from the list below and change the values.

Prices are stored in CENTS (an integer) so we never get rounding
problems like 0.1 + 0.2 = 0.30000000000000004.
"""

# The allergens a shopper can pick on the "My Allergies" page.
ALLERGENS = [
    ("nuts", "Tree nuts / peanuts"),
    ("dairy", "Dairy"),
    ("gluten", "Gluten (wheat)"),
    ("eggs", "Eggs"),
    ("sesame", "Sesame"),
]

# The diet filters shown on the shop page: (tag, label)
DIET_TAGS = [
    ("gluten_free", "Gluten-free"),
    ("plant_based", "Plant-based"),
    ("whole_grain", "Whole grain / sourdough"),
    ("nut_free", "Nut-free"),
    ("dairy_free", "Dairy-free"),
]

# Each vendor: id -> name, what they sell
VENDORS = {
    "sugar-maple": {"name": "Singh Sugar Maple Farm", "category": "Produce / Farm"},
    "fairy-greens": {"name": "Fairy Greens", "category": "Botanicals & Body Care"},
    "enchanted-flower": {"name": "Enchanted Flower Farm", "category": "Cut Flowers"},
    "north-acres": {"name": "North Acres Farm", "category": "Pastured Meats"},
    "dear-globe": {"name": "Dear Globe Coffee", "category": "Coffee & Drinks"},
    "rooted": {"name": "Rooted", "category": "Vegan / Gluten-Free"},
    "pierogi": {"name": "Pierogi & Dough", "category": "Prepared Foods"},
    "cane": {"name": "Cane Collective", "category": "Mixology / Beverages"},
    "empanadas": {"name": "Tasty Empanadas", "category": "Hot Prepared Food"},
    "crepe": {"name": "Crepe Shoppe Cafe", "category": "Hot Prepared Food"},
    "bitty-bread": {"name": "Bitty Bread Bakers", "category": "Sourdough Bakery"},
    "great-harvest": {"name": "Great Harvest Bread", "category": "Bakery"},
}


def make(id, vendor, name, price, unit, tax, **extra):
    """Build one product dictionary. Anything not given gets a safe default."""
    item = {
        "id": id,
        "vendor": vendor,
        "name": name,
        "price": price,          # cents per unit
        "unit": unit,            # "each", "lb", "stem"
        "tax": tax,              # "grocery" (0%), "prepared" (6%) or "general" (6%)
        "tags": [],              # diet tags (gluten_free, plant_based, whole_grain)
        "contains": [],          # allergens that are IN the food
        "may_contain": [],       # allergens from shared equipment (cross-contact)
        "cold": 0,               # cooler-locker units this item needs
        "hot": False,            # hot food that should not sit out
        "stock": 20,             # how many the vendor can supply per market day
        "per_slot": None,        # max of this item in one 15-minute window
        "bulk": None,            # (quantity, cheaper price) for bulk pricing
        "warning": "",           # safety message shown before adding
        "age21": False,          # needs ID check at pickup
        "choices": [],           # options like grind size
        "choice_label": "",
        "shelf_days": None,      # days it stays fresh after Friday harvest
    }
    item.update(extra)
    return item


_list = [
    # ---- Singh Sugar Maple Farm: bulk weight pricing + heat warning ----
    make("apples", "sugar-maple", "Honeycrisp Apples", 450, "lb", "grocery",
         tags=["gluten_free", "plant_based"], stock=60, bulk=(5, 400)),
    make("peaches", "sugar-maple", "Yellow Peaches", 500, "lb", "grocery",
         tags=["gluten_free", "plant_based"], stock=40, bulk=(5, 450)),
    make("ghost-peppers", "sugar-maple", "Ghost Peppers (6 pack)", 600, "each", "grocery",
         tags=["gluten_free", "plant_based"], stock=10,
         warning="HEAT WARNING: ghost peppers are around 1,000,000 Scoville units. "
                 "Wear gloves when cutting them and keep them away from kids and pets."),
    make("maple-syrup", "sugar-maple", "Maple Syrup (12 oz)", 1400, "each", "grocery",
         tags=["gluten_free", "plant_based"], stock=12),

    # ---- Fairy Greens: shelf-life tracker ----
    make("microgreens", "fairy-greens", "Microgreens Mix", 400, "each", "grocery",
         tags=["gluten_free", "plant_based"], cold=1, stock=25, shelf_days=5),
    make("sunflower-shoots", "fairy-greens", "Sunflower Shoots", 450, "each", "grocery",
         tags=["gluten_free", "plant_based"], cold=1, stock=15, shelf_days=5),
    make("lavender-soap", "fairy-greens", "Lavender Soap Bar", 800, "each", "general", stock=20),

    # ---- Enchanted Flower Farm: stem-count bundles ----
    make("bouquet", "enchanted-flower", "Seasonal Bouquet", 2200, "each", "general",
         stock=10, shelf_days=7),
    make("diy-stems", "enchanted-flower", "DIY Flower Stems", 150, "stem", "general",
         stock=120, bulk=(12, 120), shelf_days=7),

    # ---- North Acres Farm: cold-chain meats ----
    make("pork-chops", "north-acres", "Pastured Pork Chops (1 lb)", 1100, "each", "grocery",
         tags=["gluten_free"], cold=2, stock=15),
    make("ground-beef", "north-acres", "Grass-fed Ground Beef (1 lb)", 900, "each", "grocery",
         tags=["gluten_free"], cold=2, stock=20),
    make("lamb-chops", "north-acres", "Lamb Shoulder Chops (1 lb)", 1600, "each", "grocery",
         tags=["gluten_free"], cold=2, stock=8),
    make("whole-chicken", "north-acres", "Whole Chicken (about 4 lb)", 2400, "each", "grocery",
         tags=["gluten_free"], cold=3, stock=10),

    # ---- Dear Globe Coffee: grind size and temperature choices ----
    make("coffee-beans", "dear-globe", "Roasted Coffee Beans (12 oz)", 1600, "each", "grocery",
         tags=["gluten_free", "plant_based"], stock=25,
         choices=["Whole bean", "Coarse", "Medium", "Fine"], choice_label="Grind size"),
    make("drip-coffee", "dear-globe", "Fresh Brewed Coffee", 350, "each", "prepared",
         tags=["gluten_free", "plant_based"], stock=60,
         choices=["Hot", "Iced"], choice_label="Temperature"),
    make("latte", "dear-globe", "Latte", 550, "each", "prepared",
         tags=["gluten_free"], contains=["dairy"], may_contain=["nuts"], stock=40,
         choices=["Hot", "Iced"], choice_label="Temperature"),

    # ---- Rooted: strictly verified dietary tags ----
    make("kimchi", "rooted", "Kimchi Jar", 900, "each", "grocery",
         tags=["gluten_free", "plant_based"], cold=1, stock=20),
    make("hummus", "rooted", "Classic Hummus", 700, "each", "grocery",
         tags=["gluten_free", "plant_based"], contains=["sesame"], cold=1, stock=20),
    make("cashew-spread", "rooted", "Cashew Cheese Spread", 900, "each", "grocery",
         tags=["gluten_free", "plant_based"], contains=["nuts"], cold=1, stock=12),
    make("juice", "rooted", "Cold-Pressed Juice", 800, "each", "prepared",
         tags=["gluten_free", "plant_based"], cold=1, stock=30),

    # ---- Pierogi & Dough: batch limits per pickup window ----
    make("pierogi-potato", "pierogi", "Frozen Potato & Cheese Pierogi (dozen)", 1400, "each", "grocery",
         contains=["gluten", "dairy", "eggs"], cold=2, stock=20, per_slot=10),
    make("pierogi-cherry", "pierogi", "Frozen Sweet Cherry Pierogi (dozen)", 1500, "each", "grocery",
         contains=["gluten", "eggs"], may_contain=["dairy"], cold=2, stock=15, per_slot=10),
    make("pierogi-kraut", "pierogi", "Frozen Sauerkraut & Mushroom Pierogi (dozen)", 1400, "each", "grocery",
         contains=["gluten"], may_contain=["dairy", "eggs"], cold=2, stock=15, per_slot=10),
    make("pierogi-hot", "pierogi", "Hot Pierogi Box (6)", 1100, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], hot=True, stock=40, per_slot=8),

    # ---- Cane Collective: age-verification gate ----
    make("mixer-ginger", "cane", "Mocktail Mixer: Ginger Lime", 1200, "each", "general",
         tags=["gluten_free", "plant_based"], age21=True, stock=15),
    make("mixer-old-fashioned", "cane", "Craft Mixer: Smoked Old Fashioned", 1400, "each", "general",
         tags=["gluten_free", "plant_based"], age21=True, stock=15),
    make("mixer-spicy", "cane", "Craft Mixer: Spicy Margarita", 1400, "each", "general",
         tags=["gluten_free", "plant_based"], age21=True, stock=15),

    # ---- Tasty Empanadas: hot food, limited per window ----
    make("empanada-beef", "empanadas", "Beef Empanada", 450, "each", "prepared",
         contains=["gluten", "eggs"], hot=True, stock=60, per_slot=14),
    make("empanada-spinach", "empanadas", "Spinach & Cheese Empanada", 450, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], hot=True, stock=50, per_slot=14),
    make("empanada-bean", "empanadas", "Black Bean Empanada", 450, "each", "prepared",
         contains=["gluten"], may_contain=["dairy", "eggs"], hot=True, stock=40, per_slot=14),

    # ---- Crepe Shoppe Cafe ----
    make("crepe-nutella", "crepe", "Hazelnut Chocolate & Strawberry Crepe", 800, "each", "prepared",
         contains=["gluten", "dairy", "eggs", "nuts"], hot=True, stock=30, per_slot=10),
    make("crepe-ham", "crepe", "Ham & Cheese Crepe", 900, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], hot=True, stock=30, per_slot=10),
    make("crepe-lemon", "crepe", "Lemon Sugar Crepe", 700, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], may_contain=["nuts"], hot=True, stock=30, per_slot=10),

    # ---- Bitty Bread Bakers: sourdough ----
    make("sourdough-wheat", "bitty-bread", "Whole Wheat Sourdough Loaf", 900, "each", "grocery",
         tags=["whole_grain", "plant_based"], contains=["gluten"], stock=20),
    make("sourdough-cinnamon", "bitty-bread", "Cinnamon Raisin Sourdough", 800, "each", "grocery",
         tags=["plant_based"], contains=["gluten"], may_contain=["nuts"], stock=15),
    make("sourdough-rye", "bitty-bread", "Seeded Rye Sourdough", 900, "each", "grocery",
         tags=["whole_grain", "plant_based"], contains=["gluten", "sesame"], stock=12),

    # ---- Great Harvest Bread ----
    make("honey-wheat", "great-harvest", "Honey Whole Wheat Loaf", 850, "each", "grocery",
         tags=["whole_grain"], contains=["gluten"], may_contain=["nuts"], stock=20),
    make("cranberry-walnut", "great-harvest", "Cranberry Walnut Loaf", 950, "each", "grocery",
         tags=["whole_grain"], contains=["gluten", "nuts"], stock=12),
    make("scone", "great-harvest", "Pumpkin Spice Scone", 450, "each", "grocery",
         contains=["gluten", "dairy", "eggs"], may_contain=["nuts"], stock=24),
]

# The nut-free / dairy-free tags are worked out automatically from the allergen
# lists, so they can never disagree with the "contains" information.
for _p in _list:
    if "nuts" not in _p["contains"] and "nuts" not in _p["may_contain"]:
        _p["tags"].append("nut_free")
    if "dairy" not in _p["contains"] and "dairy" not in _p["may_contain"]:
        _p["tags"].append("dairy_free")

# id -> product, so we can look things up quickly
PRODUCTS = {p["id"]: p for p in _list}
