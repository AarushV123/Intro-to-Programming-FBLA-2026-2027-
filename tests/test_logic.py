
import hashlib, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the real app functions and product list so these checks match what the website uses.
import app
from data import PRODUCTS
from datetime import date

# this prints a simple result for each check, including the expected and actual values if it fails.
def check(label, got, want):
    print(("PASS" if got == want else "FAIL"), "-", label, "" if got == want else "(got {!r}, want {!r})".format(got, want))

def line(pid, qty):
    p = PRODUCTS[pid]
    return {"key": pid + "|", "product": p, "qty": qty, "choice": "", "unit_price": p["price"], "total": p["price"] * qty}

# These checks make sure tax is rounded to whole cents, including a half-cent result.
try:
    check("percent_of 350 at 6%", app.percent_of(350, 6), 21)
    check("percent_of 25 at 6%", app.percent_of(25, 6), 2)
    check("percent_of 0", app.percent_of(0, 6), 0)
except Exception as e: print("FAIL - percent_of crashed:", e)

# Every catalog item should point to a bundled image so the shop works offline.
try:
    image_dir = os.path.join(os.path.dirname(__file__), "..", "static", "images")
    missing = [p["image"] for p in PRODUCTS.values()
               if not os.path.isfile(os.path.join(image_dir, p["image"]))]
    check("all product images exist locally", missing, [])
    image_names = [p["image"] for p in PRODUCTS.values()]
    check("every product has a unique image", len(set(image_names)), len(PRODUCTS))
    image_hashes = []
    for image_name in image_names:
        with open(os.path.join(image_dir, image_name), "rb") as image_file:
            image_hashes.append(hashlib.sha256(image_file.read()).digest())
    check("every product image has unique content", len(set(image_hashes)), len(PRODUCTS))
except Exception as e: print("FAIL - product image check crashed:", e)

# A product can contain an allergen, only possibly contain it, or have no match at all.
try:
    check("contains nuts", app.allergen_hits(PRODUCTS["cashew-spread"], ["nuts"]), ["Contains nuts."])
    check("may contain nuts", app.allergen_hits(PRODUCTS["latte"], ["nuts"]), ["May contain nuts (shared equipment)."])
    check("no match", app.allergen_hits(PRODUCTS["apples"], ["nuts", "dairy"]), [])
except Exception as e: print("FAIL - allergen_hits crashed:", e)

# The daily stock limit should allow the last available item, but not one more.
try:
    check("stock ok", app.stock_problems([line("ghost-peppers", 10)], "2026-11-21", []), [])
    check("stock too high", len(app.stock_problems([line("ghost-peppers", 11)], "2026-11-21", [])), 1)
except Exception as e: print("FAIL - stock_problems crashed:", e)

# Pickup limits are per time window: cold storage has a shared limit, and pierogi have their own batch limit.
try:
    full = [{"date": "2026-11-21", "slot": "9:00 AM", "cold_units": 18, "items": []}]
    check("cold slot has room", app.slot_problems([line("kimchi", 2)], "2026-11-21", "9:00 AM", full), [])
    check("cold slot full", len(app.slot_problems([line("kimchi", 3)], "2026-11-21", "9:00 AM", full)), 1)
    check("other slot unaffected", app.slot_problems([line("kimchi", 3)], "2026-11-21", "9:15 AM", full), [])
    check("hot batch limit", len(app.slot_problems([line("pierogi-hot", 9)], "2026-11-21", "9:00 AM", [])), 1)
except Exception as e: print("FAIL - slot_problems crashed:", e)
# age calc's
try:
    t = date.today()
    check("21 today", app.age_from_birthday(date(t.year - 21, t.month, t.day)), 21)
    check("one day short of 21", app.age_from_birthday(date(t.year - 21, t.month, t.day) + __import__("datetime").timedelta(days=1)), 20)
except Exception as e: print("FAIL - age_from_birthday crashed:", e)

# in app.py after confirming the warning for ghost peppers, an error of "Method Not Allowed" happens.
#added this code to prevent this error by confirming the warning before adding the product and makes sure the request goes through...
try:
    with app.app.test_client() as client:
        confirm = client.post("/add", data={"product_id": "ghost-peppers", "qty": "1"})
        check("ghost pepper warning shown", confirm.status_code, 200)
        check("warning page shows product image", b"/static/images/peppers.jpg" in confirm.data, True)
        added = client.post(
            "/add",
            data={"product_id": "ghost-peppers", "qty": "1", "confirmed": "yes"},
            headers={"Referer": "http://localhost/add"},
        )
        check("confirmed ghost pepper redirects to shop", added.location, "/")
        with client.session_transaction() as stored:
            check("confirmed ghost pepper added", stored["cart"], {"ghost-peppers|": 1})
        shop = client.get("/")
        check("shop shows an image for every product", shop.data.count(b'class="product-image"'), len(PRODUCTS))
        check("shop shows popular item note", b"Popular pick: bought frequently" in shop.data, True)
        cart_page = client.get("/cart")
        check("cart shows product image", b"/static/images/peppers.jpg" in cart_page.data, True)
        checkout_page = client.get("/checkout")
        check("checkout shows product image", b"/static/images/peppers.jpg" in checkout_page.data, True)
except Exception as e: print("FAIL - ghost pepper confirmation crashed:", e)

# The completed order page show the purchase summary and offer a printable receipt.
try:
    from unittest.mock import patch

    receipt_order = {
        "id": "OEC-TEST",
        "date": "2026-11-21",
        "slot": "9:30 AM",
        "name": "Test Shopper",
        "items": [{"pid": "apples", "qty": 2}],
        "total": 900,
        "invoices": [{
            "vendor_name": "Singh Sugar Maple Farm",
            "subtotal": 900,
            "tax": 0,
            "total": 900,
            "flags": [],
            "lines": [{
                "name": "Honeycrisp Apples",
                "image": PRODUCTS["apples"]["image"],
                "choice": "",
                "qty": 2,
                "unit_price": 450,
                "total": 900,
            }],
        }],
    }
    with app.app.test_client() as client:
        with client.session_transaction() as stored:
            stored["my_orders"] = ["OEC-TEST"]
        with patch.object(app, "load_orders", return_value=[receipt_order]):
            response = client.get("/order/OEC-TEST")
        check("receipt page renders", response.status_code, 200)
        check("receipt shows order number", b"OEC-TEST" in response.data, True)
        check("receipt shows items purchased", b"Honeycrisp Apples" in response.data, True)
        check("receipt has print action", b"Print receipt" in response.data, True)
except Exception as e: print("FAIL - receipt page crashed:", e)

# Checkout should use submitted values and accept mock email text.
try:
    with app.app.test_client() as client:
        with client.session_transaction() as stored:
            stored["cart"] = {"apples|": 1}
        with patch.object(app, "load_orders", return_value=[]), \
             patch.object(app, "save_orders") as save_orders:
            response = client.post("/checkout", data={
                "date": "2026-11-21",
                "slot": "9:00 AM",
                "name": "Sam",
                "email": "sam",
            })
        check("checkout accepts mock email and places order", response.status_code, 302)
        check("checkout redirects to receipt", response.location, "/order/OEC-1001")
        check("checkout saves order", save_orders.call_count, 1)
except Exception as e: print("FAIL - mock checkout crashed:", e)
