#!/usr/bin/env python3
"""
Personal Finance Tracker
A comprehensive tool for managing personal finances with expense tracking,
budget management, and financial insights.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics

class Transaction:
    """Represents a single financial transaction"""
    
    def __init__(self, amount: float, category: str, description: str, 
                 transaction_type: str = "expense", date: Optional[str] = None):
        self.id = datetime.now().timestamp()
        self.amount = abs(amount)  # Store as positive, type determines sign
        self.category = category.lower()
        self.description = description
        self.type = transaction_type.lower()  # 'income' or 'expense'
        self.date = date or datetime.now().strftime("%Y-%m-%d")
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'amount': self.amount,
            'category': self.category,
            'description': self.description,
            'type': self.type,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        transaction = cls(
            amount=data['amount'],
            category=data['category'],
            description=data['description'],
            transaction_type=data['type'],
            date=data['date']
        )
        transaction.id = data['id']
        return transaction

class FinanceTracker:
    """Main finance tracker class"""
    
    def __init__(self, data_file: str = "finance_data.json"):
        self.data_file = data_file
        self.transactions: List[Transaction] = []
        self.budgets: Dict[str, float] = {}
        self.load_data()
    
    def load_data(self):
        """Load data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.transactions = [Transaction.from_dict(t) for t in data.get('transactions', [])]
                    self.budgets = data.get('budgets', {})
            except (json.JSONDecodeError, KeyError):
                print("Warning: Could not load existing data. Starting fresh.")
    
    def save_data(self):
        """Save data to JSON file"""
        data = {
            'transactions': [t.to_dict() for t in self.transactions],
            'budgets': self.budgets
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_transaction(self, amount: float, category: str, description: str, 
                       transaction_type: str = "expense"):
        """Add a new transaction"""
        transaction = Transaction(amount, category, description, transaction_type)
        self.transactions.append(transaction)
        self.save_data()
        print(f"✅ Added {transaction_type}: ${amount:.2f} for {category}")
    
    def set_budget(self, category: str, amount: float):
        """Set a budget for a category"""
        self.budgets[category.lower()] = amount
        self.save_data()
        print(f"💰 Budget set for {category}: ${amount:.2f}")
    
    def get_transactions_by_period(self, days: int = 30) -> List[Transaction]:
        """Get transactions from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [t for t in self.transactions 
                if datetime.strptime(t.date, "%Y-%m-%d") >= cutoff_date]
    
    def get_spending_by_category(self, days: int = 30) -> Dict[str, float]:
        """Get spending breakdown by category"""
        transactions = self.get_transactions_by_period(days)
        spending = {}
        
        for transaction in transactions:
            if transaction.type == "expense":
                spending[transaction.category] = spending.get(transaction.category, 0) + transaction.amount
        
        return dict(sorted(spending.items(), key=lambda x: x[1], reverse=True))
    
    def get_income_vs_expenses(self, days: int = 30) -> Dict[str, float]:
        """Calculate total income vs expenses"""
        transactions = self.get_transactions_by_period(days)
        
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expenses = sum(t.amount for t in transactions if t.type == "expense")
        
        return {
            'income': total_income,
            'expenses': total_expenses,
            'net': total_income - total_expenses
        }
    
    def check_budgets(self) -> Dict[str, Dict[str, float]]:
        """Check budget status for all categories"""
        spending = self.get_spending_by_category()
        budget_status = {}
        
        for category, budget_amount in self.budgets.items():
            spent = spending.get(category, 0)
            remaining = budget_amount - spent
            percentage = (spent / budget_amount) * 100 if budget_amount > 0 else 0
            
            budget_status[category] = {
                'budget': budget_amount,
                'spent': spent,
                'remaining': remaining,
                'percentage': percentage
            }
        
        return budget_status
    
    def get_financial_insights(self, days: int = 30) -> Dict:
        """Generate financial insights and recommendations"""
        transactions = self.get_transactions_by_period(days)
        
        if not transactions:
            return {"message": "No transactions found for the specified period."}
        
        expenses = [t.amount for t in transactions if t.type == "expense"]
        income = [t.amount for t in transactions if t.type == "income"]
        
        insights = {
            'period_days': days,
            'total_transactions': len(transactions),
            'average_expense': statistics.mean(expenses) if expenses else 0,
            'largest_expense': max(expenses) if expenses else 0,
            'smallest_expense': min(expenses) if expenses else 0,
            'most_expensive_category': '',
            'recommendations': []
        }
        
        # Find most expensive category
        spending_by_category = self.get_spending_by_category(days)
        if spending_by_category:
            insights['most_expensive_category'] = max(spending_by_category, 
                                                    key=spending_by_category.get)
        
        # Generate recommendations
        income_vs_expenses = self.get_income_vs_expenses(days)
        
        if income_vs_expenses['net'] < 0:
            insights['recommendations'].append("⚠️ You're spending more than you earn. Consider reducing expenses.")
        
        if income_vs_expenses['expenses'] > income_vs_expenses['income'] * 0.8:
            insights['recommendations'].append("💡 You're spending 80%+ of your income. Try to save more.")
        
        # Budget warnings
        budget_status = self.check_budgets()
        for category, status in budget_status.items():
            if status['percentage'] > 90:
                insights['recommendations'].append(f"🚨 You've exceeded 90% of your {category} budget!")
            elif status['percentage'] > 75:
                insights['recommendations'].append(f"⚠️ You're at {status['percentage']:.1f}% of your {category} budget.")
        
        return insights

def print_separator():
    print("=" * 50)

def main_menu():
    """Display main menu and handle user input"""
    tracker = FinanceTracker()
    
    while True:
        print_separator()
        print("💰 PERSONAL FINANCE TRACKER 💰")
        print_separator()
        print("1. Add Income")
        print("2. Add Expense")
        print("3. Set Budget")
        print("4. View Spending by Category")
        print("5. View Income vs Expenses")
        print("6. Check Budget Status")
        print("7. View Financial Insights")
        print("8. View Recent Transactions")
        print("9. Exit")
        print_separator()
        
        try:
            choice = input("Choose an option (1-9): ").strip()
            
            if choice == '1':
                amount = float(input("Enter income amount: $"))
                category = input("Enter income category (e.g., salary, freelance): ")
                description = input("Enter description: ")
                tracker.add_transaction(amount, category, description, "income")
            
            elif choice == '2':
                amount = float(input("Enter expense amount: $"))
                category = input("Enter expense category (e.g., food, transportation): ")
                description = input("Enter description: ")
                tracker.add_transaction(amount, category, description, "expense")
            
            elif choice == '3':
                category = input("Enter category name: ")
                amount = float(input(f"Enter budget amount for {category}: $"))
                tracker.set_budget(category, amount)
            
            elif choice == '4':
                days = int(input("Enter number of days to analyze (default 30): ") or "30")
                spending = tracker.get_spending_by_category(days)
                print(f"\n📊 SPENDING BY CATEGORY (Last {days} days)")
                print("-" * 40)
                if spending:
                    for category, amount in spending.items():
                        print(f"{category.capitalize()}: ${amount:.2f}")
                else:
                    print("No expenses found.")
            
            elif choice == '5':
                days = int(input("Enter number of days to analyze (default 30): ") or "30")
                summary = tracker.get_income_vs_expenses(days)
                print(f"\n💵 INCOME VS EXPENSES (Last {days} days)")
                print("-" * 40)
                print(f"Total Income: ${summary['income']:.2f}")
                print(f"Total Expenses: ${summary['expenses']:.2f}")
                print(f"Net Amount: ${summary['net']:.2f}")
                if summary['net'] >= 0:
                    print("✅ You're in the green!")
                else:
                    print("⚠️ You're spending more than you earn!")
            
            elif choice == '6':
                budget_status = tracker.check_budgets()
                print("\n🎯 BUDGET STATUS")
                print("-" * 40)
                if budget_status:
                    for category, status in budget_status.items():
                        print(f"\n{category.capitalize()}:")
                        print(f"  Budget: ${status['budget']:.2f}")
                        print(f"  Spent: ${status['spent']:.2f}")
                        print(f"  Remaining: ${status['remaining']:.2f}")
                        print(f"  Used: {status['percentage']:.1f}%")
                        
                        if status['percentage'] > 100:
                            print("  Status: 🚨 OVER BUDGET")
                        elif status['percentage'] > 75:
                            print("  Status: ⚠️ WARNING")
                        else:
                            print("  Status: ✅ ON TRACK")
                else:
                    print("No budgets set.")
            
            elif choice == '7':
                days = int(input("Enter number of days to analyze (default 30): ") or "30")
                insights = tracker.get_financial_insights(days)
                print(f"\n📈 FINANCIAL INSIGHTS (Last {days} days)")
                print("-" * 40)
                
                if "message" in insights:
                    print(insights["message"])
                else:
                    print(f"Total Transactions: {insights['total_transactions']}")
                    print(f"Average Expense: ${insights['average_expense']:.2f}")
                    print(f"Largest Expense: ${insights['largest_expense']:.2f}")
                    print(f"Most Expensive Category: {insights['most_expensive_category'].capitalize()}")
                    
                    if insights['recommendations']:
                        print("\n🔍 RECOMMENDATIONS:")
                        for rec in insights['recommendations']:
                            print(f"  {rec}")
                    else:
                        print("\n✅ Your finances look healthy!")
            
            elif choice == '8':
                days = int(input("Enter number of days to show (default 7): ") or "7")
                recent_transactions = tracker.get_transactions_by_period(days)
                print(f"\n📋 RECENT TRANSACTIONS (Last {days} days)")
                print("-" * 60)
                
                if recent_transactions:
                    for t in sorted(recent_transactions, key=lambda x: x.date, reverse=True):
                        sign = "+" if t.type == "income" else "-"
                        print(f"{t.date} | {sign}${t.amount:.2f} | {t.category.capitalize()} | {t.description}")
                else:
                    print("No recent transactions found.")
            
            elif choice == '9':
                print("💾 Saving data and exiting...")
                tracker.save_data()
                print("👋 Thank you for using Personal Finance Tracker!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
        
        except ValueError:
            print("❌ Invalid input. Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\n💾 Saving data and exiting...")
            tracker.save_data()
            break
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_menu()
