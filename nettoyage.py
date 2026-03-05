import pandas as pd

def preparer_donnees(chemin_source):
    print(f"Lecture du fichier source : {chemin_source}")
    cols = ['Origine', 'Origine IATA', 'Destination', 'Destination IATA', 
            'TRAIN_NO', 'Heure_depart', 'Heure_arrivee', 'DATE']
    df = pd.read_csv(chemin_source, sep=';', usecols=cols)

    # Création des Gares (Noeuds)
    dep = df[['Origine', 'Origine IATA']].rename(columns={'Origine': 'ville', 'Origine IATA': 'iata'})
    arr = df[['Destination', 'Destination IATA']].rename(columns={'Destination': 'ville', 'Destination IATA': 'iata'})
    df_nodes = pd.concat([dep, arr]).drop_duplicates(subset=['iata']).dropna()
    
    df_nodes.to_csv('nodes_gares.csv', index=False, sep=',', encoding='utf-8')
    print(f"Fichier 'nodes_gares.csv' créé ({len(df_nodes)} gares).")

    # Création des Trajets (Relations)
    colonnes_cles = ['Origine IATA', 'Destination IATA', 'TRAIN_NO', 'Heure_depart', 'Heure_arrivee']
    df_rels = df.groupby(colonnes_cles)['DATE'].apply(list).reset_index()
    
    df_rels.to_csv('rels_trajets.csv', index=False, sep=',', encoding='utf-8')
    print(f"Fichier 'rels_trajets.csv' créé ({len(df_rels)} trajets uniques).")

    return df_nodes, df_rels

if __name__ == "__main__":
    preparer_donnees('tgvmax.csv')