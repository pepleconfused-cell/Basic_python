import socket
import os
import platform
import time
import sys
from concurrent.futures import ThreadPoolExecutor

def dapatkan_base_ip():
    """Mencari 3 segmen awal dari IP Wi-Fi lokal perangkat dengan aman"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_asli = s.getsockname()[0]
        segmen = ip_asli.split('.')
        base_ip = f"{segmen[0]}.{segmen[1]}.{segmen[2]}."
        return base_ip, ip_asli
    except Exception:
        return None, None
    finally:
        s.close()

def ping_perangkat(ip_target):
    """Mengirim paket Ping sistem untuk mendeteksi keaktifan perangkat"""
    param = "-w 1 -c 1" if platform.system().lower() != "windows" else "-w 1000 -n 1"
    perintah = f"ping {param} {ip_target} > /dev/null 2>&1"
    status_respon = os.system(perintah)
    if status_respon == 0:
        return ip_target
    return None

def pindai_jaringan(base_ip):
    """Memindai seluruh subnet secara paralel menggunakan multi-threading"""
    daftar_ip = [f"{base_ip}{i}" for i in range(1, 255)]
    perangkat_aktif = set()
    
    with ThreadPoolExecutor(max_workers=80) as executor:
        hasil_ping = executor.map(ping_perangkat, daftar_ip)
        for ip in hasil_ping:
            if ip:
                perangkat_aktif.add(ip)
    return perangkat_aktif

def mulai_sistem_alert():
    print("=" * 60)
    print("=== SISTEM MONITORING & PERINGATAN PENGGUNA WI-FI ===")
    print("=" * 60)
    
    base_ip, ip_saya = dapatkan_base_ip()
    
    if not base_ip:
        print("[Gagal] Pastikan HP Anda sudah terhubung ke Wi-Fi!")
        return
        
    if base_ip.startswith("10."):
        print(f"IP Anda: {ip_saya}")
        print("[Peringatan] Anda menggunakan Kuota Seluler. Fitur ini wajib menggunakan Wi-Fi.")
        return

    print(f"IP HP Anda         : {ip_saya}")
    print(f"Subnet Wi-Fi       : {base_ip}1 s/d {base_ip}254")
    print("Membuat basis data pengguna awal, mohon tunggu...\n")
    
    # Pemindaian pertama untuk mencatat daftar perangkat tepercaya awal (baseline)
    perangkat_lama = pindai_jaringan(base_ip)
    
    print("-" * 60)
    print(f"Basis Data Siap! Terdeteksi awal: {len(perangkat_lama)} perangkat aktif.")
    print("Sistem sekarang siaga memantau jaringan tanpa henti...")
    print("Tekan tombol STOP (kotak merah) di Pydroid 3 untuk berhenti.")
    print("-" * 60 + "\n")

    waktu_mulai_program = time.time()
    counter_pindah_detik = 0

    try:
        while True:
            # Siklus pemindaian ulang berkala dilakukan setiap ~15 detik agar tidak membebani jaringan
            if counter_pindah_detik >= 150:  # 150 * 0.1 detik jeda sleep = 15 detik
                perangkat_baru = pindai_jaringan(base_ip)
                
                # 1. Mendeteksi Perangkat Asing Baru yang Masuk (Ada di daftar baru, tapi tidak di daftar lama)
                terdeteksi_masuk = perangkat_baru - perangkat_lama
                for ip in terdeteksi_masuk:
                    waktu_log = time.strftime("%H:%M:%S")
                    print(f"⚠️  [{waktu_log}] [PERINGATAN MASUK] Perangkat asing terhubung! IP: {ip}")
                
                # 2. Mendeteksi Perangkat yang Memutus Koneksi (Ada di daftar lama, tapi hilang di daftar baru)
                terdeteksi_keluar = perangkat_lama - perangkat_baru
                for ip in terdeteksi_keluar:
                    waktu_log = time.strftime("%H:%M:%S")
                    status_ket = "Router Utama" if ip.endswith(".1") else "Pengguna Wi-Fi"
                    print(f"ℹ️  [{waktu_log}] [KONEKSI TERPUTUS] {status_ket} keluar/mati! IP: {ip}")
                
                # Perbarui basis data untuk siklus pemindaian berikutnya
                perangkat_lama = perangkat_baru
                counter_pindah_detik = 0
            
            # 3. Fitur Stopwatch Loop yang Terus Berjalan Setiap Detik Tanpa Henti
            waktu_berjalan = time.time() - waktu_mulai_program
            sys.stdout.write(
                f"\r[SISTEM SIAGA] Waktu Berjalan: {waktu_berjalan:.2f}s | Memantau {len(perangkat_lama)} Pengguna... "
            )
            sys.stdout.flush()
            
            time.sleep(0.1)
            counter_pindah_detik += 1
            
    except KeyboardInterrupt:
        print("\n\n[Selesai] Sistem monitoring dihentikan.")

if __name__ == "__main__":
    mulai_sistem_alert()
