import subprocess
import logging

# Configurer le logging pour afficher les informations d'exécution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    try:
        # Étape 1 : Exécuter le script `app.py` 
        logger.info("Lancement des processus d'importation des données depuis le fichier Excel...")
        subprocess.run(["python", "app.py"], check=True)
       

        # Étape 2 : Exécuter le script `update.py` pour générer les compétences
        logger.info("Exécution du script update.py pour la génération des compétences...")
        subprocess.run(["python", "update.py"], check=True)

        # Étape 3 : Exécuter le script `addParent.py` pour associer les domaines et sous-domaines
        logger.info("Exécution du script addParent.py pour les mises à jour des domaines et sous-domaines...")
        subprocess.run(["python", "addParent.py"], check=True)

        logger.info("Tous les scripts ont été exécutés avec succès.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Une erreur est survenue lors de l'exécution des scripts : {e}")
    except Exception as ex:
        logger.error(f"Erreur inattendue : {ex}")
