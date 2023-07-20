
from app import app
from flask import render_template, redirect, request, url_for
import pandas as pd
import sqlalchemy as db
import urllib.parse

# Configuration for serving static files
app.static_url_path = '/static'


@app.route("/")
@app.route("/index")
def home():
    title = ""
    return render_template("index.html", title=title)


@app.route("/lifespan/pub")
def pub():
    title = "Publication List"
    return render_template("pub.html", title=title)


@app.route("/lifespan/pub/data")
def pub_data():
    sql = "SELECT * FROM manuscript_table ORDER BY year"
    engine = db.create_engine("sqlite:///citp-portal.db")
    table = pd.read_sql(sql, engine)
    return table.reset_index().to_json(orient="records")


@app.route("/lifespan/strain")
def strain():
    title = "Strains"
    return render_template("strain.html", title=title)

@app.route("/lifespan/strain/data")
def strain_data():
    sql = "SELECT * FROM all_strains_table ORDER BY strain_name"
    engine = db.create_engine("sqlite:///dbs/citp.db")
    table = pd.read_sql(sql, engine)
    return table.reset_index().to_json(orient="records")