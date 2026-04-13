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

# ====================== API FUNKCIJE AGENTA ======================
def pridobi_trenutno_vreme(lokacija):
    """Kliče zunanje brezplačne API-je za pridobitev vremena v realnem času."""
    try:
        # 1. Geocoding API (Pridobi koordinate mesta)
        geo_url = f"https://nominatim.openstreetmap.org/search?q={lokacija},+Slovenija&format=json&limit=1"
        headers = {'User-Agent': 'KamSeDatAgent/1.0'}
        geo_res = requests.get(geo_url, headers=headers, timeout=3).json()
        
        if not geo_res:
            return "Neznano"
            
        lat = geo_res[0]['lat']
        lon = geo_res[0]['lon']
        
        # 2. Vremenski API (Open-Meteo)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_res = requests.get(weather_url, timeout=3).json()
        
        if 'current_weather' in w_res:
            temp = w_res['current_weather']['temperature']
            w_code = w_res['current_weather']['weathercode']
            
            # WMO interpretacija vremenskih kod
            opis = "Jasno ali delno oblačno ⛅"
            if w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: opis = "Dežuje 🌧️"
            elif w_code in [71, 73, 75, 85, 86]: opis = "Sneži ❄️"
            elif w_code in [95, 96, 99]: opis = "Nevihta ⛈️"
            elif w_code in [45, 48]: opis = "Megla 🌫️"
            
            return f"{temp}°C, {opis}"
    except Exception as e:
        print(f"⚠️ Napaka pri vremenskem API-ju: {e}")
    
    return "Podatek ni na voljo"

# ====================== GLAVNA POT ======================
@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    try:
        data = request.json or {}
        
        # Osnovni podatki iz frontenda
        surova_lokacija = data.get('lokacija', 'Slovenija')
        lokacija = surova_lokacija.strip().capitalize()
        
        druzba = data.get('druzba', 'S prijatelji')
        proracun = data.get('proracun', 'Zmerno')
        trajanje = data.get('trajanje', 'Do 2 uri')
        mood = data.get('mood', 'Vesel')
        ze_predlagano = data.get('zePredlagano', [])
        
        trenutni_cas = datetime.now().strftime("%H:%M")
        
        # AGENT KLICE ZUNANJE API-je PREDEN RAZMISLI:
        trenutno_vreme = pridobi_trenutno_vreme(lokacija)

        # ====================== PAMETNA SPONZOR LOGIKA ======================
        sponzorski_tekst = ""
        stevilo_ai_idej = 3
        zacetna_stevilka = 1
        dovoljen_cas_za_sponzorja = "2" in str(trajanje)
        
        if proracun != "0€ (BREZPLAČNO)" and dovoljen_cas_za_sponzorja and supabase:
            try:
                res = supabase.table('sponzorji').select('*').eq('lokacija', lokacija).eq('aktiven', True).execute()
                
                if res.data and len(res.data) > 0:
                    dostopni_sponzorji = [s for s in res.data if s['ime'] not in ze_predlagano]
                    
                    if dostopni_sponzorji:
                        sponzor = random.choice(dostopni_sponzorji)
                        naslov_za_maps = sponzor.get('naslov', lokacija)
                        maps_q = f"{sponzor['ime']}, {naslov_za_maps}".replace(" ", "+")
                        opis = sponzor.get('opis', "Odlična lokalna izbira!")
                        
                        sponzorski_tekst = f"**1. {sponzor['ime']}, {lokacija}**\n{opis}\n[📍 Prikaži na zemljevidu](https://maps.google.com/maps?q={maps_q})\n---\n"
                        
                        stevilo_ai_idej = 2
                        zacetna_stevilka = 2
                        print(f"✅ Sponzor '{sponzor['ime']}' izbran za kratek izlet.")
            except Exception as e:
                print(f"🚨 Napaka pri branju sponzorjev: {e}")

        # ====================== AGENT PROMPT ======================
        if "2" in str(trajanje):
            logika_izleta = "Predlagaj hitre in sproščene aktivnosti (npr. preverjena kavarna, slaščičarna, kratek sprehod, razgledna točka)."
        else:
            logika_izleta = "Predlagaj VSEBINSKO BOGATE izlete. To pomeni kombinacijo dveh stvari (npr. pohod + preverjena restavracija, obisk narave ali muzeja + dobra kava)."

        prompt = f"""
        Deluješ kot vrhunski slovenski lokalni AI AGENT 'Kam se dat!?'. Tvoja supermoč je iskanje po spletu in analiziranje zunanjih API-jev.
        Tvoj cilj je navdušiti uporabnika z 100% REALNIMI, PREVERJENIMI lokacijami.

        TRENUTNI PODATKI V ŽIVO:
        - Lokacija: {lokacija}
        - Vreme na tej lokaciji: {trenutno_vreme} 
        - Ura: {trenutni_cas}
        - Trajanje: {trajanje} ({logika_izleta})
        - Družba: {druzba}, Proračun: {proracun}, Mood: {mood}
        - Že predlagano: {ze_predlagano}

        PRAVILA AGENTA ZA PREPREČEVANJE HALUCINACIJ IN UPORABO PODATKOV:
        1. VREMENSKA LOGIKA: Upoštevaj vreme v živo! Če piše, da 'Dežuje' ali 'Sneži' ali so zelo nizke temperature, OBVEZNO predlagaj izključno NOTRANJE AKTIVNOSTI (muzeji, preverjene kavarne, gradovi, toplice). Če je 'Jasno', pošlji ljudi v naravo!
        2. PREVERJANJE LOKALOV IN RESTAVRACIJ: Lahko predlagaš kavarne, restavracije in bare, VENDAR si imen NE SMEŠ izmišljevati! Predlagaš lahko SAMO tiste, ki si jih dejansko preveril prek iskalnika in 100% obstajajo v tem kraju na Google Zemljevidih.
        3. UPORABI GOOGLE SEARCH: Preveri obstoj vsake znamenitosti in lokala, ki ga želiš predlagati. Če Google Search ne najde jasne potrditve (ocen, naslova), te lokacije NE SMEŠ predlagati!
        4. NE IZMIŠLJUJ SI IMEN! Imena morajo biti točna. Če za kraj nimaš preverjenih lokalov, raje predlagaj samo znane javne naravne in kulturne znamenitosti v bližini.
        5. NE piši uvodov in zaključkov. Odgovor začni neposredno s številko {zacetna_stevilka}.
        6. Vsaka točka MORA imeti povezavo: [📍 Prikaži na zemljevidu](https://maps.google.com/maps?q=Ime+Lokacije,+Kraj)

        FORMAT IZPISA (točno {stevilo_ai_idej} ideji):
        **[{zacetna_stevilka}]. Ime lokacije, Kraj**
        Opis (vsaj 3 sočni stavki o tem, zakaj se splača iti tja. Podatki morajo biti resnični in preverjeni na spletu!)...
        [📍 Prikaži na zemljevidu](...)
        ---
        """

        # ====================== GEMINI API KLIC Z AGENTOM (Search Grounding) ======================
        if not API_KEY:
            return jsonify({"error": "Manjka API ključ."}), 500

        # Model Gemini 2.5 Flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}], # Vklopi agenta za iskanje po Googlu
            "generationConfig": {
                "temperature": 0.1,      # Nizka temperatura za fokus na dejstva
                "topK": 1,
                "topP": 0.1
            }
        }
        
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
        res_data = res.json()

        if 'error' in res_data:
            return jsonify({"error": res_data['error'].get('message', 'API Error')}), 500

        ai_odgovor = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        koncni_odgovor = sponzorski_tekst + ai_odgovor

        return jsonify({"odgovor": koncni_odgovor.strip()})

    except Exception as e:
        print(f"❌ KRITIČNA NAPAKA: {str(e)}")
        return jsonify({"error": "Napaka na strežniku."}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port)
