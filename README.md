# SUMO Traffic Project

Bu proje, SUMO tabanlı trafik simülasyonu ile farklı trafik kontrol stratejilerini karşılaştırmak için hazırlanmıştır.

## İçerik

- `run_fixed.py`: Sabit fazlı trafik ışığı kontrolü.
- `run_smart.py`: Yoğunluğa göre basit akıllı kontrol.
- `run_emergency.py`: Acil durum aracı önceliği ve görselleştirme.
- `run_cv_sim.py`: Bilgisayarlı görü simülasyonu ve acil araç tespiti loglama.
- `run_adaptive.py`, `run_adaptive2.py`: Daha karmaşık uyarlanabilir faz kontrolü.
- `run_greenwave.py`: Yeşil dalga (green wave) senaryosu.
- `find_route.py`: `sumolib` kullanarak en kısa yol bulma.
- `analyze_results.py`: Senaryo sonuçlarını grafiklere dönüştürme.
- `analyze_cv_log.py`: `cv_log.csv` dosyasını analiz etmek için araç.
- `save_results.py`: Örnek sonuçları `simulation_results.csv` olarak kaydeder.

## Gereksinimler

Python ortamı için:

```bash
pip install -r requirements.txt
```

Ayrıca SUMO yüklü olmalıdır. Windows için `sumo` ve `sumo-gui` komutlarının PATH üzerinde erişilebilir olması gerekir.

## Çalıştırma

### Sabit strateji

```bash
python run_fixed.py
```

### Akıllı strateji

```bash
python run_smart.py
```

### Emergency ve CV simülasyonu

```bash
python run_cv_sim.py
```

### Emergency görselleştirmesi

```bash
python run_emergency.py
```

### Yeşil dalga (green wave)

```bash
python run_greenwave.py
```

### Uyarlanabilir stratejiler

```bash
python run_adaptive.py
python run_adaptive2.py
```

### Sonuç analizi

```bash
python analyze_results.py
```

### CV log analizi

```bash
python analyze_cv_log.py
```

### CSV kaydetme

```bash
python save_results.py
```

## Notlar

- `traffic.sumocfg` ve `traffic_multi.sumocfg` konfigurasyonları farklı ağlar için kullanılır.
- `run_cv_sim.py` ve `run_greenwave.py` `sumo-gui` gerektirebilir.
- `cv_log.csv`, `simulation_results.csv`, grafikler ve `screenshots/` çıktı dosyaları çalıştırma sırasında otomatik olarak oluşturulur.
