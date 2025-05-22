import pandas as pd
from datetime import datetime
from data_handler import DataHandler

class ExpenseManager:
    """
    Class responsible for managing expenses, including adding, deleting, 
    filtering, and retrieving expense data.
    """
    
    def __init__(self, data_handler):
        """
        Initialize the ExpenseManager with a data handler.
        
        Args:
            data_handler: An instance of DataHandler to manage data persistence
        """
        self.data_handler = data_handler
        
    def add_expense(self, date, amount, category, description):
        """
        Add a new expense to the data.
        
        Args:
            date (str): Date of the expense in YYYY-MM-DD format
            amount (float): Amount spent
            category (str): Category of the expense
            description (str): Description of the expense
        
        Returns:
            bool: True if the expense was added successfully
        """
        # Validate inputs
        if not date or not amount or not category or not description:
            return False
        
        # Use the data handler's direct add method
        return self.data_handler.add_expense(
            date=date,
            amount=float(amount),
            category=category,
            description=description
        )
    
    def delete_expense(self, index):
        """
        Delete an expense by its index.
        
        Args:
            index (int): Index of the expense to delete
            
        Returns:
            bool: True if the expense was deleted successfully
        """
        # Get the expenses with IDs
        expenses_df = self.get_expenses_with_ids()
        
        if expenses_df.empty or index >= len(expenses_df):
            return False
        
        # Get the ID of the expense to delete
        expense_id = expenses_df.iloc[index]['ID']
        
        # Delete the expense by ID
        return self.data_handler.delete_expense_by_id(expense_id)
    
    def get_expenses(self):
        """
        Get all expenses as a DataFrame (without IDs).
        
        Returns:
            pandas.DataFrame: DataFrame containing all expenses
        """
        return self.data_handler.load_data()
    
    def get_expenses_with_ids(self):
        """
        Get all expenses as a DataFrame with IDs from the database.
        
        Returns:
            pandas.DataFrame: DataFrame containing all expenses with IDs
        """
        try:
            # Query the expenses table with IDs
            query = "SELECT id as ID, date as Date, amount as Amount, category as Category, description as Description FROM expenses ORDER BY date DESC"
            df = pd.read_sql(query, self.data_handler.engine)
            return df
            
        except Exception as e:
            print(f"Error loading data with IDs: {e}")
            # Create empty DataFrame with proper column types
            empty_data = {
                "ID": [], 
                "Date": [], 
                "Amount": [], 
                "Category": [], 
                "Description": []
            }
            return pd.DataFrame(empty_data)
    
    def filter_expenses(self, start_date=None, end_date=None, categories=None, 
                        min_amount=None, max_amount=None):
        """
        Filter expenses based on various criteria.
        
        Args:
            start_date (datetime.date, optional): Filter expenses from this date
            end_date (datetime.date, optional): Filter expenses until this date
            categories (list, optional): List of categories to include
            min_amount (float, optional): Minimum amount
            max_amount (float, optional): Maximum amount
            
        Returns:
            pandas.DataFrame: Filtered expenses
        """
        expenses_df = self.get_expenses()
        
        if expenses_df.empty:
            return expenses_df
            
        # Make a copy to avoid modifying the original
        filtered_df = expenses_df.copy()
        
        # Convert Date column to datetime if it's not already
        if not pd.api.types.is_datetime64_dtype(filtered_df['Date']):
            filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])
        
        # Apply date filters
        if start_date:
            filtered_df = filtered_df[filtered_df['Date'] >= pd.Timestamp(start_date)]
        
        if end_date:
            filtered_df = filtered_df[filtered_df['Date'] <= pd.Timestamp(end_date)]
        
        # Apply category filter
        if categories and len(categories) > 0:
            filtered_df = filtered_df[filtered_df['Category'].isin(categories)]
        
        # Apply amount filters
        if min_amount is not None:
            filtered_df = filtered_df[filtered_df['Amount'] >= min_amount]
        
        if max_amount is not None:
            filtered_df = filtered_df[filtered_df['Amount'] <= max_amount]
        
        return filtered_df
    
    def get_total_by_category(self):
        """
        Get total expenses grouped by category.
        
        Returns:
            pandas.DataFrame: Total expenses by category
        """
        expenses_df = self.get_expenses()
        
        if expenses_df.empty:
            return pd.DataFrame(columns=['Category', 'Total'])
            
        category_totals = expenses_df.groupby('Category')['Amount'].sum().reset_index()
        category_totals = category_totals.rename(columns={'Amount': 'Total'})
        
        return category_totals.sort_values(by='Total', ascending=False)
