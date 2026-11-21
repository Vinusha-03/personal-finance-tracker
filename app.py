from flask import Flask, render_template, request, redirect, url_for
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import calendar
import os

# Load environment variables from .env
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Read MongoDB connection string
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI is missing. Check your .env file.")

# Connect to MongoDB
client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=5000
)

# Select our database
db = client["personal_finance"]


# Home route - Display dashboard and handle transactions
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        # Get data from HTML form
        transaction_type = request.form.get("type")
        category = request.form.get("category")
        amount = float(request.form.get("amount"))
        payment_method = request.form.get("payment_method")

        date = datetime.strptime(
            request.form.get("date"), "%Y-%m-%d"
        )

        description = request.form.get("description")

        # Create transaction document
        transaction = {
            "user_id": "USER001",
            "type": transaction_type,
            "category": category,
            "amount": amount,
            "payment_method": payment_method,
            "date": date,
            "description": description
        }

        # Insert transaction into MongoDB
        result = db.transactions.insert_one(transaction)

        print("Transaction saved successfully!")
        print("Inserted ID:", result.inserted_id)

    # Get current month and year
    now = datetime.now()

    current_year = now.year
    current_month = now.month

    # Get the first and last day of the current month
    first_day = datetime(current_year, current_month, 1)

    last_day = datetime(
        current_year,
        current_month,
        calendar.monthrange(current_year, current_month)[1],
        23, 59, 59
    )

    # Fetch current month's transactions
    monthly_transactions = list(
        db.transactions.find({
            "user_id": "USER001",
            "date": {
                "$gte": first_day,
                "$lte": last_day
            }
        })
    )

    # Calculate monthly income
    monthly_income = sum(
        t["amount"] for t in monthly_transactions
        if t["type"] == "income"
    )

    # Calculate monthly expenses
    monthly_expenses = sum(
        t["amount"] for t in monthly_transactions
        if t["type"] == "expense"
    )

    # Calculate monthly savings
    monthly_savings = monthly_income - monthly_expenses 
    
    # Calculate expenses by category
    expense_categories = {}

    for transaction in monthly_transactions:

        if transaction["type"] == "expense":

            category = transaction["category"]
            amount = transaction["amount"]

            if category in expense_categories:
                expense_categories[category] += amount
            else:
                expense_categories[category] = amount

    # Fetch all transactions from MongoDB
    transactions = list(
        db.transactions.find(
            {"user_id": "USER001"}
        ).sort("date", -1)
    )
    # Calculate total income
    total_income = sum(
        t["amount"] for t in transactions
        if t["type"] == "income"
    )

    # Calculate total expenses
    total_expenses = sum(
        t["amount"] for t in transactions
        if t["type"] == "expense"
    )

    # Calculate current balance
    current_balance = total_income - total_expenses

    # Display transactions on dashboard
    return render_template(
        "index.html",
        transactions=transactions,
        total_income=total_income,
        total_expenses=total_expenses,
        current_balance=current_balance,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_savings,
        expense_categories=expense_categories
    )

# Delete transaction
@app.route("/delete/<transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):

    from bson.objectid import ObjectId

    # Delete transaction from MongoDB
    result = db.transactions.delete_one({
        "_id": ObjectId(transaction_id),
        "user_id": "USER001"
    })

    if result.deleted_count == 1:
        print("Transaction deleted successfully!")
    else:
        print("Transaction not found!")

    return redirect(url_for("home"))


# Edit transaction
@app.route("/edit/<transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):

    # Find the selected transaction
    transaction = db.transactions.find_one({
        "_id": ObjectId(transaction_id),
        "user_id": "USER001"
    })

    # Check whether transaction exists
    if transaction is None:
        return "Transaction not found!", 404

    if request.method == "POST":

        # Get updated data from HTML form
        transaction_type = request.form.get("type")
        category = request.form.get("category")
        amount = float(request.form.get("amount"))
        payment_method = request.form.get("payment_method")

        date = datetime.strptime(
            request.form.get("date"), "%Y-%m-%d"
        )

        description = request.form.get("description")

        # Update transaction in MongoDB
        db.transactions.update_one(
            {
                "_id": ObjectId(transaction_id),
                "user_id": "USER001"
            },
            {
                "$set": {
                    "type": transaction_type,
                    "category": category,
                    "amount": amount,
                    "payment_method": payment_method,
                    "date": date,
                    "description": description
                }
            }
        )

        print("Transaction updated successfully!")

        return redirect(url_for("home"))

    # Display edit form
    return render_template(
        "edit_transaction.html",
        transaction=transaction
    )



# Test MongoDB connection
@app.route("/test-db")
def test_db():
    try:
        client.admin.command("ping")
        return "MongoDB connected successfully!"
    except Exception as error:
        return f"Database connection failed: {error}", 500


# Run Flask application
if __name__ == "__main__":
    app.run(debug=True)



