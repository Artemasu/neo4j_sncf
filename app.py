from flask import Flask, render_template, request
from neo4j import GraphDatabase
from nettoyage import preparer_donnees 
from datetime import datetime

app = Flask(__name__)

URI = "bolt://100.55.66.81"
AUTH = ("neo4j", "secrets-primes-weeks")
driver = GraphDatabase.driver(URI, auth=AUTH)

def calculer_duree(h_dep, h_arr):
    fmt = '%H:%M'
    try:
        tdelta = datetime.strptime(h_arr, fmt) - datetime.strptime(h_dep, fmt)
        seconds = tdelta.total_seconds()
        if seconds < 0: seconds += 86400  # Gestion des trajets arrivant le lendemain
        heures = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{heures}h{minutes:02d}"
    except:
        return "N/A"

def configurer_base(session):
    session.run("CREATE CONSTRAINT gare_iata IF NOT EXISTS FOR (g:Gare) REQUIRE g.code_iata IS UNIQUE")

def importer_donnees_opti(session, df_nodes, df_rels):
    query_nodes = "UNWIND $batch AS l MERGE (g:Gare {code_iata: l.iata}) SET g.ville = l.ville"
    session.run(query_nodes, batch=df_nodes.to_dict('records'))

    query_rels = """
    UNWIND $batch AS l
    MATCH (dep:Gare {code_iata: l['Origine IATA']})
    MATCH (arr:Gare {code_iata: l['Destination IATA']})
    CREATE (dep)-[:TRAJET {
        `n°`: l.TRAIN_NO,
        `heure départ`: l.Heure_depart,
        `heure arrivée`: l.Heure_arrivee,
        dates: l.DATE
    }]->(arr)
    """
    dict_rels = df_rels.to_dict('records')
    chunk_size = 5000
    for i in range(0, len(dict_rels), chunk_size):
        batch = dict_rels[i:i + chunk_size]
        session.run(query_rels, batch=batch)
    print("\nImportation terminée.")

def recherche_par_date(tx, v_dep, v_arr, h_min, date_v):
    query = """
    MATCH (d:Gare)-[r:TRAJET]->(a:Gare)
    WHERE toUpper(d.ville) CONTAINS toUpper($v_dep) 
      AND toUpper(a.ville) CONTAINS toUpper($v_arr) 
      AND r.`heure départ` >= $h_min
      AND $date_v IN r.dates
    RETURN r.`n°` AS train, r.`heure départ` AS dep, r.`heure arrivée` AS arr, 
           d.ville AS ville_dep, a.ville AS ville_arr
    ORDER BY r.`heure départ` ASC
    """
    result = tx.run(query, v_dep=v_dep, v_arr=v_arr, h_min=h_min, date_v=date_v)
    return result.data()

# --- PARTIE FLASK ---
@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        v_dep = request.form.get("dep")
        v_arr = request.form.get("arr")
        h_min = request.form.get("h_min")
        date_v = request.form.get("date_v")
        
        with driver.session() as session:
            raw_results = session.execute_read(recherche_par_date, v_dep, v_arr, h_min, date_v)
            for res in raw_results:
                res['duree'] = calculer_duree(res['dep'], res['arr'])
            results = raw_results
            
    return render_template("index.html", results=results)

if __name__ == "__main__":
    with driver.session() as session:
        nb_gares = session.run("MATCH (g:Gare) RETURN count(g) AS nb").single()["nb"]
        if nb_gares == 0:
            nodes, rels = preparer_donnees('tgvmax.csv')
            configurer_base(session)
            importer_donnees_opti(session, nodes, rels)
            
    app.run(debug=True)