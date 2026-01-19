"""
Flask Web Server
CENG 3511 - Artificial Intelligence Final Project
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from dijkstra import Graph, dijkstra, find_nearest_node, find_optimal_route_tsp

app = Flask(__name__)
CORS(app)  # CORS izinleri (frontend-backend iletişimi için)

# Global değişkenler
graph_data = None
graph = None


def load_graph_data():
    """mugla_full.json dosyasını yükler"""
    global graph_data, graph
    
    try:
        with open('mugla_full.json', 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        graph = Graph(graph_data['nodes'], graph_data['edges'])
        print("✅ Graph verisi başarıyla yüklendi!")
        print(f"   - Toplam düğüm: {len(graph_data['nodes'])}")
        print(f"   - Toplam bağlantı: {sum(len(edges) for edges in graph_data['edges'].values()) // 2}")
        return True
    except FileNotFoundError:
        print("❌ HATA: mugla_full.json dosyası bulunamadı!")
        print("   Lütfen mugla_full.json dosyasını backend/ klasörüne koyun.")
        return False
    except json.JSONDecodeError:
        print("❌ HATA: mugla_full.json dosyası geçerli bir JSON değil!")
        return False
    except Exception as e:
        print(f"❌ HATA: Graph verisi yüklenirken hata: {e}")
        return False


@app.route('/')
def index():
    """Ana sayfa"""
    return """
    <html>
        <head>
            <title>Smart Route Navigator API</title>
            <style>
                body { font-family: Arial; padding: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                h1 { color: #667eea; }
                code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
                .endpoint { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🗺️ Smart Route Navigator API</h1>
                <p>Flask backend server çalışıyor! 🎉</p>
                
                <h2>API Endpoints:</h2>
                
                <div class="endpoint">
                    <strong>GET /api/graph</strong><br>
                    Graph verilerini döndürür (düğümler ve kenarlar)
                </div>
                
                <div class="endpoint">
                    <strong>POST /api/find-path</strong><br>
                    En kısa yolu hesaplar<br>
                    Body: <code>{"start_lat": 37.21, "start_lon": 28.36, "end_lat": 37.22, "end_lon": 28.37}</code>
                </div>
                
                <div class="endpoint">
                    <strong>POST /api/dijkstra</strong><br>
                    İki düğüm ID'si ile en kısa yolu hesaplar<br>
                    Body: <code>{"start_node": "node_0", "end_node": "node_10"}</code>
                </div>
                
                <p><a href="/api/graph">Graph verisini görüntüle</a></p>
            </div>
        </body>
    </html>
    """


@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Graph verisini döndürür"""
    if graph_data is None:
        return jsonify({
            'error': 'Graph verisi yüklenmedi',
            'message': 'mugla_full.json dosyasını backend/ klasörüne koyun'
        }), 500
    
    return jsonify({
        'nodes': graph_data['nodes'],
        'edges': graph_data['edges'],
        'stats': {
            'node_count': len(graph_data['nodes']),
            'edge_count': sum(len(edges) for edges in graph_data['edges'].values()) // 2
        }
    })


@app.route('/api/find-path', methods=['POST'])
def find_path():
    """
    Koordinatlardan en kısa yolu bulur
    Request body: {start_lat, start_lon, end_lat, end_lon}
    """
    if graph is None:
        return jsonify({'error': 'Graph verisi yüklenmedi'}), 500
    
    try:
        data = request.get_json()
        
        # Parametreleri al
        start_lat = float(data['start_lat'])
        start_lon = float(data['start_lon'])
        end_lat = float(data['end_lat'])
        end_lon = float(data['end_lon'])
        
        # En yakın düğümleri bul
        start_node = find_nearest_node(start_lat, start_lon, graph)
        end_node = find_nearest_node(end_lat, end_lon, graph)
        
        print(f"🔍 Yol aranıyor: {start_node} → {end_node}")
        
        # Dijkstra algoritmasını çalıştır
        result = dijkstra(graph, start_node, end_node)
        
        if result is None:
            return jsonify({
                'error': 'Yol bulunamadı',
                'message': 'Bu iki nokta arasında bağlantı yok'
            }), 404
        
        print(f"✅ Yol bulundu! Mesafe: {result['distance']} km")
        
        return jsonify({
            'success': True,
            'start_node': start_node,
            'end_node': end_node,
            'path': result['path'],
            'coordinates': result['coordinates'],
            'distance': result['distance'],
            'node_count': result['node_count']
        })
        
    except KeyError as e:
        return jsonify({'error': f'Eksik parametre: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Geçersiz değer: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500


@app.route('/api/dijkstra', methods=['POST'])
def dijkstra_endpoint():
    """
    İki düğüm ID'si ile en kısa yolu bulur
    Request body: {start_node, end_node}
    """
    if graph is None:
        return jsonify({'error': 'Graph verisi yüklenmedi'}), 500
    
    try:
        data = request.get_json()
        start_node = data['start_node']
        end_node = data['end_node']
        
        print(f"🔍 Dijkstra çalıştırılıyor: {start_node} → {end_node}")
        
        result = dijkstra(graph, start_node, end_node)
        
        if result is None:
            return jsonify({
                'error': 'Yol bulunamadı',
                'message': f'{start_node} ile {end_node} arasında bağlantı yok'
            }), 404
        
        print(f"✅ Yol bulundu! Mesafe: {result['distance']} km")
        
        return jsonify({
            'success': True,
            'path': result['path'],
            'coordinates': result['coordinates'],
            'distance': result['distance'],
            'node_count': result['node_count']
        })
        
    except KeyError as e:
        return jsonify({'error': f'Eksik parametre: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500


@app.route('/api/find-optimal-route', methods=['POST'])
def find_optimal_route():
    """
    TSP yaklaşımı: Tüm waypoint'lere uğrayarak en kısa rotayı bulur
    Request body: {
        start_lat, start_lon, 
        waypoints: [{lat, lon}, ...],
        end_lat, end_lon
    }
    """
    if graph is None:
        return jsonify({'error': 'Graph verisi yüklenmedi'}), 500
    
    try:
        data = request.get_json()
        
        # Başlangıç ve bitiş noktaları
        start_lat = float(data['start_lat'])
        start_lon = float(data['start_lon'])
        end_lat = float(data['end_lat'])
        end_lon = float(data['end_lon'])
        
        # Waypoints
        waypoints_coords = data.get('waypoints', [])
        
        # En yakın düğümleri bul
        start_node = find_nearest_node(start_lat, start_lon, graph)
        end_node = find_nearest_node(end_lat, end_lon, graph)
        
        waypoint_nodes = []
        for wp in waypoints_coords:
            wp_node = find_nearest_node(wp['lat'], wp['lon'], graph)
            waypoint_nodes.append(wp_node)
        
        print(f"🔍 TSP: Başlangıç: {start_node}")
        print(f"🔍 TSP: Waypoints: {waypoint_nodes}")
        print(f"🔍 TSP: Bitiş: {end_node}")
        
        # TSP ile en iyi rotayı bul
        result = find_optimal_route_tsp(graph, start_node, waypoint_nodes, end_node)
        
        if result is None:
            return jsonify({
                'error': 'En iyi rota bulunamadı',
                'message': 'Bu noktalar arasında geçerli bir rota yok'
            }), 404
        
        print(f"✅ En iyi rota bulundu! Mesafe: {result['total_distance']} km")
        
        return jsonify({
            'success': True,
            'optimal_order': result['optimal_order'],
            'total_distance': result['total_distance'],
            'segments': result['segments'],
            'coordinates': result['coordinates']
        })
        
    except KeyError as e:
        return jsonify({'error': f'Eksik parametre: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': f'Geçersiz değer: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Sunucu hatası: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Server sağlık kontrolü"""
    return jsonify({
        'status': 'healthy',
        'graph_loaded': graph is not None
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Smart Route Navigator - Flask Server")
    print("=" * 60)
    
    # Graph verisini yükle
    if load_graph_data():
        print("\n✅ Server başlatılıyor...")
        print("📍 URL: http://localhost:5000")
        print("📍 API: http://localhost:5000/api/graph")
        print("\n⚠️  Server'ı durdurmak için: Ctrl+C\n")
        
        app.run(debug=False, host='127.0.0.1', port=8000, use_reloader=False)
    else:
        print("\n❌ Graph verisi yüklenemedi, server başlatılamıyor!")
        print("💡 Çözüm: mugla_full.json dosyasını backend/ klasörüne koyun.")

