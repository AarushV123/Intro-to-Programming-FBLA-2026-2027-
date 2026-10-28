
import os, sys
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
