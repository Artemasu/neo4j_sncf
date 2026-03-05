import pandas as pd

def preparer_donnees(chemin_source):
    # 1. Lecture du fichier source
    print("Lecture du fichier source...")
    df = pd.read_csv(chemin_source, sep=';')

    # 2. Création du fichier NOEUDS (Gares)
    # On prend toutes les origines et destinations pour avoir une liste unique de gares
    dep = df[['Origine', 'Origine IATA']].rename(columns={'Origine': 'ville', 'Origine IATA': 'iata'})
    arr = df[['Destination', 'Destination IATA']].rename(columns={'Destination': 'ville', 'Destination IATA': 'iata'})
    
    df_nodes = pd.concat([dep, arr]).drop_duplicates(subset=['iata']).dropna()
    
    # Sauvegarde des noeuds
    df_nodes.to_csv('nodes_gares.csv', index=False, sep=',', encoding='utf-8')
    print(f"Fichier 'nodes_gares.csv' créé ({len(df_nodes)} lignes).")

    # 3. Création du fichier RELATIONS (Trajets)
    # On sélectionne les colonnes nécessaires et on peut renommer pour plus de clarté
    df_rels = df[['Origine IATA', 'Destination IATA', 'TRAIN_NO', 'Heure_depart', 'Heure_arrivee', 'DATE']]
    
    # Sauvegarde des relations
    df_rels.to_csv('rels_trajets.csv', index=False, sep=',', encoding='utf-8')
    print(f"Fichier 'rels_trajets.csv' créé ({len(df_rels)} lignes).")

    return df_nodes, df_rels

if __name__ == "__main__":
    preparer_donnees('tgvmax.csv')