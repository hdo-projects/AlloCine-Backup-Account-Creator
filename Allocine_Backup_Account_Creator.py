# -*- coding: utf-8 -*-
import re
import sys
from urllib.parse import parse_qs, urlparse

# La vérification de version doit précéder l'import des dépendances tierces.
if sys.version_info < (3, 7):
    print("La version de Python doit être 3.7 ou supérieure. Le programme ne peut pas continuer")
    sys.exit(1)

# Vérification des bibliothèques nécessaires
try:
    from bs4 import BeautifulSoup
    import requests
except ImportError as erreur:
    print("Dépendance manquante : " + str(erreur.name))
    print("Installez les dépendances avec : python -m pip install -r requirements.txt")
    sys.exit(1)

# AlloCiné redirige une page hors limites vers la dernière page réelle du profil.
PAGE_SONDE = 999
EXPRESSION_IDENTIFIANT = re.compile(r"membre-[A-Za-z0-9=_-]+")


def detecter_nombre_de_pages(identifiant_utilisateur, type_media):
    """Déduit le nombre de pages de la redirection appliquée à une page hors limites."""
    url = ('http://www.allocine.fr/' + identifiant_utilisateur + '/' + type_media
           + '/?page=' + str(PAGE_SONDE))
    reponse = requests.get(url)
    valeurs = parse_qs(urlparse(reponse.url).query).get("page")
    if not valeurs or not valeurs[0].isdigit():
        # Plus de paramètre de pagination : le profil tient sur une seule page.
        return 1
    nombre_de_pages = int(valeurs[0])
    if nombre_de_pages >= PAGE_SONDE:
        # Aucune redirection n'a eu lieu, la valeur lue n'est pas exploitable.
        return 1
    return nombre_de_pages


def recuperer_notes(identifiant_utilisateur, type_media):
    print("Démarrage de la récupération des notes pour le type de média " + type_media)
    code_html = ""

    # Récupération du nombre de pages liées au profil utilisateur
    nombre_de_pages = detecter_nombre_de_pages(identifiant_utilisateur, type_media)
    print("Nombre de pages : " + str(nombre_de_pages))
    print("Extraction des pages, le processus peut être long...")
    for i in range(1, nombre_de_pages + 1):
        url = 'http://www.allocine.fr/' + identifiant_utilisateur + '/' + type_media + '/?page=' + str(i)
        code_html = code_html + requests.get(url).text

    # Parsing de la page HTML entière
    recherche_html = BeautifulSoup(code_html, 'html.parser')
    nombre_de_medias_trouves = 0
    # Création du fichier de sortie
    liste_notes = open("liste_notes_" + type_media + ".csv", "w", encoding="utf-8")
    liste_notes.write("Nom;Note" + "\n")
    # Pour chaque film
    for balise_film in recherche_html.find_all("div", class_="card entity-card-simple userprofile-entity-card-simple"):
        # Récupérer le nom du film
        nom_film = balise_film.find('img')['alt']
        # Compile l'expression régulière pour la classe de la note
        expression_reguliere_class = re.compile('rating-mdl n[0-5][0-5] stareval-stars')
        # Extrait la note de la classe
        note_film_html = balise_film.find("div", {"class": expression_reguliere_class})['class'][1][1:]
        note_film = (note_film_html[:1] + ',' + note_film_html[1:])
        liste_notes.write(nom_film + ";" + note_film + "\n")
        nombre_de_medias_trouves = nombre_de_medias_trouves + 1
    liste_notes.close()
    print("Fin de la récupération des notes, " + str(nombre_de_medias_trouves) + " " + type_media + " sauvegardés")


def main():
    # Vérification des paramètres
    if len(sys.argv) != 2:
        print("Utilisation : python Allocine_Backup_Account_Creator.py <URL utilisateur>")
        sys.exit(1)

    # Récupération de l'identifiant utilisateur dans l'URL du profil
    correspondance = EXPRESSION_IDENTIFIANT.search(sys.argv[1])
    if correspondance is None:
        print("L'identifiant utilisateur n'a pas pu être récupéré, vérifiez le paramètre passé")
        print("L'URL attendue est de la forme http://www.allocine.fr/membre-XXXXXXXX/")
        sys.exit(1)
    identifiant_utilisateur = correspondance.group(0)

    recuperer_notes(identifiant_utilisateur, "films")
    recuperer_notes(identifiant_utilisateur, "series")
    print("Les fichiers ont été sauvegardés dans le répertoire courant au format CSV")
    sys.exit(0)


if __name__ == "__main__":
    main()
