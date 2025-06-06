import pandas as pd
from pymongo import MongoClient
from config import MONGO_URL

# Connexion à MongoDB
client = MongoClient(MONGO_URL)
db = client['service-competence']
collection = db['fiches_metiers']

def charger_donnees(path):
    try:
        # Lecture de la première feuille (ou ajuster selon besoin)
        return pd.read_excel(path, sheet_name="Arbo Principale 25-11-2024")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {e}")
        raise

def telecharger_documents():
    # Télécharger les documents de la collection
    documents = list(collection.find({}))
    return documents

def trouver_domaine_sous_domaine(code_rome, df):
    # Extraire la lettre du domaine et le sous-domaine
    lettre_domaine = code_rome[0]
    sous_domaine = code_rome[1:3]



    # Trouver le domaine et le sous-domaine dans le DataFrame
    domaine_row = df.loc[(df[' '] == lettre_domaine)]
   
    if not domaine_row.empty:
        domaine = domaine_row.iloc[0][' .3']
        
    else:
        domaine = "Domaine non trouvé"

    sous_domaine_row = df.loc[(df[' '] == lettre_domaine) & (df[' .1'] == sous_domaine) & (df[' .2'] != '')]
    if not sous_domaine_row.empty:
        sous_domaine_nom = sous_domaine_row.iloc[0][' .3']
    else:
        sous_domaine_nom = "Sous-domaine non trouvé"

    return domaine, sous_domaine_nom

def mettre_a_jour_documents(df, documents):
    for doc in documents:
        code_rome = doc.get("code_rome")
        if code_rome:
            domaine, sous_domaine = trouver_domaine_sous_domaine(code_rome, df)

            # Mettre à jour le document dans MongoDB
            collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$unset": {"parent": "", "enfant": "", "compétencesUpdate": ""},
                    "$set": {"domaine": domaine, "sous-domaine": sous_domaine}
                   
                }
            )
            print(f"Document mis à jour avec code ROME : {code_rome}")


if __name__ == "__main__":
    # Chemin local pour le fichier Excel
    chemin_fichier_local = "ROME_Arborescence_Principale_24M11.xlsx"

    # Charger et traiter le fichier Excel
    df = charger_donnees(chemin_fichier_local)

    # Télécharger les documents de la base de données
    documents = telecharger_documents()

    # Mettre à jour les documents dans MongoDB
    mettre_a_jour_documents(df, documents)

