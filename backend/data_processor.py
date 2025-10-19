import numpy as np
from typing import List, Dict


class DataProcessor:
    """Обработчик данных нажатий клавиш для извлечения биометрических признаков"""
    
    def extract_features(self, keystroke_events: List[Dict], text: str) -> Dict:
        """
        Извлечение биометрических признаков из событий нажатия клавиш
        
        Основные признаки:
        - Dwell time (время удержания клавиши)
        - Flight time (время между отпусканием одной клавиши и нажатием следующей)
        - Latency (общая задержка между нажатиями)
        - Typing speed (скорость печати)
        - Rhythm patterns (ритмические паттерны)
        """
        
        if not keystroke_events or len(keystroke_events) < 2:
            return self._empty_features()
        
        # Разделение на события нажатия и отпускания
        keydown_events = [e for e in keystroke_events if e['type'] == 'keydown']
        keyup_events = [e for e in keystroke_events if e['type'] == 'keyup']
        
        # Время удержания клавиш (dwell time)
        dwell_times = []
        for kd in keydown_events:
            matching_ku = next((ku for ku in keyup_events 
                              if ku['key'] == kd['key'] and ku['timestamp'] > kd['timestamp']), None)
            if matching_ku:
                dwell_times.append(matching_ku['timestamp'] - kd['timestamp'])
        
        # Время между нажатиями (inter-key latency)
        inter_key_latencies = []
        for i in range(len(keydown_events) - 1):
            latency = keydown_events[i + 1]['timestamp'] - keydown_events[i]['timestamp']
            inter_key_latencies.append(latency)
        
        # Flight time (время между отпусканием одной клавиши и нажатием следующей)
        flight_times = []
        for i in range(len(keyup_events) - 1):
            if i + 1 < len(keydown_events):
                flight = keydown_events[i + 1]['timestamp'] - keyup_events[i]['timestamp']
                if flight > 0:  # Только положительные значения
                    flight_times.append(flight)
        
        # Digraph latencies (время между парами символов)
        digraph_latencies = self._calculate_digraph_latencies(keydown_events)
        
        # Статистические характеристики
        features = {
            # Dwell time статистика
            'dwell_mean': float(np.mean(dwell_times)) if dwell_times else 0,
            'dwell_std': float(np.std(dwell_times)) if dwell_times else 0,
            'dwell_median': float(np.median(dwell_times)) if dwell_times else 0,
            'dwell_min': float(np.min(dwell_times)) if dwell_times else 0,
            'dwell_max': float(np.max(dwell_times)) if dwell_times else 0,
            
            # Inter-key latency статистика
            'latency_mean': float(np.mean(inter_key_latencies)) if inter_key_latencies else 0,
            'latency_std': float(np.std(inter_key_latencies)) if inter_key_latencies else 0,
            'latency_median': float(np.median(inter_key_latencies)) if inter_key_latencies else 0,
            'latency_min': float(np.min(inter_key_latencies)) if inter_key_latencies else 0,
            'latency_max': float(np.max(inter_key_latencies)) if inter_key_latencies else 0,
            
            # Flight time статистика
            'flight_mean': float(np.mean(flight_times)) if flight_times else 0,
            'flight_std': float(np.std(flight_times)) if flight_times else 0,
            'flight_median': float(np.median(flight_times)) if flight_times else 0,
            
            # Общие характеристики
            'typing_speed': self._calculate_typing_speed(keydown_events, text),
            'total_time': keydown_events[-1]['timestamp'] - keydown_events[0]['timestamp'] if keydown_events else 0,
            'key_count': len(keydown_events),
            
            # Ритмические характеристики
            'rhythm_consistency': self._calculate_rhythm_consistency(inter_key_latencies),
            
            # Digraph характеристики
            'digraph_mean': float(np.mean(list(digraph_latencies.values()))) if digraph_latencies else 0,
            'digraph_std': float(np.std(list(digraph_latencies.values()))) if digraph_latencies else 0,
            
            # Сырые данные для дополнительного анализа
            'raw_dwell_times': dwell_times[:50],  # Ограничиваем размер
            'raw_latencies': inter_key_latencies[:50],
        }
        
        return features
    
    def _calculate_typing_speed(self, keydown_events: List[Dict], text: str) -> float:
        """Расчет скорости печати (символов в минуту)"""
        if not keydown_events or len(keydown_events) < 2:
            return 0
        
        total_time_seconds = (keydown_events[-1]['timestamp'] - keydown_events[0]['timestamp']) / 1000
        if total_time_seconds == 0:
            return 0
        
        chars_per_second = len(text) / total_time_seconds
        return chars_per_second * 60  # CPM (characters per minute)
    
    def _calculate_rhythm_consistency(self, latencies: List[float]) -> float:
        """
        Расчет консистентности ритма (обратный коэффициент вариации)
        Высокое значение = более консистентный ритм
        """
        if not latencies or len(latencies) < 2:
            return 0
        
        mean = np.mean(latencies)
        std = np.std(latencies)
        
        if mean == 0:
            return 0
        
        # Коэффициент вариации (CV)
        cv = std / mean
        
        # Возвращаем обратное значение (нормализованное)
        return 1 / (1 + cv)
    
    def _calculate_digraph_latencies(self, keydown_events: List[Dict]) -> Dict[str, float]:
        """Расчет времени между конкретными парами символов (digraphs)"""
        digraphs = {}
        
        for i in range(len(keydown_events) - 1):
            key1 = keydown_events[i]['key']
            key2 = keydown_events[i + 1]['key']
            
            if len(key1) == 1 and len(key2) == 1:  # Только обычные символы
                digraph = f"{key1}{key2}"
                latency = keydown_events[i + 1]['timestamp'] - keydown_events[i]['timestamp']
                
                if digraph in digraphs:
                    digraphs[digraph] = (digraphs[digraph] + latency) / 2  # Среднее
                else:
                    digraphs[digraph] = latency
        
        return digraphs
    
    def _empty_features(self) -> Dict:
        """Возврат пустых признаков"""
        return {
            'dwell_mean': 0, 'dwell_std': 0, 'dwell_median': 0, 'dwell_min': 0, 'dwell_max': 0,
            'latency_mean': 0, 'latency_std': 0, 'latency_median': 0, 'latency_min': 0, 'latency_max': 0,
            'flight_mean': 0, 'flight_std': 0, 'flight_median': 0,
            'typing_speed': 0, 'total_time': 0, 'key_count': 0,
            'rhythm_consistency': 0, 'digraph_mean': 0, 'digraph_std': 0,
            'raw_dwell_times': [], 'raw_latencies': []
        }


