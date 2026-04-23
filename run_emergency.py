import traci
import time
import cv2
import os
import glob

CONFIG = "traffic.sumocfg"

NS_EDGES = ["N2C", "S2C"]
EW_EDGES = ["E2C", "W2C"]

EMERGENCY_VEHICLE_TYPES = {
    "ambulance": 1,
    "fire": 2,
    "police": 3,
}

AMBULANCE_DISTANCE = 150
SIM_STEP_TIME = 0.2
YELLOW_STEPS = 3
EMERGENCY_PRIORITY_DISTANCE_MARGIN = 60

# (R, G, B, A, guiShape)
VEHICLE_VISUALS = {
    "ambulance": (255, 0, 0, 255, "emergency"),
    "fire": (255, 100, 0, 255, "firebrigade"),
    "police": (0, 0, 220, 255, "police"),
}

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def activate_emergency_vehicle_siren(vehicle_id):
    try:
        traci.vehicle.setEmergencyState(vehicle_id, 1)
        return True
    except Exception:
        return False


def is_emergency_siren_active(vehicle_id):
    try:
        return traci.vehicle.getEmergencyState(vehicle_id) == 1
    except Exception:
        return False


frame_counter = 0  

# ----------------- Yardımcı Fonksiyonlar -----------------
def edge_vehicle_count(edges):
    return sum(traci.edge.getLastStepVehicleNumber(e) for e in edges)

def get_vehicle_direction(vehicle_id):
    edge = traci.vehicle.getRoadID(vehicle_id)
    if edge in NS_EDGES: return "NS"
    if edge in EW_EDGES: return "EW"
    return None

def take_screenshot(ns_count, ew_count, active_vehicle, max_count=20):
    """SUMO ekranını kaydedip üstüne canlı overlay ekler"""
    global frame_counter
    filename = os.path.join(SCREENSHOT_DIR, f"frame_{frame_counter:05d}.png")
    traci.gui.screenshot("View #0", filename)
    
    # 1. TUZAK ÇÖZÜMÜ: Dosyanın diske yazılmasını bekle
    while not os.path.exists(filename):
        time.sleep(0.01)
    time.sleep(0.05) # Dosyanın 0 byte kalmaması için ufak ekstra pay
    
    frame = cv2.imread(filename)
    if frame is not None:
        frame = overlay_info(frame, ns_count, ew_count, active_vehicle, max_count)
        cv2.imwrite(filename, frame)
    
    frame_counter += 1

def count_to_color(count, max_count=20):
    """Trafik sayısını yeşil → turuncu → kırmızı renk skalasına çevir"""
    ratio = min(count / max_count, 1.0)
    r = int(0 + ratio * 255)
    g = int(255 - ratio * 255)
    b = 0
    return (b, g, r)  # BGR format

def overlay_info(frame, ns_count, ew_count, active_vehicle, max_count=20):
    h, w, _ = frame.shape
    panel_height = 100
    overlay = frame.copy()
    
    # Üst panele yarı saydam siyah bir arka plan ekleyelim (yazılar daha net okunsun)
    cv2.rectangle(overlay, (0, 0), (w, panel_height), (30, 30, 30), -1)
    
    # NS bar
    ns_color = count_to_color(ns_count, max_count)
    ns_length = int((ns_count / max(max_count, 1)) * (w // 2.5))
    cv2.rectangle(overlay, (20, 20), (20 + ns_length, 60), ns_color, -1)
    cv2.putText(overlay, f"NS Yogunluk: {ns_count}", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # EW bar
    ew_color = count_to_color(ew_count, max_count)
    ew_length = int((ew_count / max(max_count, 1)) * (w // 2.5))
    cv2.rectangle(overlay, (w // 2 + 20, 20), (w // 2 + 20 + ew_length, 60), ew_color, -1)
    cv2.putText(overlay, f"EW Yogunluk: {ew_count}", (w // 2 + 20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Aktif acil araç
    if active_vehicle:
        veh_type = traci.vehicle.getTypeID(active_vehicle)
        
        # 2. TUZAK ÇÖZÜMÜ: RGB'den BGR'ye çevir ki yazılar doğru renkte olsun
        r, g, b = VEHICLE_VISUALS[veh_type][0], VEHICLE_VISUALS[veh_type][1], VEHICLE_VISUALS[veh_type][2]
        bgr_color = (b, g, r)
        
        cv2.putText(overlay, f"🚨 GECIS USTUNLUGU: {veh_type.upper()}", (w // 2 - 150, h - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr_color, 3)
    
    return overlay

# ----------------- Trafik ve Acil Araç -----------------
def safe_switch_to_green(tls_id, direction):
    current_phase = traci.trafficlight.getPhase(tls_id)

    if direction == "NS":
        if current_phase == 0:
            return
        if current_phase in (2, 3):
            traci.trafficlight.setPhase(tls_id, 3)
        else:
            traci.trafficlight.setPhase(tls_id, 1)

    elif direction == "EW":
        if current_phase == 2:
            return
        if current_phase in (0, 1):
            traci.trafficlight.setPhase(tls_id, 1)
        else:
            traci.trafficlight.setPhase(tls_id, 3)

    for _ in range(YELLOW_STEPS):
        traci.simulationStep()
        time.sleep(SIM_STEP_TIME)

        ns_count = edge_vehicle_count(NS_EDGES)
        ew_count = edge_vehicle_count(EW_EDGES)
        active_vehicle = select_highest_priority_vehicle()
        take_screenshot(ns_count, ew_count, active_vehicle)

    if direction == "NS":
        traci.trafficlight.setPhase(tls_id, 0)
    else:
        traci.trafficlight.setPhase(tls_id, 2)

def select_highest_priority_vehicle():
    selected_vehicle = None
    best_score = float("inf")
    best_distance = float("inf")
    best_priority = float("inf")

    for veh_id in traci.vehicle.getIDList():
        vtype = traci.vehicle.getTypeID(veh_id)
        if vtype not in EMERGENCY_VEHICLE_TYPES:
            continue

        edge = traci.vehicle.getRoadID(veh_id)
        if edge not in NS_EDGES + EW_EDGES:
            continue

        lane_id = traci.vehicle.getLaneID(veh_id)
        lane_pos = traci.vehicle.getLanePosition(veh_id)
        lane_length = traci.lane.getLength(lane_id)
        distance_to_junction = max(lane_length - lane_pos, 0)

        priority = EMERGENCY_VEHICLE_TYPES[vtype]
        score = distance_to_junction + (priority - 1) * EMERGENCY_PRIORITY_DISTANCE_MARGIN

        if score < best_score or (score == best_score and priority < best_priority) or (score == best_score and priority == best_priority and distance_to_junction < best_distance):
            best_score = score
            best_priority = priority
            best_distance = distance_to_junction
            selected_vehicle = veh_id

    return selected_vehicle

# ----------------- Ana Döngü -----------------
def main():
    traci.start(["sumo-gui", "-c", CONFIG, "--start"])
    tls_id = traci.trafficlight.getIDList()[0]

    sim_end = 200
    decision_every = 10
    threshold = 2
    emergency_mode = False

    global frame_counter
    frame_counter = 0

    for t_step in range(sim_end):
        traci.simulationStep()
        time.sleep(SIM_STEP_TIME)
        
        ns_count = edge_vehicle_count(NS_EDGES)
        ew_count = edge_vehicle_count(EW_EDGES)
        
        active_vehicle = select_highest_priority_vehicle()
        
        if active_vehicle:
            veh_type = traci.vehicle.getTypeID(active_vehicle)
            color = VEHICLE_VISUALS[veh_type][:4]
            shape = VEHICLE_VISUALS[veh_type][4]
            traci.vehicle.setColor(active_vehicle, color)
            traci.vehicle.setShapeClass(active_vehicle, shape)
            siren_on = activate_emergency_vehicle_siren(active_vehicle)

            lane_id = traci.vehicle.getLaneID(active_vehicle)
            lane_pos = traci.vehicle.getLanePosition(active_vehicle)
            lane_length = traci.lane.getLength(lane_id)
            distance_to_junction = max(lane_length - lane_pos, 0)

            if siren_on and is_emergency_siren_active(active_vehicle) and distance_to_junction <= AMBULANCE_DISTANCE:
                direction = get_vehicle_direction(active_vehicle)
                if direction:
                    safe_switch_to_green(tls_id, direction)
                    if not emergency_mode:
                        print(f"🚨 {active_vehicle} 150m içinde → Öncelik verildi")
                        emergency_mode = True
        
        if emergency_mode and not active_vehicle:
            print("✅ Acil araç geçti → NORMAL MOD")
            emergency_mode = False

        if t_step % decision_every == 0 and not emergency_mode:
            if ns_count > ew_count + threshold:
                safe_switch_to_green(tls_id, "NS")
            elif ew_count > ns_count + threshold:
                safe_switch_to_green(tls_id, "EW")
        
        take_screenshot(ns_count, ew_count, active_vehicle, max_count=20)

    traci.close()
    print(f"📁 Tüm ekran görüntüleri {SCREENSHOT_DIR} klasörüne kaydedildi.")
    create_video_with_overlay()

# ----------------- Video Oluştur -----------------
def create_video_with_overlay():
    print("🎬 Video oluşturuluyor...")
    img_files = sorted(glob.glob(f"{SCREENSHOT_DIR}/frame_*.png"))
    if not img_files:
        print("❌ PNG bulunamadı!")
        return
    
    frame = cv2.imread(img_files[0])
    height, width, _ = frame.shape
    out = cv2.VideoWriter("simulation_video_overlay_color.mp4",
                          cv2.VideoWriter_fourcc(*'mp4v'), 10, (width, height))
    
    for f in img_files:
        img = cv2.imread(f)
        out.write(img)
    out.release()
    print("✅ simulation_video_overlay_color.mp4 başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()