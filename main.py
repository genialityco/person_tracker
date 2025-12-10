import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import os

# ============================================================================
# INSTALACIÓN REQUERIDA (solo estas 3 librerías):
# pip install ultralytics opencv-python numpy
# ============================================================================
# NOTA: ByteTrack NO es necesario - usamos tracking integrado basado en IoU
# que funciona excelente para cámaras fijas en bares
# ============================================================================

class BarAnalyticsSystem:
    def __init__(self, video_source=0, save_path="analytics_data"):
        """
        Sistema de análisis para bar al aire libre
        
        Args:
            video_source: 0 para webcam, o ruta a video/stream RTSP
            save_path: carpeta para guardar datos de analytics
        """
        # Modelo YOLO para detección
        self.model = YOLO('yolov8n.pt')  # Usar yolov8m.pt para más precisión
        
        # Configuración de video
        self.cap = cv2.VideoCapture(video_source)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        
        # Tracking con ByteTrack (implementado manualmente)
        self.tracks = {}  # track_id: info del track
        self.next_track_id = 1
        self.max_age = 30  # frames para considerar track perdido
        
        # Analytics
        self.hourly_counts = defaultdict(int)
        self.daily_counts = defaultdict(int)
        self.entry_times = {}  # track_id: tiempo de entrada
        self.stay_durations = []
        self.sentiment_data = {'positivo': 0, 'neutral': 0, 'negativo': 0}
        
        # Configuración
        self.save_path = save_path
        os.makedirs(save_path, exist_ok=True)
        
        # Zona de interés (ROI) - ajustar según tu cámara
        # Formato: (x1, y1, x2, y2) - porcentaje de la imagen
        self.roi = (0.1, 0.2, 0.9, 0.8)  # 10-90% ancho, 20-80% alto
        
    def get_roi_mask(self, frame_shape):
        """Crear máscara de la zona de interés"""
        h, w = frame_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        x1 = int(w * self.roi[0])
        y1 = int(h * self.roi[1])
        x2 = int(w * self.roi[2])
        y2 = int(h * self.roi[3])
        mask[y1:y2, x1:x2] = 255
        return mask, (x1, y1, x2, y2)
    
    def simple_track(self, detections, frame_count):
        """
        Tracking basado en IoU (Intersection over Union)
        Perfecto para cámaras fijas como las de bares
        No requiere ByteTrack - funcionalidad integrada
        """
        if not detections:
            # Envejecer tracks existentes
            tracks_to_remove = []
            for track_id, track_info in self.tracks.items():
                track_info['age'] += 1
                if track_info['age'] > self.max_age:
                    tracks_to_remove.append(track_id)
            
            for track_id in tracks_to_remove:
                self.end_track(track_id)
                del self.tracks[track_id]
            return []
        
        tracked = []
        unmatched_dets = list(range(len(detections)))
        
        # Matching simple por IoU
        for track_id, track_info in list(self.tracks.items()):
            best_iou = 0
            best_idx = -1
            
            for i in unmatched_dets:
                iou = self.calculate_iou(track_info['bbox'], detections[i]['bbox'])
                if iou > best_iou and iou > 0.3:
                    best_iou = iou
                    best_idx = i
            
            if best_idx >= 0:
                # Match encontrado
                self.tracks[track_id]['bbox'] = detections[best_idx]['bbox']
                self.tracks[track_id]['age'] = 0
                self.tracks[track_id]['conf'] = detections[best_idx]['conf']
                tracked.append({'id': track_id, **detections[best_idx]})
                unmatched_dets.remove(best_idx)
            else:
                # No match, envejecer
                track_info['age'] += 1
                if track_info['age'] > self.max_age:
                    self.end_track(track_id)
                    del self.tracks[track_id]
        
        # Crear nuevos tracks para detecciones sin match
        for idx in unmatched_dets:
            track_id = self.next_track_id
            self.next_track_id += 1
            self.tracks[track_id] = {
                'bbox': detections[idx]['bbox'],
                'age': 0,
                'conf': detections[idx]['conf']
            }
            self.start_track(track_id)
            tracked.append({'id': track_id, **detections[idx]})
        
        return tracked
    
    def calculate_iou(self, box1, box2):
        """Calcular Intersection over Union"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        
        return inter / union if union > 0 else 0
    
    def start_track(self, track_id):
        """Registrar entrada de una persona"""
        now = datetime.now()
        self.entry_times[track_id] = now
        
        # Conteo por hora y día
        hour_key = now.strftime("%Y-%m-%d %H:00")
        day_key = now.strftime("%Y-%m-%d")
        self.hourly_counts[hour_key] += 1
        self.daily_counts[day_key] += 1
    
    def end_track(self, track_id):
        """Registrar salida de una persona y calcular estadía"""
        if track_id in self.entry_times:
            entry = self.entry_times[track_id]
            exit_time = datetime.now()
            duration = (exit_time - entry).total_seconds() / 60  # minutos
            
            if duration > 1:  # Filtrar detecciones muy cortas
                self.stay_durations.append(duration)
            
            del self.entry_times[track_id]
    
    def analyze_sentiment(self, frame, bbox):
        """
        Análisis de sentimiento básico basado en movimiento y postura
        Para análisis facial real, integrar DeepFace o FER
        """
        x1, y1, x2, y2 = map(int, bbox)
        person_roi = frame[y1:y2, x1:x2]
        
        if person_roi.size == 0:
            return 'neutral'
        
        # Análisis simple: usar brillo y actividad
        # En producción, usar modelos de reconocimiento facial
        brightness = np.mean(person_roi)
        
        # Heurística simple (reemplazar con modelo real)
        if brightness > 140:
            sentiment = 'positivo'
        elif brightness < 100:
            sentiment = 'negativo'
        else:
            sentiment = 'neutral'
        
        return sentiment
    
    def process_frame(self, frame, frame_count):
        """Procesar un frame del video"""
        # Crear máscara ROI
        mask, roi_coords = self.get_roi_mask(frame.shape)
        
        # Detección con YOLO
        results = self.model(frame, classes=[0], conf=0.4, verbose=False)  # class 0 = person
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                
                # Verificar si está en ROI
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                if mask[center_y, center_x] > 0:
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'conf': conf
                    })
        
        # Tracking
        tracked_objects = self.simple_track(detections, frame_count)
        
        # Análisis de sentimiento (cada 30 frames para eficiencia)
        if frame_count % 30 == 0:
            for obj in tracked_objects:
                sentiment = self.analyze_sentiment(frame, obj['bbox'])
                self.sentiment_data[sentiment] += 1
        
        return tracked_objects, roi_coords
    
    def draw_analytics(self, frame, tracked_objects, roi_coords):
        """Dibujar información en el frame"""
        # Dibujar ROI
        x1, y1, x2, y2 = roi_coords
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(frame, "ZONA DE ANALISIS", (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Dibujar personas detectadas
        for obj in tracked_objects:
            x1, y1, x2, y2 = map(int, obj['bbox'])
            track_id = obj['id']
            
            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # ID y confianza
            label = f"ID: {track_id} ({obj['conf']:.2f})"
            cv2.putText(frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Panel de información
        info_y = 30
        cv2.rectangle(frame, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (400, 200), (255, 255, 255), 2)
        
        # Estadísticas actuales
        cv2.putText(frame, f"Personas actuales: {len(tracked_objects)}", (20, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 30
        
        # Conteo del día
        today = datetime.now().strftime("%Y-%m-%d")
        cv2.putText(frame, f"Total hoy: {self.daily_counts[today]}", (20, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 30
        
        # Tiempo promedio de estadía
        if self.stay_durations:
            avg_stay = np.mean(self.stay_durations)
            cv2.putText(frame, f"Estadia prom: {avg_stay:.1f} min", (20, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        info_y += 30
        
        # Sentimientos
        total_sentiment = sum(self.sentiment_data.values())
        if total_sentiment > 0:
            pos_pct = (self.sentiment_data['positivo'] / total_sentiment) * 100
            neu_pct = (self.sentiment_data['neutral'] / total_sentiment) * 100
            neg_pct = (self.sentiment_data['negativo'] / total_sentiment) * 100
            
            cv2.putText(frame, f"Sentimiento:", (20, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            info_y += 25
            cv2.putText(frame, f"  Positivo: {pos_pct:.1f}%", (20, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            info_y += 20
            cv2.putText(frame, f"  Neutral: {neu_pct:.1f}%", (20, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            info_y += 20
            cv2.putText(frame, f"  Negativo: {neg_pct:.1f}%", (20, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame
    
    def save_analytics(self):
        """Guardar datos de analytics a JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        data = {
            'timestamp': timestamp,
            'hourly_counts': dict(self.hourly_counts),
            'daily_counts': dict(self.daily_counts),
            'stay_durations': self.stay_durations,
            'avg_stay_duration': np.mean(self.stay_durations) if self.stay_durations else 0,
            'sentiment_data': self.sentiment_data,
            'total_sentiment': sum(self.sentiment_data.values())
        }
        
        filename = os.path.join(self.save_path, f'analytics_{timestamp}.json')
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Analytics guardados en: {filename}")
        return filename
    
    def print_report(self):
        """Imprimir reporte en consola"""
        print("\n" + "="*60)
        print("REPORTE DE ANALYTICS - BAR AL AIRE LIBRE")
        print("="*60)
        
        # Conteo por día
        print("\n📅 CONTEO POR DÍA:")
        for day, count in sorted(self.daily_counts.items()):
            print(f"  {day}: {count} personas")
        
        # Conteo por hora (últimas 24 horas)
        print("\n⏰ CONTEO POR HORA (últimas entradas):")
        for hour, count in sorted(self.hourly_counts.items())[-24:]:
            print(f"  {hour}: {count} personas")
        
        # Tiempo de estadía
        if self.stay_durations:
            print(f"\n⏱️  TIEMPO DE ESTADÍA:")
            print(f"  Promedio: {np.mean(self.stay_durations):.1f} minutos")
            print(f"  Mínimo: {np.min(self.stay_durations):.1f} minutos")
            print(f"  Máximo: {np.max(self.stay_durations):.1f} minutos")
        
        # Sentimientos
        total = sum(self.sentiment_data.values())
        if total > 0:
            print(f"\n😊 ANÁLISIS DE SENTIMIENTO:")
            print(f"  Positivo: {(self.sentiment_data['positivo']/total)*100:.1f}%")
            print(f"  Neutral:  {(self.sentiment_data['neutral']/total)*100:.1f}%")
            print(f"  Negativo: {(self.sentiment_data['negativo']/total)*100:.1f}%")
        
        print("\n" + "="*60 + "\n")
    
    def run(self, show_video=True, save_interval=300):
        """
        Ejecutar el sistema de análisis
        
        Args:
            show_video: Mostrar video en tiempo real
            save_interval: Segundos entre guardados automáticos
        """
        print("🚀 Iniciando sistema de análisis...")
        print("Presiona 'q' para salir, 's' para guardar reporte manual")
        
        frame_count = 0
        last_save = datetime.now()
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error leyendo frame o fin del video")
                    break
                
                # Procesar frame
                tracked_objects, roi_coords = self.process_frame(frame, frame_count)
                
                # Dibujar analytics
                if show_video:
                    frame_display = self.draw_analytics(frame.copy(), tracked_objects, roi_coords)
                    cv2.imshow('Bar Analytics System', frame_display)
                
                # Auto-save periódico
                if (datetime.now() - last_save).seconds >= save_interval:
                    self.save_analytics()
                    last_save = datetime.now()
                
                # Controles
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.save_analytics()
                    self.print_report()
                
                frame_count += 1
        
        finally:
            # Guardar datos finales
            print("\n📊 Generando reporte final...")
            self.save_analytics()
            self.print_report()
            
            self.cap.release()
            cv2.destroyAllWindows()


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

def select_video_source():
    """Menú interactivo para seleccionar fuente de video"""
    print("\n" + "="*60)
    print("SISTEMA DE ANÁLISIS DE BAR - SELECCIÓN DE FUENTE")
    print("="*60)
    print("\nSelecciona la fuente de video:")
    print("1. Webcam/Cámara USB")
    print("2. Archivo de video (MP4, AVI, etc.)")
    print("3. Cámara IP/RTSP")
    print("4. Salir")
    print("="*60)
    
    while True:
        choice = input("\nIngresa tu opción (1-4): ").strip()
        
        if choice == '1':
            cam_id = input("ID de cámara (0 para default): ").strip()
            try:
                cam_id = int(cam_id) if cam_id else 0
                return cam_id
            except:
                print("❌ ID inválido, usando cámara 0")
                return 0
        
        elif choice == '2':
            file_path = input("Ruta del archivo de video: ").strip()
            if os.path.exists(file_path):
                return file_path
            else:
                print(f"❌ Archivo no encontrado: {file_path}")
                retry = input("¿Intentar de nuevo? (s/n): ").lower()
                if retry != 's':
                    return None
        
        elif choice == '3':
            rtsp_url = input("URL RTSP (ej: rtsp://user:pass@ip:554/stream): ").strip()
            return rtsp_url
        
        elif choice == '4':
            print("Saliendo...")
            return None
        
        else:
            print("❌ Opción inválida. Intenta de nuevo.")


if __name__ == "__main__":
    # Seleccionar fuente de video
    video_source = select_video_source()
    
    if video_source is None:
        print("No se seleccionó ninguna fuente de video.")
        exit()
    
    # Crear sistema con la fuente seleccionada
    print(f"\n✓ Fuente seleccionada: {video_source}")
    system = BarAnalyticsSystem(video_source=video_source)
    
    # Configurar opciones de ejecución
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE ANÁLISIS")
    print("="*60)
    
    show_video = input("¿Mostrar video en tiempo real? (s/n, default=s): ").lower()
    show_video = show_video != 'n'
    
    save_interval = input("Intervalo de guardado en segundos (default=300): ").strip()
    try:
        save_interval = int(save_interval) if save_interval else 300
    except:
        save_interval = 300
    
    # Ejecutar sistema
    print("\n🚀 Iniciando análisis...")
    print("Presiona 'q' para salir, 's' para guardar reporte manual")
    system.run(show_video=show_video, save_interval=save_interval)