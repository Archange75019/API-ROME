import sys
import pandas as pd
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import requests
import logging
from pymongo.errors import CursorNotFound
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
from config import MONGO_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connexion à MongoDB
client = MongoClient(MONGO_URL)
db = client['service-competence']
collection = db['fiches_metiers']

# Load the tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

def clean_competences(competences):
    """Clean and filter the competences generated by GPT-2."""
    cleaned = {
        "hard_skills": [],
        "soft_skills": [],
        "methodology": []
    }

    stop_words = ["transition écologique", "auxiliary", "reverse", "job category"]

    for category, skills in competences.items():
        if isinstance(skills, list):
            cleaned[category] = [
                                    skill.strip() for skill in skills
                                    if not any(stop_word in skill.lower() for stop_word in stop_words)
                                ][:40]  # Limit to 40 elements

    return cleaned

def generate_competences(properties):
    """Generate competences using the GPT-2 model."""
    try:
        input_text = (
            "Generate a structured list of 30 to 40 complementary hard skills, soft skills, and methodologies "
            f"for the job titled '{properties.get('nom_poste', '')}' based on the following job data. "
            "Each category should contain a list of unique items. The output should be in the following format:\n"
            "\nJob Data:\n"
            f"Hard Skills: {properties.get('hard_skills', [])}\n"
            f"Soft Skills: {properties.get('soft_skills', [])}\n"
            f"Methodology: {properties.get('methodology', [])}\n"
        )
        print("input_text: ", input_text)
        logger.info(f"Input sent to GPT-2:\n{input_text}")

        input_ids = tokenizer.encode(input_text, return_tensors="pt", padding=True)
        attention_mask = (input_ids != tokenizer.pad_token_id).long()

        output = model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_new_tokens=300,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            pad_token_id=tokenizer.pad_token_id
        )

        generated_text = tokenizer.decode(output[0], skip_special_tokens=True).strip()
        print("generated_text: ", generated_text)
        logger.info(f"Generated text:\n{generated_text}")

        structured_output = {
            "hard_skills": [],
            "soft_skills": [],
            "methodology": []
        }

        current_category = None
        for line in generated_text.split("\n"):
            line = line.strip()
            if line.startswith("Hard Skills:"):
                current_category = "hard_skills"
            elif line.startswith("Soft Skills:"):
                current_category = "soft_skills"
            elif line.startswith("Methodology:"):
                current_category = "methodology"
            elif current_category and line.startswith("-"):
                structured_output[current_category].append(line[1:].strip())

        # If the generated text does not contain the expected categories, use the input properties directly
        if not any(structured_output.values()):
            structured_output = properties

        for category in structured_output:
            structured_output[category] = structured_output[category][:40]

        return structured_output

    except Exception as e:
        logger.error(f"Error generating competences: {e}")
        return properties

def telecharger_et_traiter_excel(url, chemin_fichier_local):
    try:
        # Étape 1 : Télécharger le fichier depuis l'URL
        response = requests.get(url)

        # Vérifier si la requête a réussi
        if response.status_code == 200:
            # Sauvegarder le fichier localement
            with open(chemin_fichier_local, 'wb') as fichier_local:
                fichier_local.write(response.content)
            print(f"Fichier téléchargé et sauvegardé : {chemin_fichier_local}")
            return True
        else:
            print(f"Échec du téléchargement. Code statut : {response.status_code}")
            return False
    except Exception as e:
        print(f"Une erreur s'est produite lors du téléchargement : {e}")
        return False

def charger_donnees(path):
    try:
        # Lecture de la première feuille (ou ajuster selon besoin)
        return pd.read_excel(path, sheet_name="Arbo Principale 25-11-2024")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {e}")
        sys.exit(1)

def trouver_code_rome(nom_poste, df):
    mots = nom_poste.split()
    for col in df.columns:
        if df[col].dtype == 'object':
            for index, row in df.iterrows():
                ligne = str(row[col])
                if all(mot.lower() in ligne.lower() for mot in mots):
                    if ' ' in df.columns and ' .1' in df.columns and ' .2' in df.columns:
                        return str(df.loc[index, ' ']) + str(df.loc[index, ' .1']) + str(df.loc[index, ' .2'])
    return None

def est_code_rome_valide(code_rome):
    if len(code_rome) < 4:
        return False
    return code_rome[0].isalpha() and code_rome[1:].isdigit()

def telecharger_page(nom_poste, code_rome):
    nom_poste_formatte = re.sub(r"[^\w\s-]", "", nom_poste).replace("/", " ").replace(" ", "-").lower()
    url = f"https://candidat.francetravail.fr/metierscope/fiche-metier/{code_rome}/{nom_poste_formatte}"

    try:
        existing_document = collection.find_one({"code_rome": code_rome})
        if existing_document:
            print(f"Un document avec le code ROME {code_rome} existe déjà dans la base de données.")
            return existing_document["missions"]

        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            metiers_associes_list = soup.find('ul', {'data-cy': 'liste-libelle-metier'})
            metiers_associes = [li.get_text(strip=True) for li in metiers_associes_list.find_all('li')] if metiers_associes_list else []

            missions_list = soup.find('ul', {'data-cy': 'liste-descriptif-metier'})
            missions = [li.get_text(strip=True) for li in missions_list.find_all('li')] if missions_list else []

            certifications_list = soup.find('ul', {'data-cy': 'liste-certification-metier'})
            certifications = [li.get_text(strip=True) for li in certifications_list.find_all('li')] if certifications_list else []

            if not certifications:
                acces_metier_paragraph = soup.find('p', {'data-cy': 'texte-acces-metier'})
                if acces_metier_paragraph:
                    certifications_text = acces_metier_paragraph.get_text(strip=True)
                    certifications = [certifications_text]

            savoir_faire_sections = soup.find_all('div', {'data-cy': 'liste-savoir-faire-principaux'})
            savoir_faire_data = {}
            for section in savoir_faire_sections:
                title = section.find('p', {'role': 'heading', 'aria-level': '5'}).get_text(strip=True)
                items = [li.get_text(strip=True) for li in section.find_all('li')]
                savoir_faire_data[title] = items

            savoir_faire_secondaires_sections = soup.find_all('div', {'data-cy': 'liste-savoir-faire-secondaires'})
            savoir_faire_data_secondaires = {}
            for section in savoir_faire_secondaires_sections:
                title = section.find('p', {'role': 'heading', 'aria-level': '5'}).get_text(strip=True)
                items = [li.get_text(strip=True) for li in section.find_all('li')]
                savoir_faire_data_secondaires[title] = items

            savoir_faire_professionnels_list = soup.find('ul', {'data-cy': 'liste-savoir-professionels'})
            savoir_faire_professionnels = [li.get_text(strip=True) for li in savoir_faire_professionnels_list.find_all('li')] if savoir_faire_professionnels_list else []

            domaine_expertise_list = soup.find('div', {'id': 'fm-collapse-2-0'})
            domaine_expertise = [li.get_text(strip=True) for li in domaine_expertise_list.find_all('li')] if domaine_expertise_list else []

            normes_procede_list = soup.find('div', {'id': 'fm-collapse-2-1'})
            normes_procede = [li.get_text(strip=True) for li in normes_procede_list.find_all('li')] if normes_procede_list else []

            conditions_travail_list = soup.find('ul', {'data-cy': 'liste-contexte-conditions'})
            conditions_travail = [li.get_text(strip=True) for li in conditions_travail_list.find_all('li')] if conditions_travail_list else []

            horaire_duree_list = soup.find('ul', {'data-cy': 'liste-contexte-horaires'})
            horaire_duree = [li.get_text(strip=True) for li in horaire_duree_list.find_all('li')] if horaire_duree_list else []

            statut_emploi_list = soup.find('ul', {'data-cy': 'liste-contexte-types'})
            statut_emploi = [li.get_text(strip=True) for li in statut_emploi_list.find_all('li')] if statut_emploi_list else []

            document = {
                "nom_poste": nom_poste,
                "url": url,
                "code_rome": code_rome,
                "metiers_associes": metiers_associes,
                "missions": missions,
                "certifications": certifications,
                "savoir_faire_data": savoir_faire_data,
                "savoir_faire_data_secondaires": savoir_faire_data_secondaires,
                "savoir_faire_professionnels": savoir_faire_professionnels,
                "domaine_expertise": domaine_expertise,
                "normes_procede": normes_procede,
                "conditions_travail": conditions_travail,
                "horaire_duree": horaire_duree,
                "statut_emploi": statut_emploi
            }

            collection.insert_one(document)
            print(f"Les données ont été insérées dans la base de données pour le code ROME : {code_rome}")
            return missions
        else:
            print(f"Erreur lors du téléchargement de la page. Code de statut : {response.status_code}")
            return []
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return []

if __name__ == "__main__":
    # URL du fichier Excel
    url = "https://www.francetravail.org/files/live/sites/peorg/files/documents/Statistiques-et-analyses/Open-data/ROME/ROME%20Arborescence%20Principale%2024M11.xlsx"

    # Chemin local pour enregistrer le fichier
    chemin_fichier_local = "ROME_Arborescence_Principale_24M11.xlsx"

    # Télécharger le fichier Excel
    if telecharger_et_traiter_excel(url, chemin_fichier_local):
        # Charger et traiter le fichier Excel
        df = charger_donnees(chemin_fichier_local)

        # Récupérer le dernier code ROME inséré dans la base de données
        dernier_document = collection.find_one(sort=[("code_rome", -1)])
        dernier_code_rome = dernier_document["code_rome"] if dernier_document else None

        start_index = 0
        if dernier_code_rome:
            # Trouver l'index de la ligne correspondant au dernier code ROME
            for index, row in df.iterrows():
                current_code_rome = trouver_code_rome(row[' .3'], df)
                print(current_code_rome)
                if current_code_rome == dernier_code_rome:
                    start_index = index
                    break

        # Itérer sur chaque ligne du DataFrame à partir de l'index trouvé
        for index, row in df.iterrows():
            if index >= start_index:
                nom_poste = row[' .3']
                code_rome = trouver_code_rome(nom_poste, df)
                if code_rome and est_code_rome_valide(code_rome):
                    telecharger_page(nom_poste, code_rome)
