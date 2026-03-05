from flask import Flask, render_template, request
from neo4j import GraphDatabase
from datetime import datetime

app = Flask(__name__)

URI = "bolt://100.55.66.81"
AUTH = ("neo4j", "secrets-primes-weeks")
driver = GraphDatabase.driver(URI, auth=AUTH)

def calculer_duree(heure_dep, heure_arr):
    """Calcule le temps de trajet pour l'affichage utilisateur."""
    format_heure = '%H:%M'
    try:
        depart = datetime.strptime(heure_dep, format_heure)
        arrivee = datetime.strptime(heure_arr, format_heure)
        difference = arrivee - depart
        
        secondes_totales = difference.total_seconds()
        if secondes_totales < 0: 
            secondes_totales += 86400 
            
        h = int(secondes_totales // 3600)
        m = int((secondes_totales % 3600) // 60)
        return f"{h}h{m:02d}"
    except: 
        return "N/A"

def recherche_itineraires(tx, ville_dep, ville_arr, heure_min, date_voyage, seulement_direct):
    """Requête Cypher pour trouver des trajets directs ou avec une escale."""
    # On met la limite de sauts
    limite_sauts = "1" if seulement_direct else "1..2"

    query = f"""
    MATCH chemin = (dep:Gare)-[:TRAJET*{limite_sauts}]->(arr:Gare)
    WHERE dep.ville =~ ('(?i).*' + $ville_dep + '.*') 
      AND arr.ville =~ ('(?i).*' + $ville_arr + '.*')
      AND ALL(rel IN relationships(chemin) WHERE $date_voyage IN rel.dates)
      AND (relationships(chemin)[0]).`heure départ` >= $heure_min
    
    WITH chemin, relationships(chemin) AS trajets
    WHERE size(trajets) = 1 OR (trajets[1]).`heure départ` > (trajets[0]).`heure arrivée`
    
    RETURN 
        [t IN trajets | {{
            no: t.`n°`, 
            dep: t.`heure départ`, 
            arr: t.`heure arrivée`,
            v_dep: startNode(t).ville, 
            v_arr: endNode(t).ville
        }}] AS liste_trajets,
        size(trajets) AS nb_escales
    ORDER BY (trajets[0]).`heure départ` ASC
    """
    resultat = tx.run(query, ville_dep=ville_dep, ville_arr=ville_arr, 
                      heure_min=heure_min, date_voyage=date_voyage)
    return resultat.data()

@app.route("/", methods=["GET", "POST"])
def index():
    resultats_finaux = []
    formulaire = {}
    
    if request.method == "POST":
        v_depart = request.form.get("dep")
        v_arrivee = request.form.get("arr")
        h_souhaitee = request.form.get("h_min")
        date_v = request.form.get("date_v")
        option_direct = request.form.get("direct_only") == "on"
        
        formulaire = {
            "dep": v_depart, "arr": v_arrivee, 
            "h_min": h_souhaitee, "date_v": date_v, 
            "direct_only": option_direct
        }

        with driver.session() as session:
            donnees_brutes = session.execute_read(
                recherche_itineraires, v_depart, v_arrivee, h_souhaitee, date_v, option_direct
            )
            
            vus = set()
            for itineraire in donnees_brutes:
                # Clé unique Numéro train + Heure départ
                identifiant = f"{itineraire['liste_trajets'][0]['no']}-{itineraire['liste_trajets'][0]['dep']}"
                
                if identifiant not in vus:
                    # Calcul de la durée du trajet
                    h_dep_finale = itineraire['liste_trajets'][0]['dep']
                    h_arr_finale = itineraire['liste_trajets'][-1]['arr']
                    itineraire['duree_totale'] = calculer_duree(h_dep_finale, h_arr_finale)
                    
                    resultats_finaux.append(itineraire)
                    vus.add(identifiant)
            
    return render_template("index.html", results=resultats_finaux, params=formulaire)

if __name__ == "__main__":
    app.run(debug=True)