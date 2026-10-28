"""
Old Ellicott City Farmers Market - Pre-Order & Pickup System
============================================================

IMPORTANT:============================HOW TO RUN APP:============================================
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000 in your browser.

What this program does:
  1. A user can check online for what things are at the market, buy from different vendors, and the app will send the respective amount to 
     each vendor
  2. Since this is a real-world local business at the Old Ellicott City farmers market, the app uses the Maryland tax on some specific items.
  3. There are pickup slots from 9 AM to 1 PM on market Saturdays; there is also cold food and limits on how much hot food you can get from 
     one specific vendor.
  4. There is also an allergy option where you can select which allergies or food restrictions you have, and then the app will tell you/give you
     warnings about what foods you can eat vs. the foods you cannot eat.
  5. Lastly, the Cane Collective items need an ID because they have items that are for people 21+ years old.
"""

import json
# json lets the app save orders and load them later, meaning every order gets saved and can be pulled again

import os
# os helps json and helps the app find the orders file on the computer

import re
# the import re helps check that email addresses and phone numbers are valid emails/numbers

#This helps the app know the data, time and that type of stuff
from datetime import date, datetime, timedelta

#we used flask as the main way to create the website and its very useful for UI and handling user interactions
from flask import Flask, flash, redirect, render_template, request, session, url_for

from data import ALLERGENS, DIET_TAGS, PRODUCTS, VENDORS
#imports the information from the data.py file, meaining the vendors, food....

app = Flask(__name__)

app.secret_key = "password"

#settings
TAX_PERCENT = {"grocery": 0, "prepared": 6, "general": 6}   # used to set the MD tax
MIN_AGE = 21                  
COLD_CAPACITY = 20            # This is how many cold food items can be stored in each pickup slot
OPEN_MINUTES = 9 * 60         # 9 am open time
CLOSE_MINUTES = 13 * 60       # 1 PM close time
SLOT_LENGTH = 15              
ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.json")
# Used to store all orders in the orders.json file, important for saving data


@app.template_filter("money")
def money(cents):
    return "${:,.2f}".format(cents / 100)
#This allows for using cents and go too the second decimal spot with the $ sign

@app.template_filter("nice_date")
def nice_date(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%a, %b ") + str(d.day)
#Makes the dates easy to look at like "Sat, Nov 21"

def percent_of(cents, percent):
    return (cents * percent + 50) // 100
#Calculates the percentage

def market_dates():
    """These are the dates the market is open for, this function is used the make the list
    of avaliable dates the user can purchase things on.
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
    """We arranged this project so there are 15 minute pickup windows, which means 
    the customers can choose a specific time to pick up their orders."""
    slots = []
    for minutes in range(OPEN_MINUTES, CLOSE_MINUTES, SLOT_LENGTH):
        hour, minute = divmod(minutes, 60)
        suffix = "AM" if hour < 12 else "PM"
        hour12 = hour if hour <= 12 else hour - 12
        slots.append("{}:{:02d} {}".format(hour12, minute, suffix))
    return slots


def best_by(product, market_day):
    """This is another cool feature where the app will give you the dates for when it 
    would be best to pick up the items from the market, (shelf life things)"""
    if not product["shelf_days"] or market_day is None:
        return ""
    picked = market_day - timedelta(days=1)
    final = picked + timedelta(days=product["shelf_days"])
    return final.strftime("%b ") + str(final.day)


app.jinja_env.globals["best_by"] = best_by


#section for the orders part of the website.
def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE) as f:
        return json.load(f)


def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2) # .dump basically just dumps the orders to json


def sold_units(orders, date_iso):
    sold = {}
    for order in orders:
        if order["date"] == date_iso:
            for item in order["items"]:
                sold[item["pid"]] = sold.get(item["pid"], 0) + item["qty"] # pid is the product id and qty is the quantity sold
    return sold
    #self explanitory - how many units were sold on that day

def slot_usage(orders, date_iso, slot):
    """This function is used because we need to track how many cold units and 
    how many of each product are already booked in a specific pickup window(15 minute time slot)"""
    used = {"cold": 0, "items": {}}
    for order in orders:
        if order["date"] == date_iso and order["slot"] == slot:
            used["cold"] += order["cold_units"]
            for item in order["items"]:
                used["items"][item["pid"]] = used["items"].get(item["pid"], 0) + item["qty"]
    return used
                # this nested for loop is used because each order can contain multiple items and we need
                # to count the total quantity of each product booked in that time slot because there is a limit 
                #for how much can be picked up at once

# this is the part for the shopping cart section
def cart_lines(cart):
    lines = []
    for key, qty in cart.items():
        pid, _, choice = key.partition("|") #partitition is a func that allows you to split the string and use the parts separately
        product = PRODUCTS.get(pid)
        if product is None:
            continue
        unit_price = product["price"]
        #since this is real life, there are discounts added in the actual
        # farmers market, so the more you buy of one item, the cheaper the unit price becomes
        if product["bulk"] and qty >= product["bulk"][0]:
            unit_price = product["bulk"][1]
        lines.append({
            "key": key, "product": product, "qty": qty, "choice": choice,
            "unit_price": unit_price, "total": unit_price * qty,
        })
    return lines
            # this function might look complicated but it just calculates the total price for each line in the cart 
            # while applying any bulk discounts if they are able to be placed

def allergen_hits(product, allergens):
    """Check if a product contains or may contain any of the shopper's allergens."""
    hits = []
    for a in allergens:
        if a in product["contains"]:
            hits.append("Contains {}.".format(a))
        elif a in product["may_contain"]:
            hits.append("May contain {} (shared equipment).".format(a))
    return hits # this for loop checks each allergen againt the product's "contains" and "may_contain" lists and returns any matches found
    # its used because we need to inform the shopper if the product contains or may contain any of their allergens before they add it to the cart


def safety_reasons(product, allergens):
    """We added a saftey check just in case so the user has to click
    through confirmation actually being able to add items to the cart"""
    reasons = allergen_hits(product, allergens)
    if product["warning"]:    # this just means if the product has a warning, it will be added to the safety reasons list
        reasons.append(product["warning"])
    return reasons


def build_invoices(lines, allergens):
    """This is a long function and the reason is because each vendor needs to get a 
    share/seperate bill of what they are owed and what they are responsible for for the user
    """
    by_vendor = {}
    for line in lines:
        by_vendor.setdefault(line["product"]["vendor"], []).append(line)

    invoices = []
    for vendor_id, vendor_lines in by_vendor.items():
        subtotal = sum(l["total"] for l in vendor_lines)

        #in this app there is two types of tax, meaning some products are different with diff tax rates
        # this means we need to calc the total for each item seperatly
        class_totals = {} 
        for l in vendor_lines:
            cls = l["product"]["tax"]
            class_totals[cls] = class_totals.get(cls, 0) + l["total"]
        tax = sum(percent_of(amount, TAX_PERCENT[cls]) for cls, amount in class_totals.items())

        #The reason we made this is to ensure that the vendor is awarer of the special 
        # things for eaach order
        # all of these things are flags about each possible order
        flags = []
        if any(l["product"]["age21"] for l in vendor_lines):
            flags.append("ID CHECK REQUIRED AT PICKUP (21+)") # appends the ID check requirement to the flags list
        if any(l["product"]["cold"] for l in vendor_lines):
            flags.append("Keep cold: bag goes in the cooler locker") # similar to the other append but it just adds that it needs to be cold
        if any(l["product"]["hot"] for l in vendor_lines):
            flags.append("Hot food: make fresh so it is ready at the start of the window")
        for lines in vendor_lines:
            for hit in allergen_hits(lines["product"], allergens):
                flags.append("ALLERGY ALERT - {}: {}".format(lines["product"]["name"], hit))

        invoices.append({ # adds the invoice for this vendor to the invoices list
            "vendor_id": vendor_id, "vendor_name": VENDORS[vendor_id]["name"],
            "lines": vendor_lines, "subtotal": subtotal, "tax": tax,
            "total": subtotal + tax, "flags": flags,
        }) 
    return invoices 


def qty_by_product(lines):
    #Total quantity per product id
    # this is used to group quantities by product id
    totals = {}
    for line in lines:
        pid = line["product"]["id"]
        totals[pid] = totals.get(pid, 0) + line["qty"]
    return totals


# checks
def stock_problems(lines, date_iso, orders):
    # this is used because we need to check if there is enough stock for the given market day
    sold = sold_units(orders, date_iso)
    problems = []
    for pid, qty in qty_by_product(lines).items():
        left = PRODUCTS[pid]["stock"] - sold.get(pid, 0)
        if qty > left:
            problems.append("Only {} of {} left for this market day.".format(max(left, 0), PRODUCTS[pid]["name"]))
    return problems


def slot_problems(lines, date_iso, slot, orders): # fixed
    # Sometimes the per window limits are too much for certain products and that can cause problems.
    # this func is used to check if there are problems with the given slot
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
    status = []
    for slot in time_slots():
        problems = slot_problems(lines, date_iso, slot, orders)
        status.append({"slot": slot, "ok": not problems, "reason": " ".join(problems)}) # ..
    return status


def age_from_birthday(birthday): 
    today = date.today()
    years = today.year - birthday.year
    if (today.month, today.day) < (birthday.month, birthday.day):
        years -= 1
    return years


#pages
@app.before_request 
"""the @ is a decorator and we use this decorator because we want to chec if the cart is actually their before each request"""

def ensure_cart_exists():
    cart = session.get("cart")
    if not isinstance(cart, dict): # isinstance checks if the cart is a dict 
        session["cart"] = {}


@app.context_processor # another decorator to make the data available in all templates
def add_cart_count():
    return {"cart_count": sum(session.get("cart", {}).values())} # session.get gets the cart from the session and js creates a empty dict if it doesn't exist


@app.route("/") # @app.route is a decorator that maps the URL "/" to the shop function
def shop(): 
    dates = market_dates()
    next_date = dates[0] if dates else None
    orders = load_orders()
    sold = sold_units(orders, next_date.isoformat()) if next_date else {}
# we use this to create the actuall shop page
# the tags, vendors, searchs.... are put here because they are used to filter the items displayed on the shop page
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


# we use this function and the @app route to handle the profile pg, where the shopper is able to update their allergies
# then it gets stored and used to filter risky items in the shop page
@app.route("/profile", methods=["GET", "POST"])
def profile():
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

    # bc people have allergies and dietary restrictions, there is a confirmation step before adding risky items to the cart
    reasons = safety_reasons(product, session.get("allergens", []))
    if reasons and request.form.get("confirmed") != "yes":
        return render_template("confirm.html", product=product, qty=qty, choice=choice, reasons=reasons)

    cart = session.get("cart", {})
    key = product["id"] + "|" + choice
    cart[key] = cart.get(key, 0) + qty

    # since people might want more than one thing of an item, we need to check if there is enough items in stock so ppl can add them to the cart without exceeding the available quantity
    total = sum(q for k, q in cart.items() if k.split("|")[0] == product["id"])
    if total > product["stock"]:
        cart[key] -= total - product["stock"]
        flash("Limited harvest: only {} of {} available.".format(product["stock"], product["name"]))
        if cart[key] <= 0:
            del cart[key] 
    else:                               # this whole long if statmenet is used because we need to handle the case where the total quantity in the cart does not exceed the available stock
        flash("Added {} x {} to your cart.".format(qty, product["name"])) 
    session["cart"] = cart
    return redirect(request.referrer or url_for("shop"))


@app.route("/cart") # using @app.route again to map the URL "/cart" to the cart_page function, this just helps to allow the website to go to different pages
def cart_page():
    lines = cart_lines(session.get("cart", {}))
    invoices = build_invoices(lines, session.get("allergens", [])) # build invoices func to generate the list of invoices for the cart items
    return render_template(            # render template is the func used to generate the HTML for the cart page
        "cart.html", invoices=invoices,
        subtotal=sum(i["subtotal"] for i in invoices),
        tax=sum(i["tax"] for i in invoices),
        total=sum(i["total"] for i in invoices),
    )


@app.route("/cart/update", methods=["POST"]) # @app.route is used again just like before to map the URL "/cart/update" to the update_cart function, this helps to allow the website to handle updating the cart items
def update_cart():
    cart = session.get("cart", {})
    key = request.form.get("key", "")
    if key in cart:
        try:
            qty = int(request.form.get("qty", "0"))
        except ValueError:
            qty = cart[key]
        product = PRODUCTS[key.split("|")[0]] # we use key split because the key in the cart is a combination of the product ID and the choice, separated by a | character
        if qty <= 0:
            del cart[key]
        else:
            cart[key] = min(qty, product["stock"])
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.route("/cart/clear", methods=["POST"]) # similarly @app.route is used again here to map the URL "/cart/clear" to the clear_cart function, this helps to allow the website to handle clearing the cart items
def clear_cart():
    """Remove every item from the cart."""
    session["cart"] = {}
    flash("Your cart has been cleared.")
    return redirect(url_for("cart_page"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    # the GET shows the checkout while the POST means the shopper submitted it.
    cart = session.get("cart", {})
    lines = cart_lines(cart)
    if not lines:
        # this means that there is nothing to pay for like the cart is empty, so it will send the shopper back to the store.
        flash("Your cart is empty.")
        return redirect(url_for("shop"))

    dates = market_dates()
    if not dates:
        flash("The market season is over. See you next year!")
        return redirect(url_for("cart_page"))
    # this will keep the checkout focused on the next few market days, and ignore dates not on that list.
    date_choices = [d.isoformat() for d in dates[:4]]
    chosen_date = request.values.get("date", date_choices[0])
    if chosen_date not in date_choices:
        chosen_date = date_choices[0]

    allergens = session.get("allergens", [])
    orders = load_orders()
    invoices = build_invoices(lines, allergens)
    # we need to ask for an age check only if at least one item in the cart requires it, so this line of code does that
    needs_age = any(l["product"]["age21"] for l in lines)
    slots = slot_status(lines, chosen_date, orders)
    errors = []
    form = {"name": "", "email": "", "phone": "", "slot": "", "dob": ""}

    if request.method == "POST":
        # this line of code takes out extra spaces so they dont cause some errors 

        # Check contact details before saving an order, so the customer can be reached, important for the day of when the order transaction happens, makes the user experience smoother.
        # easier and allows the process between the user and the vendor to go smoothly.
        if len(form["name"]) < 2:
            errors.append("Please enter your name.")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", form["email"]):
            errors.append("Please enter a valid email address.")
        if form["phone"] and len(re.sub(r"\D", "", form["phone"])) != 10:
            errors.append("Phone numbers need 10 digits (or leave it blank).")

        # Only check a birthday for carts with age-restricted items but people can also lie about age, this is just a safety filter, the ID verification will happen at pickup.
        if needs_age:
            try:
                birthday = date.fromisoformat(form["dob"])
                if birthday > date.today():
                    errors.append("Birth date cannot be in the future.")
                elif age_from_birthday(birthday) < MIN_AGE:
                    errors.append("Cane Collective items are for ages {}+. Please remove them from your cart.".format(MIN_AGE))
            except ValueError:
                errors.append("Please enter your birth date to buy Cane Collective items.")

        errors += stock_problems(lines, chosen_date, orders)
        if form["slot"] not in time_slots():
            errors.append("Please choose a pickup time.")
        else:
            errors += slot_problems(lines, chosen_date, form["slot"], orders)

        if not errors:

                # it is easiest if we create the order dictionary first and then append it to the orders list because it allows us to reference the order ID immediately after creation.
                # and by doing this we can immediately use the order ID for the receipt page.
            order = {
                "id": "OEC-{}".format(1001 + len(orders)),
                "name": form["name"], "email": form["email"].lower(), "phone": form["phone"],
                "date": chosen_date, "slot": form["slot"],
                # We only need to record that an age check was needed, not the birthday itself.
                "age_checked": needs_age,
                "cold_units": sum(l["product"]["cold"] * l["qty"] for l in lines),
                "items": [{"pid": l["product"]["id"], "qty": l["qty"]} for l in lines],
                # Each vendor gets their own invoice so they can prepare their part of the order and they can also get the money from the user based on what part they are owed based on the users order
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

            # The render template function below is used to display the checkout page with all the necessary information for the user to complete their order.
            # this means it will show the checkout page with the current cart items, available pickup dates and times, and any relevant errors or warnings based on what they orderd
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
    return render_template("receipt.html", order=order) # render template is used again here because it allows the user to view the details of their completed order.


@app.route("/lookup", methods=["GET", "POST"])
def lookup():
    if request.method == "POST":
        order_id = request.form.get("order_id", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        for order in load_orders():
            if order["id"] == order_id and order["email"] == email:
                session["my_orders"] = session.get("my_orders", []) + [order_id]
                return redirect(url_for("receipt", order_id=order_id))
        flash("We could not find an order with that number and email.") # if the order is not found, we display this message instead of just throwing an error.
    return render_template("lookup.html")


@app.route("/vendor/<vendor_id>") 
def vendor_queue(vendor_id):
# this func shows the fulfillment queue for a specific vendor, allowing them to see
# which orders they need to prepare for a given date and what are all of the things they need to do for that order.
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


#all of the functions with the @app.route decorator were used to define the routes for the web application so everything connects with each other smoothly and
# when clicking on something, the website would go to the right page and not throw errors.

if __name__ == "__main__":
    app.run(debug=True)

# this is the most essential thing because it allows the web application to run and be accessible through a local server, making it possible for users to interact with the website.
