#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Juniper-U - Version Finale avec IA Adaptative
Développé par Wouf (2018-2026)

Fonctionnalités :
- IA adaptative avec apprentissage continu
- Base de connaissances évolutive
- Exploration/Exploitation automatique
- Multilingue (FR/EN extensible)
- 5 tailles de grilles (20/30/40/50/100)
"""

import random
import webbrowser
import json
import os
import sys
import math
import time as time_module
from datetime import datetime
from tkinter import Tk, Toplevel, Menu, messagebox, StringVar, BooleanVar, IntVar, filedialog, Button
import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# SYSTÈME DE TRADUCTION
# ============================================================================

FALLBACK_TEXTS = {
    'app.title': 'Juniper-U',
    'error.no_lang.message': "Fichiers de langue manquants!\nUtilisation du français par défaut.",
    'button.ok': 'OK'
}

class TranslationManager:
    def __init__(self):
        self.texts = {}
        self.current_lang = 'fr'
        self.load_languages()
    
    def load_languages(self):
        locales_dir = 'locales'
        
        if not os.path.exists(locales_dir):
            print(f"Warning: '{locales_dir}' directory not found. Using fallback.")
            self.texts = {'fr': FALLBACK_TEXTS}
            return
        
        for filename in os.listdir(locales_dir):
            if filename.endswith('.json'):
                lang_code = filename.replace('.json', '')
                filepath = os.path.join(locales_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.texts[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")
        
        if not self.texts:
            self.texts = {'fr': FALLBACK_TEXTS}
            messagebox.showwarning("Warning", FALLBACK_TEXTS['error.no_lang.message'])
    
    def get(self, key: str, lang: Optional[str] = None) -> str:
        if lang is None:
            lang = self.current_lang
        
        if lang in self.texts and key in self.texts[lang]:
            return self.texts[lang][key]
        
        if 'fr' in self.texts and key in self.texts['fr']:
            return self.texts['fr'][key]
        
        return key
    
    def get_available_languages(self) -> List[Tuple[str, str]]:
        lang_names = {'fr': 'Français', 'en': 'English'}
        return [(code, lang_names.get(code, code.upper())) for code in self.texts.keys()]
    
    def set_language(self, lang_code: str):
        if lang_code in self.texts:
            self.current_lang = lang_code

i18n = TranslationManager()


# ============================================================================
# GESTION DES PRÉFÉRENCES
# ============================================================================

class PreferencesManager:
    PREFS_FILE = 'juniper_preferences.json'
    
    @classmethod
    def load(cls) -> Dict:
        defaults = {
            'language': 'fr',
            'player_name': 'Joueur',
            'last_grid': 20,
            'last_time_budget': 10  # Changé de 3 à 10
        }
        
        if not os.path.exists(cls.PREFS_FILE):
            return defaults
        
        try:
            with open(cls.PREFS_FILE, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
                return {**defaults, **prefs}
        except:
            return defaults
    
    @classmethod
    def save(cls, prefs: Dict):
        try:
            with open(cls.PREFS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving preferences: {e}")


# ============================================================================
# BASE DE CONNAISSANCES
# ============================================================================

class KnowledgeBase:
    """Gestion de la base de connaissances avec séquences validées"""
    
    def __init__(self):
        self.knowledge_dir = 'knowledge'
        self.sequences = {}
        self.stats = {}
        self.properties = {}  # NOUVEAU : Propriétés des nombres par grille
        self.dirty = False
        self.changes_since_save = 0
        self.last_save = time_module.time()
        
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self.load()
        self._ensure_properties()  # Générer si manquant
    
    def _ensure_properties(self):
        """S'assurer que les propriétés sont calculées pour toutes les grilles"""
        for grid_size in [20, 30, 40, 50, 100]:
            if grid_size not in self.properties or not self.properties[grid_size]:
                print(f"📊 Calcul des propriétés pour grille {grid_size}...")
                self.properties[grid_size] = self._compute_properties(grid_size)
    
    def _compute_properties(self, grid_size: int) -> Dict:
        """Calcule les propriétés STATIQUES de chaque nombre (ne changent jamais)"""
        properties = {}
        
        for n in range(1, grid_size + 1):
            # Liste COMPLÈTE des diviseurs (sans n lui-même)
            divisors = [x for x in range(1, n) if n % x == 0]
            
            # Liste COMPLÈTE des multiples dans la grille
            multiples = list(range(n * 2, grid_size + 1, n))
            
            # Tous les nombres connectés (diviseurs + multiples)
            all_connections = divisors + multiples
            
            properties[str(n)] = {
                'divisors': divisors,              # Liste STATIQUE
                'multiples': multiples,            # Liste STATIQUE
                'all_connections': all_connections, # Liste STATIQUE
                'total_static': len(all_connections) # Connexions max théoriques
            }
        
        return properties
    
    def get_dynamic_connections(self, grid_size: int, number: int, 
                               already_played: List[int]) -> List[int]:
        """Retourne les connexions ACTUELLES (après avoir retiré les coups joués)"""
        props = self.get_properties(grid_size, number)
        
        # Connexions statiques
        all_static = props.get('all_connections', [])
        
        # Filtrer ce qui est déjà joué
        dynamic = [x for x in all_static if x not in already_played and x != number]
        
        return dynamic
    
    def get_available_from_number(self, grid_size: int, number: int, 
                                   already_played: List[int]) -> List[int]:
        """Retourne les coups jouables après un nombre (ultra-rapide)"""
        props = self.get_properties(grid_size, number)
        
        # Connexions = diviseurs + multiples
        connections = props.get('all_connections', [])
        
        # Filtrer ce qui est déjà joué
        available = [x for x in connections if x not in already_played]
        
        return available
    
    def analyze_move_quality(self, grid_size: int, move: int, 
                             already_played: List[int]) -> Dict:
        """Analyse la qualité d'un coup EN TENANT COMPTE des coups déjà joués"""
        
        # Connexions ACTUELLES après ce coup
        remaining = self.get_dynamic_connections(grid_size, move, already_played + [move])
        
        # Analyser qualité des coups suivants possibles
        next_moves_quality = []
        for next_move in remaining[:5]:  # Top 5
            # Connexions après avoir joué move PUIS next_move
            next_connections = self.get_dynamic_connections(
                grid_size, 
                next_move, 
                already_played + [move, next_move]
            )
            next_moves_quality.append({
                'move': next_move,
                'connections_after': len(next_connections)
            })
        
        return {
            'move': move,
            'connections_now': len(remaining),  # Connexions MAINTENANT
            'is_trap': len(remaining) < 3,
            'best_next_moves': sorted(next_moves_quality, 
                                     key=lambda x: x['connections_after'], 
                                     reverse=True)
        }
    
    def get_properties(self, grid_size: int, number: int) -> Dict:
        """Récupère les propriétés d'un nombre"""
        if grid_size not in self.properties:
            self.properties[grid_size] = self._compute_properties(grid_size)
        
        return self.properties[grid_size].get(str(number), {})
    
    def get_best_moves_by_connections(self, grid_size: int, available: List[int], 
                                     already_played: List[int],
                                     min_connections: int = 5) -> List[Tuple[int, int]]:
        """Retourne les coups triés par connexions DYNAMIQUES (tenant compte des coups joués)"""
        scored = []
        
        for move in available:
            # Connexions dynamiques après avoir joué ce coup
            remaining = self.get_dynamic_connections(grid_size, move, already_played + [move])
            total = len(remaining)
            
            if total >= min_connections:
                scored.append((move, total))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def load(self):
        """Charge toutes les bases de connaissances"""
        COMPATIBLE_VERSION = "2.0"
        
        for grid_size in [20, 30, 40, 50, 100]:
            filename = os.path.join(self.knowledge_dir, f'knowledge_{grid_size}.json')
            
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # Vérifier version
                        file_version = data.get('version', '1.0')
                        if file_version != COMPATIBLE_VERSION:
                            print(f"⚠️  Version incompatible : {filename} (v{file_version}, attendu v{COMPATIBLE_VERSION})")
                            print(f"   → Fichier ignoré, nouvelle base créée")
                            self.sequences[grid_size] = {}
                            self.stats[grid_size] = {}
                            self.properties[grid_size] = {}
                            continue
                        
                        self.sequences[grid_size] = data.get('sequences', {})
                        self.stats[grid_size] = data.get('stats', {})
                        self.properties[grid_size] = data.get('properties', {})
                        print(f"📚 Base chargée : grille {grid_size} ({len(self.sequences[grid_size])} séquences)")
                except Exception as e:
                    print(f"❌ Erreur chargement {filename}: {e}")
                    print(f"   → Fichier corrompu, nouvelle base créée")
                    self.sequences[grid_size] = {}
                    self.stats[grid_size] = {}
                    self.properties[grid_size] = {}
            else:
                self.sequences[grid_size] = {}
                self.stats[grid_size] = {}
                self.properties[grid_size] = {}
    
    def get_sequence(self, grid_size: int, sequence_key: str) -> Optional[Dict]:
        """Récupère une séquence validée"""
        return self.sequences.get(grid_size, {}).get(sequence_key)
    
    def update_sequence(self, grid_size: int, sequence_key: str, outcome: str, 
                       confidence: float, depth: int, is_terminal: bool = False):
        """
        Met à jour ou crée une séquence
        
        is_terminal : True si la partie est TERMINÉE (aucun coup disponible)
                      → confiance = 1.0 (certitude absolue)
        """
        if grid_size not in self.sequences:
            self.sequences[grid_size] = {}
        
        if sequence_key not in self.sequences[grid_size]:
            # Première fois : utiliser la confiance fournie
            self.sequences[grid_size][sequence_key] = {
                'outcome': outcome,
                'confidence': 1.0 if is_terminal else confidence,
                'depth': depth,
                'wins': 1 if outcome == 'win' else 0,
                'losses': 1 if outcome == 'lose' else 0,
                'verified_count': 1,
                'is_terminal': is_terminal,
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            cert = "✓ CERTAIN" if is_terminal else f"~{confidence:.2f}"
            print(f"  ➕ Nouvelle séquence : {sequence_key} → {outcome} ({cert})")
        else:
            seq = self.sequences[grid_size][sequence_key]
            
            # Si déjà terminal, garder confiance 1.0
            if seq.get('is_terminal', False):
                return
            
            # Si devient terminal maintenant
            if is_terminal:
                seq['confidence'] = 1.0
                seq['is_terminal'] = True
                seq['outcome'] = outcome  # Mettre à jour le résultat définitif
                seq['last_updated'] = datetime.now().isoformat()
                return
            
            # Sinon, mise à jour statistique normale
            if outcome == 'win':
                seq['wins'] = seq.get('wins', 0) + 1
            else:
                seq['losses'] = seq.get('losses', 0) + 1
            
            seq['verified_count'] = seq.get('verified_count', 0) + 1
            
            # Confiance basée sur cohérence + profondeur
            total = seq['wins'] + seq['losses']
            win_rate = seq['wins'] / total if total > 0 else 0.5
            
            # Si 100% cohérent ET profondeur élevée → quasi-certain
            if (win_rate == 1.0 or win_rate == 0.0) and depth >= 15:
                seq['confidence'] = 0.98
            elif (win_rate == 1.0 or win_rate == 0.0) and depth >= 10:
                seq['confidence'] = 0.95
            else:
                # Confiance selon cohérence
                confidence_from_rate = abs(win_rate - 0.5) * 2  # 0.5→0, 1.0→1.0
                verification_bonus = min(0.2, seq['verified_count'] * 0.01)
                seq['confidence'] = min(0.90, confidence_from_rate + verification_bonus)
            
            seq['depth'] = max(seq.get('depth', 0), depth)  # Garder max depth
            seq['last_updated'] = datetime.now().isoformat()
        
        self.dirty = True
        self.changes_since_save += 1
        
        # Sauvegarde PLUS FRÉQUENTE pour debug
        if self.changes_since_save >= 10 or \
           time_module.time() - self.last_save > 60:
            print(f"💾 Auto-sauvegarde ({self.changes_since_save} modifications)")
            self.save()
    
    def propagate_certainties(self, grid_size: int):
        """
        Remonte les certitudes depuis les positions terminales
        
        RÈGLES :
        1. On ne peut propager QUE si TOUS les coups possibles sont explorés
        2. Logique : Si c'est mon tour et TOUS mes coups gagnent → je gagne
                     Si c'est mon tour et TOUS mes coups perdent → je perds
        3. On propage uniquement les certitudes (1.0)
        """
        
        changed = True
        iterations = 0
        max_iterations = 10
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for seq_key, seq_data in list(self.sequences.get(grid_size, {}).items()):
                
                # Si déjà certain, skip
                if seq_data.get('confidence', 0) >= 0.99:
                    continue
                
                # Reconstruire l'état pour cette séquence
                moves = [int(m) for m in seq_key.split('-')] if seq_key else []
                state = GameState(moves=moves, max_n=grid_size)
                
                # Qui joue après cette séquence ?
                next_player = state.current_player
                
                # TOUS les coups possibles
                all_possible_moves = state.available_moves
                
                if not all_possible_moves:
                    continue
                
                # Vérifier qu'on a exploré TOUS les coups
                children_data = []
                all_explored = True
                
                for next_move in all_possible_moves:
                    child_key = f"{seq_key}-{next_move}" if seq_key else str(next_move)
                    child_seq = self.get_sequence(grid_size, child_key)
                    
                    if not child_seq or child_seq.get('confidence', 0) < 0.99:
                        # Branche manquante ou incertaine
                        all_explored = False
                        break
                    
                    children_data.append({
                        'move': next_move,
                        'outcome': child_seq['outcome']
                    })
                
                # Si on n'a pas TOUT exploré, on ne peut PAS propager
                if not all_explored:
                    continue
                
                # Maintenant on peut propager !
                child_outcomes = [c['outcome'] for c in children_data]
                
                # LOGIQUE MINIMAX CORRECTE :
                # Parent = WIN  ⟺  TOUS les enfants = LOSE (adversaire perd toujours)
                # Parent = LOSE ⟺  AU MOINS UN enfant = WIN (adversaire a un coup gagnant)
                
                wins = child_outcomes.count('win')
                losses = child_outcomes.count('lose')
                total = len(child_outcomes)
                
                if losses == total:
                    # TOUS les coups perdent → parent gagne
                    parent_outcome = 'win'
                elif wins >= 1:
                    # Au moins un coup gagne → parent perd (adversaire le jouera)
                    parent_outcome = 'lose'
                else:
                    # Cas impossible normalement (on a vérifié que tous sont certains)
                    continue
                
                # Mettre à jour le parent
                seq_data['outcome'] = parent_outcome
                seq_data['confidence'] = 1.0
                seq_data['is_terminal'] = True
                changed = True
                print(f"  🔼 Propagation : {seq_key} → {parent_outcome.upper()} (1.0) [toutes branches explorées]")
        
        # Message supprimé pour lisibilité console
        # if iterations > 0:
        #     print(f"✅ Propagation terminée après {iterations} itération(s)")
        
        return changed
    
    def is_saturated(self, grid_size: int, sequence_key: str) -> bool:
        """Vérifie si une séquence est saturée (bien connue)"""
        seq = self.get_sequence(grid_size, sequence_key)
        
        if not seq:
            return False
        
        return seq['confidence'] >= 0.95 and seq.get('verified_count', 0) >= 30
    
    def find_shortest_unsaturated(self, grid_size: int, max_results: int = 5) -> List[str]:
        """Trouve les séquences non saturées les plus courtes"""
        unsaturated = []
        
        # Parcourir par profondeur croissante
        for depth in range(1, 10):
            for seq_key in self.sequences.get(grid_size, {}):
                if len(seq_key.split('-')) != depth:
                    continue
                
                if not self.is_saturated(grid_size, seq_key):
                    unsaturated.append(seq_key)
            
            if len(unsaturated) >= max_results:
                return unsaturated[:max_results]
        
        return unsaturated
    
    def get_any_uncertain_position(self, max_depth: int = 6) -> Optional[str]:
        """Trouve n'importe quelle position avec confiance < 0.99"""
        for grid_size in self.sequences.keys():
            for seq_key, seq_data in self.sequences[grid_size].items():
                if len(seq_key.split('-')) > max_depth:
                    continue
                confidence = seq_data.get('confidence', 0)
                if confidence < 0.99:
                    return seq_key
        return None
    
    def get_coverage(self, grid_size: int) -> float:
        """Calcule le taux de couverture"""
        if grid_size not in self.sequences:
            return 0.0
        
        total_sequences = len(self.sequences[grid_size])
        saturated_sequences = sum(
            1 for seq_key in self.sequences[grid_size]
            if self.is_saturated(grid_size, seq_key)
        )
        
        return saturated_sequences / total_sequences if total_sequences > 0 else 0.0
    
    def save(self):
        """Sauvegarde toutes les bases (SANS les propriétés - calculées en mémoire)"""
        
        # AVANT de sauvegarder : propager les certitudes !
        for grid_size in self.sequences.keys():
            if len(self.sequences.get(grid_size, {})) > 10:  # Si assez de données
                self.propagate_certainties(grid_size)
        
        for grid_size in self.sequences.keys():
            filename = os.path.join(self.knowledge_dir, f'knowledge_{grid_size}.json')
            
            data = {
                'grid_size': grid_size,
                'version': '2.0',
                'last_updated': datetime.now().isoformat(),
                'sequences': self.sequences[grid_size],
                'stats': {
                    'total_sequences': len(self.sequences[grid_size]),
                    'coverage': self.get_coverage(grid_size)
                }
            }
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving {filename}: {e}")
        
        self.dirty = False
        self.changes_since_save = 0
        self.last_save = time_module.time()
        # Message supprimé pour lisibilité console
        # print("💾 Base de connaissances sauvegardée")

knowledge = KnowledgeBase()


# ============================================================================
# LOGIQUE DE JEU
# ============================================================================

class Player(Enum):
    IA = "IA"
    HUMAN = "JOUEUR"


@dataclass
class GameState:
    moves: List[int] = field(default_factory=list)
    current_player: Player = Player.HUMAN
    max_n: int = 20
    resigned: bool = False
    
    @property
    def last_move(self) -> Optional[int]:
        return self.moves[-1] if self.moves else None
    
    @property
    def available_moves(self) -> List[int]:
        if not self.moves:
            return [x for x in range(2, self.max_n + 1, 2)]
        
        last = self.last_move
        return [
            x for x in range(1, self.max_n + 1)
            if x not in self.moves and (last % x == 0 or x % last == 0)
        ]
    
    @property
    def is_finished(self) -> bool:
        return len(self.available_moves) == 0
    
    def copy_with_move(self, move: int, next_player: Player) -> 'GameState':
        return GameState(
            moves=self.moves + [move],
            current_player=next_player,
            max_n=self.max_n
        )


class AdaptiveAI:
    """IA adaptative avec apprentissage continu"""
    
    @staticmethod
    def minimax_alpha_beta(state: GameState, depth: int, max_depth: int,
                          alpha: float, beta: float, is_ia: bool) -> bool:
        """Minimax avec Alpha-Beta pruning"""
        remaining = len(state.available_moves)
        
        if state.is_finished or depth >= max_depth:
            return not is_ia
        
        # Profondeur adaptative en fin de partie
        if remaining <= 5:
            max_depth = 99
        
        if is_ia:
            for move in state.available_moves:
                next_state = state.copy_with_move(move, Player.HUMAN)
                if AdaptiveAI.minimax_alpha_beta(next_state, depth + 1, max_depth, alpha, beta, False):
                    return True
                alpha = max(alpha, 0)
                if beta <= alpha:
                    break
            return False
        else:
            for move in state.available_moves:
                next_state = state.copy_with_move(move, Player.IA)
                if not AdaptiveAI.minimax_alpha_beta(next_state, depth + 1, max_depth, alpha, beta, True):
                    return False
                beta = min(beta, 1)
                if beta <= alpha:
                    break
            return True
    
    @staticmethod
    def find_move_with_time_budget(state: GameState, time_budget: float) -> int:
        """
        Trouve le meilleur coup avec budget temps
        Utilise TOUT le temps disponible pour apprendre !
        Learning se fait AVANT de jouer (meilleure perception UX)
        """
        start_time = time_module.time()
        current_key = "-".join(map(str, state.moves))
        
        # === PHASE 1 : Lookup rapide (< 0.01s) ===
        quick_move = AdaptiveAI._quick_lookup(state, current_key)
        
        chosen_move = None
        
        if quick_move is not None:
            # Trouvé instantanément !
            print(f"✅ Exploit réussi : {quick_move}")
            chosen_move = quick_move
        else:
            # === PHASE 2 : Pas trouvé → Calculer ===
            print(f"⚠️  Position inconnue, calcul")
            
            # CRITIQUE : Grille 40+ = TOUJOURS HEURISTIQUE
            if state.max_n >= 40:
                print(f"🎲 Grille {state.max_n} : heuristique obligatoire (minimax impossible)")
                if len(state.moves) == 0:
                    chosen_move = AdaptiveAI._heuristic_first_move(state)
                else:
                    chosen_move = AdaptiveAI._quick_heuristic_move(state)
            
            # Grilles ≤30 = minimax possible
            elif state.max_n <= 30:
                print(f"🎯 Grille {state.max_n} : calcul minimax adaptatif")
                chosen_move = AdaptiveAI._minimax_move(state, time_budget * 0.6)
        
        # === PHASE 3 : APPRENTISSAGE avec le temps restant (AVANT de jouer) ===
        time_used = time_module.time() - start_time
        learning_time = time_budget - time_used - 0.2  # Garder 0.2s de marge
        
        print(f"⏱️  Coup décidé en {time_used:.2f}s / {time_budget:.1f}s → Apprentissage: {learning_time:.2f}s")
        
        if learning_time > 0.5:
            print(f"📚 Apprentissage approfondi pendant {learning_time:.1f}s...")
            AdaptiveAI._deep_learning(state, learning_time)
            print(f"✅ Apprentissage terminé, je joue : {chosen_move}")
        elif learning_time > 0:
            # Petit délai psychologique minimum (0.5s)
            import time
            time.sleep(min(0.5, learning_time))
        
        return chosen_move
    
    @staticmethod
    def _heuristic_first_move(state: GameState) -> int:
        """Heuristique rapide pour premier coup sur grandes grilles"""
        # Sur grandes grilles, éviter petits nombres
        if state.max_n >= 40:
            available = [x for x in range(10, state.max_n + 1, 2)]  # Commence à 10
        else:
            available = [x for x in range(2, state.max_n + 1, 2)]
        
        # Utiliser les connexions DYNAMIQUES
        scored = knowledge.get_best_moves_by_connections(
            state.max_n, 
            available,
            state.moves,  # Coups déjà joués
            min_connections=8
        )
        
        if scored:
            # Garder top 30%
            top_count = max(3, len(scored) // 3)
            top_moves = [m for m, _ in scored[:top_count]]
            
            choice = random.choice(top_moves)
            # Afficher connexions dynamiques
            dynamic_conn = knowledge.get_dynamic_connections(state.max_n, choice, state.moves + [choice])
            print(f"  🎲 Heuristique : {choice} ({len(dynamic_conn)} connexions disponibles)")
            return choice
        
        # Fallback : au moins éviter les très petits
        if state.max_n >= 40:
            safe = [x for x in available if x >= state.max_n // 4]
            if safe:
                return random.choice(safe)
        
        print(f"  ⚠️ Aucun coup avec 8+ connexions, choix aléatoire")
        return random.choice(available)
    
    @staticmethod
    def _quick_heuristic_move(state: GameState) -> int:
        """
        Coup heuristique avec lookahead 2 coups (< 0.5s)
        Évalue la qualité en simulant les réponses adversaire
        ET enrichit la base quand on découvre des positions terminales !
        """
        available = state.available_moves
        
        if not available:
            return None
        
        # RÈGLE CRITIQUE : Si le dernier coup adverse était 1, jouer un GRAND PREMIER !
        if len(state.moves) > 0 and state.moves[-1] == 1:
            # Chercher le plus grand nombre premier disponible
            primes = []
            for n in available:
                if n > state.max_n * 0.8:  # Grands nombres seulement
                    # Vérifier si premier
                    is_prime = n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))
                    if is_prime:
                        primes.append(n)
            
            if primes:
                choice = max(primes)  # Le plus grand premier
                print(f"  🎯 Adversaire a joué 1 → Grand premier : {choice}")
                return choice
        
        # TOUJOURS filtrer 1 (piège mortel pour celui qui le joue)
        if len(available) > 1 and 1 in available:
            available = [x for x in available if x != 1]
        
        # Si un seul coup, le jouer
        if len(available) == 1:
            return available[0]
        
        # Limiter le nombre de candidats si trop nombreux
        if len(available) > 10:
            # Pré-filtrer par connexions pour réduire
            prefilter = knowledge.get_best_moves_by_connections(
                state.max_n,
                available,
                state.moves,
                min_connections=3
            )
            if prefilter:
                available = [m for m, _ in prefilter[:10]]
        
        # RÈGLE CRITIQUE : Éliminer les coups qui ne laissent que "1" après riposte adverse
        # ET enrichir la base avec ces positions perdantes !
        safe_moves = []
        trapped_count = 0
        
        for move in available:
            next_state = state.copy_with_move(move, Player.HUMAN)
            adversary_moves = next_state.available_moves
            
            # Vérifier chaque riposte adverse
            is_safe = True
            for adv_move in adversary_moves[:5]:  # Limiter à 5 ripostes max
                after_adv = next_state.copy_with_move(adv_move, Player.IA)
                my_options_after = after_adv.available_moves
                
                # Si je n'ai que [1] ou [] après cette riposte = PIÈGE !
                if len(my_options_after) == 0 or (len(my_options_after) == 1 and 1 in my_options_after):
                    is_safe = False
                    
                    # ENRICHIR LA BASE : Cette séquence mène à LOSE !
                    trapped_seq_key = "-".join(map(str, after_adv.moves))
                    knowledge.update_sequence(
                        state.max_n,
                        trapped_seq_key,
                        'lose',
                        0.95,  # Haute confiance (détection heuristique)
                        depth=2,
                        is_terminal=False
                    )
                    trapped_count += 1
                    break
            
            if is_safe:
                safe_moves.append(move)
        
        if trapped_count > 0:
            print(f"  📚 Enrichissement filtrage : +{trapped_count} positions piégées détectées")
        
        # Garder les coups sûrs, sinon garder tous (pas le choix)
        if safe_moves:
            available = safe_moves
        
        # LOOKAHEAD 2 coups : évaluer chaque candidat
        evaluated = []
        enriched_count = 0
        
        for move in available:
            # Simuler notre coup
            next_state = state.copy_with_move(move, Player.HUMAN)
            adversary_moves = next_state.available_moves
            
            # Construire la clé de séquence
            our_seq_key = "-".join(map(str, next_state.moves))
            
            if not adversary_moves:
                # Adversaire coincé = TERMINAL = WIN !
                # ENRICHIR LA BASE ! 📚
                knowledge.update_sequence(
                    state.max_n,
                    our_seq_key,
                    'win',
                    1.0,
                    2,  # depth 2 (lookahead)
                    is_terminal=True
                )
                enriched_count += 1
                evaluated.append((move, 1000))
                continue
            
            # Évaluer les réponses adversaire
            our_options_after = []
            
            for adv_move in adversary_moves[:8]:  # Limiter à 8 réponses max
                # Simuler la réponse adversaire
                after_adv = next_state.copy_with_move(adv_move, Player.IA)
                our_moves_after = after_adv.available_moves
                
                # Construire la clé après réponse adversaire
                adv_seq_key = "-".join(map(str, after_adv.moves))
                
                # Si on est coincé après cette réponse = position LOSE pour nous
                if not our_moves_after:
                    # ENRICHIR ! 📚
                    knowledge.update_sequence(
                        state.max_n,
                        adv_seq_key,
                        'lose',
                        1.0,
                        2,
                        is_terminal=True
                    )
                    enriched_count += 1
                    our_options_after.append(0)
                else:
                    our_options_after.append(len(our_moves_after))
            
            if not our_options_after:
                score = 0
            else:
                # Score = MINIMUM d'options (worst case)
                score = min(our_options_after)
            
            evaluated.append((move, score))
        
        if enriched_count > 0:
            print(f"  📚 Enrichissement : +{enriched_count} positions terminales découvertes")
        
        # Trier par score décroissant
        evaluated.sort(key=lambda x: x[1], reverse=True)
        
        # Choisir parmi les 3 meilleurs (un peu d'aléatoire)
        top_moves = [m for m, s in evaluated[:3]]
        choice = random.choice(top_moves)
        
        best_score = evaluated[0][1]
        print(f"  ⚡ Heuristique 2-ply : {choice} (score worst-case: {best_score})")
        
        return choice
    
    @staticmethod
    def _quick_lookup(state: GameState, current_key: str) -> Optional[int]:
        """Lookup ultra-rapide dans la base"""
        best_move = None
        best_confidence = 0
        
        for move in state.available_moves:
            key = f"{current_key}-{move}" if current_key else str(move)
            seq = knowledge.get_sequence(state.max_n, key)
            
            if seq and seq['outcome'] == 'win' and seq['confidence'] > best_confidence:
                best_move = move
                best_confidence = seq['confidence']
        
        return best_move if best_confidence >= 0.85 else None
    
    @staticmethod
    def _calculate_exploration_rate(time_budget: float, state: GameState) -> float:
        """Calcule le taux d'exploration optimal"""
        current_key = "-".join(map(str, state.moves))
        
        # Facteur temps
        time_factor = min(time_budget / 10.0, 1.0)
        
        # Facteur position connue
        seq = knowledge.get_sequence(state.max_n, current_key)
        if seq and seq.get('verified_count', 0) > 30:
            known_factor = 0.1
        elif seq:
            known_factor = 0.3
        else:
            known_factor = 0.6
        
        # Facteur couverture
        coverage = knowledge.get_coverage(state.max_n)
        coverage_factor = 0.5 if coverage < 0.8 else 0.2
        
        exploration_rate = (time_factor * 0.3 + known_factor * 0.4 + coverage_factor * 0.3)
        
        return min(0.5, exploration_rate)
    
    @staticmethod
    def _explore_ucb(state: GameState) -> int:
        """Exploration avec UCB (Upper Confidence Bound)"""
        current_key = "-".join(map(str, state.moves))
        total_games = sum(
            sum(seq.get('verified_count', 0) for seq in knowledge.sequences.get(state.max_n, {}).values())
            for _ in range(1)
        ) or 1
        
        ucb_scores = []
        available = state.available_moves.copy()
        
        # FILTRER 1 si pas le seul coup possible
        if len(available) > 1 and 1 in available:
            available = [x for x in available if x != 1]
        
        # FILTRER petits nombres si adversaire a joué 1
        if state.last_move == 1 and len(available) > 5:
            better_moves = [x for x in available if x > 6]
            if better_moves:
                available = better_moves
        
        for move in available:
            key = f"{current_key}-{move}" if current_key else str(move)
            seq = knowledge.get_sequence(state.max_n, key)
            
            if seq:
                wins = seq.get('wins', 0)
                plays = seq.get('verified_count', 1)
                win_rate = wins / plays
                exploration_bonus = math.sqrt(2 * math.log(total_games) / plays)
                ucb = win_rate + exploration_bonus
            else:
                ucb = 999.0
            
            ucb_scores.append((move, ucb))
        
        return max(ucb_scores, key=lambda x: x[1])[0]
    
    @staticmethod
    def _minimax_move(state: GameState, time_budget: float) -> int:
        """Calcul minimax avec profondeur adaptée au temps"""
        available = state.available_moves.copy()
        
        # FILTRE 1 : Éviter 1 si pas le seul coup
        if len(available) > 1 and 1 in available:
            available = [x for x in available if x != 1]
        
        # STRATÉGIE SPÉCIALE : Si adversaire vient de jouer 1
        if state.last_move == 1 and len(available) > 3:
            # Chercher les GRANDS NOMBRES PREMIERS (victoire immédiate !)
            def is_prime(n):
                if n < 2:
                    return False
                for i in range(2, int(n**0.5) + 1):
                    if n % i == 0:
                        return False
                return True
            
            large_primes = [x for x in available if is_prime(x) and x > state.max_n * 0.5]
            
            if large_primes:
                # VICTOIRE GARANTIE avec le plus grand premier !
                best_prime = max(large_primes)
                print(f"  🎯 APRÈS 1 → Coup gagnant immédiat : {best_prime} (premier)")
                return best_prime
            
            # Sinon, au moins éviter les petits nombres
            better_moves = [x for x in available if x > 6]
            if better_moves:
                available = better_moves
                print(f"  ⚠️  Après 1, évitement des petits nombres → {len(available)} candidats")
        
        grid_size = state.max_n
        
        # PROFONDEUR ADAPTÉE AU TEMPS ET À LA GRILLE
        if grid_size <= 20:
            # Grille 20 : minimax complet possible avec 2-3s
            if time_budget >= 2.0:
                depth = 99  # Complet
                print(f"🎯 Grille {grid_size} : minimax complet (optimal garanti)")
            else:
                depth = 10
                print(f"⚡ Grille {grid_size} : minimax profondeur {depth} (temps limité)")
        
        elif grid_size <= 30:
            # Grille 30 : minimax complet nécessite 3-5s
            if time_budget >= 3.0:
                depth = 99
                print(f"🎯 Grille {grid_size} : minimax complet")
            else:
                depth = 8
                print(f"⚡ Grille {grid_size} : minimax profondeur {depth}")
        
        elif grid_size <= 40:
            # Grille 40 : complet impossible, profondeur très limitée
            if time_budget >= 5.0:
                depth = 8
            elif time_budget >= 3.0:
                depth = 6
            elif time_budget >= 1.5:
                depth = 4
            else:
                depth = 3  # Très limité pour éviter timeout
            print(f"⚡ Grille {grid_size} : minimax profondeur {depth}")
        
        elif len(state.moves) == 0:
            # Premier coup grandes grilles
            if grid_size >= 50:
                depth = 3
            else:
                depth = 5
        elif len(state.moves) <= 2:
            if grid_size >= 50:
                depth = 5
            else:
                depth = 8
        elif time_budget > 5:
            depth = 10
        else:
            depth = 8
        
        # Limiter le nombre de candidats pour grandes grilles
        if grid_size >= 50 and len(available) > 10:
            # Utiliser les propriétés pour filtrer intelligemment
            scored = knowledge.get_best_moves_by_connections(
                grid_size, 
                available, 
                state.moves,
                min_connections=5
            )
            
            if scored:
                available = [m for m, _ in scored[:10]]
                print(f"  🎯 Filtrage intelligent : {len(available)} meilleurs candidats")
            else:
                # Fallback si tous ont < 5 connexions
                scored_all = knowledge.get_best_moves_by_connections(
                    grid_size,
                    available,
                    state.moves,
                    min_connections=0
                )
                available = [m for m, _ in scored_all[:10]]
        
        winning_moves = []
        
        for move in available:
            test_state = state.copy_with_move(move, Player.HUMAN)
            
            # Tester si ce coup est gagnant
            is_winning = AdaptiveAI.minimax_alpha_beta(
                test_state,
                0, depth, float('-inf'), float('inf'), False
            )
            
            if is_winning:
                # Calculer combien de coups restent après ce coup
                remaining = len(test_state.available_moves)
                winning_moves.append((move, remaining))
        
        if winning_moves:
            # TRIER : Préférer le coup qui laisse MOINS d'options à l'adversaire
            # (= victoire plus rapide)
            winning_moves.sort(key=lambda x: x[1])
            best_move = winning_moves[0][0]
            
            print(f"✅ {len(winning_moves)} coup(s) gagnant(s)")
            print(f"   Meilleur : {best_move} ({winning_moves[0][1]} coups restants)")
            
            return best_move
        
        print(f"⚠️  Aucun coup gagnant trouvé ! Choix aléatoire.")
        return random.choice(available)
    
    @staticmethod
    def _validate_move(state: GameState, move: int, time_budget: float):
        """Valide un coup calculé, détecte si position terminale"""
        
        if time_budget < 0.5:
            return
        
        start_time = time_module.time()
        current_key = "-".join(map(str, state.moves))
        extended_key = f"{current_key}-{move}" if current_key else str(move)
        
        # RÈGLE : Position finissant par 1 = LOSE (sauf si terminal)
        if extended_key.endswith('-1') or extended_key == '1':
            next_state = state.copy_with_move(move, Player.HUMAN)
            if not next_state.is_finished:
                # Position X-1 = LOSE (celui qui joue 1 perd)
                print(f"  ⚠️  Position {extended_key} : LOSE automatique (finit par 1)")
                knowledge.update_sequence(state.max_n, extended_key, 'lose', 0.99, 1, is_terminal=False)
                return
        
        # Créer l'état après ce coup
        next_state = state.copy_with_move(move, Player.HUMAN)
        
        # VÉRIFIER SI TERMINAL
        is_terminal = next_state.is_finished
        
        if is_terminal:
            outcome = 'win'
            print(f"  ✓ TERMINAL : {extended_key} → WIN (confiance 1.0)")
            knowledge.update_sequence(state.max_n, extended_key, outcome, 1.0, 99, is_terminal=True)
            return
        
        # Validation normale
        for depth in [8, 10, 12, 15]:
            elapsed = time_module.time() - start_time
            remaining = time_budget - elapsed
            
            estimated_time = 0.3 if state.max_n <= 30 else 0.5
            
            if remaining < estimated_time + 0.1:
                print(f"  ⏱️  Temps insuffisant pour depth {depth}, arrêt validation")
                return
            
            result = AdaptiveAI.minimax_alpha_beta(
                next_state,
                0, depth, float('-inf'), float('inf'), False
            )
            
            outcome = 'win' if result else 'lose'
            confidence = 0.85 + (depth / 100)
            
            knowledge.update_sequence(state.max_n, extended_key, outcome, confidence, depth, is_terminal=False)
    
    @staticmethod
    def _deep_learning(state: GameState, time_budget: float):
        """Apprentissage profond avec vérification stricte du temps"""
        
        if time_budget < 0.5:
            return
        
        start_time = time_module.time()
        current_key = "-".join(map(str, state.moves))
        positions_analyzed = 0
        
        print(f"=" * 60)
        print(f"🧠 APPRENTISSAGE PROFOND DÉMARRÉ (budget: {time_budget:.1f}s)")
        print(f"=" * 60)
        
        # BOUCLE JUSQU'À ÉPUISEMENT DU TEMPS !
        while True:
            elapsed = time_module.time() - start_time
            remaining = time_budget - elapsed
            
            if remaining < 0.6:
                print(f"  ⏱️  Budget épuisé ({elapsed:.2f}s utilisés)")
                break
            
            # Chercher positions à analyser
            targets = []
            
            # Vérifier si branche actuelle saturée
            if knowledge.is_saturated(state.max_n, current_key):
                shortest = knowledge.find_shortest_unsaturated(state.max_n, 10)
                if shortest:
                    targets = shortest[:5]  # Max 5 branches par itération
                    depth_min = len(targets[0].split('-'))
                    print(f"  🎯 Focus profondeur {depth_min} ({len(targets)} branches)")
            else:
                # Branche actuelle pas saturée
                targets = [current_key]
            
            # Si plus rien à analyser, chercher n'importe quelle position incertaine
            if not targets:
                uncertain = knowledge.get_any_uncertain_position(max_depth=6)
                if uncertain:
                    targets = [uncertain]
                else:
                    print(f"  ✅ Toutes les positions connues sont saturées !")
                    break
            
            # Analyser les branches trouvées
            for branch_key in targets:
                elapsed = time_module.time() - start_time
                remaining = time_budget - elapsed
                
                if remaining < 0.6:
                    break
                
                # Allouer temps pour cette branche (max 2s)
                allocated = min(2.0, remaining - 0.2)
                AdaptiveAI._validate_sequence_deep(branch_key, state.max_n, allocated)
                positions_analyzed += 1
            
            # Si aucune branche analysée, sortir
            if not targets:
                break
        
        # Rapport final
        elapsed = time_module.time() - start_time
        print(f"=" * 60)
        print(f"✅ APPRENTISSAGE TERMINÉ : {positions_analyzed} branches analysées en {elapsed:.2f}s")
        print(f"=" * 60)
    
    @staticmethod
    def _validate_sequence_deep(sequence_key: str, grid_size: int, time_budget: float):
        """Validation profonde d'une séquence"""
        moves = [int(m) for m in sequence_key.split('-')] if sequence_key else []
        state = GameState(moves=moves, max_n=grid_size)
        
        for depth in [10, 12, 15]:
            if time_budget < 0.3:
                break
            
            # Tester tous les coups possibles
            for move in state.available_moves[:3]:
                extended_key = f"{sequence_key}-{move}" if sequence_key else str(move)
                
                result = AdaptiveAI.minimax_alpha_beta(
                    state.copy_with_move(move, Player.HUMAN),
                    0, depth, float('-inf'), float('inf'), False
                )
                
                outcome = 'win' if result else 'lose'
                confidence = 0.85 + (depth / 80)
                
                knowledge.update_sequence(grid_size, extended_key, outcome, confidence, depth)
            
            time_budget -= 0.3


@dataclass
class Score:
    ia: int = 0
    human: int = 0
    
    def __str__(self) -> str:
        return f"{i18n.get('game.ai')} : {self.ia}    {i18n.get('game.you')} : {self.human}"
    
    def increment(self, winner: Player) -> None:
        if winner == Player.IA:
            self.ia += 1
        else:
            self.human += 1


class JuniperGame:
    def __init__(self, grid_size: int = 20, time_budget: float = 3.0, player_name: str = 'Joueur'):
        self.grid_size = grid_size
        self.time_budget = time_budget
        self.player_name = player_name
        self.state: Optional[GameState] = None
        self.score = Score()
        self.first_player = Player.HUMAN
        self.game_in_progress = False
    
    def new_game(self, force: bool = False) -> bool:
        if self.game_in_progress and not force:
            return False
        
        self.first_player = Player.IA if self.first_player == Player.HUMAN else Player.HUMAN
        self.state = GameState(current_player=self.first_player, max_n=self.grid_size)
        self.game_in_progress = True
        return True
    
    def play_move(self, move: int) -> Tuple[bool, Optional[Player]]:
        if not self.game_in_progress or not self.state:
            return False, None
        
        if move not in self.state.available_moves:
            return False, None
        
        next_player = Player.IA if self.state.current_player == Player.HUMAN else Player.HUMAN
        self.state = self.state.copy_with_move(move, next_player)
        
        if self.state.is_finished:
            winner = Player.HUMAN if self.state.current_player == Player.IA else Player.IA
            self.score.increment(winner)
            self.game_in_progress = False
            return True, winner
        
        return True, None
    
    def ai_move(self) -> Tuple[Optional[int], Optional[Player]]:
        if not self.state or self.state.current_player != Player.IA:
            return None, None
        
        move = AdaptiveAI.find_move_with_time_budget(self.state, self.time_budget)
        
        if move is None:
            return None, None
        
        success, winner = self.play_move(move)
        return move if success else None, winner
    
    def export_game(self, filepath: str, player_name: str):
        if not self.state or not self.state.moves:
            return False
        
        moves = self.state.moves
        first_is_ia = self.first_player == Player.IA
        
        if hasattr(self.state, 'resigned') and self.state.resigned:
            result = "0-1"
            result_comment = " {Abandoned}"
        elif not self.game_in_progress and self.state.is_finished:
            last_player_index = len(moves) - 1
            last_is_ia = (first_is_ia and last_player_index % 2 == 0) or \
                        (not first_is_ia and last_player_index % 2 == 1)
            result = "0-1" if not last_is_ia else "1-0"
            result_comment = ""
        else:
            result = "*"
            result_comment = ""
        
        content = f"""[Event "Juniper Green"]
[Site "JuniperU v2.0 AI"]
[Date "{datetime.now().strftime('%Y.%m.%d')}"]
[Grid "{self.grid_size}"]
[TimeControl "{self.time_budget}s"]
[FirstPlayer "{'IA' if first_is_ia else player_name}"]
[SecondPlayer "{player_name if first_is_ia else 'IA'}"]
[Result "{result}"]

"""
        
        for i in range(0, len(moves), 2):
            move_num = i // 2 + 1
            white_move = moves[i]
            black_move = moves[i+1] if i+1 < len(moves) else None
            
            if black_move:
                content += f"{move_num}. {white_move} {black_move}\n"
            else:
                content += f"{move_num}. {white_move} {result}{result_comment}\n"
        
        if len(moves) % 2 == 0 and result != "*":
            content += f"{result}{result_comment}\n"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error exporting game: {e}")
            return False


# ============================================================================
# INTERFACE GRAPHIQUE
# ============================================================================

class HistoryWindow:
    def __init__(self, parent_ui, game: JuniperGame):
        self.parent_ui = parent_ui
        self.game = game
        
        self.window = Toplevel(parent_ui.root)
        self.window.title(i18n.get('history.title'))
        self.window.geometry("450x350")
        self.window.resizable(True, True)
        self.window.configure(bg='#2C3E50')
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self._create_widgets()
        self.update_history()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.window, style='Game.TFrame', padding=15)
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(
            main_frame,
            text=i18n.get('history.title'),
            style='Title.TLabel',
            font=('Arial', 13, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        history_frame = ttk.Frame(main_frame, style='Game.TFrame')
        history_frame.pack(fill='both', expand=True, pady=10)
        
        self.history_text = ttk.Label(
            history_frame,
            text="",
            style='History.TLabel',
            justify='left'
        )
        self.history_text.pack(side='left', fill='both', expand=True)
        
        legend_label = ttk.Label(
            main_frame,
            text=i18n.get('history.legend'),
            style='Info.TLabel'
        )
        legend_label.pack(pady=5)
        
        button_frame = ttk.Frame(main_frame, style='Game.TFrame')
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text=i18n.get('button.copy'),
            command=self.copy_history
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text=i18n.get('button.export'),
            command=self.export_game
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text=i18n.get('button.close'),
            command=self.on_close
        ).pack(side='left', padx=5)
    
    def update_history(self):
        if not self.game.state or not self.game.state.moves:
            self.history_text.config(text=i18n.get('history.no_moves'))
            self.window.title(f"{i18n.get('button.history')} (0)")
            return
        
        moves = self.game.state.moves
        first_is_human = self.game.first_player == Player.HUMAN
        
        lines = []
        current_line = []
        
        for i, move in enumerate(moves):
            is_human = (i % 2 == 0 and first_is_human) or (i % 2 == 1 and not first_is_human)
            icon = "🟢" if is_human else "🔴"
            current_line.append(f"{icon} {move:2d}")
            
            if len(current_line) == 4:
                lines.append("  →  ".join(current_line))
                current_line = []
        
        if current_line:
            lines.append("  →  ".join(current_line))
        
        if lines:
            lines[-1] += "  ◄"
        
        self.history_text.config(text="\n\n".join(lines))
        
        num_text = f"({len(moves)} {i18n.get('history.moves') if len(moves) > 1 else i18n.get('history.move')})"
        self.window.title(f"{i18n.get('button.history')} {num_text}")
    
    def copy_history(self):
        if not self.game.state:
            return
        
        moves = self.game.state.moves
        first_is_human = self.game.first_player == Player.HUMAN
        
        text_lines = [
            f"Partie Juniper-U (grille 1-{self.game.grid_size}, temps {self.game.time_budget}s)",
            f"Démarrée par : {i18n.get('game.you') if first_is_human else i18n.get('game.ai')}",
            ""
        ]
        
        for i, move in enumerate(moves):
            is_human = (i % 2 == 0 and first_is_human) or (i % 2 == 1 and not first_is_human)
            player = i18n.get('game.you') if is_human else i18n.get('game.ai')
            text_lines.append(f"{i+1}. {player}: {move}")
        
        text = "\n".join(text_lines)
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        
        self.window.lift()
        self.window.focus_force()
        self.window.attributes('-topmost', True)
        
        messagebox.showinfo(
            i18n.get('history.copied_title'), 
            i18n.get('history.copied'),
            parent=self.window
        )
        
        self.window.attributes('-topmost', False)
    
    def export_game(self):
        self.window.lift()
        self.window.focus_force()
        self.parent_ui._export_game_dialog()
    
    def on_close(self):
        self.window.destroy()
        self.parent_ui.history_window = None


class JuniperUI:
    def __init__(self, root: Tk):
        self.root = root
        self.history_window: Optional[HistoryWindow] = None
        self.buttons = []
        self.current_font_size = 10
        self.background_learning_active = False  # Pour contrôler l'apprentissage en arrière-plan
        
        self.prefs = PreferencesManager.load()
        i18n.set_language(self.prefs['language'])
        
        self.lang_var = StringVar(value=self.prefs['language'])
        self.player_name_var = StringVar(value=self.prefs['player_name'])
        self.grid_size_var = IntVar(value=self.prefs['last_grid'])
        self.time_budget_var = StringVar(value=f"{self.prefs.get('last_time_budget', 10)}s")
        self.beginner_mode_var = BooleanVar(value=False)
        
        self.game = JuniperGame(
            grid_size=self.prefs['last_grid'],
            time_budget=self.prefs['last_time_budget'],
            player_name=self.prefs['player_name']
        )
        
        self._setup_window()
        self._create_menu()
        self._create_widgets()
        self._update_display()
    
    def _setup_window(self):
        self.root.title(i18n.get('app.title'))
        self.root.resizable(False, False)
        self.root.configure(bg='#2C3E50')
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Game.TFrame', background='#2C3E50')
        style.configure('Title.TLabel',
                       background='#2C3E50',
                       foreground='#ECF0F1',
                       font=('Arial', 12, 'bold'))
        style.configure('Info.TLabel',
                       background='#2C3E50',
                       foreground='#95A5A6',
                       font=('Arial', 10))
        style.configure('Score.TLabel',
                       background='#34495E',
                       foreground='#ECF0F1',
                       font=('Arial', 11),
                       padding=10)
        style.configure('History.TLabel',
                       background='#34495E',
                       foreground='#ECF0F1',
                       font=('Courier', 10),
                       padding=10)
        style.configure('Played.TButton',
                       font=('Arial', 9),  # Pas de barré
                       padding=8,
                       background='#95A5A6',    # Gris MOYEN (plus foncé)
                       foreground='#2C3E50')    # Texte très foncé
        # Forcer le fond gris MOYEN même en disabled
        style.map('Played.TButton',
                 background=[('disabled', '#95A5A6')],
                 foreground=[('disabled', '#2C3E50')],
                 relief=[('disabled', 'sunken')])  # Enfoncé pour effet visuel
        
        for font_size in [7, 8, 9, 10, 11, 12]:
            style.configure(f'Number{font_size}.TButton',
                           font=('Arial', font_size, 'bold'),
                           padding=6,
                           background='white',      # Fond blanc explicite
                           foreground='black')      # Texte noir
            style.configure(f'Playable{font_size}.TButton',
                           font=('Arial', font_size, 'bold'),
                           padding=6,
                           borderwidth=3,
                           background='#FF8C00',  # Orange vif
                           foreground='white')     # Texte blanc
            # Map pour l'état hover
            style.map(f'Playable{font_size}.TButton',
                     background=[('active', '#FFA500')],  # Orange plus clair au survol
                     foreground=[('active', 'white')])
    
    def _create_menu(self):
        menubar = Menu(self.root)
        menubar.add_command(label=i18n.get('menu.help'), command=self._show_help)
        menubar.add_command(label=i18n.get('menu.ai_stats'), command=self._show_ai_stats)
        menubar.add_command(label=i18n.get('menu.quit'), command=self.root.quit)
        self.root.config(menu=menubar)
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, style='Game.TFrame', padding=15)
        main_frame.pack(fill='both', expand=True)
        
        self.config_frame = ttk.LabelFrame(
            main_frame,
            text=i18n.get('config.title'),
            style='Game.TFrame',
            padding=15
        )
        self.config_frame.pack(fill='x', pady=(0, 15))
        
        # Langue
        lang_frame = ttk.Frame(self.config_frame, style='Game.TFrame')
        lang_frame.pack(fill='x', pady=5)
        
        ttk.Label(lang_frame, text=i18n.get('config.language'), style='Title.TLabel').pack(side='left', padx=5)
        
        lang_names = {code: name for code, name in i18n.get_available_languages()}
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=list(lang_names.values()),
            state='readonly',
            width=18
        )
        self.lang_combo.pack(side='left', padx=5)
        self.lang_combo.bind('<<ComboboxSelected>>', self._on_language_changed)
        
        # Nom
        player_frame = ttk.Frame(self.config_frame, style='Game.TFrame')
        player_frame.pack(fill='x', pady=5)
        
        ttk.Label(player_frame, text=i18n.get('config.player'), style='Title.TLabel').pack(side='left', padx=5)
        player_entry = ttk.Entry(player_frame, textvariable=self.player_name_var, width=20)
        player_entry.pack(side='left', padx=5)
        
        # Grille
        grid_frame = ttk.Frame(self.config_frame, style='Game.TFrame')
        grid_frame.pack(fill='x', pady=5)
        
        ttk.Label(grid_frame, text=i18n.get('config.grid'), style='Title.TLabel').pack(side='left', padx=5)
        self.grid_combo = ttk.Combobox(
            grid_frame,
            textvariable=self.grid_size_var,
            values=[20, 30, 40, 50, 100],
            state='readonly',
            width=18
        )
        self.grid_combo.pack(side='left', padx=5)
        self.grid_combo.bind('<<ComboboxSelected>>', self._on_grid_changed)
        
        # Temps
        time_frame = ttk.Frame(self.config_frame, style='Game.TFrame')
        time_frame.pack(fill='x', pady=5)
        
        ttk.Label(time_frame, text=i18n.get('config.time'), style='Title.TLabel').pack(side='left', padx=5)
        self.time_combo = ttk.Combobox(
            time_frame,
            textvariable=self.time_budget_var,
            values=['5s', '10s', '30s'],
            state='readonly',
            width=18
        )
        self.time_combo.pack(side='left', padx=5)
        
        # Mode Débutant
        beginner_frame = ttk.Frame(self.config_frame, style='Game.TFrame')
        beginner_frame.pack(fill='x', pady=5)
        
        self.beginner_check = ttk.Checkbutton(
            beginner_frame,
            text=i18n.get('config.beginner'),
            variable=self.beginner_mode_var,
            command=self._update_display
        )
        self.beginner_check.pack(side='left', padx=5)
        
        tooltip_label = ttk.Label(beginner_frame, text="ℹ️", style='Info.TLabel', cursor='hand2')
        tooltip_label.pack(side='left')
        tooltip_label.bind('<Button-1>', 
            lambda e: messagebox.showinfo(i18n.get('config.beginner'), i18n.get('config.beginner_tooltip')))
        
        # Actions
        self.actions_frame = ttk.Frame(main_frame, style='Game.TFrame')
        self.actions_frame.pack(fill='x', pady=(0, 15))
        
        self.new_game_button = ttk.Button(
            self.actions_frame,
            text=i18n.get('button.new_game'),
            command=self._new_game
        )
        self.new_game_button.pack(side='left', padx=5)
        
        self.resign_button = ttk.Button(
            self.actions_frame,
            text=i18n.get('button.resign'),
            command=self._resign_game,
            state='disabled'
        )
        self.resign_button.pack(side='left', padx=5)
        
        self.history_button = ttk.Button(
            self.actions_frame,
            text=f"{i18n.get('button.history')} (0)",
            command=self._open_history,
            state='disabled'
        )
        self.history_button.pack(side='left', padx=5)
        
        # Info
        self.info_label = ttk.Label(
            main_frame,
            text=i18n.get('game.click_new_game'),
            style='Title.TLabel',
            justify='center'
        )
        self.info_label.pack(pady=(0, 5))
        
        self.turn_label = ttk.Label(main_frame, text="", style='Info.TLabel')
        self.turn_label.pack(pady=(0, 15))
        
        # Grille
        self.game_frame = ttk.Frame(main_frame, style='Game.TFrame')
        self.game_frame.pack(pady=10)
        
        self._create_game_grid()
        
        # Score
        self.score_label = ttk.Label(
            main_frame,
            text="",
            style='Score.TLabel',
            justify='center'
        )
        self.score_label.pack(pady=(15, 0), fill='x')
    
    def _create_game_grid(self):
        for widget in self.game_frame.winfo_children():
            widget.destroy()
        self.buttons = []
        
        grid_size = self.grid_size_var.get()
        
        if grid_size <= 20:
            cols, font_size = 5, 9
        elif grid_size <= 30:
            cols, font_size = 6, 8
        elif grid_size <= 40:
            cols, font_size = 8, 8
        elif grid_size <= 50:
            cols, font_size = 10, 7
        else:
            cols, font_size = 14, 7
        
        self.current_font_size = font_size
        
        for i in range(1, grid_size + 1):
            btn = ttk.Button(
                self.game_frame,
                text=str(i),
                width=4,
                command=lambda num=i: self._human_move(num)
            )
            btn.configure(style=f'Number{font_size}.TButton')
            btn.grid(row=(i-1)//cols, column=(i-1)%cols, padx=2, pady=2)
            self.buttons.append(btn)
    
    def _on_language_changed(self, event=None):
        lang_names = {name: code for code, name in i18n.get_available_languages()}
        selected_name = self.lang_var.get()
        
        if selected_name in lang_names:
            i18n.set_language(lang_names[selected_name])
            self._refresh_ui()
            self._save_preferences()
    
    def _on_grid_changed(self, event=None):
        grid_size = self.grid_size_var.get()
        self._create_game_grid()
        
        if grid_size == 100:
            messagebox.showinfo(
                i18n.get('warning.grid100.title'),
                i18n.get('warning.grid100.message')
            )
    
    def _refresh_ui(self):
        self.root.title(i18n.get('app.title'))
        self.config_frame.config(text=i18n.get('config.title'))
        self.new_game_button.config(text=i18n.get('button.new_game'))
        self.resign_button.config(text=i18n.get('button.resign'))
        self._update_display()
        
        if self.history_window:
            try:
                self.history_window.window.title(i18n.get('history.title'))
                self.history_window.update_history()
            except:
                pass
    
    def _update_display(self):
        if self.game.state and self.game.state.moves:
            last = self.game.state.last_move
            
            # Si premier coup : afficher qui commence avec le coup
            if len(self.game.state.moves) == 1:
                starter_text = i18n.get('game.ai') if self.game.first_player == Player.IA else i18n.get('game.you')
                self.info_label.config(
                    text=f"{'🤖' if self.game.first_player == Player.IA else '👤'} {starter_text} {i18n.get('game.starts')} : {last}"
                )
            else:
                # Après le premier coup : afficher seulement le dernier coup
                self.info_label.config(text=f"{i18n.get('game.last_move')} : {last}")
        elif self.game.game_in_progress and self.game.state:
            # Partie commencée mais aucun coup encore joué
            starter_text = i18n.get('game.ai') if self.game.first_player == Player.IA else i18n.get('game.you')
            self.info_label.config(
                text=f"{'🤖' if self.game.first_player == Player.IA else '👤'} {starter_text} {i18n.get('game.starts')} !"
            )
        else:
            self.info_label.config(text=i18n.get('game.click_new_game'))
        
        if self.game.game_in_progress and self.game.state:
            if self.game.state.current_player == Player.HUMAN:
                self.turn_label.config(text=i18n.get('game.your_turn'))
            else:
                self.turn_label.config(text=i18n.get('game.ai_thinking'))
        else:
            self.turn_label.config(text="")
        
        self.score_label.config(text=f"{i18n.get('score.label')} : {self.game.score}")
        
        if self.game.game_in_progress:
            self.new_game_button.config(state='disabled')
            self.resign_button.config(state='normal')
        else:
            self.new_game_button.config(state='normal')
            self.resign_button.config(state='disabled')
        
        if self.game.state and self.game.state.moves:
            num_moves = len(self.game.state.moves)
            self.history_button.config(
                text=f"{i18n.get('button.history')} ({num_moves})",
                state='normal'
            )
        else:
            self.history_button.config(
                text=f"{i18n.get('button.history')} (0)",
                state='disabled'
            )
        
        if self.game.game_in_progress:
            self.config_frame.pack_forget()
        else:
            self.config_frame.pack(fill='x', pady=(0, 15), before=self.actions_frame)
        
        if self.game.state:
            available = self.game.state.available_moves if self.game.game_in_progress else []
            beginner_mode = self.beginner_mode_var.get()
            font_size = self.current_font_size
            
            for i, btn in enumerate(self.buttons, 1):
                if i <= self.game.grid_size:
                    if i in self.game.state.moves:
                        btn.config(state='disabled', text=str(i), style='Played.TButton')
                    elif i in available and self.game.state.current_player == Player.HUMAN:
                        btn.config(state='normal', text=str(i))
                        btn.config(style=f'Playable{font_size}.TButton' if beginner_mode else f'Number{font_size}.TButton')
                    else:
                        # Cases non jouables
                        # Toujours utiliser le style Number normal (pas de style spécial)
                        btn.config(state='disabled' if beginner_mode else 'normal', 
                                  text=str(i), 
                                  style=f'Number{font_size}.TButton')
        
        if self.history_window:
            try:
                self.history_window.update_history()
            except:
                self.history_window = None
    
    def _new_game(self):
        if self.history_window:
            try:
                self.history_window.on_close()
            except:
                pass
            self.history_window = None
        
        self._start_new_game()
    
    def _start_new_game(self):
        self._save_preferences()
        
        time_str = self.time_budget_var.get().replace('s', '')
        time_budget = float(time_str)
        
        self.game.grid_size = self.grid_size_var.get()
        self.game.time_budget = time_budget
        self.game.player_name = self.player_name_var.get()
        
        if len(self.buttons) != self.game.grid_size:
            self._create_game_grid()
        
        for i, btn in enumerate(self.buttons, 1):
            if i <= self.game.grid_size:
                btn.config(state='normal', text=str(i), style=f'Number{self.current_font_size}.TButton')
        
        self.game.new_game()
        self._update_display()
        
        if self.game.first_player == Player.IA:
            self.root.after(500, self._ai_turn)
    
    def _resign_game(self):
        if not messagebox.askyesno(i18n.get('resign.title'), i18n.get('resign.message')):
            return
        
        self.game.score.increment(Player.IA)
        self.game.game_in_progress = False
        
        if self.game.state:
            self.game.state.resigned = True
        
        self._update_display()
        
        if messagebox.askyesno(
            i18n.get('defeat.title'),
            i18n.get('defeat.message') + f"\n\n{i18n.get('export.prompt_message')}"
        ):
            self._export_game_dialog()
        
        if self.history_window:
            try:
                self.history_window.on_close()
            except:
                pass
            self.history_window = None
    
    def _human_move(self, move: int):
        # Arrêter l'apprentissage en arrière-plan car le joueur a joué
        self.background_learning_active = False
        
        if not self.game.game_in_progress:
            return
        
        if move not in self.game.state.available_moves:
            return
        
        success, winner = self.game.play_move(move)
        
        if not success:
            return
        
        self._update_display()
        
        if winner:
            self.root.after(500, lambda: self._game_over(winner))
        else:
            self.root.after(500, self._ai_turn)
    
    def _start_background_learning(self):
        """Démarrer l'apprentissage en arrière-plan pendant le tour du joueur"""
        print(f"🔍 DEBUG: _start_background_learning appelée (state={self.game.state is not None}, active={self.background_learning_active})")
        
        if not self.game.state:
            print("❌ Pas de state, apprentissage arrière-plan annulé")
            return
            
        if self.background_learning_active:
            print("⚠️  Apprentissage déjà actif, skip")
            return
        
        print("✅ Démarrage du thread d'apprentissage arrière-plan...")
        self.background_learning_active = True
        
        import threading
        
        def learn_in_background():
            try:
                print("🧠 Apprentissage en arrière-plan démarré...")
                state = self.game.state
                grid_size = state.max_n
                
                # Apprentissage continu pendant max 30 secondes
                start_time = time_module.time()
                positions_learned = 0
                attempts = 0
                
                print(f"  📊 Grille : {grid_size}, Position actuelle : {'-'.join(map(str, state.moves))}")
                
                while self.background_learning_active and (time_module.time() - start_time) < 30:
                    # EXPLORER DE NOUVELLES POSITIONS depuis la position actuelle
                    # Au lieu de chercher des positions incertaines existantes
                    
                    # Prendre la position actuelle ou une position courte
                    if len(state.moves) <= 3:
                        base_position = "-".join(map(str, state.moves))
                    else:
                        # Prendre les 2-3 premiers coups seulement
                        base_position = "-".join(map(str, state.moves[:2]))
                    
                    # Créer l'état correspondant
                    base_moves = [int(m) for m in base_position.split('-')] if base_position else []
                    explore_state = GameState(moves=base_moves, max_n=grid_size)
                    
                    # Explorer les coups disponibles
                    available = explore_state.available_moves
                    if not available:
                        print(f"  ℹ️  Plus de coups à explorer depuis {base_position}")
                        break
                    
                    # Prendre un coup aléatoire disponible
                    import random
                    move = random.choice(available[:min(10, len(available))])
                    
                    extended_key = f"{base_position}-{move}" if base_position else str(move)
                    
                    # Vérifier si déjà connu avec certitude
                    existing = knowledge.get_sequence(grid_size, extended_key)
                    if existing and existing.get('confidence', 0) >= 0.99:
                        attempts += 1
                        if attempts > 20:
                            print(f"  ℹ️  Trop de positions déjà saturées")
                            break
                        continue
                    
                    print(f"  🔍 Explore nouvelle branche #{positions_learned+1}: {extended_key}")
                    
                    # Analyser cette nouvelle branche avec minimax
                    extended_state = explore_state.copy_with_move(move, Player.HUMAN)
                    result = AdaptiveAI.minimax_alpha_beta(
                        extended_state, 0, 10, float('-inf'), float('inf'), False
                    )
                    outcome = 'win' if result else 'lose'
                    knowledge.update_sequence(grid_size, extended_key, outcome, 0.90, 10)
                    
                    positions_learned += 1
                    attempts += 1
                    
                    if positions_learned % 5 == 0:
                        print(f"  📊 {positions_learned} nouvelles positions explorées...")
                    
                    # Vérifier si le joueur a joué (donc arrêter l'apprentissage)
                    if not self.background_learning_active:
                        print(f"  ⏹️  Arrêt demandé")
                        break
                
                elapsed = time_module.time() - start_time
                if positions_learned > 0:
                    print(f"✅ Apprentissage arrière-plan : {positions_learned} positions en {elapsed:.1f}s")
                    print(f"  💾 Sauvegarde...")
                    knowledge.save()
                    print(f"  ✅ Sauvegarde terminée")
                else:
                    print(f"ℹ️  Apprentissage arrière-plan : 0 positions ({attempts} tentatives)")
            except Exception as e:
                print(f"❌ Erreur apprentissage arrière-plan : {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.background_learning_active = False
        
        thread = threading.Thread(target=learn_in_background, daemon=True)
        thread.start()
        print("🚀 Thread lancé !")
    
    def _ai_turn(self):
        """Tour de l'IA avec indicateur de réflexion"""
        # Afficher que l'IA réfléchit
        self.turn_label.config(text=i18n.get('game.ai_thinking'))
        self.root.update()  # Forcer l'affichage
        
        # Lancer le calcul dans un thread pour ne pas bloquer l'interface
        import threading
        
        def compute_in_background():
            move, winner = self.game.ai_move()
            # Retour dans le thread principal Tkinter
            self.root.after(0, lambda: self._ai_move_done(move, winner))
        
        thread = threading.Thread(target=compute_in_background, daemon=True)
        thread.start()
    
    def _ai_move_done(self, move, winner):
        """Appelé quand l'IA a fini de calculer"""
        if move is None:
            return
        
        self._update_display()
        
        if winner:
            self.root.after(500, lambda: self._game_over(winner))
        else:
            # L'IA a joué, maintenant c'est au tour du joueur
            # Démarrer l'apprentissage en arrière-plan pendant que le joueur réfléchit
            self._start_background_learning()
    
    def _game_over(self, winner: Player):
        """Afficher message de fin avec délai pour voir le dernier coup"""
        # APPRENTISSAGE POST-PARTIE : Enregistrer le résultat
        if self.game.state and len(self.game.state.moves) > 0:
            grid_size = self.game.state.max_n
            sequence_key = "-".join(map(str, self.game.state.moves))
            
            # Déterminer l'issue pour l'IA
            outcome = 'lose' if winner == Player.HUMAN else 'win'
            
            # Enregistrer dans la base
            knowledge.update_sequence(
                grid_size,
                sequence_key,
                outcome,
                1.0,  # Confiance max (partie réelle)
                depth=99,  # Validation réelle
                is_terminal=True
            )
            
            print(f"📚 Partie enregistrée : {len(self.game.state.moves)} coups → {outcome.upper()}")
            knowledge.save()  # Sauvegarde TOUT (pas de paramètre)
        
        if winner == Player.HUMAN:
            title = i18n.get('victory.title')
            msg = i18n.get('victory.message')
        else:
            title = i18n.get('defeat.title')
            msg = i18n.get('defeat.message')
        
        # Délai de 1.5s pour laisser voir le dernier coup
        self.root.after(1500, lambda: self._show_game_over_dialog(title, msg))
    
    def _show_game_over_dialog(self, title: str, msg: str):
        """Afficher le dialogue de fin de partie"""
        if messagebox.askyesno(title, msg + f"\n\n{i18n.get('export.prompt_message')}"):
            self._export_game_dialog()
        
        if self.history_window:
            try:
                self.history_window.on_close()
            except:
                pass
            self.history_window = None
    
    def _open_history(self):
        if not self.game.game_in_progress and not self.game.state:
            return
        
        if self.history_window:
            try:
                self.history_window.window.lift()
                self.history_window.window.focus_force()
                return
            except:
                self.history_window = None
        
        self.history_window = HistoryWindow(self, self.game)
    
    def _export_game_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title(i18n.get('export.title'))
        dialog.geometry("380x150")
        dialog.resizable(False, False)
        dialog.configure(bg='#2C3E50')
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, style='Game.TFrame', padding=20)
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(main_frame, text=i18n.get('export.player_name'), style='Title.TLabel').pack(pady=(0, 10))
        
        player_var = StringVar(value=self.player_name_var.get())
        entry = ttk.Entry(main_frame, textvariable=player_var, width=35, font=('Arial', 11))
        entry.pack(pady=(0, 20))
        entry.focus()
        
        button_frame = ttk.Frame(main_frame, style='Game.TFrame')
        button_frame.pack()
        
        def do_export():
            player_name = player_var.get().strip()
            if not player_name:
                player_name = "Joueur"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"juniper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                if self.game.export_game(filename, player_name):
                    messagebox.showinfo(
                        i18n.get('export.success_title'),
                        i18n.get('export.success'),
                        parent=dialog
                    )
                    dialog.destroy()
                else:
                    messagebox.showerror(
                        i18n.get('export.error_title'),
                        i18n.get('export.error'),
                        parent=dialog
                    )
        
        cancel_btn = Button(
            button_frame,
            text=i18n.get('button.cancel'),
            command=dialog.destroy,
            font=('Arial', 10),
            bg='#E74C3C',
            fg='white',
            padx=20,
            pady=8,
            relief='raised',
            cursor='hand2'
        )
        cancel_btn.pack(side='left', padx=5)
        
        export_btn = Button(
            button_frame,
            text=i18n.get('button.export'),
            command=do_export,
            font=('Arial', 10, 'bold'),
            bg='#27AE60',
            fg='white',
            padx=20,
            pady=8,
            relief='raised',
            cursor='hand2'
        )
        export_btn.pack(side='left', padx=5)
        
        entry.bind('<Return>', lambda e: do_export())
    
    def _save_preferences(self):
        lang_names = {name: code for code, name in i18n.get_available_languages()}
        selected_name = self.lang_var.get()
        lang_code = lang_names.get(selected_name, 'fr')
        
        time_str = self.time_budget_var.get().replace('s', '')
        time_budget = float(time_str)
        
        prefs = {
            'language': lang_code,
            'player_name': self.player_name_var.get(),
            'last_grid': self.grid_size_var.get(),
            'last_time_budget': time_budget
        }
        PreferencesManager.save(prefs)
    
    def _show_help(self):
        """Ouvrir l'aide dans le navigateur (HTML) ou messagebox (fallback)"""
        # Déterminer le fichier HTML selon la langue
        lang = i18n.current_lang
        help_file = os.path.join('locales', f'help_{lang}.html')
        
        # Vérifier si le fichier HTML existe
        if os.path.exists(help_file):
            import subprocess
            import platform
            
            abs_path = os.path.abspath(help_file)
            
            # Sur Linux, utiliser xdg-open directement (meilleur focus)
            if platform.system() == 'Linux':
                try:
                    subprocess.Popen(['xdg-open', abs_path], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                except:
                    # Fallback webbrowser si xdg-open échoue
                    import webbrowser
                    webbrowser.open('file://' + abs_path, new=2)
            else:
                # Windows/Mac : utiliser webbrowser
                import webbrowser
                webbrowser.open('file://' + abs_path, new=2)
        else:
            # Fallback : utiliser le texte du fichier locale
            messagebox.showinfo(i18n.get('help.title'), i18n.get('help.content'))
    
    def _show_ai_stats(self):
        """Afficher les statistiques d'apprentissage de l'IA"""
        stats_window = Toplevel(self.root)
        stats_window.title(i18n.get('stats.title'))
        stats_window.geometry("650x400")
        stats_window.resizable(False, False)
        
        # Fond blanc - approche simple
        stats_window['bg'] = 'white'
        
        # Frame principal
        main_frame = tk.Frame(stats_window, bg='white', bd=0)
        main_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Titre
        title_label = tk.Label(
            main_frame,
            text=i18n.get('stats.header'),
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#2C3E50'
        )
        title_label.pack(pady=(0, 20))
        
        # Frame pour les statistiques
        stats_frame = tk.Frame(main_frame, bg='white')
        stats_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Charger les stats pour chaque grille
        knowledge_dir = 'knowledge'
        grid_sizes = [20, 30, 40, 50, 100]
        has_data = False
        
        for grid_size in grid_sizes:
            filename = os.path.join(knowledge_dir, f'knowledge_{grid_size}.json')
            
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sequences = data.get('sequences', {})
                    total = len(sequences)
                    
                    if total > 0:
                        has_data = True
                        
                        # Estimation du total possible (très approximatif)
                        estimated_total = {
                            20: 2500,
                            30: 5000,
                            40: 10000,
                            50: 15000,
                            100: 50000
                        }.get(grid_size, 10000)
                        
                        # Pourcentage
                        percent = (total / estimated_total) * 100
                        
                        # Date de dernière MAJ
                        last_update = data.get('last_updated', i18n.get('stats.never'))
                        if last_update != i18n.get('stats.never'):
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(last_update)
                                last_update = dt.strftime('%d/%m %H:%M')
                            except:
                                pass
                        
                        # Barre de progression
                        bar_length = 20
                        filled = int((total / estimated_total) * bar_length)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        # Couleur selon pourcentage - COULEURS FORTES
                        if percent >= 20:
                            color = '#27AE60'  # Vert foncé
                            bg_color = '#D5F4E6'  # Fond vert clair
                        elif percent >= 5:
                            color = '#E67E22'  # Orange foncé
                            bg_color = '#FCE5CD'  # Fond orange clair
                        else:
                            color = '#C0392B'  # Rouge foncé
                            bg_color = '#FADBD8'  # Fond rouge clair
                        
                        # Créer la ligne avec fond coloré
                        line_text = f"Grille {grid_size:3d} : [{bar}] {total}/{estimated_total} ({percent:.0f}%) - {last_update}"
                        
                        line_label = tk.Label(
                            stats_frame,
                            text=line_text,
                            font=('Courier', 11, 'bold'),
                            fg=color,
                            bg=bg_color,      # Fond coloré selon progression
                            anchor='w',
                            padx=10,
                            pady=5
                        )
                        line_label.pack(fill='x', pady=3)
                        
                except Exception as e:
                    print(f"Erreur lecture {filename}: {e}")
        
        if not has_data:
            no_data_label = tk.Label(
                stats_frame,
                text=i18n.get('stats.no_data'),
                font=('Arial', 11),
                bg='white',
                justify='center'
            )
            no_data_label.pack(pady=40)
        
        # Message en bas (APRÈS la liste)
        info_label = tk.Label(
            main_frame,
            text=i18n.get('stats.info'),
            font=('Arial', 9, 'italic'),
            fg='#7f8c8d',
            bg='white'
        )
        info_label.pack(pady=(10, 15))
        
        # Bouton fermer
        close_button = tk.Button(
            main_frame,
            text=i18n.get('button.close'),
            command=stats_window.destroy,
            font=('Arial', 11),
            bg='#3498db',
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        close_button.pack(pady=10)
    
    def _open_website(self):
        webbrowser.open('http://site2wouf.fr/juniper')


def main():
    root = Tk()
    app = JuniperUI(root)
    
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')
    
    # Sauvegarder la base à la fermeture
    def on_closing():
        knowledge.save()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
