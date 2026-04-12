import os
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Varen uvoz Supabase
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

# ====================== INIT IN KLJUČI ======================
load_dotenv()

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# ====================== SUPABASE INIT ======================
supabase = None
if SUPABASE_URL and SUPABASE_KEY and create_client:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Baza uspešno povezana!")
    except Exception as e:
        print(f"❌ Napaka pri bazi: {e}")

# ====================== GLAVNA POT ======================
@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    try:
        data = request.json or {}

        # Očistimo vhodne podatke
        surova_lokacija = data.get('lokacija', 'Slovenija')
        lokacija = surova_lokacija.strip().capitalize()
        
        druzba = data.get('druzba', 'S prijatelji')
        proracun = data.get('proracun', 'Zmerno')
        mood = data.get('mood', 'Vesel')
        ze_predlagano = data.get('zePredlagano', [])

        trenutni_cas = datetime.now().strftime("%H:%M")

        # ====================== SPONZOR LOGIKA ======================
        sponzorski_tekst = ""
        stevilo_ai_idej = 3
        zacetna_stevilka = 1 

        if proracun != "0€ (BREZPLAČNO)" and supabase:
            try:
                # Pridobimo vse aktivne sponzorje za to lokacijo
                res = supabase.table('sponzorji').select('*').eq('lokacija', lokacija).eq('aktiven', True).execute()
                
                if res.data and len(res.data) > 0:
                    # Izberemo tiste, ki še niso bili predlagani v tej seji
                    dostopni_sponzorji = [s for s in res.data if s['ime'] not in ze_predlagano]
                    
                    if dostopni_sponzorji:
                        # Naključna izbira med sponzorji v mestu
                        sponzor = random.choice(dostopni_sponzorji)
                        
                        # Uporabimo točen naslov za Maps, če obstaja, sicer mesto
                        naslov_za_maps = sponzor.get('naslov', lokacija)
                        maps_q = f"{sponzor['ime']}, {naslov_za_maps}".replace(" ", "+")
                        
                        opis = sponzor.get('opis', "Odlična lokalna izbira!")
                        
                        sponzorski_tekst = f"**1. {sponzor['ime']}, {lokacija}**\n{opis}\n[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query={maps_q})\n---\n"
                        
                        stevilo_ai_idej = 2
                        zacetna_stevilka = 2 
                        print(f"✅ Sponzor dodan: {sponzor['ime']} ({naslov_za_maps})")
            except Exception as e:
                print(f"🚨 Napaka pri branju sponzorjev: {e}")

        # ====================== PROMPT FORMAT ======================
        if zacetna_stevilka == 2:
            format_navodila = f"""**2. Ime lokacije, Kraj**
Opis v vsaj treh stavkih...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+lokacije)
---
**3. Ime lokacije, Kraj**
Opis v vsaj treh stavkih...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+lokacije)"""
        else:
            format_navodila = f"""**1. Ime lokacije, Kraj**
Opis v vsaj treh stavkih...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+lokacije)
---
**2. Ime lokacije, Kraj**
Opis v vsaj treh stavkih...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+lokacije)
---
**3. Ime lokacije, Kraj**
Opis v vsaj treh stavkih...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+lokacije)"""

        prompt = f"""
        Deluješ kot slovenski lokalni insider. Predlagaj natanko {stevilo_ai_idej} ideje za izlet.
        Lokacija: {lokacija}, Družba: {druzba}, Proračun: {proracun}, Mood: {mood}, Ura: {trenutni_cas}.
        Ne ponavljaj teh lokacij: {ze_predlagano}.

        STROGA PRAVILA:
        1. NE piši uvodnih pozdravov (npr. "Tukaj so predlogi...").
        2. NE piši zaključnih stavkov.
        3. Odgovor naj bo IZKLJUČNO v spodnjem formatu (številčenje naj se začne s {zacetna_stevilka}):

        {format_navodila}
        """

        # ====================== AI KLIC ======================
        if not API_KEY:
            return jsonify({"error": "Manjka API ključ."}), 500

        # Nastavljeno na Gemini 2.5 Flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_data = res.json()

        if 'error' in res_data:
            error_msg = res_data['error'].get('message', 'Neznana napaka')
            return jsonify({"error": error_msg}), 500

        ai_odgovor = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        koncni_odgovor = sponzorski_tekst + ai_odgovor

        return jsonify({"odgovor": koncni_odgovor.strip()})

    except Exception as e:
        print(f"❌ KRITIČNA NAPAKA: {str(e)}")
        return jsonify({"error": "Napaka na strežniku."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port)
