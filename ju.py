# -*- coding: utf-8 -*-
# Juniper-U est développé par Wouf (2018)


import random, webbrowser
from tkinter import *
from tkinter import messagebox

# les variables globales
IA = False  # c'estl IA qui commence (bascule si new game)
partieencours = False
partie = []
scoreIA, scorejoueur = 0, 0


class Juniper:
    def __init__(self, partie, IA_turn):
        self.partie = partie
        self.IA_turn = IA_turn  # est-ce à l'IA de jouer ?
        self.variantes = [x for x in range(1, 21) if x not in partie and (partie[-1] % x == 0 or x % partie[-1] == 0)]
        self.fini = (len(self.variantes) == 0)

    def __repr__(self):
        debug = str(self.partie)
        debug += "\n"
        debug += "                     " + str(self.variantes)
        debug += "\n"
        if self.fini:
            debug += "partie  terminée"
        else:
            debug += "partie en cours"
        debug += "\n"
        if self.IA_turn:
            debug += "C'est à l'ordinateur de joué"
        else:
            debug += "C'est au joueur de joué"

        debug += "\n -------------------------------------------------------------"
        return debug


def aide():
    message = """Le jeu de Juniper green

    Je choisis un nombre entre 1 et 20
    À tour de rôle, chaque joueur doit choisir un nombre parmi les multiples ou les diviseurs du nombre choisi précédemment par son adversaire 
    Un nombre ne peut être joué qu'une seule fois.

    Le premier nombre choisi doit être pair !
    La partie se joue en (au moins) deux manches, je commence la première, vous commencez la deuxième !

    Développé par Wouf sur Python 3.6.4 ce petit soft est gratuit, et ne peut être vendu!
    Mais rien ne vous empèche de faire un petit don paypal à wouf@libertysurf.fr !

    Les sources et des notions de stratégie sont disponibles sur:
    http://site2wouf.fr/juniper

    Vous pouvez aussi y poser des questions !

    wOuf
    """
    messagebox.showinfo("Aide", message)


def lien():
    webbrowser.open('http://site2wouf.fr/juniper')


def affichscore():
    return "IA  :" + str(scoreIA) + "    JOUEUR :" + str(scorejoueur)


def affichpartie():
    if IA:
        libele = "IA - JOUEUR :"
    else:
        libele = "JOUEUR - IA :"
    libele += "\n"
    for x in partie:
        libele += str(x) + "-"
    return libele


def newgame():
    global partieencours, scoreIA, IA, partie
    if partieencours:
        if messagebox.askyesno("Abandon ?", "Vous abandonnez la partie en cours ?"):
            partieencours = False
            partie = []
            for i in button:
                i.configure(state="normal")
            scoreIA += 1
            IA = not IA

            label1.configure(text=affichpartie())
            label3.configure(text=affichscore())
            exit


    else:
        partie = []
        IA = not IA
        for i in button:
            i.configure(state="normal")
        label3.configure(text=affichscore())
        label1.configure(text=affichpartie())
        partieencours = True
        if IA:
            jouer(partie)


def fonction(x):
    global partie
    if len(partie) == 0:
        if x % 2 == 0:
            partie.append(x)
            button[x - 1].configure(state="disabled")
            label1.configure(text=affichpartie())
            jouer(partie)
    else:
        if partie[-1] % x == 0 or x % partie[-1] == 0:
            partie.append(x)
            button[x - 1].configure(state="disabled")
            label1.configure(text=affichpartie())
            jouer(partie)


def make_children(p):
    """ Cette fonction reçoit un objet de la classe Juniper
    renvoie ses enfants (les sous-variantes)
    en tant qu'objets de la classe Juniper"""

    children = []
    for v in p.variantes:
        children.append(Juniper(p.partie + [v], not p.IA_turn))
    return children


def evalue_noeud(p):
    """ Cette fonction reçoit un objet de la classe Juniper et
    renvoie un booleen :
    True si l'IA gagne en jouant les bons coups coups
    False si le joueur gagne en jouant les bons coups"""

    if p.fini:
        if p.IA_turn:
            return False
        else:
            return True
    else:
        if p.IA_turn:
            t = False
            for enfants in make_children(p):
                t = t or evalue_noeud(enfants)
        else:
            t = True
            for enfants in make_children(p):
                t = t and evalue_noeud(enfants)
        return t


def choix_variante(p):
    global scorejoueur, partieencours, partie
    """ Cette fonction reçoit un objet de la classe Juniper et
    renvoie l'entier qui doit être choisi pour que le joueur
    puisse se tromper dans une variante gagnante pour lui
    avec la frequence la plus grande.

    """

    variantes = p.variantes
    if len(variantes) == 0:
        return 0
    if len(variantes) == 1:
        return variantes[0]
    if 1 in variantes:
        variantes.remove(1)

    return random.choice(variantes)


def perdu():
    global scorejoueur, partieencours
    # perdu
    for i in button:
        i.configure(state="disabled")
    scorejoueur += 1
    label3.configure(text=affichscore())
    messagebox.showinfo("GAME OVER", "Bravo !")
    partieencours = False


def testgain():
    global partie, scoreIA, partieencours
    if len([x for x in range(1, 21) if x not in partie and (partie[-1] % x == 0 or x % partie[-1] == 0)]) == 0:

        scoreIA += 1
        for i in button:
            i.configure(state="disabled")
        label3.configure(text=affichscore())
        partieencours = False
        messagebox.showinfo("GAME OVER", "J'ai gagné !")
        partie = []


def jouer(p=[]):
    """ p est une liste de coups
        c'est à dire la partie.
        Appeler sans parametre elle fait
        commencer l'IA.
        Cette fonction renvoie le coup
        joué par l'IA."""

    if len(p) == 0:
        # IA commence
        choix = random.choice([2, 4, 6, 8, 10, 12, 16, 18, 20])
        button[choix - 1].configure(state="disabled")
        partie.append(choix)
        label1.configure(text=affichpartie())
        testgain()
        return

    p2 = Juniper([int(x) for x in p], True)
    possibles = [i for i in p2.variantes if evalue_noeud(Juniper(p2.partie + [i], False))]
    if len(possibles) != 0:
        ia = random.choice(possibles)
        partie.append(ia)
        label1.configure(text=affichpartie())
        button[ia - 1].configure(state="disabled")
        testgain()
        return

    ia = choix_variante(Juniper(p, True))
    if ia != 0:
        partie.append(ia)
        label1.configure(text=affichpartie())
        button[ia - 1].configure(state="disabled")
        testgain()
    else:
        perdu()
    return


fenetre = Tk()
fenetre.title("JuniPeR-U")
menubar = Menu(fenetre)
menubar.add_command(label="New Game", command=newgame)
menubar.add_command(label="Help", command=aide)
menubar.add_command(label="En ligne", command=lien)
fenetre.config(menu=menubar)
frame1 = Frame(fenetre)
label1 = Label(frame1, text=affichpartie())
label1.pack()
frame1.pack()
frame2 = Frame(fenetre)

button = []
for i in range(1, 21):
    button.append(
        Button(frame2, state="disabled", borderwidth=2, width=6, height=3, text=i, command=lambda i=i: fonction(i)))

    # positionnement
    no = 1
for i in button:
    i.grid(column=(no - 1) % 5, row=(no - 1) // 5)
    no += 1

frame2.pack()
frame3 = Frame(fenetre)  # les scores
label3 = Label(frame3, text=affichscore())
label3.pack()
frame3.pack()
fenetre.mainloop()

