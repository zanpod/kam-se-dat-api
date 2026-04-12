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

        # Osnovni podatki iz frontenda
        surova_lokacija = data.get('lokacija', 'Slovenija')
        lokacija = surova_lokacija.strip().capitalize()
        
        druzba = data.get('druzba', 'S prijatelji')
        proracun = data.get('proracun', 'Zmerno')
        trajanje = data.get('trajanje', 'Do 2 uri')
        mood = data.get('mood', 'Vesel')
        ze_predlagano = data.get('zePredlagano', [])

        trenutni_cas = datetime.now().strftime("%H:%M")

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

        # ====================== MOČAN PROMPT ======================
        if "2" in str(trajanje):
            logika_izleta = "Predlagaj hitre in sproščene aktivnosti (kava, kratek sprehod, razgledna točka)."
        else:
            logika_izleta = "Predlagaj VSEBINSKO BOGATE izlete. To pomeni kombinacijo dveh stvari (npr. pohod + ogled gradu, obisk jezera + muzej)."

        prompt = f"""
        Deluješ kot vrhunski slovenski lokalni insider 'Kam se dat!?'. 
        Tvoj cilj je navdušiti uporabnika z 100% REALNIMI lokacijami.

        PODATKI:
        - Lokacija: {lokacija}
        - Trajanje: {trajanje} ({logika_izleta})
        - Družba: {druzba}, Proračun: {proracun}, Mood: {mood}
        - Že predlagano: {ze_predlagano}

        STROGA PRAVILA ZA PREPREČEVANJE HALUCINACIJ:
        1. NE IZMIŠLJUJ SI IMEN ZASEBNIH LOKALOV ALI RESTAVRACIJ! Če za določeno mesto (npr. Slovenske Konjice) ne poznaš 100% točnega in obstoječega lokala, predlagaj JAVNE ZNAMENITOSTI (grad, park, jezero, cerkev, hrib) ali pa uporabi splošen izraz (npr. "lokalna kavarna na trgu").
        2. Imena znamenitosti morajo biti resnična.
        3. NE piši uvodov. Odgovor začni neposredno s številko {zacetna_stevilka}.
        4. Vsaka točka MORA imeti povezavo: [📍 Prikaži na zemljevidu](https://maps.google.com/maps?q=Ime+Lokacije,+Kraj)

        FORMAT IZPISA:
        **[Številka]. Ime lokacije, Kraj**
        Opis (vsaj 3 sočni stavki o tem, zakaj se splača iti tja)...
        [📍 Prikaži na zemljevidu](...)
        ---
        """

        # ====================== GEMINI API KLIC ======================
        if not API_KEY:
            return jsonify({"error": "Manjka API ključ."}), 500

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
        
        # TUKAJ JE KLJUČNA SPREMEMBA: Dodali smo "generationConfig" s temperaturo 0.15
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.15,
                "topK": 32,
                "topP": 0.8
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
