# PROTOCOLE


## ENVOI

### CLIENT

- Connection à une gameroom : ```CONNECT <room-id>```.
- Pret à jouer: ```READY```.
- Joue: ```MOVE <move>```.
- Récupère une liste de donnée : ```GET <info-type>```.
- Préviens le serveur que le client est toujours en vie: ```ALIVE```.
- Créer une room de jeu : ```CREATE_ROOM <name> <visibility> <args>```

### SERVEUR
- Accepte la connection à une gameroom : ```ACCEPT```.
- Annonce que tous les joueurs sont prêts : ```READY```.
- Donne l'état du jeu pour chaque client : ```INIT <data>```.
- Met à jour l'état du jeu : ```UPDATE <object> <data>``` (seulement une partie des données).
- Annonce la fin de partie et le gagnant : ```END <player-name>```.
- Renvoie une liste de donnée : ```SEND <info-type> <info>```.
- Demande au client s'il est toujours en vie : ```ALIVE```.
- Envoie un code d'erreur au client : ```ERROR <error-id>```.

## ECOUTE

### CLIENT

- ```ACCEPT``` : Met à jour l'UI: propose à l'utilisateurs des options de jeu et finalement le bouton "ready" qui envoie la requete ```READY``` au serveur.
- ```READY``` : Passe le client en mode "jeu" et créé sans initialiser les objets du jeu. Le client attend la requete ``INIT`` pour finir d'initialiser les objets.
- ```INIT <data>``` : Initialise les objets du jeu qui viennent d'être créé avec les valeurs de ``data``.
- ```UPDATE <object> <data>``` : Met à jour les données d'un objet spécifique (plutot que de tout le plateau par exemple).
- ```END <player-name>``` : Passe le jeu en mode "écran de victoire" et affiche le nom du gagnant.
- ```ALIVE``` : Renvoie ```ALIVE```.
- ```ERROR <error-id>``` : Comportement dépend complètement de l'erreur. Peut refaire la requête, planter, se déconnecter, etc...
- ```CREATE_ROOM <name> <visibility> <args>``` : Créer une gameroom se nommant ``name`` étant ``public`` ou ``private`` avec les arguments ``args``. S'il n'y a pas assez de place pour créer la room, ou si le client n'a pas le droit de créer une room, renvoie une erreur.


### SERVEUR

- ```CONNECT <room-id>``` : Vérifie que la room spécifiée existe, est disponible (pas en jeu), pas pleine et renvoie ```ACCEPT```. Sinon renvoie une erreur.
- ```READY``` : Met à jour l'état du client, quand tous les clients sont dans l'état prêt, renvoie ```READY``` et met le jeu en mode "jeu".
- ```MOVE <move>``` : Vérifie que le "move" est valide, si oui effectue le "move" et renvoie ```UPDATE <object> <data>``` sinon renvoie une erreur.
- ```GET <info-type>``` : renvoie le type d'info demandé et renvoie ```SEND <info-type> <info>```. Erreurs peuvent êtres créées si le client n'a pas l'autorisation d'accès ou si le type d'info n'existe pas.
    
- ```ALIVE``` : Confirme bien que le client est en vie et ne l'expulse pas. Attends **30** secondes avant de redemander si le client est en vie.

## ERREURS
0. ```ROOM_NT_FOUND``` : La room est introuvable.
1. ```ROOM_FULL``` : La room est pleine.
2. ```ROOM_NOT_AVLABLE``` : La room n'est pas disponible.
3. ```INVALID_MOVE``` : Le "move" du client est invalide.
4. ```INFO_NOT_EXIST``` : Le type d'info n'existe pas.
5. ```INFO_NOT_ACCESS``` : Le client n'a pas accès à ce type d'infos.
6. ```ROOM_CANT_CREATE``` : N'a pas pu créer la room.
6. ```ROOM_CREATE_NAUTH``` : Le client n'a pas l'autorisation de créer la room.


## INFO TYPE
- ```MEMLIST``` : La liste des membres de la room. Le client à besoin d'être membre de la room sinon renvoie l'erreur ```INFO_NOT_ACCESS```. 