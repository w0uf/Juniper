#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de livre d'ouvertures pour Juniper
Format compact type échecs : 1. 2! 4!? 2. 20 10 3. 5...
"""

import json
import os
from collections import defaultdict


def get_move_notation(seqs, position_before, move_played, grid_size):
    """
    Détermine la notation d'un coup selon les critères :
    !   = Voie gagnante parmi les plus rapides (optimal)
    ?   = Voie perdante alors qu'une gagnante existait (erreur)
    !?  = Voie perdante mais résistante (pose difficultés)
    ''  = Autres cas
    """
    # Position après le coup
    if position_before:
        position_after = f"{position_before}-{move_played}"
    else:
        position_after = str(move_played)
    
    after_data = seqs.get(position_after)
    if not after_data:
        return ''
    
    # Chercher tous les coups alternatifs depuis position_before
    all_alternatives = {}
    for key, data in seqs.items():
        if position_before:
            if key.startswith(position_before + '-') and key.count('-') == position_before.count('-') + 1:
                alt_move = key.split('-')[-1]
                all_alternatives[alt_move] = data
        else:
            # Premier coup
            if '-' not in key:
                all_alternatives[key] = data
    
    # Outcome du coup joué
    # IMPORTANT : outcome est pour le joueur AU TRAIT (qui doit jouer maintenant)
    # Si outcome='win' → le joueur qui va jouer gagne → mon coup était mauvais
    # Si outcome='lose' → le joueur qui va jouer perd → mon coup était bon
    outcome_after = after_data['outcome']
    i_win = (outcome_after == 'win')  # Si la position est WIN pour moi (au trait), c'est bon
    
    # Chercher coups alternatifs gagnants (positions WIN pour le joueur au trait)
    winning_alternatives = [
        move for move, data in all_alternatives.items()
        if data['outcome'] == 'win'  # WIN pour le joueur au trait
    ]
    
    if i_win:
        # Coup gagnant
        if len(winning_alternatives) <= 3:
            # Peu d'alternatives gagnantes, c'est optimal
            return '!'
        else:
            # Beaucoup de coups gagnent, c'est un parmi d'autres
            return ''
    else:
        # Coup perdant
        if winning_alternatives:
            # Erreur : il existait un coup gagnant
            return '?'
        else:
            # Tous les coups perdent (défense)
            # Vérifier si résistant (pose difficultés)
            difficulty = get_position_difficulty(seqs, position_after)
            if difficulty >= 0.25:  # 25%+ de pièges
                return '!?'
            else:
                return ''


def get_position_difficulty(seqs, position):
    """
    Calcule la difficulté d'une position perdante
    = % de continuations qui font perdre l'adversaire
    """
    continuations = []
    for key, data in seqs.items():
        if key.startswith(position + '-') and key.count('-') == position.count('-') + 1:
            continuations.append(data['outcome'])
    
    if not continuations:
        return 0.0
    
    # 'win' = je gagne après cette continuation (position difficile pour l'adversaire)
    winning_count = continuations.count('win')
    return winning_count / len(continuations)


def generate_opening_line(seqs, current_position, max_depth=10, current_depth=0):
    """
    Génère une ligne d'ouverture au format compact
    Returns: string like "1. 2! 4!? 2. 20 10 3. 5..."
    """
    if current_depth >= max_depth:
        return ""
    
    # Trouver tous les coups possibles depuis cette position
    moves = {}
    for key, data in seqs.items():
        if current_position:
            if key.startswith(current_position + '-') and key.count('-') == current_position.count('-') + 1:
                move = key.split('-')[-1]
                moves[move] = data
        else:
            # Premier coup
            if '-' not in key:
                moves[key] = data
    
    if not moves:
        return ""
    
    # Notation et tri
    moves_with_notation = {}
    for move in moves.keys():
        notation = get_move_notation(seqs, current_position, move, None)
        moves_with_notation[move] = notation
    
    # Trier par ordre numérique
    sorted_moves = sorted(moves_with_notation.keys(), key=int)
    
    # Construire la ligne
    move_number = current_depth + 1
    parts = []
    
    # Afficher le numéro de coup
    parts.append(f"{move_number}.")
    
    # Afficher tous les coups avec leur notation
    move_strs = []
    for move in sorted_moves:
        notation = moves_with_notation[move]
        move_strs.append(f"{move}{notation}")
    
    parts.extend(move_strs)
    
    line = " ".join(parts)
    
    # Pour la ligne principale, continuer avec le premier coup gagnant
    # ou le coup avec notation spéciale
    next_move = None
    for move in sorted_moves:
        notation = moves_with_notation[move]
        if notation in ['!', '!!']:
            next_move = move
            break
    
    if not next_move and sorted_moves:
        next_move = sorted_moves[0]
    
    if next_move:
        if current_position:
            next_position = f"{current_position}-{next_move}"
        else:
            next_position = next_move
        
        continuation = generate_opening_line(seqs, next_position, max_depth, current_depth + 1)
        if continuation:
            line += " " + continuation
    
    return line


def generate_opening_book(knowledge_file, max_depth=10):
    """
    Génère le livre d'ouvertures depuis un fichier JSON
    Affiche toutes les parties (séquences) comme des lignes
    """
    with open(knowledge_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    grid_size = data['grid_size']
    seqs = data['sequences']
    
    print(f"📖 LIVRE D'OUVERTURES - GRILLE {grid_size}")
    print("=" * 70)
    print()
    
    # Collecter toutes les séquences et les trier par longueur puis alphabétiquement
    all_sequences = []
    for key in seqs.keys():
        depth = len(key.split('-'))
        if depth <= max_depth:
            all_sequences.append(key)
    
    # Trier pour regrouper les variantes ensemble
    # Ex: "2", "2-4", "2-4-12", "2-6", "4", "4-8"
    all_sequences.sort(key=lambda x: [int(m) for m in x.split('-')])
    
    # Afficher chaque séquence comme une partie
    for seq_key in all_sequences:
        line = format_sequence_as_game(seqs, seq_key)
        if line:
            print(line)
    
    print()
    
    # Statistiques
    total_positions = len(seqs)
    depths = defaultdict(int)
    for key in seqs.keys():
        depth = len(key.split('-'))
        depths[depth] += 1
    
    print("=" * 70)
    print(f"📊 STATISTIQUES :")
    print(f"   Total positions : {total_positions}")
    for depth in sorted(depths.keys())[:5]:
        print(f"   Profondeur {depth} : {depths[depth]} positions")


def format_sequence_as_game(seqs, sequence_key):
    """
    Formate une séquence comme une partie d'échecs
    Ex: "2-4-12-6-3-9" devient "1. 2 4!? 2. 12! 6 3. 3! 9!"
    """
    moves = sequence_key.split('-')
    
    parts = []
    turn_number = 1
    
    for i, move in enumerate(moves):
        # Position avant ce coup
        position_before = "-".join(moves[:i]) if i > 0 else ""
        
        # Notation du coup
        notation = get_move_notation(seqs, position_before, move, None)
        
        # Début d'un nouveau tour (tous les 2 coups)
        if i % 2 == 0:
            parts.append(f"{turn_number}.")
            turn_number += 1
        
        # Ajouter le coup avec sa notation
        parts.append(f"{move}{notation}")
    
    return " ".join(parts)


if __name__ == "__main__":
    import sys
    import os
    
    # Mode interactif si pas d'arguments
    if len(sys.argv) < 2:
        print("📖 GÉNÉRATEUR DE LIVRE D'OUVERTURES JUNIPER")
        print("=" * 70)
        print()
        
        # Lister les fichiers JSON disponibles
        knowledge_dir = 'knowledge'
        if os.path.exists(knowledge_dir):
            json_files = [f for f in os.listdir(knowledge_dir) if f.endswith('.json')]
            
            if json_files:
                print("📁 Fichiers de base disponibles :")
                for i, filename in enumerate(sorted(json_files), 1):
                    filepath = os.path.join(knowledge_dir, filename)
                    # Lire la taille
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            grid = data.get('grid_size', '?')
                            count = len(data.get('sequences', {}))
                        print(f"  {i}. {filename} (grille {grid}, {count} positions)")
                    except:
                        print(f"  {i}. {filename}")
                
                print()
                
                # Demander le choix
                try:
                    choice = input("Choisissez un fichier (numéro) : ").strip()
                    choice_idx = int(choice) - 1
                    
                    if 0 <= choice_idx < len(json_files):
                        selected_file = os.path.join(knowledge_dir, sorted(json_files)[choice_idx])
                    else:
                        print("❌ Numéro invalide")
                        sys.exit(1)
                except (ValueError, KeyboardInterrupt):
                    print("\n❌ Annulé")
                    sys.exit(1)
            else:
                print("❌ Aucun fichier JSON trouvé dans knowledge/")
                sys.exit(1)
        else:
            print("❌ Dossier knowledge/ introuvable")
            print("\nUtilisation : python generate_opening_book.py <fichier.json> [profondeur]")
            sys.exit(1)
        
        # Demander la profondeur
        try:
            depth_input = input("Profondeur maximale d'analyse (défaut 10) : ").strip()
            max_depth = int(depth_input) if depth_input else 10
        except ValueError:
            max_depth = 10
        
        print()
        
    else:
        # Mode ligne de commande
        selected_file = sys.argv[1]
        max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    if not os.path.exists(selected_file):
        print(f"❌ Fichier non trouvé : {selected_file}")
        sys.exit(1)
    
    generate_opening_book(selected_file, max_depth)
