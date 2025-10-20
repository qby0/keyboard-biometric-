import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import euclidean, cosine
from typing import Dict, List, Tuple
import pickle
import os


class KeystrokeBiometrics:
    """
    Machine learning model for biometric identification
    based on keystroke patterns
    """
    
    def __init__(self):
        # Глобальный скейлер для нормализации признаков; обучается на всех доступных вектрах
        self.scaler = StandardScaler()
        self.feature_names = [
            'dwell_mean', 'dwell_std', 'dwell_median', 'dwell_min', 'dwell_max',
            'latency_mean', 'latency_std', 'latency_median', 'latency_min', 'latency_max',
            'flight_mean', 'flight_std', 'flight_median',
            'typing_speed', 'total_time', 'key_count',
            'rhythm_consistency', 'digraph_mean', 'digraph_std'
        ]
    
    def train(self, users_data: Dict):
        """
        Обучение скейлера на всех доступных образцах пользователей.
        Distance-based идентификация не требует обучаемой модели, но
        корректная нормализация признаков повышает качество сравнения.
        """
        if not users_data:
            return

        vectors: List[np.ndarray] = []
        for _, user_info in users_data.items():
            for features in user_info.get('features', []):
                vectors.append(self._features_to_vector(features))

        if len(vectors) < 2:
            # Недостаточно данных для устойчивой нормализации
            return

        X = np.array(vectors)
        self.scaler.fit(X)
    
    def identify(self, features: Dict, users_data: Dict, top_k: int = 5) -> List[Dict]:
        """
        Identify user by features
        
        Returns top-K similar users with similarity scores
        """
        if not users_data:
            return []
        
        feature_vector = self._features_to_vector(features)
        
        # Собираем все векторы для потенциальной подстройки скейлера
        all_vectors = [feature_vector]
        for _, user_info in users_data.items():
            all_vectors.extend([self._features_to_vector(f) for f in user_info.get('features', [])])

        all_vectors_array = np.array(all_vectors)

        # Если скейлер ещё не обучен (первый запуск) — обучим на всех доступных векторах
        if not hasattr(self.scaler, 'mean_'):
            try:
                self.scaler.fit(all_vectors_array)
            except Exception:
                pass

        # Нормализуем тестовый и пользовательские векторы одним и тем же скейлером
        all_vectors_normalized = self.scaler.transform(all_vectors_array)
        test_vector_normalized = all_vectors_normalized[0]
        
        # Calculate distance to each user
        similarities = []
        vector_idx = 1
        for username, user_info in users_data.items():
            user_features_list = user_info.get('features', [])
            
            if not user_features_list:
                continue
            
            # Calculate distances to all user samples
            scores = []
            for _ in user_features_list:
                user_vector_normalized = all_vectors_normalized[vector_idx]
                vector_idx += 1
                
                # Use multiple metrics
                euclidean_dist = np.linalg.norm(test_vector_normalized - user_vector_normalized)
                manhattan_dist = np.sum(np.abs(test_vector_normalized - user_vector_normalized))
                cosine_sim = self._safe_cosine_similarity(test_vector_normalized, user_vector_normalized)
                
                # Calculate weighted temporal characteristics
                timing_score = self._calculate_timing_similarity(features, user_features_list[len(scores)])
                
                # Combined score
                combined_score = self._calculate_advanced_score(
                    euclidean_dist, manhattan_dist, cosine_sim, timing_score
                )
                scores.append(combined_score)
            
            # Average similarity score with user
            avg_similarity = np.mean(scores)
            max_similarity = np.max(scores)
            min_similarity = np.min(scores)
            
            similarities.append({
                'username': username,
                'similarity': float(avg_similarity),
                'max_similarity': float(max_similarity),
                'min_similarity': float(min_similarity),
                'samples_count': len(user_features_list),
                'confidence': self._calculate_confidence(scores)
            })
        
        # Sort by descending similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
    
    def _features_to_vector(self, features: Dict) -> np.ndarray:
        """Convert feature dictionary to vector"""
        vector = []
        for feature_name in self.feature_names:
            value = features.get(feature_name, 0)
            # Handle inf and nan
            if np.isnan(value) or np.isinf(value):
                value = 0
            vector.append(value)
        return np.array(vector)
    
    def _safe_euclidean_distance(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Safe computation of Euclidean distance"""
        try:
            return euclidean(v1, v2)
        except:
            return float('inf')
    
    def _safe_cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Safe computation of cosine similarity"""
        try:
            # Cosine distance to similarity (1 - distance)
            return 1 - cosine(v1, v2)
        except:
            return 0
    
    def _calculate_timing_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Compare temporal typing characteristics
        Lower difference means higher similarity
        """
        # Key temporal parameters
        timing_params = ['dwell_mean', 'latency_mean', 'flight_mean', 'typing_speed']
        
        total_diff = 0
        count = 0
        
        for param in timing_params:
            val1 = features1.get(param, 0)
            val2 = features2.get(param, 0)
            
            if val1 == 0 and val2 == 0:
                continue
            
            # Relative difference (normalized)
            max_val = max(abs(val1), abs(val2), 1)
            diff = abs(val1 - val2) / max_val
            total_diff += diff
            count += 1
        
        if count == 0:
            return 50
        
        # Convert difference to similarity (0 = 100%, 1 = 0%)
        avg_diff = total_diff / count
        similarity = 100 * (1 - min(avg_diff, 1))
        
        return similarity
    
    def _calculate_advanced_score(self, euclidean_dist: float, manhattan_dist: float, 
                                   cosine_sim: float, timing_score: float) -> float:
        """
        Calculate improved combined similarity score
        
        Returns value from 0 to 100
        """
        # Euclidean distance (normalized, lower = better)
        # Use sigmoid for non-linear transformation
        euclidean_score = 100 / (1 + euclidean_dist)
        
        # Manhattan distance (lower = better)
        manhattan_score = 100 / (1 + manhattan_dist)
        
        # Cosine similarity (already from -1 to 1, convert to 0-100)
        cosine_score = (cosine_sim + 1) * 50
        
        # Weighted combination (higher weight on temporal characteristics)
        combined = (
            0.25 * euclidean_score +
            0.25 * manhattan_score +
            0.20 * cosine_score +
            0.30 * timing_score
        )
        
        return max(0, min(100, combined))
    
    def _calculate_combined_score(self, euclidean_dist: float, cosine_sim: float) -> float:
        """
        Calculate combined similarity score (legacy)
        
        Returns value from 0 to 100
        """
        # Normalize Euclidean distance (lower = better)
        euclidean_score = 100 / (1 + euclidean_dist)
        
        # Cosine similarity already from 0 to 1, scale to 100
        cosine_score = cosine_sim * 100
        
        # Weighted combination
        combined = 0.6 * euclidean_score + 0.4 * cosine_score
        
        return max(0, min(100, combined))  # Constraint [0, 100]
    
    def _calculate_confidence(self, scores: List[float]) -> float:
        """
        Calculate identification confidence
        
        High confidence = low variation between samples
        """
        if not scores or len(scores) < 2:
            return 0
        
        std = np.std(scores)
        mean = np.mean(scores)
        
        if mean == 0:
            return 0
        
        # Inverse coefficient of variation, normalized to [0, 100]
        cv = std / mean
        confidence = 100 / (1 + cv)
        
        return float(confidence)
    
    def save_model(self, filepath: str):
        """Сохранить параметры нормализации (скейлер) и имена признаков"""
        model_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Загрузить сохранённый скейлер и имена признаков"""
        if not os.path.exists(filepath):
            return False

        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        return True

