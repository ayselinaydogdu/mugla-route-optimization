/**
 * Smart Route Navigator - Frontend Script
 * CENG 3511 - Artificial Intelligence Final Project
 * TSP yaklaşımı: Tüm ara duraklara uğrayarak en kısa yol
 */

// Global değişkenler
let map;
let graphData = null;
let markers = []; // Tüm marker'lar
let pathPolylines = []; // Tüm yol parçaları
let waypoints = []; // Seçilen noktalar {lat, lon, marker}

// Python Backend API URL
const API_URL = 'http://localhost:8000/api';

// Maksimum nokta sayısı
const MAX_WAYPOINTS = 7;

// Marker renkleri
const MARKER_COLORS = [
    'blue',    // Başlangıç
    'gold',    // Ara 1
    'orange',  // Ara 2
    'violet',  // Ara 3
    'green',   // Ara 4
    'grey',    // Ara 5
    'red'      // Bitiş
];

/**
 * Sayfa yüklendiğinde çalışır
 */
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadGraphData();
    setupEventListeners();
});

/**
 * Leaflet haritasını başlatır
 */
function initMap() {
    const muglaCenterLat = 37.2156;
    const muglaCenterLon = 28.3638;
    
    map = L.map('map').setView([muglaCenterLat, muglaCenterLon], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    map.on('click', onMapClick);
    
    console.log('✅ Harita başlatıldı');
}

/**
 * Graph verisini Python API'den yükler
 */
async function loadGraphData() {
    try {
        updateStatus('Graph verisi yükleniyor...', 'loading');
        
        const response = await fetch(`${API_URL}/graph`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        graphData = data;
        
        document.getElementById('totalNodes').textContent = data.stats.node_count;
        document.getElementById('totalEdges').textContent = data.stats.edge_count;
        
        updateStatus('🔵 Başlangıç noktası seçin', 'ready');
        console.log('✅ Graph verisi yüklendi:', data.stats);
        
    } catch (error) {
        console.error('❌ Graph yüklenemedi:', error);
        updateStatus('Hata: Backend bağlantısı başarısız!', 'error');
        alert('Backend sunucusu çalışmıyor! Terminal\'de "python3 backend/app.py" komutunu çalıştırın.');
    }
}

/**
 * Event listener'ları ayarlar
 */
function setupEventListeners() {
    const resetBtn = document.getElementById('resetBtn');
    resetBtn.addEventListener('click', resetMap);
}

/**
 * Harita tıklandığında çalışır
 */
function onMapClick(e) {
    if (!graphData) {
        alert('Graph verisi henüz yüklenmedi. Lütfen bekleyin.');
        return;
    }
    
    if (waypoints.length >= MAX_WAYPOINTS) {
        alert(`Maksimum ${MAX_WAYPOINTS} nokta seçebilirsiniz!`);
        return;
    }
    
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    
    addWaypoint(lat, lon);
}

/**
 * Yeni nokta ekler
 */
function addWaypoint(lat, lon) {
    const pointIndex = waypoints.length;
    
    let color = MARKER_COLORS[pointIndex];
    let label;
    
    if (pointIndex === 0) {
        label = '🔵 Başlangıç';
    } else if (pointIndex < MAX_WAYPOINTS - 1) {
        label = `🟡 Ara Durak ${pointIndex}`;
    } else {
        label = '🔴 Bitiş';
    }
    
    const marker = L.marker([lat, lon], {
        icon: L.icon({
            iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(map);
    
    marker.bindPopup(label).openPopup();
    
    waypoints.push({ lat, lon, marker, label, originalIndex: pointIndex });
    markers.push(marker);
    
    updateWaypointsList();
    
    if (pointIndex === 0) {
        updateStatus('🟡 Ara durakları ekleyin', 'waiting');
    } else if (pointIndex < MAX_WAYPOINTS - 1) {
        updateStatus(`🟡 Daha fazla ara durak ekleyin veya 🔴 Bitiş seçin`, 'waiting');
    } else {
        updateStatus('✅ Noktalar hazır! "Rotayı Hesapla" ile en kısa yolu bulun', 'ready');
    }
    
    if (waypoints.length >= 2) {
        document.getElementById('calculateBtn').style.display = 'block';
    }
    
    console.log(`✅ Nokta ${pointIndex + 1} eklendi:`, label);
}

/**
 * Waypoints listesini günceller
 */
function updateWaypointsList() {
    document.getElementById('startNode').textContent = waypoints[0] 
        ? `${waypoints[0].lat.toFixed(5)}, ${waypoints[0].lon.toFixed(5)}` 
        : '-';
    
    document.getElementById('endNode').textContent = waypoints.length >= 2
        ? `${waypoints[waypoints.length-1].lat.toFixed(5)}, ${waypoints[waypoints.length-1].lon.toFixed(5)}`
        : '-';
    
    const araDurakSayisi = Math.max(0, waypoints.length - 2);
    document.getElementById('pathNodes').textContent = waypoints.length >= 2
        ? `${waypoints.length} nokta (${araDurakSayisi} ara durak)`
        : `${waypoints.length}/${MAX_WAYPOINTS} nokta`;
}

/**
 * İki nokta arası mesafeyi hesaplar (API'den)
 */
async function getDistance(point1, point2) {
    try {
        const response = await fetch(`${API_URL}/find-path`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_lat: point1.lat,
                start_lon: point1.lon,
                end_lat: point2.lat,
                end_lon: point2.lon
            })
        });
        
        if (!response.ok) {
            return { distance: Infinity, coordinates: [], node_count: 0 };
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Mesafe hesaplama hatası:', error);
        return { distance: Infinity, coordinates: [], node_count: 0 };
    }
}

/**
 * Permütasyonları oluşturur (ara duraklar için)
 */
function permute(arr) {
    if (arr.length <= 1) return [arr];
    
    const result = [];
    for (let i = 0; i < arr.length; i++) {
        const rest = [...arr.slice(0, i), ...arr.slice(i + 1)];
        const perms = permute(rest);
        for (const perm of perms) {
            result.push([arr[i], ...perm]);
        }
    }
    return result;
}

/**
 * TSP: En kısa rotayı bulur (Python Backend'de hesaplanır)
 */
async function findOptimalRoute() {
    if (waypoints.length < 2) {
        alert('En az 2 nokta (Başlangıç ve Bitiş) gerekli!');
        return;
    }
    
    updateStatus('🔍 Python Backend\'de TSP çalışıyor...', 'calculating');
    
    const start = waypoints[0];
    const end = waypoints[waypoints.length - 1];
    const middlePoints = waypoints.slice(1, -1); // Ara duraklar
    
    console.log(`📊 Başlangıç: ${start.label}`);
    console.log(`📊 Bitiş: ${end.label}`);
    console.log(`📊 Ara duraklar: ${middlePoints.length}`);
    
    try {
        // Python Backend'e TSP isteği gönder
        const response = await fetch(`${API_URL}/find-optimal-route`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_lat: start.lat,
                start_lon: start.lon,
                waypoints: middlePoints.map(wp => ({ lat: wp.lat, lon: wp.lon })),
                end_lat: end.lat,
                end_lon: end.lon
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'En iyi rota bulunamadı');
        }
        
        const result = await response.json();
        
        console.log('✅ Python Backend\'den en iyi rota alındı:', result);
        
        // Sonuçları göster
        await drawOptimalRouteFromBackend(result);
        
    } catch (error) {
        console.error('❌ TSP hatası:', error);
        updateStatus('❌ Hata: ' + error.message, 'error');
        alert('En iyi rota bulunamadı!\n' + error.message);
    }
}

/**
 * Backend'den gelen optimal rotayı çizer
 */
async function drawOptimalRouteFromBackend(result) {
    pathPolylines.forEach(poly => map.removeLayer(poly));
    pathPolylines = [];
    
    const segmentColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
    let totalNodes = 0;
    
    // Her segmenti çiz
    result.segments.forEach((segment, i) => {
        const color = segmentColors[i % segmentColors.length];
        
        const polyline = L.polyline(segment.coordinates, {
            color: color,
            weight: 5,
            opacity: 0.8,
            smoothFactor: 1
        }).addTo(map);
        
        pathPolylines.push(polyline);
        totalNodes += segment.node_count;
    });
    
    // Rota sırasını göster
    let rotaMetni = result.optimal_order.map((nodeId, i) => {
        if (i === 0) return '🔵 Başlangıç';
        if (i === result.optimal_order.length - 1) return '🔴 Bitiş';
        return `🟡 Ara ${i}`;
    }).join(' → ');
    
    console.log('✅ En kısa rota (Python):', rotaMetni);
    console.log(`📏 Toplam mesafe: ${result.total_distance} km`);
    
    updateStatus('✅ En kısa rota bulundu! (Python Dijkstra + TSP)', 'success');
    document.getElementById('distance').textContent = `${result.total_distance} km`;
    document.getElementById('pathNodes').textContent = `${waypoints.length} nokta, ${totalNodes} düğüm`;
    
    const bounds = L.latLngBounds(result.coordinates);
    map.fitBounds(bounds, { padding: [50, 50] });
    
    document.getElementById('resetBtn').style.display = 'block';
    
    const midPoint = result.coordinates[Math.floor(result.coordinates.length / 2)];
    L.popup()
        .setLatLng(midPoint)
        .setContent(`
            <div style="text-align: center;">
                <strong>🏆 En Kısa Rota!</strong><br>
                <small>(Python Dijkstra + TSP)</small><br>
                ${rotaMetni}<br>
                Toplam: ${result.total_distance} km<br>
                Düğüm: ${totalNodes}
            </div>
        `)
        .openOn(map);
}

/**
 * Direkt rota hesaplar (ara durak yoksa)
 */
async function calculateDirectRoute(route) {
    updateStatus('Dijkstra algoritması çalışıyor...', 'calculating');
    
    pathPolylines.forEach(poly => map.removeLayer(poly));
    pathPolylines = [];
    
    try {
        const segment = await getDistance(route[0], route[1]);
        
        if (segment.distance === Infinity) {
            throw new Error('Bu iki nokta arasında yol bulunamadı!');
        }
        
        const polyline = L.polyline(segment.coordinates, {
            color: '#3b82f6',
            weight: 5,
            opacity: 0.8,
            smoothFactor: 1
        }).addTo(map);
        
        pathPolylines.push(polyline);
        
        updateStatus('✅ Rota hesaplandı!', 'success');
        document.getElementById('distance').textContent = `${segment.distance.toFixed(3)} km`;
        document.getElementById('pathNodes').textContent = `${segment.node_count} düğüm`;
        
        const bounds = L.latLngBounds(segment.coordinates);
        map.fitBounds(bounds, { padding: [50, 50] });
        
        document.getElementById('resetBtn').style.display = 'block';
        
        L.popup()
            .setLatLng(segment.coordinates[Math.floor(segment.coordinates.length / 2)])
            .setContent(`
                <div style="text-align: center;">
                    <strong>📍 En Kısa Yol</strong><br>
                    🔵 Başlangıç → 🔴 Bitiş<br>
                    Mesafe: ${segment.distance.toFixed(3)} km
                </div>
            `)
            .openOn(map);
            
    } catch (error) {
        console.error('❌ Rota hesaplanamadı:', error);
        updateStatus('❌ Hata: ' + error.message, 'error');
        alert('Rota hesaplanamadı!\n' + error.message);
    }
}

/**
 * Optimal rotayı çizer
 */
async function drawOptimalRoute(route, segments, totalDistance) {
    pathPolylines.forEach(poly => map.removeLayer(poly));
    pathPolylines = [];
    
    const segmentColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
    let allCoordinates = [];
    let totalNodes = 0;
    
    // Her segmenti çiz
    for (let i = 0; i < segments.length; i++) {
        const color = segmentColors[i % segmentColors.length];
        
        const polyline = L.polyline(segments[i].coordinates, {
            color: color,
            weight: 5,
            opacity: 0.8,
            smoothFactor: 1
        }).addTo(map);
        
        pathPolylines.push(polyline);
        allCoordinates.push(...segments[i].coordinates);
        totalNodes += segments[i].node_count;
    }
    
    // Rota sırasını göster
    let rotaMetni = '';
    route.forEach((point, i) => {
        if (i > 0) rotaMetni += ' → ';
        rotaMetni += point.label;
    });
    
    console.log('✅ En kısa rota bulundu:', rotaMetni);
    console.log(`📏 Toplam mesafe: ${totalDistance.toFixed(3)} km`);
    
    updateStatus('✅ En kısa rota bulundu!', 'success');
    document.getElementById('distance').textContent = `${totalDistance.toFixed(3)} km`;
    document.getElementById('pathNodes').textContent = `${route.length} nokta, ${totalNodes} düğüm`;
    
    const bounds = L.latLngBounds(allCoordinates);
    map.fitBounds(bounds, { padding: [50, 50] });
    
    document.getElementById('resetBtn').style.display = 'block';
    
    const midPoint = allCoordinates[Math.floor(allCoordinates.length / 2)];
    L.popup()
        .setLatLng(midPoint)
        .setContent(`
            <div style="text-align: center;">
                <strong>🏆 En Kısa Rota Bulundu!</strong><br>
                ${rotaMetni}<br>
                Toplam: ${totalDistance.toFixed(3)} km<br>
                Düğüm: ${totalNodes}
            </div>
        `)
        .openOn(map);
}

/**
 * Haritayı sıfırlar
 */
function resetMap() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    pathPolylines.forEach(poly => map.removeLayer(poly));
    pathPolylines = [];
    
    waypoints = [];
    
    updateStatus('🔵 Başlangıç noktası seçin', 'ready');
    document.getElementById('startNode').textContent = '-';
    document.getElementById('endNode').textContent = '-';
    document.getElementById('distance').textContent = '-';
    document.getElementById('pathNodes').textContent = '-';
    document.getElementById('resetBtn').style.display = 'none';
    document.getElementById('calculateBtn').style.display = 'none';
    
    map.setView([37.2156, 28.3638], 13);
    
    console.log('🔄 Harita sıfırlandı');
}

/**
 * Durum mesajını günceller
 */
function updateStatus(message, type) {
    const statusElement = document.getElementById('status');
    statusElement.textContent = message;
    
    switch(type) {
        case 'loading':
        case 'calculating':
            statusElement.style.color = '#f59e0b';
            break;
        case 'success':
            statusElement.style.color = '#22c55e';
            break;
        case 'error':
            statusElement.style.color = '#ef4444';
            break;
        case 'ready':
        case 'waiting':
        default:
            statusElement.style.color = '#ffffff';
            break;
    }
}

// Hesapla butonunu ekle
window.addEventListener('load', function() {
    const infoPanel = document.getElementById('infoPanel');
    const calculateBtn = document.createElement('button');
    calculateBtn.id = 'calculateBtn';
    calculateBtn.className = 'reset-btn';
    calculateBtn.textContent = '🏆 En Kısa Rotayı Bul (Python TSP)';
    calculateBtn.style.display = 'none';
    calculateBtn.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
    calculateBtn.style.color = 'white';
    calculateBtn.style.marginBottom = '10px';
    calculateBtn.addEventListener('click', findOptimalRoute);
    
    const resetBtn = document.getElementById('resetBtn');
    infoPanel.insertBefore(calculateBtn, resetBtn);
});

console.log('🗺️ Smart Route Navigator - Python TSP Modu');
console.log('📡 Backend URL:', API_URL);
console.log('🏆 Python Dijkstra + TSP ile en kısa yol bulur');


