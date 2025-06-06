# Projet d'Analyse et d'Insertion des Données ROME

Ce projet permet de lire, analyser et insérer des données issues d'un fichier Excel contenant l'arborescence des métiers en France (système ROME) dans une base de données MongoDB. Le programme s'exécute en trois étapes principales permettant de traiter, enrichir et mettre à jour les données.

---

## ⚙️ Fonctionnalités

1. **Téléchargement et lecture du fichier Excel** :
    - Télécharge un fichier Excel depuis un lien donné.
    - Lit ce fichier pour extraire les données nécessaires à l'analyse.

2. **Extraction et vérification des informations ROME** :
    - Vérifie si le format d'un code ROME est valide.

3. **Téléchargement des informations métiers** :
    - Télécharge, pour chaque poste et code ROME, les données d'une page web publique (comme France Travail).
    - Extrait des informations comme les missions, certifications, savoir-faire, conditions de travail, etc.

4. **Insertion et mise à jour dans la base MongoDB** :
    - Ajoute les données extraites dans une base MongoDB.
    - Génère des suggestions de compétences complémentaires à l'aide d'un modèle GPT-2.
    - Met à jour les informations sur les domaines et sous-domaines associés.

---

## 📁 Structure des Fichiers

### 1. **index.py** (Point d'entrée principal) :
- Lance séquentiellement les scripts suivants :
    - `app.py` : Téléchargement et parsing des données.
    - `update.py` : Génération des compétences avec GPT.
    - `addParent.py` : Association des domaines et sous-domaines dans MongoDB.

### 2. **app.py** (Téléchargement et insertion initiale des données) :
- Télécharge le fichier Excel contenant l'arborescence des métiers (système ROME).
- Insère les informations métiers de base dans MongoDB.

### 3. **update.py** (Génération des compétences complémentaires) :
- Génère des **hard skills**, **soft skills** et **méthodologies** via GPT-2.
- Nettoie et applique des filtres pour s'assurer de la pertinence.

### 4. **addParent.py** (Mise à jour des domaines et sous-domaines) :
- Associe des informations supplémentaires comme le domaine et le sous-domaine pour chaque code ROME.

### 5. **config.py** :
- Contient les paramètres sensibles, comme l'URL de connexion à **MongoDB Atlas**.

Exemple :
   ```python
   MONGO_URL = "mongodb+srv://<utilisateur>:<mot_de_passe>@cluster0.mongodb.net/service-competence"
   ```
⚠️ Remplacez `<utilisateur>` et `<mot_de_passe>` avec vos propres identifiants MongoDB.

---

## 🛠️ Prérequis

- Python 3.12 ou supérieur
- Les bibliothèques suivantes (à installer avec `pip`) :
  ```
  pip install pandas requests beautifulsoup4 pymongo transformers
  ```

- **MongoDB Atlas** :
    - Configurez un cluster MongoDB Atlas.
    - Stockez les informations de connexion dans un fichier `config.py`.

---

## 🚀 Lancer le Projet

Exécutez la commande suivante à partir du terminal pour lancer toute la chaîne de traitement :

```
python  index.py

```

> **Remarque** : Le script **index.py** s'occupe de lancer les trois étapes mentionnées ci-dessous dans le bon ordre.

---

## 🔄 Détails des Étapes

### 1. Téléchargement et lecture du fichier Excel
- Le script `app.py` télécharge un fichier Excel contenant l'arborescence des métiers ROME et traite chaque ligne pour extraire les informations d'intérêt (par exemple : nom du poste, code ROME).

- Exemple d'extrait du code :
   ```python
   url = "https://www.francetravail.org/files/ROME_Arborescence_Principale.xlsx"
   chemin_fichier_local = "ROME_Arborescence_Principale.xlsx"
   telecharger_et_traiter_excel(url, chemin_fichier_local)
   ```

---

### 2. Génération des compétences complémentaires

Le programme utilise le modèle GPT-2 via le script `update.py` pour enrichir chaque métier avec les compétences suivantes :
- **Hard Skills** : Compétences techniques.
- **Soft Skills** : Compétences comportementales.
- **Methodology** : Méthodes de travail.

**Workflow :**
- Extraction des données MongoDB associées à un métier.
- Génération des compétences.
- Nettoyage des résultats pour garantir leur pertinence.

---

### 3. Mise à jour des domaines et sous-domaines
Le script `addParent.py` associe automatiquement des informations de domaine et sous-domaine pour chaque code ROME. Cela est réalisé en :
- Comparant les données du code ROME avec un fichier Excel.
- Mettant à jour MongoDB avec les nouvelles informations.

---

## 🧪 Résultats attendus

- Une collection MongoDB mise à jour contenant :
    - **Données de base** : Nom du poste, code ROME.
    - **Informations enrichies** : Missions, compétences techniques et comportementales, sous-domaines, etc.

### Exemple de document dans MongoDB :

```
{ "nom_poste": "Ingénieur logiciel", "code_rome": "M1805", "missions": ["Conception de logiciels", "Test d'applications"], "hard_skills": ["Python", "Architecture Cloud", "DevOps"], "soft_skills": ["Travail en équipe", "Adaptabilité"], "methodology": ["Kanban", "Scrum"], "domaine": "Informatique", "sous-domaine": "Développement" }
````


---

## Prochaines améliorations 💡

1. **Tests** :
    - Ajouter une suite de tests unitaires pour vérifier chaque fonction.
    - Utiliser `pytest` pour valider le fonctionnement de bout en bout.

2. **Performances** :
    - Implémenter des requêtes MongoDB optimisées (e.g., pagination pour `find()`).
    - Utiliser des **bulk operations** lors de la mise à jour.

3. **Sécurité des données** :
    - Stocker les informations sensibles comme `MONGO_URL` dans des variables d'environnement.

4. **Modèle GPT-2** :
    - Envisager l'utilisation d'un modèle AI plus récent (comme GPT-3) pour des résultats encore plus précis.

---

## 📝 Auteur

**Arnaud Escalier**