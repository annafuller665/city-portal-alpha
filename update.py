
from pathlib import Path
import os
import pandas as pd
import psycopg2
import sqlite3

PORT = 5432


def update_db(dbname):

    conn = psycopg2.connect(
        dbname=dbname, user=os.environ["DB_USER"], password=os.environ["DB_PWD"], host=os.environ["DB_HOST"], port=PORT
    )

    c = conn.cursor()

    # STRAINS
    query = (
        "SELECT strain_id, strain_name, species_name FROM all_strains_table"
    )
    c.execute(query)
    res = c.fetchall()
    all_strains_table = pd.DataFrame.from_records(
        res,
        columns=["strain_id", "strain_name", "species_name"],
    )


    # PUBLICATIONS
    query = (
        "SELECT manuscript_id, doi, author, journal, year, study_phase FROM manuscript_table"
    )

    c.execute(query)
    res = c.fetchall()

    manuscript_table = pd.DataFrame.from_records(
        res,
        columns=["manuscript_id", "doi", "author", "journal", "year", "study_phase"],
    )


    # COMPOUNDS 

    query = (
        "SELECT comp_id, comp_name, comp_abbr, control_name FROM all_compounds_table"
    )

    c.execute(query)
    res = c.fetchall()

    all_compounds_table = pd.DataFrame.from_records(
        res,
        columns=["comp_id", "comp_name", "comp_abbr", "control_name"],
    )

    query = (
        "SELECT comp_id, alternate_comp_name FROM compound_reference_table"
    )
    
    c.execute(query)
    res = c.fetchall()

    compound_reference_table = pd.DataFrame.from_records(
        res,
        columns=["comp_id", "alternate_comp_names"],
    )

    compound_reference_table = compound_reference_table.groupby("comp_id").agg(
        {"alternate_comp_names": lambda x: ", ".join(x)}
    )

    all_compounds_table = all_compounds_table.merge(
        compound_reference_table, on="comp_id", how="left"
    )



    # EXPERIMENTS

    query = "SELECT experiment_id, experiment_name, experiment_type_name, lab_name, start_date, CONCAT(author, ' (', year,')') AS reference, experiment_complete, validated AS experiment_validated FROM experiment_table LEFT JOIN manuscript_table ON experiment_table.manuscript_id=manuscript_table.manuscript_id"

    if dbname != "citp-manuscript":
        query = "SELECT experiment_id, experiment_name, experiment_type_name, lab_name, start_date, NULL AS reference, experiment_complete, validated AS experiment_validated FROM experiment_table"

    c.execute(query)
    res = c.fetchall()

    all_experiments = pd.DataFrame.from_records(
        res,
        columns=[
            "experiment_id",
            "experiment_name",
            "experiment_type_name",
            "lab_name",
            "start_date",
            "reference",
            "experiment_complete",
            "experiment_validated",
        ],
    )

    # PLATES

    query = "SELECT plate_table.plate_id, plate_table.plate_name, plate_table.tech_initial, experiment_table.experiment_id, all_strains_table.strain_name, all_strains_table.species_name, all_compounds_table.comp_id, all_compounds_table.comp_name, experimental_conditions_table.exp_cond_name, xreps.replicate_num, xcomps.concentration, xcomps.concentration_units, plate_table.validated AS plate_validated FROM plate_table, xstrainthaws, experiment_table, worm_thaws_table, all_strains_table, tech_table, xreps, xcomps, experimental_conditions_table, all_compounds_table WHERE (plate_table.xstrain_id = xstrainthaws.xstrain_id AND xstrainthaws.experiment_id = experiment_table.experiment_id AND xstrainthaws.worm_thaw_id = worm_thaws_table.worm_thaw_id AND worm_thaws_table.strain_id = all_strains_table.strain_id AND plate_table.tech_initial = tech_table.tech_initial AND plate_table.xrep_id = xreps.xrep_id AND xreps.xcomp_id = xcomps.xcomp_id AND xcomps.exp_cond_id = experimental_conditions_table.exp_cond_id AND xcomps.comp_id = all_compounds_table.comp_id) ORDER BY xreps.replicate_num, plate_table.xstrain_id, all_compounds_table.comp_name, xcomps.concentration, plate_table.plate_id"

    c.execute(query)
    res = c.fetchall()

    all_plates = pd.DataFrame.from_records(
        res,
        columns=[
            "plate_id",
            "plate_name",
            "tech_initial",
            "experiment_id",
            "strain_name",
            "species_name",
            "comp_id",
            "comp_name",
            "exp_cond_name",
            "replicate_num",
            "concentration",
            "concentration_units",
            "plate_validated",
        ],
    )

    # OBSERVATIONS

    query = "SELECT observation_table.observation_id, observation_table.observation_date, plate_table.plate_id, observation_table.alive, observation_table.dead, observation_table.censor, observation_table.lost, observation_table.bag, observation_table.extrusion, CONCAT(observation_table.lost, ' lost, ', observation_table.bag, ' bag, ', observation_table.extrusion, ' ext.') AS observation_reason, observation_table.notes AS observation_notes, observation_table.validated AS observation_validated FROM observation_table, plate_table, xstrainthaws, experiment_table, worm_thaws_table, all_strains_table, tech_table, xreps, xcomps, experimental_conditions_table, all_compounds_table WHERE (observation_table.plate_id = plate_table.plate_id AND plate_table.xstrain_id = xstrainthaws.xstrain_id AND xstrainthaws.experiment_id = experiment_table.experiment_id AND xstrainthaws.worm_thaw_id = worm_thaws_table.worm_thaw_id AND worm_thaws_table.strain_id = all_strains_table.strain_id AND plate_table.tech_initial = tech_table.tech_initial AND plate_table.xrep_id = xreps.xrep_id AND xreps.xcomp_id = xcomps.xcomp_id AND xcomps.exp_cond_id = experimental_conditions_table.exp_cond_id AND xcomps.comp_id = all_compounds_table.comp_id) ORDER BY plate_table.plate_id, observation_table.observation_date"

    c.execute(query)
    res = c.fetchall()

    all_observations = pd.DataFrame.from_records(
        res,
        columns=[
            "observation_id",
            "observation_date",
            "plate_id",
            "alive",
            "dead",
            "censor",
            "lost",
            "bag",
            "extrusion",
            "observation_reason",
            "observation_notes",
            "observation_validated",
        ],
    )

    # WORM RECORDS

    query = "SELECT t1.death_id, t1.observation_id, t1.indiv_death, t1.indiv_censor, t1.death_age, t2.death_age AS death_no_censor, t1.notes AS death_notes FROM (SELECT death_table.indiv_death, death_table.indiv_censor, observation_table.death_age, observation_table.notes, experiment_table.start_date, observation_table.observation_date, experiment_table.experiment_complete, experiment_table.validated, observation_table.validated, plate_table.validated, plate_table.plate_name, experiment_table.experiment_name, all_strains_table.strain_name, all_strains_table.species_name, tech_table.tech_name, experiment_table.lab_name, experiment_table.experiment_type_name, xreps.replicate_num, xcomps.concentration, xcomps.concentration_units, experimental_conditions_table.exp_cond_name, all_compounds_table.comp_name, death_table.death_id, observation_table.observation_id, plate_table.plate_id, experiment_table.experiment_id, observation_table.lost, observation_table.bag, observation_table.extrusion, all_compounds_table.comp_id FROM death_table, observation_table, plate_table, xstrainthaws, experiment_table, worm_thaws_table, all_strains_table, tech_table, xreps, xcomps, experimental_conditions_table, all_compounds_table WHERE (death_table.observation_id = observation_table.observation_id AND observation_table.plate_id = plate_table.plate_id AND plate_table.xstrain_id = xstrainthaws.xstrain_id AND xstrainthaws.experiment_id = experiment_table.experiment_id AND xstrainthaws.worm_thaw_id = worm_thaws_table.worm_thaw_id AND worm_thaws_table.strain_id = all_strains_table.strain_id AND plate_table.tech_initial = tech_table.tech_initial AND plate_table.xrep_id = xreps.xrep_id AND xreps.xcomp_id = xcomps.xcomp_id AND xcomps.exp_cond_id = experimental_conditions_table.exp_cond_id AND xcomps.comp_id = all_compounds_table.comp_id) ORDER BY plate_table.plate_id, observation_table.observation_date) t1 LEFT JOIN (SELECT observation_table.death_age, death_table.indiv_death, death_table.death_id FROM observation_table, death_table WHERE (observation_table.observation_id = death_table.observation_id AND death_table.indiv_death = 1)) t2 ON t1.death_id = t2.death_id ORDER BY t1.experiment_id, t1.plate_id, t1.observation_id, t1.death_id"

    c.execute(query)
    res = c.fetchall()

    all_worm_deaths = pd.DataFrame.from_records(
        res,
        columns=[
            "death_id",
            "observation_id",
            "indiv_death",
            "indiv_censor",
            "death_age",
            "death_no_censor",
            "death_notes",
        ],
    )

    c.close()
    conn.close()

    path = "citp-portal.db" 

    Path(path).touch()

    conn = sqlite3.connect(path)
    c = conn.cursor()

    all_compounds_table.to_sql(
        "all_compounds_table", conn, if_exists="replace", index=False
    )
    manuscript_table.to_sql(
        "manuscript_table", conn, if_exists="replace", index=False
    )
    all_experiments.to_sql("all_experiments", conn, if_exists="replace", index=False)
    all_plates.to_sql("all_plates", conn, if_exists="replace", index=False)
    all_observations.to_sql("all_observations", conn, if_exists="replace", index=False)
    all_worm_deaths.to_sql("all_worm_deaths", conn, if_exists="replace", index=False)
    all_strains_table.to_sql("all_strains_table", conn, if_exists="replace", index=False)
    c.close()
    conn.close()



update_db("citp-portal")
