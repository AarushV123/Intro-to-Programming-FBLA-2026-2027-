## Summary of the app - 
Old Ellicott City Farmers Market - Pre-Order System is a digital ordering platform that allows shoppers to buy things from 12 vendors in a single checkout. It manages the complexities in real life like pickup time slots, knowing when to take out the foods so they dont perish because they are not in the right temprature and dietary filters.

## The steps to run the code
## 1. First you need to install the requirnments which is flask
    pip install -r requirements.txt
## 2. Then you will need to run this line of code to get the app online:
    python app.py
## 3. Then you can open the app by openning this website
Open http://127.0.0.1:5000

## These are the list of files:
- app.py: routes and all the logic (tax, slots, constraints, invoices)
- data.py: gives all of the vendors and products, basically all of there information
- templates/: the HTML pages
- static/style.css: styling the website
- orders.json: created automatically when the first order is placed, it basically saves all of the orders

## Other info:
- The market vendor list: this sample uses the 12 vendors instead of all of the vendors in the actual old ellicott city farmers market
- Because this is a real life app, we encorperated tax as well and its based of off maryland
- The Vendor queue pages have no login. A real system would actually need one...
- Images of the food are added and cited in static/images/IMAGE-CREDITS.txt.
- The app also allows your order history
- The app also marks the most popular picks
