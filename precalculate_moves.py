#!/usr/bin/env python3
"""
Pré-calcul des premiers coups optimaux pour différentes grilles
À exécuter UNE FOIS pour enrichir la base de connaissances
"""
import json
import os
from datetime import datetime

def get_moves(n, max_n, played):
    """Retourne diviseurs et multiples disponibles"""
    moves = []
    for x in range(1, n):
        if n % x == 0 and x not in played:
            moves.append(x)
    for x in range(n * 2, max_n + 1, n):
        if x not in played:
            moves.append(x)
    return sorted(moves)

def minimax(played, max_n, depth=0, max_depth=50):
    """Minimax pour déterminer si position gagnante"""
    if depth > max_depth:
        return None  # Trop profond, incertain
    
    if not played:
        return False
    
    last = played[-1]
    avail = get_moves(last, max_n, played)
    
    if not avail:
        return True  # Adversaire coincé = on gagne
    
    # Si adversaire a AU MOINS UN coup gagnant, on perd
    for m in avail:
        result = minimax(played + [m], max_n, depth + 1, max_depth)
        if result is None:
            return None  # Incertain
        if result:  # Adversaire gagne avec ce coup
            return False  # Donc on perd
    
    return True  # Tous les coups adversaire perdent = on gagne

def compute_first_moves(grid_size):
    """Calcule tous les premiers coups pour une grille"""
    print(f"\n{'='*60}")
    print(f"Grille {grid_size} : Calcul des premiers coups...")
    print(f"{'='*60}")
    
    results = {}
    
    # Tester tous les nombres pairs (premiers coups possibles)
    for first_move in range(2, grid_size + 1, 2):
        print(f"  Test {first_move}...", end=" ", flush=True)
        result = minimax([first_move], grid_size)
        
        if result is None:
            print("⚠️  Incertain (trop complexe)")
            continue
        
        outcome = 'win' if result else 'lose'
        results[str(first_move)] = {
            'outcome': outcome,
            'confidence': 1.0,
            'depth': 99,
            'wins': 1 if outcome == 'win' else 0,
            'losses': 1 if outcome == 'lose' else 0,
            'verified_count': 1,
            'is_terminal': True,
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'note': 'Pre-calculated first move'
        }
        print(f"{'✅ WIN' if result else '❌ LOSE'}")
    
    return results

def inject_into_knowledge(grid_size, sequences):
    """Injecte les séquences dans le fichier knowledge"""
    knowledge_dir = 'knowledge'
    os.makedirs(knowledge_dir, exist_ok=True)
    
    filename = os.path.join(knowledge_dir, f'knowledge_{grid_size}.json')
    
    # Charger existant si présent
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'grid_size': grid_size,
            'version': '2.0',
            'sequences': {},
            'stats': {}
        }
    
    # Fusionner
    data['sequences'].update(sequences)
    data['last_updated'] = datetime.now().isoformat()
    data['stats'] = {
        'total_sequences': len(data['sequences']),
        'pre_calculated': len(sequences)
    }
    
    # Sauvegarder
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(sequences)} séquences injectées dans {filename}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🚀 PRÉ-CALCUL DES PREMIERS COUPS OPTIMAUX")
    print("="*60)
    
    # Grille 20 : rapide, peut tout calculer
    #sequences_20 = compute_first_moves(20)
    #inject_into_knowledge(20, sequences_20)
    
    # Grille 40 : un peu plus long
    sequences_50 = compute_first_moves(50)
    inject_into_knowledge(50, sequences_50)
    
    print("\n" + "="*60)
    print("✅ PRÉ-CALCUL TERMINÉ !")
    print("="*60)
    print("\nLa base de connaissances est maintenant enrichie.")
    print("Les premiers coups seront instantanés ! ⚡")
