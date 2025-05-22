# Mini Chat

## Serveur

On peut compiler le serveur en se rendant dans ```/cpp/server/``` et en tappant la commande ```g++ *.cpp -Iheaders -o server```.
Il peut être executé avec ```./server <port="12345">```


## Client

Le client se trouve dans ```python/client/``` et peut s'executer avec ```python3 main.py <host="localhost"> <port=12345>```:

## Protocole

Le protocole d'échange est le suivant : (ce qu'envoie le client est précédé de ```clt:``` et le serveur de ```srv```)

### Erreurs génériques

```cpp
srv: ERROR 10                          // arguments invalides
srv: ERROR 11                          // commande inexistante
```

### Connexion

```cpp
srv: TCHAT 1                           // numéro de version du protocole
```

### Identification

#### Client non identifié
```cpp
clt: *
srv: ERROR 01                          // identification nécessaire
```

#### Identification
```cpp
clt: LOGIN <pseudo>

srv: OKAY!                             // pseudo validé et enregistré par le serveur

srv: ERROR 20                          // pseudo invalide
srv: ERROR 23                          // pseudo déjà pris
```

### Rejoindre un groupe

```cpp
clt: ENTER <group>

srv: OKAY!                             // au client
srv: ENTER <group> <pseudo> <ts>       // aux membres du groupe

srv: ERROR 31                          // groupe inexistant
srv: ERROR 35                          // déjà dans le groupe
srv: ERROR 36                          // groupe plein
```

### Quitter un groupe

```cpp
clt: LEAVE <group>

srv: OKAY!                             // au client
srv: LEAVE <group> <pseudo> <ts>       // aux membres du groupe

srv: ERROR 31                          // groupe inexistant
srv: ERROR 34                          // pas dans le groupe
```

### Lister les membres du groupe

```cpp
clt: LSMEM <group>

srv: LSMEM <group> <nb>                // nombre de membres
srv: <pseudo>                          // <nb> ligne de pseudo

srv: ERROR 31                          // groupe inexistant
srv: ERROR 34                          // pas dans le groupe
```

### Créer un groupe

```cpp
clt: CREAT <group>

srv: OKAY!

srv: ERROR 30                          // nom de groupe invalide
srv: ERROR 33                          // groupe existant
```

### Envoyer des messages dans un groupe

```cpp
clt: SPEAK <group>
clt: <message-multiligne>

srv: SPEAK <pseudo> <group> <ts>       // aux membres du groupe
srv: <message-multiligne>

srv: ERROR 31                          // groupe inexistant
srv: ERROR 34                          // pas dans le groupe
srv: ERROR 10                          // argument invalide (message vide)
```

### Envoyer un message privé

```cpp
clt: MSGPV <pseudo>                    // pseudo destinataire
clt: <message-multiligne>

srv: MSGPV <pseudo> <ts>               // pseudo émetteurice
srv: <message-multiligne>

srv: ERROR 21                          // pseudo inexistant
srv: ERROR 10                          // argument invalide (message vide)
```

### Vérification connectivité

```cpp
srv: ALIVE                             // aux clients silencieux depuis plus de 15s

clt: ALIVE
```

## Formats

### Pseudos et nom de groupe

```regex
[a-zA-Z0-9_-]{1,16}
```

### Messages multilignes

```bash
*: <msg>
*: <msg>...
*: .
```