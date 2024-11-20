from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, Flask, Response
import sqlite3
from datetime import datetime
from scipy.stats import norm
import numpy as np
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
import os


main = Blueprint('main', __name__)

DATABASE = 'database/mariokart.db'
MAIN_TABLE = 'luke_liam'
CURR_DIR = os.getcwd()
EXPORT_FILE = os.path.join(CURR_DIR, 'database', 'archive', 'luke_liam_snapshot_')




def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def fit_norm(distribution):
    score_margins = np.array(distribution)

    mu, sigma = norm.fit(score_margins)

    return mu, sigma


def get_american_odds(prob):
    if prob < 0.5:
        odds = int((100 * ((1-prob)/prob)))
        odds = f"+{odds}"
    else:
        odds = int((-100 * (prob/(1-prob))))
        odds = f"{odds}"

    return odds


def get_handicap_odds(handicap, distribution=None, mu=None, sigma=None):
    if distribution is not None:
        mu, sigma = fit_norm(distribution)

    if handicap > 0:
        prob = 1 - norm.cdf(handicap, loc=mu, scale=sigma)
    elif handicap < 0:
        prob = norm.cdf(handicap, loc=mu, scale=sigma)

    return get_american_odds(prob)


def get_many_odds(distribution, margin_array):
    rtn = []

    mu, sigma = fit_norm(distribution)

    for margin in margin_array:
        rtn.append(
            {
                "margin": margin,
                "p1_odds": get_handicap_odds(margin, mu=mu, sigma=sigma),
                "p2_odds": get_handicap_odds((-1)*margin, mu=mu, sigma=sigma)
            }
        )
    return rtn


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


@main.route('/', methods=['GET', 'POST'])
def index():
    prior_tally = current_app.config['PRIOR_TALLY']

    conn = get_db_connection()

    cups = conn.execute('''
        SELECT id, name
        FROM maps
        ORDER BY SUBSTR(id, 1, 1), CAST(SUBSTR(id, 2) AS INTEGER)
    ''').fetchall()

    # Handle form submission
    if request.method == 'POST':
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # map_name = request.form['map']
        selected_cup = request.form['cup']
        try:
            player1_score = int(request.form['player1_score'])
            player2_score = int(request.form['player2_score'])

            score = player1_score - player2_score
            # Insert new row into the database
            conn.execute(
                'INSERT INTO luke_liam (Map, Player1_Score, Player2_Score, Score, timestamp) VALUES (?, ?, ?, ?, ?)',
                (selected_cup, player1_score, player2_score, score, current_time)
            )
            conn.commit()
        except ValueError:
            return render_template('index.html', error="Scores must be numeric.", cups=cups)

    # Query running tally for each player
    total = conn.execute(
        'SELECT SUM(Score) FROM luke_liam'
    ).fetchone()[0] or 0

    num_games = conn.execute(
        'SELECT COUNT(*) FROM luke_liam'
    ).fetchone()[0] or 0

    avg_score = 0
    
    if num_games > 0:
        avg_score = total/num_games
        avg_score = f"{avg_score:.3f}"

    total += prior_tally
    
    winner = "Tied"

    if total > 0:
        winner = "Luke"
    elif total < 0:
        winner = "Liam"
    
    odds = get_many_odds(get_score_margins(), [1, 3, 5, 10, 15, 20, 25, 30])
    conn.close()
    return render_template(
        'index.html',
        total=total,
        curr_winner=winner,
        avg_score=avg_score,
        num_games=num_games,
        cups=cups,
        odds=odds
    )

@main.route('/graph')
def graph():
    prior_tally = current_app.config['PRIOR_TALLY']
    conn = get_db_connection()

    # Query cumulative scores
    rows = conn.execute('SELECT Score FROM luke_liam').fetchall()
    conn.close()

    # Calculate running tally
    cumulative_sum = prior_tally
    cumulative_scores = []
    for row in rows:
        cumulative_sum += row['Score']
        cumulative_scores.append(cumulative_sum)

    # Prepare data for the graph
    x_labels = list(range(1, len(cumulative_scores) + 1))  # Game numbers

    return render_template(
        'graph.html',
        x_labels=x_labels,
        cumulative_scores=cumulative_scores)


@main.route('/by-cup', methods=['GET'])
def by_cup():
    conn = get_db_connection()

    # Fetch total scores for each cup
    cup_scores = conn.execute('''
        SELECT 
            maps.name AS cup_name,
            SUM(luke_liam.score) AS total_score,
            COUNT(luke_liam.id) AS race_count
        FROM luke_liam
        JOIN maps ON luke_liam.map = maps.id
        WHERE luke_liam.map != 'N'
        GROUP BY maps.id, maps.name
        ORDER BY total_score DESC
    ''').fetchall()

    player1_best = conn.execute('''
        SELECT
            maps.id AS map_id,
            maps.name AS map_name,
            SUM(luke_liam.score) AS total_score,
            COUNT(luke_liam.id) AS times_played
        FROM luke_liam
        JOIN maps ON luke_liam.map = maps.id
        WHERE luke_liam.map != 'N'
        GROUP BY maps.name
        ORDER BY total_score DESC
        LIMIT 1;
    ''').fetchone()

    player2_best = conn.execute('''
        SELECT 
            maps.id AS map_id,
            maps.name AS map_name,
            SUM(luke_liam.score) AS total_score,
            COUNT(luke_liam.id) AS times_played
        FROM luke_liam
        JOIN maps ON luke_liam.map = maps.id
        WHERE luke_liam.map != 'N'
        GROUP BY maps.name
        ORDER BY total_score ASC
        LIMIT 1;
    ''').fetchone()


    # Get dropdown options
    dropdown_options = conn.execute('''
        SELECT DISTINCT luke_liam.map, maps.id AS map_id, maps.name AS cup_name
        FROM luke_liam
        JOIN maps ON luke_liam.map = maps.id
        WHERE luke_liam.map != 'N'
    ''').fetchall()

    # Default to the first map in the dropdown
    default_map = dropdown_options[0]['map'] if dropdown_options else None

    # Query cumulative score for the default map
    cumulative_score = None
    score_history = []
    if default_map:
        rows = conn.execute('''
            SELECT SUM(score) AS cumulative_score
            FROM luke_liam
            WHERE map = ?
        ''', (default_map,)).fetchall()

        cumulative_score = rows[0]['cumulative_score']

        # Query score history for the graph
        history_rows = conn.execute('''
            SELECT id, score
            FROM luke_liam
            WHERE map = ?
            ORDER BY id
        ''', (default_map,)).fetchall()

        cumulative_sum = 0
        for row in history_rows:
            cumulative_sum += row['score']
            score_history.append(cumulative_sum)

    conn.close()

    return render_template(
        'by_cup.html',
        player1_best=player1_best,
        player2_best=player2_best,
        dropdown_options=dropdown_options,
        default_map=default_map,
        cumulative_score=cumulative_score,
        score_history=score_history,
        cup_scores=cup_scores
    )


@main.route('/archive', methods=['POST'])
def archive_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Query to select all data from the table
    cursor.execute(f"SELECT * FROM {MAIN_TABLE}")
    rows = cursor.fetchall()

    # Get column names
    column_names = [description[0] for description in cursor.description]

    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # Write to CSV
    with open(f"{EXPORT_FILE}{current_time}.csv", 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(column_names)  # Write header
        writer.writerows(rows)  # Write data

    conn.close()
    print(f"Snapshot of '{MAIN_TABLE}' exported to {EXPORT_FILE}")
    return redirect(url_for('main.index'))


@main.route('/by-cup/data', methods=['GET'])
def get_map_data():
    selected_map_id = request.args.get('map')
    conn = get_db_connection()

    

    # Calculate cumulative score for the map
    cumulative_score_row = conn.execute('''
        SELECT SUM(score) AS total_score
        FROM luke_liam
        WHERE map = ?
    ''', (selected_map_id,)).fetchone()

    cumulative_score = cumulative_score_row['total_score'] if cumulative_score_row else 0

    # Get score history for the graph
    rows = conn.execute('''
        SELECT id, score
        FROM luke_liam
        WHERE map = ?
        ORDER BY id
    ''', (selected_map_id,)).fetchall()

    cumulative_sum = 0
    score_history = []
    for row in rows:
        cumulative_sum += row['score']
        score_history.append(cumulative_sum)

    margins = [1, 3, 5, 10, 15, 20, 25, 30]
    score_margins = [row['score'] for row in rows]  # List of individual scores
    odds = get_many_odds(score_margins, margins)

    conn.close()

    response = {
        'cumulative_score': cumulative_score,
        'score_history': score_history
    }
    print(response) 

    return jsonify({
        'cumulative_score': cumulative_score,
        'score_history': score_history,
        'odds': odds
    })

@main.route('/plot.png')
def plot_png():

    score_margins = get_score_margins()
    mu, sigma = fit_norm(score_margins)

    # Generate x values and PDF
    x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 1000)
    pdf = norm.pdf(x, loc=mu, scale=sigma)

    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, pdf, label=f'Normal Distribution\nμ={mu:.3f}, σ={sigma:.3f}')
    ax.fill_between(x, pdf, alpha=0.3, color='blue')
    ax.set_title('Normal Distribution Curve')
    ax.set_xlabel('Score Margin')
    ax.set_ylabel('Probability Density')
    ax.legend(loc='upper left')
    ax.grid()

    # Save the plot to a BytesIO object
    output = io.BytesIO()
    plt.savefig(output, format='png', bbox_inches='tight')
    output.seek(0)
    plt.close(fig)  # Close the figure to free memory

    # Return the image as a response
    return Response(output.getvalue(), mimetype='image/png')