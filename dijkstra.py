"""
Dijkstra's Shortest Path Algorithm Implementation
CENG 3511 - Artificial Intelligence Final Project
"""

import heapq
import math
from typing import Dict, List, Tuple, Optional


class Graph:
    """Graph sınıfı - Düğümler ve kenarları tutar"""
    
    def __init__(self, nodes: Dict, edges: Dict):
        """
        Args:
            nodes: {node_id: {lat: float, lon: float}}
            edges: {node_id: [{node: str, weight: float}]}
        """
        self.nodes = nodes
        self.edges = edges
    
    def get_neighbors(self, node_id: str) -> List[Dict]:
        """Bir düğümün komşularını döndürür"""
        return self.edges.get(node_id, [])
    
    def node_exists(self, node_id: str) -> bool:
        """Düğüm var mı kontrol eder"""
        return node_id in self.nodes
    
    def get_node_coords(self, node_id: str) -> Tuple[float, float]:
        """Düğümün koordinatlarını döndürür (lat, lon)"""
        node = self.nodes.get(node_id)
        if node:
            return (node['lat'], node['lon'])
        return None


def dijkstra(graph: Graph, start_node: str, end_node: str) -> Optional[Dict]:
    """
    Dijkstra algoritması ile en kısa yolu bulur
    
    Args:
        graph: Graph objesi
        start_node: Başlangıç düğümü ID'si
        end_node: Varış düğümü ID'si
    
    Returns:
        {
            'path': [node_id1, node_id2, ...],
            'distance': float,
            'coordinates': [[lat1, lon1], [lat2, lon2], ...]
        }
        veya None (yol bulunamazsa)
    """
    
    # Validasyon
    if not graph.node_exists(start_node):
        print(f"Hata: Başlangıç düğümü '{start_node}' bulunamadı!")
        return None
    
    if not graph.node_exists(end_node):
        print(f"Hata: Varış düğümü '{end_node}' bulunamadı!")
        return None
    
    # Mesafeler - başlangıçta tümü sonsuz
    distances = {node: float('inf') for node in graph.nodes}
    distances[start_node] = 0
    
    # Önceki düğümleri takip et (yolu geri oluşturmak için)
    previous = {node: None for node in graph.nodes}
    
    # Priority queue (min-heap)
    # Format: (mesafe, düğüm_id)
    pq = [(0, start_node)]
    
    # Ziyaret edilen düğümler
    visited = set()
    
    while pq:
        current_distance, current_node = heapq.heappop(pq)
        
        # Zaten ziyaret edildiyse atla
        if current_node in visited:
            continue
        
        visited.add(current_node)
        
        # Hedefe ulaştıysak dur
        if current_node == end_node:
            break
        
        # Eğer bu düğüme giden mesafe, kayıtlı mesafeden büyükse atla
        if current_distance > distances[current_node]:
            continue
        
        # Komşu düğümleri kontrol et
        neighbors = graph.get_neighbors(current_node)
        
        for neighbor in neighbors:
            neighbor_node = neighbor['node']
            weight = neighbor['weight']
            
            # Yeni mesafeyi hesapla
            new_distance = current_distance + weight
            
            # Daha kısa bir yol bulduysak güncelle
            if new_distance < distances[neighbor_node]:
                distances[neighbor_node] = new_distance
                previous[neighbor_node] = current_node
                heapq.heappush(pq, (new_distance, neighbor_node))
    
    # Yol bulunamadıysa
    if distances[end_node] == float('inf'):
        print(f"Uyarı: '{start_node}' ile '{end_node}' arasında yol bulunamadı!")
        return None
    
    # Yolu geri oluştur
    path = []
    current_node = end_node
    
    while current_node is not None:
        path.append(current_node)
        current_node = previous[current_node]
    
    path.reverse()
    
    # Koordinatları ekle
    coordinates = []
    for node_id in path:
        coords = graph.get_node_coords(node_id)
        if coords:
            coordinates.append([coords[0], coords[1]])  # [lat, lon]
    
    return {
        'path': path,
        'distance': round(distances[end_node], 3),
        'coordinates': coordinates,
        'node_count': len(path)
    }


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    İki koordinat arası mesafeyi hesaplar (Haversine formülü)
    
    Args:
        lat1, lon1: İlk nokta (derece)
        lat2, lon2: İkinci nokta (derece)
    
    Returns:
        Mesafe (km)
    """
    R = 6371  # Dünya yarıçapı (km)
    
    # Dereceyi radyana çevir
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formülü
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def find_nearest_node(lat: float, lon: float, graph: Graph) -> str:
    """
    Tıklanan koordinata en yakın düğümü bulur
    
    Args:
        lat: Tıklanan latitude
        lon: Tıklanan longitude
        graph: Graph objesi
    
    Returns:
        En yakın düğümün ID'si
    """
    nearest_node = None
    min_distance = float('inf')
    
    for node_id, node_data in graph.nodes.items():
        distance = haversine_distance(
            lat, lon, 
            node_data['lat'], node_data['lon']
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_node = node_id
    
    return nearest_node


def find_optimal_route_tsp(graph: Graph, start_node: str, waypoints: List[str], end_node: str) -> Optional[Dict]:
    """
    TSP (Traveling Salesman Problem) yaklaşımı
    Tüm waypoint'lere uğrayarak başlangıç ve bitiş arasındaki en kısa yolu bulur
    
    Args:
        graph: Graph objesi
        start_node: Başlangıç düğümü ID'si
        waypoints: Ara durak düğüm ID'leri listesi
        end_node: Bitiş düğümü ID'si
    
    Returns:
        {
            'optimal_order': [node_id1, node_id2, ...],  # En iyi sıralama
            'total_distance': float,
            'segments': [segment1, segment2, ...],  # Her segment'in detayları
            'coordinates': [[lat1, lon1], [lat2, lon2], ...]
        }
    """
    from itertools import permutations
    
    # Validasyon
    if not graph.node_exists(start_node):
        print(f"Hata: Başlangıç düğümü '{start_node}' bulunamadı!")
        return None
    
    if not graph.node_exists(end_node):
        print(f"Hata: Bitiş düğümü '{end_node}' bulunamadı!")
        return None
    
    for wp in waypoints:
        if not graph.node_exists(wp):
            print(f"Hata: Waypoint '{wp}' bulunamadı!")
            return None
    
    # Eğer waypoint yoksa, direkt yol hesapla
    if len(waypoints) == 0:
        result = dijkstra(graph, start_node, end_node)
        if result:
            return {
                'optimal_order': [start_node, end_node],
                'total_distance': result['distance'],
                'segments': [result],
                'coordinates': result['coordinates']
            }
        return None
    
    # Tüm waypoint permütasyonlarını test et
    best_distance = float('inf')
    best_order = None
    best_segments = None
    
    print(f"🔍 TSP: {len(waypoints)} ara durak için {len(list(permutations(waypoints)))} kombinasyon test ediliyor...")
    
    for perm in permutations(waypoints):
        # Bu permütasyon için rotayı oluştur: start → perm[0] → perm[1] → ... → end
        route = [start_node] + list(perm) + [end_node]
        
        total_distance = 0
        segments = []
        valid = True
        
        # Her segment için Dijkstra çalıştır
        for i in range(len(route) - 1):
            segment = dijkstra(graph, route[i], route[i + 1])
            
            if segment is None:
                valid = False
                break
            
            total_distance += segment['distance']
            segments.append(segment)
        
        # Eğer bu rota geçerliyse ve daha kısaysa kaydet
        if valid and total_distance < best_distance:
            best_distance = total_distance
            best_order = route
            best_segments = segments
    
    if best_order is None:
        print(" Hiçbir geçerli rota bulunamadı!")
        return None
    
    # Tüm koordinatları birleştir
    all_coordinates = []
    for segment in best_segments:
        all_coordinates.extend(segment['coordinates'])
    
    print(f" En kısa rota bulundu: {' → '.join(best_order)}")
    print(f" Toplam mesafe: {best_distance:.3f} km")
    
    return {
        'optimal_order': best_order,
        'total_distance': round(best_distance, 3),
        'segments': best_segments,
        'coordinates': all_coordinates
    }


# Test kodu
if __name__ == "__main__":
    # Örnek test verisi
    test_nodes = {
        "node_0": {"lat": 37.2156, "lon": 28.3638},
        "node_1": {"lat": 37.2160, "lon": 28.3640},
        "node_2": {"lat": 37.2165, "lon": 28.3645},
        "node_3": {"lat": 37.2170, "lon": 28.3650},
        "node_4": {"lat": 37.2175, "lon": 28.3655}
    }
    
    test_edges = {
        "node_0": [{"node": "node_1", "weight": 0.5}],
        "node_1": [{"node": "node_0", "weight": 0.5}, {"node": "node_2", "weight": 0.6}],
        "node_2": [{"node": "node_1", "weight": 0.6}, {"node": "node_3", "weight": 0.7}],
        "node_3": [{"node": "node_2", "weight": 0.7}, {"node": "node_4", "weight": 0.5}],
        "node_4": [{"node": "node_3", "weight": 0.5}]
    }
    
    graph = Graph(test_nodes, test_edges)
    
    # Test 1: Normal Dijkstra
    print("=" * 60)
    print("TEST 1: Normal Dijkstra (node_0 → node_3)")
    print("=" * 60)
    result = dijkstra(graph, "node_0", "node_3")
    if result:
        print("En kısa yol bulundu!")
        print(f"Yol: {' → '.join(result['path'])}")
        print(f"Mesafe: {result['distance']} km")
        print(f"Düğüm sayısı: {result['node_count']}")
    else:
        print(" Yol bulunamadı!")
    
    print("\n")
    
    # Test 2: TSP ile ara duraklar
    print("=" * 60)
    print("TEST 2: TSP (node_0 → [node_1, node_3] → node_4)")
    print("=" * 60)
    result_tsp = find_optimal_route_tsp(graph, "node_0", ["node_1", "node_3"], "node_4")
    if result_tsp:
        print(f"En iyi rota: {' → '.join(result_tsp['optimal_order'])}")
        print(f"Toplam mesafe : {result_tsp['total_distance']} km")
