"""
data.py 
Thiis is all about the vendors info
"""

# These are some allergies we encorperated into this project, we could not get all because there are millions of possible allergies
ALLERGENS = [
    ("nuts", "Tree nuts / peanuts"),
    ("dairy", "Dairy"),
    ("gluten", "Gluten (wheat)"),
    ("eggs", "Eggs"),
    ("sesame", "Sesame"),
]

# Just like the alergies, we also put diet things so people can choose what restrictions they have
DIET_TAGS = [
    ("gluten_free", "Gluten-free"),
    ("plant_based", "Plant-based"),
    ("whole_grain", "Whole grain / sourdough"),
    ("nut_free", "Nut-free"),
    ("dairy_free", "Dairy-free"),
]

# This is all of the vendors and what each of them sell, this code alows the user to know each vendor,
# what they sell and things like that so the user can see everything on one page.
VENDORS = {
    "sugar-maple": {"name": "Singh Sugar Maple Farm", "category": "Produce / Farm"},
    "fairy-greens": {"name": "Fairy Greens", "category": "Botanicals & Body Care"},
    "enchanted-flower": {"name": "Enchanted Flower Farm", "category": "Cut Flowers"},
    "north-acres": {"name": "North Acres Farm", "category": "Pastured Meats"},
    "dear-globe": {"name": "Dear Globe Coffee", "category": "Coffee & Drinks"},
    "rooted": {"name": "Rooted", "category": "Vegan / Gluten-Free"},
    "pierogi": {"name": "Pierogi", "category": "Prepared Dough"},
    "cane": {"name": "Cane Collective", "category": "Mixology / Beverages"},
    "empanadas": {"name": "Tasty Empanadas", "category": "Prepared Empanadas"},
    "crepe": {"name": "Crepe Shoppe Cafe", "category": "Prepared Crepes"},
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
        "tax": tax,              # this is based on md tax"grocery" (0%), "prepared" (6%) or "general" (6%)
        "tags": [],              # these are teh possible diet/alergy tags... (gluten_free, plant_based, whole_grain)
        "contains": [],          # contains means all of the things that contain the specific thing like it could contain allergies or gluten, its like that type of stuff
        "may_contain": [],       # allergens from shared equipment meaning they touch each other so they can each have the allergy
        "cold": 0,               #
        "hot": False,            #
        "stock": 20,             # 
        "per_slot": None,        # max of this item in one 15-minute window
        "bulk": None,            # 
        "warning": "",           # the safety mesage shown before adding so the user knows about the warning
        "age21": False,          # needs ID check at pickup, some places have items that are not able to be sold to everyone
        "choices": [],           #
        "choice_label": "",
        "shelf_days": None,      # How many days it can stay after being bought
    }
    item.update(extra)
    return item


_list = [
    make("apples", "sugar-maple", "Honeycrisp Apples", 450, "lb", "grocery",
         tags=["gluten_free", "plant_based"], stock=60, bulk=(5, 400)),
    make("peaches", "sugar-maple", "Yellow Peaches", 500, "lb", "grocery",
         tags=["gluten_free", "plant_based"], stock=40, bulk=(5, 450)),
    make("ghost-peppers", "sugar-maple", "Ghost Peppers (6 pack)", 600, "each", "grocery",
         tags=["gluten_free", "plant_based"], stock=10,
         warning="HEAT WARNING: ghost peppers are around 1,000,000 Scoville units. "),
    make("maple-syrup", "sugar-maple", "Maple Syrup (12 oz)", 1400, "each", "grocery",
         tags=["gluten_free", "plant_based"], stock=12),



    make("microgreens", "fairy-greens", "Microgreens Mix", 400, "each", "grocery",
         tags=["gluten_free", "plant_based"], cold=1, stock=25, shelf_days=5),
    make("sunflower-shoots", "fairy-greens", "Sunflower Shoots", 450, "each", "grocery",
         tags=["gluten_free", "plant_based"], cold=1, stock=15, shelf_days=5),
    make("lavender-soap", "fairy-greens", "Lavender Soap", 800, "each", "general", stock=20),



    make("bouquet", "enchanted-flower", "Seasonal Bouquet", 2200, "each", "general",
         stock=10, shelf_days=7),
    make("diy-stems", "enchanted-flower", "DIY Flower Stems", 150, "stem", "general",
         stock=120, bulk=(12, 120), shelf_days=7),



    make("pork-chops", "north-acres", "Pastured Pork Chops (1 lb)", 1100, "each", "grocery",
         tags=["gluten_free"], cold=2, stock=15),
    make("ground-beef", "north-acres", "Grass-fed Ground Beef (1 lb)", 900, "each", "grocery",
         tags=["gluten_free"], cold=2, stock=20),
    make("lamb-chops", "north-acres", "Lamb Shoulder Chops (1 lb)", 1600, "each", "grocery",
         tags=["gluten_free"], cold=2, stock=8),
    make("whole-chicken", "north-acres", "Whole Chicken (about 4 lb)", 2400, "each", "grocery",
         tags=["gluten_free"], cold=3, stock=10),



    make("coffee-beans", "dear-globe", "Roasted Coffee Beans (12 oz)", 1600, "each", "grocery",
         tags=["gluten_free", "plant_based"], stock=25,
         choices=["Whole bean", "Coarse", "Medium", "Fine"], choice_label="Grind size"),
    make("drip-coffee", "dear-globe", "Fresh Brewed Coffee", 350, "each", "prepared",
         tags=["gluten_free", "plant_based"], stock=60,
         choices=["Hot", "Iced"], choice_label="Temperature"),
    make("latte", "dear-globe", "Latte", 550, "each", "prepared",
         tags=["gluten_free"], contains=["dairy"], may_contain=["nuts"], stock=40,
         choices=["Hot", "Iced"], choice_label="Temperature"),




    make("kimchi", "rooted", "Kimchi Jar", 900, "each", "grocery",
         tags=["gluten_free", "plant_based"], cold=1, stock=20),
    make("hummus", "rooted", "Classic Hummus", 700, "each", "grocery",
         tags=["gluten_free", "plant_based"], contains=["sesame"], cold=1, stock=20),
    make("cashew-spread", "rooted", "Cashew Cheese Spread", 900, "each", "grocery",
         tags=["gluten_free", "plant_based"], contains=["nuts"], cold=1, stock=12),
    make("juice", "rooted", "Cold-Pressed Juice", 800, "each", "prepared",
         tags=["gluten_free", "plant_based"], cold=1, stock=30),




    make("pierogi-potato", "pierogi", "Frozen Potato & Cheese Pierogi (dozen)", 1400, "each", "grocery",
         contains=["gluten", "dairy", "eggs"], cold=2, stock=20, per_slot=10),
    make("pierogi-cherry", "pierogi", "Frozen Sweet Cherry Pierogi (dozen)", 1500, "each", "grocery",
         contains=["gluten", "eggs"], may_contain=["dairy"], cold=2, stock=15, per_slot=10),
    make("pierogi-kraut", "pierogi", "Frozen Sauerkraut & Mushroom Pierogi (dozen)", 1400, "each", "grocery",
         contains=["gluten"], may_contain=["dairy", "eggs"], cold=2, stock=15, per_slot=10),
    make("pierogi-hot", "pierogi", "Hot Pierogi Box (6)", 1100, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], hot=True, stock=40, per_slot=8),





    make("mixer-ginger", "cane", "Mocktail Mixer: Ginger Lime", 1200, "each", "general",
         tags=["gluten_free", "plant_based"], stock=15),
    make("mixer-old-fashioned", "cane", "Craft Mixer: Smoked Old Fashioned", 1400, "each", "general",
         tags=["gluten_free", "plant_based"], stock=15),
    make("mixer-spicy", "cane", "Craft Mixer: Spicy Margarita", 1400, "each", "general",
         tags=["gluten_free", "plant_based"], stock=15),




    make("empanada-beef", "empanadas", "Beef Empanada", 450, "each", "prepared",
         contains=["gluten", "eggs"], hot=True, stock=60, per_slot=14),
    make("empanada-spinach", "empanadas", "Spinach & Cheese Empanada", 450, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], hot=True, stock=50, per_slot=14),
    make("empanada-bean", "empanadas", "Black Bean Empanada", 450, "each", "prepared",
         contains=["gluten"], may_contain=["dairy", "eggs"], hot=True, stock=40, per_slot=14),





    make("crepe-nutella", "crepe", "Hazelnut Chocolate & Strawberry Crepe", 800, "each", "prepared",
         contains=["gluten", "dairy", "eggs", "nuts"], hot=True, stock=30, per_slot=10),
    make("crepe-ham", "crepe", "Ham & Cheese Crepe", 900, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], hot=True, stock=30, per_slot=10),
    make("crepe-lemon", "crepe", "Lemon Sugar Crepe", 700, "each", "prepared",
         contains=["gluten", "dairy", "eggs"], may_contain=["nuts"], hot=True, stock=30, per_slot=10),




    make("sourdough-wheat", "bitty-bread", "Whole Wheat Sourdough Loaf", 900, "each", "grocery",
         tags=["whole_grain", "plant_based"], contains=["gluten"], stock=20),
    make("sourdough-cinnamon", "bitty-bread", "Cinnamon Raisin Sourdough", 800, "each", "grocery",
         tags=["plant_based"], contains=["gluten"], may_contain=["nuts"], stock=15),
    make("sourdough-rye", "bitty-bread", "Seeded Rye Sourdough", 900, "each", "grocery",
         tags=["whole_grain", "plant_based"], contains=["gluten", "sesame"], stock=12),




    make("honey-wheat", "great-harvest", "Honey Whole Wheat Loaf", 850, "each", "grocery",
         tags=["whole_grain"], contains=["gluten"], may_contain=["nuts"], stock=20),
    make("cranberry-walnut", "great-harvest", "Cranberry Walnut Loaf", 950, "each", "grocery",
         tags=["whole_grain"], contains=["gluten", "nuts"], stock=12),
    make("scone", "great-harvest", "Pumpkin Spice Scone", 450, "each", "grocery",
         contains=["gluten", "dairy", "eggs"], may_contain=["nuts"], stock=24),
]


for _p in _list:
    if "nuts" not in _p["contains"] and "nuts" not in _p["may_contain"]:
        _p["tags"].append("nut_free")
        #makes a list of nut free items by using traversing through the list and putting taking all of the items not in the 'contains nuts list' or the 'may contain list'
    if "dairy" not in _p["contains"] and "dairy" not in _p["may_contain"]:
        _p["tags"].append("dairy_free")
        #makes a lis of dairy free items by using traversing through the list and putting taking all of the items not in the 'contains dairy list' or the 'may contain list'


# id helps to check the product, so it can look things up quickly
PRODUCTS = {p["id"]: p for p in _list}
