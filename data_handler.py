import pandas as pd
import os
import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Dict, List, Any

class DataHandler:
    """
    Class responsible for data persistence, loading and saving expense data.
    Uses PostgreSQL database for storage.
    """
    
    def __init__(self):
        """
        Initialize the DataHandler with database connection.
        """
        # Get database connection from environment variables
        self.db_url = os.environ.get('DATABASE_URL', '')
        if self.db_url:
            self.engine = create_engine(self.db_url)
        else:
            raise ValueError("DATABASE_URL environment variable not set")
        
    def load_data(self) -> pd.DataFrame:
        """
        Load expense data from the database.
        
        Returns:
            pandas.DataFrame: DataFrame containing expense data
        """
        try:
            # Query the expenses table
            query = "SELECT * FROM expenses ORDER BY date DESC"
            df = pd.read_sql(query, self.engine)
            
            # Rename id column and set expected column order
            if 'id' in df.columns:
                # Drop the id column for consistency with old interface
                df = df[['date', 'amount', 'category', 'description']]
            
            # Create a dictionary for column renaming
            rename_dict: Dict[str, str] = {
                'date': 'Date',
                'amount': 'Amount',
                'category': 'Category',
                'description': 'Description'
            }
            
            # Rename columns for consistency with old interface
            df = df.rename(columns=rename_dict)
            
            return df
            
        except Exception as e:
            # If there's an error, return an empty DataFrame
            print(f"Error loading data: {e}")
            empty_data: Dict[str, List[Any]] = {"Date": [], "Amount": [], "Category": [], "Description": []}
            return pd.DataFrame(empty_data)
    
    def save_data(self, df):
        """
        Save expense data to the database.
        This completely replaces the data in the database with the data in the DataFrame.
        
        Args:
            df (pandas.DataFrame): DataFrame containing expense data
            
        Returns:
            bool: True if the data was saved successfully
        """
        try:
            # Ensure all expected columns exist
            expected_columns = ['Date', 'Amount', 'Category', 'Description']
            for col in expected_columns:
                if col not in df.columns:
                    raise ValueError(f"Missing column '{col}' in the data to save")
            
            # Create a copy of the dataframe with lowercase column names for SQL
            df_sql = df.copy()
            df_sql.columns = [col.lower() for col in df_sql.columns]
            
            # Clear existing data
            with self.engine.connect() as connection:
                connection.execute(text("TRUNCATE TABLE expenses"))
                connection.commit()
            
            # Save data to database
            df_sql.to_sql('expenses', self.engine, if_exists='append', index=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
            
    def add_expense(self, date, amount, category, description):
        """
        Add a single expense to the database.
        
        Args:
            date (str): Date of the expense
            amount (float): Amount of the expense
            category (str): Category of the expense
            description (str): Description of the expense
            
        Returns:
            bool: True if the expense was added successfully
        """
        try:
            query = text("""
                INSERT INTO expenses (date, amount, category, description)
                VALUES (:date, :amount, :category, :description)
            """)
            
            with self.engine.connect() as connection:
                connection.execute(query, {
                    'date': date,
                    'amount': amount,
                    'category': category,
                    'description': description
                })
                connection.commit()
                
            return True
        
        except Exception as e:
            print(f"Error adding expense: {e}")
            return False
            
    def delete_expense_by_id(self, expense_id):
        """
        Delete an expense by its ID.
        
        Args:
            expense_id (int): ID of the expense to delete
            
        Returns:
            bool: True if the expense was deleted successfully
        """
        try:
            query = text("DELETE FROM expenses WHERE id = :id")
            
            with self.engine.connect() as connection:
                connection.execute(query, {'id': expense_id})
                connection.commit()
                
            return True
            
        except Exception as e:
            print(f"Error deleting expense: {e}")
            return False
