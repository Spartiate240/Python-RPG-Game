# Python RPG

Jeu de rôle en Python avec une interface graphique pygame. Le projet propose
une boucle de jeu simple : créer ou charger une partie, explorer une zone,
affronter des ennemis, améliorer le groupe et gérer sa progression.

## Lancer le jeu

Depuis la racine du projet :

```bash
python main.py
```

La dépendance principale est pygame. Si elle n'est pas déjà installée :

```bash
python -m pip install pygame
```

Le point d'entrée est [main.py](main.py). Il crée une instance de
`PygameApp`, puis lance sa boucle d'événements et de rendu.

## Fonctionnement de l'application

### Menu principal

Le menu permet de :

- commencer une nouvelle partie ;
- charger la sauvegarde existante ;
- quitter en sauvegardant la progression.

### Exploration

Après une nouvelle partie, le joueur commence au village. L'écran
d'exploration affiche :

- la région et la zone actuelles ;
- l'or du chef de groupe ;
- le résumé des membres du groupe ;
- les accès aux régions, à la boutique, aux quêtes, aux titres et à l'état du
    groupe ;
- le bouton de rencontre qui démarre un combat.

Les régions et leurs zones sont définies dans [data/regions.json](data/regions.json).
Le chemin de navigation est :

```text
Exploration -> Régions -> Zones -> Exploration
```

### Combat

Une rencontre choisit un ennemi parmi ceux configurés pour la zone. Le combat
est géré par [core/battle.py](core/battle.py) et présenté par
[ui/battle.py](ui/battle.py).

Le système actuel :

- trie les combattants selon leur vitesse ;
- joue automatiquement les tours des ennemis et des compagnons ;
- permet au joueur de choisir une attaque normale ou un skill avant de
    sélectionner la carte ennemie ;
- expose les skills déclarés par les armes équipées ; les skills de défense ou
    de zone sont exécutés dès leur sélection ;
- permet de fuir ;
- calcule les dégâts à partir de l'attaque et de la défense ;
- attribue l'expérience et l'or en cas de victoire ;
- applique les montées de niveau et les bonus de statistiques liés à l'XP ;
- tire les drops configurés par l'ennemi et les ajoute à l'inventaire partagé ;
- affiche la victoire, la défaite ou la fuite.

Les ennemis sont décrits dans [data/enemies.json](data/enemies.json) et
instanciés par [entities/enemy.py](entities/enemy.py).

### Boutique

La boutique permet de choisir un marchand puis d'acheter les objets de son
stock. Les quantités diminuent pendant la partie et les achats sont ajoutés à
l'inventaire partagé du groupe.

Les données des marchands se trouvent dans
[data/merchants.json](data/merchants.json). Le stock courant est sauvegardé
avec la partie et restauré lors du chargement. Une nouvelle partie repart du
stock défini dans le catalogue.

### État du groupe et équipement

L'écran d'état permet de :

- sélectionner un membre du groupe ;
- voir ses statistiques ;
- consulter l'équipement porté ;
- retirer une arme, une pièce d'armure ou un familier ;
- équiper un objet depuis l'inventaire partagé.

Les règles métier sont regroupées dans
[core/inventory.py](core/inventory.py). Les objets équipables utilisent les
emplacements `weapon`, `helmet`, `chest`, `legs`, `boots`, `arms` et `pet`
(familier équipé).

Les potions de soin peuvent être utilisées hors combat et pendant un combat.
Elles consomment une unité de l'inventaire et restaurent les PV de la cible.
Les modèles génériques sont définis dans [items/base.py](items/base.py).

### Quêtes et titres

Le tableau des quêtes permet d'accepter une quête puis de réclamer sa
récompense lorsque ses conditions sont remplies. Les conditions actuellement
prises en charge sont :

- nombre de victoires ;
- or gagné ;
- quêtes terminées ;
- niveau du chef de groupe.

Les titres suivent ces mêmes statistiques. Certains titres peuvent débloquer
un compagnon, comme le Gardien du village. Les récompenses peuvent inclure de
l'or, de l'expérience, des objets ou un compagnon.

La logique correspondante se trouve dans
[core/progression.py](core/progression.py). Les catalogues sont définis dans
[data/quests.json](data/quests.json) et [data/titles.json](data/titles.json).

## Sauvegarde

La sauvegarde est écrite dans
[progression/Saved_progress.json](progression/Saved_progress.json).

Elle contient notamment :

- les membres du groupe et leur équipement ;
- les points de vie, niveaux, expérience et or ;
- la zone actuelle ;
- l'inventaire partagé ;
- les statistiques de progression ;
- l'état des quêtes et des titres.

La sérialisation générale est gérée par [core/game.py](core/game.py), tandis
que [party/party.py](party/party.py) sérialise les membres du groupe.

## Architecture

```text
main.py                     Point d'entrée
core/
    gui.py                    Boucle pygame, événements et coordination
    game.py                   État global et persistance
    battle.py                 Logique des combats sans dépendance pygame
    catalog.py                Chargement des catalogues JSON
    inventory.py              Inventaire partagé et équipement
    progression.py            Quêtes, titres et récompenses
    shop.py                   Achats et gestion du stock marchand
    encounter.py              Création des rencontres et combats
ui/
    main_menu.py              Rendu du menu principal
    exploration.py            Rendu de l'écran d'exploration
    regions.py                Rendu de la sélection des régions
    zones.py                  Rendu de la sélection des zones
    shop.py                   Rendu de la boutique
    quests.py                 Rendu du tableau des quêtes
    titles.py                 Rendu des titres
    status.py                 Rendu de l'état du groupe
    battle.py                 Rendu et interactions du combat
    game_over.py              Rendu de la fin de partie
    renderer.py               Rendu pygame partagé et chargement des sprites
    widgets.py                Boutons et composants UI partagés
    theme.py                  Palette partagée de l'interface
entities/
    combatant.py              Classe abstraite commune aux combattants
    ally.py                   Base de Player et Companion, équipement et stats
    player.py                 Personnage contrôlé et sérialisation du joueur
    companion.py              Allié recruté et comportement automatique
    enemy.py                  Ennemi, IA basique et chargement depuis JSON
    merchant.py               Modèle métier d'un marchand
party/
    party.py                  Membres, actifs/réserve et sérialisation du groupe
items/
    base.py                   Modèles Item, Consumable et Equipment
progression/
    generate_xp_table.py       Générateur de table d'expérience
    level_manager.py           Calcul des paliers et bonus de niveau
    xp_table.json              Table d'expérience générée
    Saved_progress.json        Sauvegarde de la partie
data/
    *.json                     Catalogues de contenu
    assets/                    Sprites et ressources graphiques
```

### `core/gui.py`

`PygameApp` reste le coordinateur de l'application. Il contient encore :

- la boucle pygame ;
- la gestion des clics et des transitions d'écran ;
- la coordination de l'état courant, de la sauvegarde et des managers métier ;
- les primitives de délégation entre les événements, les services et les écrans.

La navigation dans les régions et les zones est fournie par `Catalogs`, et la
création d'une rencontre est déléguée à [core/encounter.py](core/encounter.py).

Les rendus, boutons, interactions d'écran et ressources graphiques sont
délégués aux modules du package [ui](ui). Les achats sont gérés par
[core/shop.py](core/shop.py), tandis que les règles de combat restent
calculées par [core/battle.py](core/battle.py). `PygameApp` conserve donc la
coordination sans porter le rendu détaillé ni la logique métier spécialisée.

### `core/catalog.py`

`Catalogs` charge les fichiers JSON et expose les catalogues des ennemis,
objets, armes, armures, familiers, quêtes, titres, régions et marchands. Il
reconstruit également le stock initial des marchands et fournit les recherches
de régions et de zones.

### `core/shop.py` et `core/encounter.py`

`ShopService` gère les achats, la consommation du stock et l'ajout des objets
à l'inventaire partagé, sans dépendance à pygame. `EncounterService` construit
un combat à partir de la zone courante et du catalogue des ennemis.

### `ui/`

Chaque écran pygame possède son module dédié : menu principal, exploration,
régions, zones, boutique, quêtes, titres, statut, combat et fin de partie.
`ui/renderer.py` centralise les panneaux, textes, boutons, sprites et
spritesheets. `ui/widgets.py` contient les composants partagés, notamment
`Button`, tandis que `ui/theme.py` regroupe la palette commune.

### `entities/`

La hiérarchie des combattants est la suivante :

```text
Combatant
├── Enemy
└── Ally
        ├── Player
        └── Companion
```

`Merchant` reste volontairement en dehors de cette hiérarchie : un marchand
ne combat pas.

## Données et ressources

Les fichiers JSON de [data](data) permettent d'ajouter du contenu sans
modifier directement l'interface :

- `enemies.json` : statistiques, récompenses et sprites des ennemis ;
- `regions.json` : régions, zones et ennemis possibles ;
- `items.json` : potions et matériaux ;
- `weapons.json` : armes et dégâts ;
- `armor.json` : armures et bonus ;
- `pets.json` : compagnons/familiers et effets ;
- `merchants.json` : marchands et stocks ;
- `quests.json` : conditions et récompenses des quêtes ;
- `titles.json` : conditions et récompenses des titres.

Les chemins de sprites sont résolus relativement au dossier `data`. Les
ressources de l'interface sont dans
[data/assets/sprites/UI](data/assets/sprites/UI), avec des manifestes pour les
spritesheets.

## État actuel et limites connues

Le socle jouable et les principaux systèmes de progression sont en place. Les
limites actuelles sont :

- les compétences de soin et leurs effets persistants restent à compléter ;
- la boutique permet l'achat, mais pas encore la revente depuis l'interface ;
- les drops dont l'identifiant est absent des catalogues sont ignorés ;
- les effets textuels de certains titres ne modifient pas encore les règles
    de combat.

## Pistes d'évolution

Les évolutions naturelles sont :

1. Tests automatisés et sauvegardes versionnées.
2. Guilde/Ville.
3. Effets persistants et combat enrichi.
4. Revente et économie.
5. Gestion avancée du groupe.
6. Interface, audio et polish.
7. Simulation d’équilibrage et distribution du jeu.