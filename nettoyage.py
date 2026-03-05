import pandas as pd

def preparer_donnees(chemin_csv): # Sépare le CSV en deux structures (noeuds et relations).

    df_complet = pd.read_csv(chemin_csv, sep=';')
    df = df_complet.head(10000)

    dep = df[['Origine', 'Origine IATA']].rename(columns={'Origine': 'ville', 'Origine IATA': 'iata'})
    arr = df[['Destination', 'Destination IATA']].rename(columns={'Destination': 'ville', 'Destination IATA': 'iata'})
    
    # Dédoublonnage
    df_nodes = pd.concat([dep, arr]).drop_duplicates(subset=['iata']).dropna()

    # Liste des trajets (Relations)
    df_trajets = df[['Origine IATA', 'Destination IATA', 'TRAIN_NO', 'Heure_depart', 'Heure_arrivee', 'DATE']]
    
    return df_nodes, df_trajets

if __name__ == "__main__":
    nodes, rels = preparer_donnees('tgvmax.csv')
    print(f"Mode TEST activé : {len(nodes)} gares et {len(rels)} trajets extraits.")