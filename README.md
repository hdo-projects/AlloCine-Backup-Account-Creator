# AlloCine-Backup-Account-Creator
Ce projet a pour but de permettre à un utilisateur de sauvegarder ses notes de films et séries notés sur le site internet AlloCiné

## Pourquoi ce projet ?
J'ai créé ce projet car AlloCiné ne permet pas d'extraire dans un format spécifique toutes ses notes attribuées aux différents films et séries. Le script permet donc de sauvegarder ses notes régulièrement si jamais AlloCiné venait à perdre les données des utilisateurs.

## Installation
L'installation de python en version 3.7 au minimum est nécessaire.<br />
Les dépendances s'installent avec :
```
python -m pip install -r requirements.txt
```

## Comment l'utiliser ?
```
python Allocine_Backup_Account_Creator.py <URL du profil utilisateur>
```
Le script créera deux fichiers *liste_notes_films.csv* et *liste_notes_series.csv* qui contiennent le nom du film ou série et sa note associée. Ils sont encodés en UTF-8 avec BOM et utilisent le point-virgule comme séparateur, pour s'ouvrir directement dans Excel en français.

Options disponibles :

| Option | Description |
| --- | --- |
| `-s`, `--sortie DOSSIER` | dossier de destination des fichiers CSV (par défaut : le dossier courant) |
| `-d`, `--delai SECONDES` | pause entre deux pages, pour ménager le site (par défaut : 0.5) |
| `-h`, `--help` | affiche l'aide |

La sortie console sera du type :<br />
```
Identifiant utilisateur : membre-XXXXXXXX
Démarrage de la récupération des notes pour le type de média films
Nombre de pages : 18
Extraction des pages, le processus peut être long...
Fin de la récupération des notes, 642 films sauvegardés dans .\liste_notes_films.csv
Démarrage de la récupération des notes pour le type de média series
Nombre de pages : 1
Extraction des pages, le processus peut être long...
Fin de la récupération des notes, 19 series sauvegardés dans .\liste_notes_series.csv
Les fichiers ont été sauvegardés au format CSV dans C:\...
```

Le script renvoie le code de sortie `0` en cas de succès et `1` si aucune note n'a pu être sauvegardée (URL invalide, profil privé ou inexistant).
