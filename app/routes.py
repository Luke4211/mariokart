from flask import Blueprint, render_template, request, redirect, url_for, current_app
import sqlite3

main = Blueprint('main', __name__)

DATABASE = 'database/mariokart.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@main.route('/', methods=['GET', 'POST'])
def index():
    prior_tally = current_app.config['PRIOR_TALLY']

    conn = get_db_connection()

    # Handle form submission
    if request.method == 'POST':
        map_name = request.form['map']
        player1_score = int(request.form['player1_score'])
        player2_score = int(request.form['player2_score'])

        score = player1_score - player2_score
        # Insert new row into the database
        conn.execute(
            'INSERT INTO luke_liam (Map, Score) VALUES (?, ?)',
            (map_name, score,)
        )
        conn.commit()

    # Query running tally for each player
    total = conn.execute(
        'SELECT SUM(Score) FROM luke_liam'
    ).fetchone()[0] or 0

    total += prior_tally
    
    winner = "Tied"

    if total > 0:
        winner = "Luke"
    elif total < 0:
        winner = "Liam"
    return render_template(
        'index.html', total=total, curr_winner=winner
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
