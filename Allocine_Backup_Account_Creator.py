# -*- coding: utf-8 -*-
import re
import sys
import time
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


URL_BASE = "https://www.allocine.fr"
TYPES_DE_MEDIA = ("films", "series")
ENTETES_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}
DELAI_EXPIRATION = 20
DELAI_ENTRE_PAGES = 0.5
# AlloCiné redirige une page hors limites vers la dernière page réelle du profil.
PAGE_SONDE = 999
# Garde-fou si la redirection ci-dessus venait à disparaître.
PAGES_MAX = 200

EXPRESSION_IDENTIFIANT = re.compile(r"membre-[A-Za-z0-9=_-]+")


def construire_url(identifiant_utilisateur, type_media, numero_de_page):
    return "{}/{}/{}/?page={}".format(URL_BASE, identifiant_utilisateur, type_media, numero_de_page)


def creer_session():
    session = requests.Session()
    session.headers.update(ENTETES_HTTP)
    return session


def telecharger(session, url):
    """Renvoie la réponse HTTP, ou None si la page est inaccessible."""
    try:
        reponse = session.get(url, timeout=DELAI_EXPIRATION)
    except requests.RequestException as erreur:
        print("  Erreur réseau sur {} : {}".format(url, erreur))
        return None
    if reponse.status_code != 200:
        print("  Réponse inattendue ({}) pour {}".format(reponse.status_code, url))
        return None
    return reponse


def detecter_nombre_de_pages(session, identifiant_utilisateur, type_media):
    """Déduit le nombre de pages de la redirection appliquée à une page hors limites.

    Renvoie None si le nombre de pages ne peut pas être déterminé.
    """
    reponse = telecharger(session, construire_url(identifiant_utilisateur, type_media, PAGE_SONDE))
    if reponse is None:
        return None
    valeurs = parse_qs(urlparse(reponse.url).query).get("page")
    if not valeurs or not valeurs[0].isdigit():
        # Plus de paramètre de pagination : le profil tient sur une seule page.
        return 1
    nombre_de_pages = int(valeurs[0])
    if nombre_de_pages >= PAGE_SONDE:
        # Aucune redirection n'a eu lieu, la valeur lue n'est pas exploitable.
        return None
    return nombre_de_pages


def extraire_notes(code_html):
    """Renvoie la liste des couples (nom, note) trouvés dans une page de profil."""
    page = BeautifulSoup(code_html, 'html.parser')
    notes = []
    for balise_film in page.find_all("div", class_="card entity-card-simple userprofile-entity-card-simple"):
        # Récupérer le nom du film
        nom_film = balise_film.find('img')['alt']
        # Compile l'expression régulière pour la classe de la note
        expression_reguliere_class = re.compile('rating-mdl n[0-5][0-5] stareval-stars')
        # Extrait la note de la classe
        note_film_html = balise_film.find("div", {"class": expression_reguliere_class})['class'][1][1:]
        note_film = (note_film_html[:1] + ',' + note_film_html[1:])
        notes.append((nom_film, note_film))
    return notes


def recuperer_notes(session, identifiant_utilisateur, type_media):
    """Sauvegarde les notes d'un type de média. Renvoie True si un fichier a été écrit."""
    print("Démarrage de la récupération des notes pour le type de média " + type_media)

    premiere_reponse = telecharger(session, construire_url(identifiant_utilisateur, type_media, 1))
    if premiere_reponse is None:
        print("Profil inaccessible pour le type de média " + type_media + ", rien n'a été sauvegardé")
        return False

    notes = extraire_notes(premiere_reponse.text)
    if not notes:
        print("Aucune note trouvée pour le type de média " + type_media)
        print("Vérifiez l'URL du profil et le fait qu'il soit public")
        return False

    nombre_de_pages = detecter_nombre_de_pages(session, identifiant_utilisateur, type_media)
    if nombre_de_pages is None:
        nombre_de_pages = PAGES_MAX
        print("Nombre de pages indéterminable, parcours page par page jusqu'à la dernière")
    else:
        print("Nombre de pages : " + str(nombre_de_pages))
    print("Extraction des pages, le processus peut être long...")

    for numero_de_page in range(2, nombre_de_pages + 1):
        time.sleep(DELAI_ENTRE_PAGES)
        url = construire_url(identifiant_utilisateur, type_media, numero_de_page)
        reponse = telecharger(session, url)
        if reponse is None:
            print("  Arrêt à la page {} sur {}".format(numero_de_page, nombre_de_pages))
            break
        notes_de_la_page = extraire_notes(reponse.text)
        if not notes_de_la_page:
            break
        notes.extend(notes_de_la_page)

    # Création du fichier de sortie
    liste_notes = open("liste_notes_" + type_media + ".csv", "w", encoding="utf-8")
    liste_notes.write("Nom;Note" + "\n")
    for nom_film, note_film in notes:
        liste_notes.write(nom_film + ";" + note_film + "\n")
    liste_notes.close()
    print("Fin de la récupération des notes, " + str(len(notes)) + " " + type_media + " sauvegardés")
    return True


def main():
    # Vérification des paramètres
    if len(sys.argv) != 2:
        print("Utilisation : python Allocine_Backup_Account_Creator.py <URL utilisateur>")
        sys.exit(1)

    # Récupération de l'identifiant utilisateur dans l'URL du profil
    correspondance = EXPRESSION_IDENTIFIANT.search(sys.argv[1])
    if correspondance is None:
        print("L'identifiant utilisateur n'a pas pu être récupéré, vérifiez le paramètre passé")
        print("L'URL attendue est de la forme https://www.allocine.fr/membre-XXXXXXXX/")
        sys.exit(1)
    identifiant_utilisateur = correspondance.group(0)

    session = creer_session()
    resultats = [
        recuperer_notes(session, identifiant_utilisateur, type_media)
        for type_media in TYPES_DE_MEDIA
    ]

    if not any(resultats):
        print("Aucune note n'a pu être sauvegardée")
        sys.exit(1)
    print("Les fichiers ont été sauvegardés dans le répertoire courant au format CSV")
    sys.exit(0)


if __name__ == "__main__":
    main()
