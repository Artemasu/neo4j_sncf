import pandas as pd

def preparer_donnees(chemin_csv):
    """
    Sépare le CSV en deux structures (nœuds et relations).
    On utilise .head(1000) pour ne garder que les 1000 premières lignes pour les tests.
    """
    # Lecture du fichier complet
    df_complet = pd.read_csv(chemin_csv, sep=';')

    # --- ÉCHANTILLONNAGE POUR LES TESTS ---
    # On ne garde que les 1000 premières lignes pour gagner du temps
    # Supprimez ".head(1000)" pour importer la totalité des 346 925 trajets à la fin
    df = df_complet.head(10000) 

    # --- LISTE DES GARES (Nœuds) ---
    dep = df[['Origine', 'Origine IATA']].rename(columns={'Origine': 'ville', 'Origine IATA': 'iata'})
    arr = df[['Destination', 'Destination IATA']].rename(columns={'Destination': 'ville', 'Destination IATA': 'iata'})
    
    # Dédoublonnage pour respecter l'unicité du schéma
    df_nodes = pd.concat([dep, arr]).drop_duplicates(subset=['iata']).dropna()

    # --- LISTE DES TRAJETS (Relations) ---
    df_trajets = df[['Origine IATA', 'Destination IATA', 'TRAIN_NO', 'Heure_depart', 'Heure_arrivee', 'DATE']]
    
    return df_nodes, df_trajets

if __name__ == "__main__":
    nodes, rels = preparer_donnees('tgvmax.csv')
    print(f"Mode TEST activé : {len(nodes)} gares et {len(rels)} trajets extraits.")