import numpy as np
from scipy.stats import shapiro, anderson
import sqlite3

DATABASE = 'database/mariokart.db'




def get_score_margins(cup=None):
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # TODO: Add code to check if nup not none, and then filter the query
    # to pull rows only for that cup

    # Query to fetch all score margins
    where_clause = ''
    if cup is not None:
        f"WHERE Map = '{cup}' "

    query = f"SELECT Score FROM luke_liam {where_clause};"
    cursor.execute(query)

    # Fetch all rows and convert to a list
    margins = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return margins


def shapiro_test():
    # Step 1: Generate sample data (e.g., normal distribution)
    #data = np.random.normal(loc=0, scale=1, size=100)  # Mean=0, Std Dev=1, 100 samples
    print("Shapiro Test:")
    data = get_score_margins()

    # Step 2: Perform Shapiro-Wilk test
    stat, p = shapiro(data)

    # Step 3: Interpret the result
    alpha = 0.05  # Significance level
    if p > alpha:
        print(f"Data appears to be normally distributed (p = {p:.5f}).")
    else:
        print(f"Data does not appear to be normally distributed (p = {p:.5f}).")


def anderson_test():
    # Perform Anderson-Darling test
    data = get_score_margins()
    result = anderson(data, dist='norm')

    # Output results
    print("Anderson-Darling Test:")
    print(f"Statistic: {result.statistic}")
    print("Critical values and significance levels:")
    for cv, sig in zip(result.critical_values, result.significance_level):
        print(f"Critical Value: {cv}, Significance Level: {sig}%")

    # Interpretation
    if result.statistic < result.critical_values[2]:  # 5% significance level
        print("The data appears to be normally distributed (at 5% significance).")
    else:
        print("The data does not appear to be normally distributed (at 5% significance).")


shapiro_test()

anderson_test()