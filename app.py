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
        if seconds < 0: seconds += 86400 
        heures = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{heures}h{minutes:02d}"
    except: return "N/A"

def recherche_itineraires(tx, v_dep, v_arr, h_min, date_v, direct_only):
    hop_limit = "1" if direct_only else "1..2"
    query = f"""
    MATCH p = (d:Gare)-[:TRAJET*{hop_limit}]->(a:Gare)
    WHERE toUpper(d.ville) CONTAINS toUpper($v_dep) 
      AND toUpper(a.ville) CONTAINS toUpper($v_arr)
      AND ALL(r IN relationships(p) WHERE $date_v IN r.dates)
      AND (relationships(p)[0]).`heure départ` >= $h_min
      AND (size(relationships(p)) = 1 OR 
          (relationships(p)[1]).`heure départ` > (relationships(p)[0]).`heure arrivée`)
    RETURN 
        [r IN relationships(p) | {{
            no: r.`n°`, dep: r.`heure départ`, arr: r.`heure arrivée`,
            v_dep: startNode(r).ville, v_arr: endNode(r).ville
        }}] AS segments,
        size(relationships(p)) AS nb_segments
    ORDER BY (relationships(p)[0]).`heure départ` ASC
    """
    result = tx.run(query, v_dep=v_dep, v_arr=v_arr, h_min=h_min, date_v=date_v)
    return result.data()

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    params = {}
    if request.method == "POST":
        params = {
            "dep": request.form.get("dep"),
            "arr": request.form.get("arr"),
            "h_min": request.form.get("h_min"),
            "date_v": request.form.get("date_v"),
            "direct_only": request.form.get("direct_only") == "on"
        }
        with driver.session() as session:
            raw = session.execute_read(recherche_itineraires, params["dep"], params["arr"], 
                                       params["h_min"], params["date_v"], params["direct_only"])
            
            # --- FUSION PAR NUMÉRO DE TRAIN (ANTI-DOUBLONS) ---
            uniques = {}
            for iti in raw:
                # On identifie le trajet par le numéro du 1er train et son heure de départ
                train_id = f"{iti['segments'][0]['no']}-{iti['segments'][0]['dep']}"
                if train_id not in uniques:
                    iti['total_duree'] = calculer_duree(iti['segments'][0]['dep'], iti['segments'][-1]['arr'])
                    uniques[train_id] = iti
            
            results = list(uniques.values())
            
    return render_template("index.html", results=results, params=params)

if __name__ == "__main__":
    app.run(debug=True)