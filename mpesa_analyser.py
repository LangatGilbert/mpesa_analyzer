#modules/packages required
import os

#for data manipulation/wrangling
import numpy as np
from numpy import int64
import pandas as pd

#for date manipulation
import datetime as datetime
import calendar

# Function to calculate missing values by column
def missing_values_table(df):
    #Total missing values 
    mis_val = df.isnull().sum()
    
    #percentage of missing values
    mis_val_percent = 100 * df.isnull().sum() / len(df)
    
    # Make a table with the results
    mis_val_table = pd.concat([mis_val,mis_val_percent], axis =1)
    
    # Rename the colums
    mis_val_table_ren_columns = mis_val_table.rename(
    columns = {0 : 'Missing Values', 1 : '% of Total Values'})
    
    # Sort the table by percentage of missing descending
    mis_val_table_ren_columns = mis_val_table_ren_columns[
        mis_val_table_ren_columns.iloc[:,1] != 0].sort_values(
        '% of Total Values', ascending=False).round(1)
    
    # Print some summary information
    # print("Your selected dataframe has " + str(df.shape[1])+ " columns.\n"
    #      "There are " + str(mis_val_table_ren_columns.shape[0])+
    #      " columns that have missing values.")
    
    # Return the dataframe with missing information
    return mis_val_table_ren_columns

#function for checking missing values per column

#Create a new function:
def num_missing(x):
    return sum(x.isnull())


def pdf_cleaner_wrangler(dfs):

    df = dfs[1]

    #no_tables = [len(dfs)]
    for i in range(2, len(dfs)):
        df_s = dfs[i]
        #print(df_s.shape)
        ##rename null headers
        if ((df_s.columns).isna().any() == True):
            df_s.columns = df_s.columns.fillna('null_column')
        else:
            pass
        
        # dropping columns with > 98% missing
        missing_df = missing_values_table(df_s)
        missing_columns = list(missing_df[missing_df['% of Total Values']> 98].index)
        #print('We will remove %d columns.' % len(missing_columns))
        #print(missing_columns)
        df_s.drop(missing_columns, axis =1, inplace=True)
        
        df = pd.DataFrame(np.concatenate([df.values, df_s.values]), columns=df.columns)

    #renaming df columns
    df.rename(columns = {'Receipt No.':'CODE','Completion Time':'TIME',
                        'Details':'DETAILS','Transaction\rStatus':'STATUS', 'Paid In':'MONEY IN', 
                        'Withdrawn':'MONEY OUT', 'Balance':'BALANCE'}, inplace = True)

    #drop row with null receipt number
    mpesa_df = df[df['CODE'].notna()] 


    #clean the text columns
    mpesa_df['DETAILS'] = mpesa_df['DETAILS'].str.replace('\r',' ')

    #filling null values in MONEY IN and MONEY OUT columns
    mpesa_df[['MONEY IN','MONEY OUT','BALANCE']] = mpesa_df[['MONEY IN','MONEY OUT','BALANCE']].fillna(0)

    #get string after dash
    receiptient = []
    for row in df.itertuples():
        new = row.DETAILS.split("-")
        receiptient.append(new[1] if 1 < len(new) else None)

    mpesa_df['RECIPIENT'] = receiptient

    #clean the receiver_desc columns
    mpesa_df['RECIPIENT'] = mpesa_df['RECIPIENT'].str.replace('\r',' ')

    #cleaning the numerical columns
    num_col = ['MONEY IN','MONEY OUT','BALANCE']
    for col in num_col:
        mpesa_df[col] = mpesa_df[col].replace(',', '',regex=True)
        mpesa_df[col] = pd.to_numeric(mpesa_df[col])
        
    mpesa_df['TIME']= pd.to_datetime(mpesa_df['TIME'])
    mpesa_df['DETAILS'] = mpesa_df['DETAILS'].astype(str)

    #extract year,month and quarter transaction
    mpesa_df['year'] = mpesa_df['TIME'].dt.year
    mpesa_df['month'] = mpesa_df['TIME'].dt.month
    mpesa_df['month'] = mpesa_df['month'].apply(lambda x: calendar.month_name[x])
    mpesa_df['quarter'] = mpesa_df['TIME'].dt.quarter

    mpesa_df['COHORT']= mpesa_df['year'].astype(str) + "_" + mpesa_df['month'].astype(str)

    #sorting df by date
    mpesa_df=mpesa_df.sort_values(by=['TIME'],ascending =True)

    #convert the negative MONEY OUT as positive
    mpesa_df['MONEY OUT'] = abs(mpesa_df['MONEY OUT'])


    #group the transactions
    text_group = []
    for row in mpesa_df.itertuples():
        if 'Funds Charge' in row.DETAILS:
            text_group.append('Charges')
        elif 'Business Payment from' in row.DETAILS:
            text_group.append('Business Payments')
        elif 'Loan Repayment' in row.DETAILS:
            text_group.append('Loan Repayment')
        elif 'Receive International Transfer From' in row.DETAILS:
            text_group.append('Received-International')
        elif 'Airtime' in row.DETAILS:
            text_group.append('Airtime')
        elif 'Customer Transfer to' in row.DETAILS:
            text_group.append('Sending')
        elif 'Customer Transfer Fuliza' in row.DETAILS:
            text_group.append('Fuliza')   
        elif 'Customer Withdrawal At' in row.DETAILS:
            text_group.append('Withdrawal')
        elif 'Withdrawal Charge' in row.DETAILS: 
            text_group.append('Charges')
        elif 'Buy Bundles' in row.DETAILS: 
            text_group.append('Buy Bundles')
        elif 'Pay Bill' in row.DETAILS:
            text_group.append('Pay Bills')
        elif 'Pay Bill Charge' in row.DETAILS:
            text_group.append('Charges')
        elif 'Merchant Payment' in row.DETAILS: 
            text_group.append('Merchant Payments')
        elif 'Funds received from' in row.DETAILS: 
            text_group.append('Received')
        elif 'OverDraft' in row.DETAILS: 
            text_group.append('Overdraft')
        elif 'Promotion Payment from' in row.DETAILS: 
            text_group.append('Promotion Payments')
        elif 'Deposit of Funds at ' in row.DETAILS: 
            text_group.append('Deposit')
        elif 'M-Shwari Deposit' in row.DETAILS: 
            text_group.append('M-Shwari Deposit')
        elif 'M-Shwari Withdraw' in row.DETAILS: 
            text_group.append('M-Shwari Withdraws')
        elif 'Pay Merchant Charge' in row.DETAILS: 
            text_group.append('Charges')
        elif 'Reversal' in row.DETAILS: 
            text_group.append('Reversal')
        elif 'M-Shwari Lock Deposit' in row.DETAILS: 
            text_group.append('M-Shwari Deposits')
        elif 'M-Shwari Loan Disburse' in row.DETAILS: 
            text_group.append('M-Shwari Loan')
        else :
            text_group.append('unclassified')
            
    mpesa_df['ACTIVITY'] = text_group

    #derive amount transacted
    mpesa_df['TOTAL AMOUNT'] = mpesa_df['MONEY OUT'] + mpesa_df['MONEY IN']

    return mpesa_df
            



