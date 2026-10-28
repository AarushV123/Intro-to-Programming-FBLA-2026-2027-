# Old Ellicott City Farmers Market - Pre-Order System

Teacher reference build (Flask). Not intended to be submitted as student work.

## Run it
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

## Files
- app.py: routes and all the logic (tax, slots, constraints, invoices)
- data.py: vendors and products (prices in cents)
- templates/: the HTML pages
- static/style.css: styling
- orders.json: created automatically when the first order is placed

## Things to verify before real use
- The market vendor list: this sample uses the 12 vendors named in the project brief, not all 15.
- Tax rules: groceries 0%, prepared food and general goods 6%, per Maryland guidance. Edge cases
  (juice, roasted coffee beans, bakery items, mixers) should be checked with the Maryland Comptroller.
- Capacity numbers (COLD_CAPACITY, per_slot limits) are sample values.
- Vendor queue pages have no login. A real system needs one.
