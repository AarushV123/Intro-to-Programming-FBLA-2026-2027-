"""
Old Ellicott City Farmers Market - Pre-Order & Pickup System
============================================================

How to run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in your browser.

What this program does:
  1. Multi-vendor cart: one order, one receipt, but a separate invoice per vendor.
  2. Tax by category: groceries 0%, prepared food and general goods 6% (Maryland).
  3. Pickup slots: 15-minute windows from 9:00 AM to 1:00 PM on market Saturdays,
     with a shared cold-locker capacity and per-window limits on hot food.
  4. Allergy profile: a safety confirmation is required before adding a risky item.
  5. Age gate: Cane Collective items need a 21+ check and an ID flag at pickup.

Prices, stock and capacity numbers are sample data. Always check tax rules with
the Maryland Comptroller before using real numbers.
"""

import json
import os
import re
from datetime import date, datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, session, url_for

from data import ALLERGENS, DIET_TAGS, PRODUCTS, VENDORS

app = Flask(__name__)
app.secret_key = "change-this-secret-before-real-use"

#settings
TAX_PERCENT = {"grocery": 0, "prepared": 6, "general": 6}   # Maryland sales tax
MIN_AGE = 21                  # age needed for Cane Collective items
COLD_CAPACITY = 20            # cooler-locker units available in each 15-minute slot
OPEN_MINUTES = 9 * 60         # market opens at 9:00 AM (minutes after midnight)
CLOSE_MINUTES = 13 * 60       # market closes at 1:00 PM
SLOT_LENGTH = 15              # minutes per pickup window
ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.json")


#formatting changes
@app.template_filter("money")
def money(cents):
    """Turn 1250 into '$12.50'."""
    return "${:,.2f}".format(cents / 100)


@app.template_filter("nice_date")
def nice_date(iso):
    """Turn '2026-11-21' into 'Sat, Nov 21'."""
    d = date.fromisoformat(iso)
    return d.strftime("%a, %b ") + str(d.day)


def percent_of(cents, percent):
    """percent% of cents, rounded to the nearest cent using only whole numbers."""
    return (cents * percent + 50) // 100


def market_dates():
    """Dates a customer can still order for.

    The market runs Saturdays May 23 - Oct 24, 2026 plus a Thanksgiving market
    on Nov 21. Online orders close at 5:00 PM on the Friday before.
    """
    all_dates = []
    day = date(2026, 5, 23)
    while day <= date(2026, 10, 24):
        all_dates.append(day)
        day += timedelta(days=7)
    all_dates.append(date(2026, 11, 21))

    now = datetime.now()
    open_dates = []
    for d in all_dates:
        cutoff = datetime(d.year, d.month, d.day, 17, 0) - timedelta(days=1)
        if now < cutoff:
            open_dates.append(d)
    return open_dates


def time_slots():
    """Every 15-minute window label: '9:00 AM', '9:15 AM' ... '12:45 PM'."""
    slots = []
    for minutes in range(OPEN_MINUTES, CLOSE_MINUTES, SLOT_LENGTH):
        hour, minute = divmod(minutes, 60)
        suffix = "AM" if hour < 12 else "PM"
        hour12 = hour if hour <= 12 else hour - 12
        slots.append("{}:{:02d} {}".format(hour12, minute, suffix))
    return slots


def best_by(product, market_day):
    """Best-by date for fresh items: picked the day before market + shelf life."""
    if not product["shelf_days"] or market_day is None:
        return ""
    picked = market_day - timedelta(days=1)
    final = picked + timedelta(days=product["shelf_days"])
    return final.strftime("%b ") + str(final.day)


app.jinja_env.globals["best_by"] = best_by


#saved orders
def load_orders():
    """Read every saved order from orders.json (empty list if none yet)."""
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE) as f:
        return json.load(f)


def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)


def sold_units(orders, date_iso):
    """How many of each product are already ordered for one market day."""
    sold = {}
    for order in orders:
        if order["date"] == date_iso:
            for item in order["items"]:
                sold[item["pid"]] = sold.get(item["pid"], 0) + item["qty"]
    return sold


def slot_usage(orders, date_iso, slot):
    """Cold units and per-product counts already booked in one pickup window."""
    used = {"cold": 0, "items": {}}
    for order in orders:
        if order["date"] == date_iso and order["slot"] == slot:
            used["cold"] += order["cold_units"]
            for item in order["items"]:
                used["items"][item["pid"]] = used["items"].get(item["pid"], 0) + item["qty"]
    return used


#cart logic
def cart_lines(cart):
    """Turn the session cart into a list of lines with prices worked out.

    Cart keys look like 'latte|Hot' (product id, then the option chosen).
    """
    lines = []
    for key, qty in cart.items():
        pid, _, choice = key.partition("|")
        product = PRODUCTS.get(pid)
        if product is None:
            continue
        unit_price = product["price"]
        # bulk pricing: buy enough and every unit gets the cheaper price
        if product["bulk"] and qty >= product["bulk"][0]:
            unit_price = product["bulk"][1]
        lines.append({
            "key": key, "product": product, "qty": qty, "choice": choice,
            "unit_price": unit_price, "total": unit_price * qty,
        })
    return lines


def allergen_hits(product, allergens):
    """Plain-English allergy matches between a product and the shopper's profile."""
    hits = []
    for a in allergens:
        if a in product["contains"]:
            hits.append("Contains {}.".format(a))
        elif a in product["may_contain"]:
            hits.append("May contain {} (shared equipment).".format(a))
    return hits


def safety_reasons(product, allergens):
    """Everything that needs a confirmation click before the item is added."""
    reasons = allergen_hits(product, allergens)
    if product["warning"]:
        reasons.append(product["warning"])
    return reasons


def build_invoices(lines, allergens):
    """Split one cart into one invoice per vendor, with tax worked out per vendor."""
    by_vendor = {}
    for line in lines:
        by_vendor.setdefault(line["product"]["vendor"], []).append(line)

    invoices = []
    for vendor_id, vendor_lines in by_vendor.items():
        subtotal = sum(l["total"] for l in vendor_lines)

        # add up each tax class separately, then apply that class's rate
        class_totals = {}
        for l in vendor_lines:
            cls = l["product"]["tax"]
            class_totals[cls] = class_totals.get(cls, 0) + l["total"]
        tax = sum(percent_of(amount, TAX_PERCENT[cls]) for cls, amount in class_totals.items())

        # notes the vendor needs when they pack the order
        flags = []
        if any(l["product"]["age21"] for l in vendor_lines):
            flags.append("ID CHECK REQUIRED AT PICKUP (21+)")
        if any(l["product"]["cold"] for l in vendor_lines):
            flags.append("Keep cold: bag goes in the cooler locker")
        if any(l["product"]["hot"] for l in vendor_lines):
            flags.append("Hot food: make fresh so it is ready at the start of the window")
        for l in vendor_lines:
            for hit in allergen_hits(l["product"], allergens):
                flags.append("ALLERGY ALERT - {}: {}".format(l["product"]["name"], hit))

        invoices.append({
            "vendor_id": vendor_id, "vendor_name": VENDORS[vendor_id]["name"],
            "lines": vendor_lines, "subtotal": subtotal, "tax": tax,
            "total": subtotal + tax, "flags": flags,
        })
    return invoices


def qty_by_product(lines):
    """Total quantity per product id (different options of one product are added)."""
    totals = {}
    for l in lines:
        pid = l["product"]["id"]
        totals[pid] = totals.get(pid, 0) + l["qty"]
    return totals


# checks
def stock_problems(lines, date_iso, orders):
    """Harvest limits: is there enough left for this market day?"""
    sold = sold_units(orders, date_iso)
    problems = []
    for pid, qty in qty_by_product(lines).items():
        left = PRODUCTS[pid]["stock"] - sold.get(pid, 0)
        if qty > left:
            problems.append("Only {} of {} left for this market day.".format(max(left, 0), PRODUCTS[pid]["name"]))
    return problems


def slot_problems(lines, date_iso, slot, orders):
    """Cold-locker capacity and per-window batch limits for one pickup slot."""
    used = slot_usage(orders, date_iso, slot)
    problems = []

    cold_needed = sum(l["product"]["cold"] * l["qty"] for l in lines)
    if cold_needed and used["cold"] + cold_needed > COLD_CAPACITY:
        problems.append("The cold lockers are full at this time.")

    for pid, qty in qty_by_product(lines).items():
        limit = PRODUCTS[pid]["per_slot"]
        if limit and used["items"].get(pid, 0) + qty > limit:
            problems.append("{} is at its limit for this window.".format(PRODUCTS[pid]["name"]))
    return problems


def slot_status(lines, date_iso, orders):
    """For every slot: is it available, and if not, why not?"""
    status = []
    for slot in time_slots():
        problems = slot_problems(lines, date_iso, slot, orders)
        status.append({"slot": slot, "ok": not problems, "reason": " ".join(problems)})
    return status


def age_from_birthday(birthday):
    today = date.today()
    years = today.year - birthday.year
    if (today.month, today.day) < (birthday.month, birthday.day):
        years -= 1
    return years


#pages
@app.before_request
def ensure_cart_exists():
    """A fresh session should start with an empty cart."""
    cart = session.get("cart")
    if not isinstance(cart, dict):
        session["cart"] = {}


@app.context_processor
def add_cart_count():
    """Makes 'cart_count' available in every template for the nav bar."""
    return {"cart_count": sum(session.get("cart", {}).values())}


@app.route("/")
def shop():
    dates = market_dates()
    next_date = dates[0] if dates else None
    orders = load_orders()
    sold = sold_units(orders, next_date.isoformat()) if next_date else {}

    # filters from the URL
    chosen_tags = request.args.getlist("tag")
    vendor = request.args.get("vendor", "")
    search = request.args.get("q", "").strip().lower()
    hide_allergens = request.args.get("hide") == "1"
    allergens = session.get("allergens", [])

    items = []
    for product in PRODUCTS.values():
        if vendor and product["vendor"] != vendor:
            continue
        vendor_name = VENDORS[product["vendor"]]["name"].lower()
        if search and search not in product["name"].lower() and search not in vendor_name:
            continue
        if any(tag not in product["tags"] for tag in chosen_tags):
            continue
        hits = allergen_hits(product, allergens)
        if hide_allergens and hits:
            continue
        items.append({"p": product, "left": product["stock"] - sold.get(product["id"], 0), "hits": hits})

    return render_template(
        "shop.html", items=items, vendors=VENDORS, diet_tags=DIET_TAGS,
        chosen_tags=chosen_tags, vendor=vendor, search=request.args.get("q", ""),
        hide=hide_allergens, allergens=allergens, next_date=next_date,
        days_away=(next_date - date.today()).days if next_date else None,
    )


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """Where the shopper tells us which allergens to watch for."""
    if request.method == "POST":
        valid = [key for key, _ in ALLERGENS]
        session["allergens"] = [a for a in request.form.getlist("allergen") if a in valid]
        flash("Allergy profile saved. We will ask you to confirm before adding risky items.")
        return redirect(url_for("shop"))
    return render_template("profile.html", allergen_list=ALLERGENS, mine=session.get("allergens", []))


@app.route("/add", methods=["POST"])
def add_to_cart():
    product = PRODUCTS.get(request.form.get("product_id", ""))
    if product is None:
        flash("That item could not be found.")
        return redirect(url_for("shop"))

    try:
        qty = int(request.form.get("qty", "1"))
    except ValueError:
        qty = 0
    if qty < 1 or qty > product["stock"]:
        flash("Please pick a quantity between 1 and {}.".format(product["stock"]))
        return redirect(url_for("shop"))

    choice = request.form.get("choice", "")
    if product["choices"] and choice not in product["choices"]:
        choice = product["choices"][0]

    # safety rule: a risky item needs a "yes, I understand" click first
    reasons = safety_reasons(product, session.get("allergens", []))
    if reasons and request.form.get("confirmed") != "yes":
        return render_template("confirm.html", product=product, qty=qty, choice=choice, reasons=reasons)

    cart = session.get("cart", {})
    key = product["id"] + "|" + choice
    cart[key] = cart.get(key, 0) + qty

    # never let one product go over its stock in total
    total = sum(q for k, q in cart.items() if k.split("|")[0] == product["id"])
    if total > product["stock"]:
        cart[key] -= total - product["stock"]
        flash("Limited harvest: only {} of {} available.".format(product["stock"], product["name"]))
        if cart[key] <= 0:
            del cart[key]
    else:
        flash("Added {} x {} to your cart.".format(qty, product["name"]))
    session["cart"] = cart
    return redirect(request.referrer or url_for("shop"))


@app.route("/cart")
def cart_page():
    lines = cart_lines(session.get("cart", {}))
    invoices = build_invoices(lines, session.get("allergens", []))
    return render_template(
        "cart.html", invoices=invoices,
        subtotal=sum(i["subtotal"] for i in invoices),
        tax=sum(i["tax"] for i in invoices),
        total=sum(i["total"] for i in invoices),
    )


@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart = session.get("cart", {})
    key = request.form.get("key", "")
    if key in cart:
        try:
            qty = int(request.form.get("qty", "0"))
        except ValueError:
            qty = cart[key]
        product = PRODUCTS[key.split("|")[0]]
        if qty <= 0:
            del cart[key]
        else:
            cart[key] = min(qty, product["stock"])
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.route("/cart/clear", methods=["POST"])
def clear_cart():
    """Remove every item from the cart."""
    session["cart"] = {}
    flash("Your cart has been cleared.")
    return redirect(url_for("cart_page"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    lines = cart_lines(cart)
    if not lines:
        flash("Your cart is empty.")
        return redirect(url_for("shop"))

    dates = market_dates()
    if not dates:
        flash("The market season is over. See you next year!")
        return redirect(url_for("cart_page"))
    date_choices = [d.isoformat() for d in dates[:4]]
    chosen_date = request.values.get("date", date_choices[0])
    if chosen_date not in date_choices:
        chosen_date = date_choices[0]

    allergens = session.get("allergens", [])
    orders = load_orders()
    invoices = build_invoices(lines, allergens)
    needs_age = any(l["product"]["age21"] for l in lines)
    slots = slot_status(lines, chosen_date, orders)
    errors = []
    form = {"name": "", "email": "", "phone": "", "slot": "", "dob": ""}

    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in form}

        # 1. contact details
        if len(form["name"]) < 2:
            errors.append("Please enter your name.")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", form["email"]):
            errors.append("Please enter a valid email address.")
        if form["phone"] and len(re.sub(r"\D", "", form["phone"])) != 10:
            errors.append("Phone numbers need 10 digits (or leave it blank).")

        # 2. age gate
        if needs_age:
            try:
                birthday = date.fromisoformat(form["dob"])
                if birthday > date.today():
                    errors.append("Birth date cannot be in the future.")
                elif age_from_birthday(birthday) < MIN_AGE:
                    errors.append("Cane Collective items are for ages {}+. Please remove them from your cart.".format(MIN_AGE))
            except ValueError:
                errors.append("Please enter your birth date to buy Cane Collective items.")

        # 3. stock and pickup slot
        errors += stock_problems(lines, chosen_date, orders)
        if form["slot"] not in time_slots():
            errors.append("Please choose a pickup time.")
        else:
            errors += slot_problems(lines, chosen_date, form["slot"], orders)

        if not errors:
            order = {
                "id": "OEC-{}".format(1001 + len(orders)),
                "name": form["name"], "email": form["email"].lower(), "phone": form["phone"],
                "date": chosen_date, "slot": form["slot"],
                "age_checked": needs_age,   # we keep only yes/no, never the birth date
                "cold_units": sum(l["product"]["cold"] * l["qty"] for l in lines),
                "items": [{"pid": l["product"]["id"], "qty": l["qty"]} for l in lines],
                "invoices": [
                    {
                        "vendor_id": inv["vendor_id"], "vendor_name": inv["vendor_name"],
                        "subtotal": inv["subtotal"], "tax": inv["tax"], "total": inv["total"],
                        "flags": inv["flags"],
                        "lines": [
                            {"name": l["product"]["name"], "choice": l["choice"], "qty": l["qty"],
                             "unit_price": l["unit_price"], "total": l["total"]}
                            for l in inv["lines"]
                        ],
                    }
                    for inv in invoices
                ],
                "total": sum(inv["total"] for inv in invoices),
            }
            orders.append(order)
            save_orders(orders)
            session["cart"] = {}
            session["my_orders"] = session.get("my_orders", []) + [order["id"]]
            return redirect(url_for("receipt", order_id=order["id"]))

    any_open = any(s["ok"] for s in slots)
    return render_template(
        "checkout.html", invoices=invoices, total=sum(i["total"] for i in invoices),
        date_choices=date_choices, chosen_date=chosen_date, slots=slots, any_open=any_open,
        needs_age=needs_age, min_age=MIN_AGE, errors=errors, form=form,
    )


@app.route("/order/<order_id>")
def receipt(order_id):
    order = next((o for o in load_orders() if o["id"] == order_id), None)
    if order is None or order_id not in session.get("my_orders", []):
        flash("Please look up your order with your order number and email.")
        return redirect(url_for("lookup"))
    return render_template("receipt.html", order=order)


@app.route("/lookup", methods=["GET", "POST"])
def lookup():
    if request.method == "POST":
        order_id = request.form.get("order_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        for order in load_orders():
            if order["id"] == order_id and order["email"] == email:
                session["my_orders"] = session.get("my_orders", []) + [order_id]
                return redirect(url_for("receipt", order_id=order_id))
        flash("We could not find an order with that number and email.")
    return render_template("lookup.html")


@app.route("/vendor/<vendor_id>")
def vendor_queue(vendor_id):
    """Fulfillment queue a vendor can open on Saturday morning to pack orders."""
    if vendor_id not in VENDORS:
        flash("Unknown vendor.")
        return redirect(url_for("shop"))
    orders = load_orders()
    days = sorted({o["date"] for o in orders})
    chosen = request.args.get("date", days[0] if days else "")
    queue = []
    for order in sorted(orders, key=lambda o: time_slots().index(o["slot"])):
        if order["date"] != chosen:
            continue
        for inv in order["invoices"]:
            if inv["vendor_id"] == vendor_id:
                queue.append({"order": order, "invoice": inv})
    return render_template("vendor.html", vendor=VENDORS[vendor_id], vendors=VENDORS,
                           vendor_id=vendor_id, queue=queue, days=days, chosen=chosen)


if __name__ == "__main__":
    app.run(debug=True)
