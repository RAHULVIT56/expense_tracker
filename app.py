import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from expense_manager import ExpenseManager
from data_handler import DataHandler

# Set page configuration
st.set_page_config(
    page_title="Personal Expense Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'expenses_added' not in st.session_state:
    st.session_state.expenses_added = False

# Initialize data handler and expense manager with database connection
data_handler = DataHandler()
expense_manager = ExpenseManager(data_handler)

# Load predefined categories
categories = [
    "Food & Dining", 
    "Transportation", 
    "Housing", 
    "Utilities", 
    "Entertainment", 
    "Shopping",
    "Healthcare", 
    "Education", 
    "Travel", 
    "Personal Care", 
    "Gifts & Donations", 
    "Other"
]

# App title and description
st.title("Personal Expense Manager")
st.markdown("Track, categorize, and analyze your personal expenses")

# Create sidebar for adding expenses
with st.sidebar:
    st.header("Add New Expense")
    
    # Form for adding new expenses
    with st.form(key="add_expense_form"):
        date_input = st.date_input(
            "Date", 
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
        
        amount = st.number_input(
            "Amount", 
            min_value=0.01, 
            step=0.01, 
            format="%.2f"
        )
        
        category = st.selectbox("Category", categories)
        
        description = st.text_area("Description", height=100)
        
        submit_button = st.form_submit_button(label="Add Expense")
        
        if submit_button:
            if amount <= 0:
                st.error("Amount must be greater than zero.")
            elif not description.strip():
                st.error("Please provide a description.")
            else:
                # Add expense
                expense_manager.add_expense(
                    date=date_input.strftime("%Y-%m-%d"),
                    amount=amount,
                    category=category,
                    description=description
                )
                st.success("Expense added successfully!")
                st.session_state.expenses_added = True
                # Force a rerun to refresh the main page
                st.rerun()

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Expenses", "Statistics", "Filters"])

with tab1:
    st.header("Your Expenses")
    
    # Get expenses with IDs from database
    expenses_with_ids = expense_manager.get_expenses_with_ids()
    
    if expenses_with_ids.empty:
        st.info("No expenses recorded yet. Use the sidebar to add your first expense.")
    else:
        # Display expenses with IDs
        st.dataframe(
            expenses_with_ids,
            use_container_width=True,
            hide_index=True
        )
        
        # Delete expense functionality
        col1, col2 = st.columns([1, 4])
        with col1:
            expense_to_delete = st.number_input(
                "Row to delete", 
                min_value=0, 
                max_value=len(expenses_with_ids)-1 if not expenses_with_ids.empty else 0,
                step=1
            )
        with col2:
            if st.button("Delete Selected Expense"):
                if expense_manager.delete_expense(expense_to_delete):
                    st.success("Expense deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete expense.")

with tab2:
    st.header("Expense Statistics")
    
    expenses_df = expense_manager.get_expenses()
    
    if expenses_df.empty:
        st.info("No expenses recorded yet. Add some expenses to see statistics.")
    else:
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Expenses by Category")
            category_totals = expenses_df.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(
                category_totals, 
                values='Amount', 
                names='Category',
                title='Expense Distribution by Category',
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            st.subheader("Expenses Over Time")
            # Convert date strings to datetime
            expenses_df['Date'] = pd.to_datetime(expenses_df['Date'])
            
            # Group by date and sum the amounts
            daily_expenses = expenses_df.groupby('Date')['Amount'].sum().reset_index()
            
            fig_line = px.line(
                daily_expenses, 
                x='Date', 
                y='Amount',
                title='Daily Expenses Over Time',
                markers=True
            )
            st.plotly_chart(fig_line, use_container_width=True)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        total_spent = expenses_df['Amount'].sum()
        avg_expense = expenses_df['Amount'].mean()
        max_expense = expenses_df['Amount'].max()
        
        metric_cols = st.columns(3)
        metric_cols[0].metric("Total Spent", f"${total_spent:.2f}")
        metric_cols[1].metric("Average Expense", f"${avg_expense:.2f}")
        metric_cols[2].metric("Largest Expense", f"${max_expense:.2f}")
        
        # Top spending categories
        st.subheader("Top Spending Categories")
        top_categories = category_totals.sort_values('Amount', ascending=False).head(5)
        fig_bar = px.bar(
            top_categories,
            x='Category',
            y='Amount',
            title='Top 5 Spending Categories',
            color='Category'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.header("Filter Expenses")
    
    expenses_df = expense_manager.get_expenses()
    
    if expenses_df.empty:
        st.info("No expenses recorded yet. Add some expenses to use filters.")
    else:
        # Create filter options
        st.subheader("Filter Options")
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            # Get min and max dates from the dataset
            expenses_df['Date'] = pd.to_datetime(expenses_df['Date'])
            min_date = expenses_df['Date'].min().date()
            max_date = expenses_df['Date'].max().date()
            
            start_date = st.date_input(
                "Start Date",
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )
        
        # Category filter
        selected_categories = st.multiselect(
            "Categories",
            options=categories,
            default=[]
        )
        
        # Amount range filter
        min_amount = float(expenses_df['Amount'].min())
        max_amount = float(expenses_df['Amount'].max())
        
        # Make sure min and max are different to avoid slider error
        if min_amount == max_amount:
            max_amount += 1.0
            
        amount_range = st.slider(
            "Amount Range ($)",
            min_value=min_amount,
            max_value=max_amount,
            value=[min_amount, max_amount],
            step=1.0
        )
        
        # Apply filters
        filtered_df = expense_manager.filter_expenses(
            start_date=start_date,
            end_date=end_date,
            categories=selected_categories if selected_categories else None,
            min_amount=amount_range[0],
            max_amount=amount_range[1]
        )
        
        # Display filtered results
        st.subheader("Filtered Results")
        
        if filtered_df.empty:
            st.info("No expenses match your filter criteria.")
        else:
            st.dataframe(filtered_df, use_container_width=True)
            
            # Summary of filtered results
            st.metric("Total Filtered Amount", f"${filtered_df['Amount'].sum():.2f}")
            
            # Download filtered data as CSV
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv,
                file_name="filtered_expenses.csv",
                mime="text/csv"
            )
