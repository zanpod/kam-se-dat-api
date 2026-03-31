import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# 1. Naložimo nastavitve iz .env datoteke
load_dotenv()

app = Flask(__name__)
CORS(app)

# 2. Varno preberemo ključ iz .env datoteke
API_KEY = os.environ.get("GEMINI_API_KEY")

# Varnostno preverjanje, da takoj veš, če .env ne deluje
if not API_KEY:
    print("🚨 KRITIČNA NAPAKA: API ključ ni najden! Preveri, če imaš datoteko .env in v njej GEMINI_API_KEY=...")

@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    data = request.json
    lokacija = data.get('lokacija')
    druzba = data.get('druzba')
    proracun = data.get('proracun')
    trajanje = data.get('trajanje')
    mood = data.get('mood')

    # Pridobimo trenutni čas in dan (da AI ne pošilja v zaprte gostilne)
    trenutni_cas = datetime.now().strftime("%H:%M")
    trenutni_dan = datetime.now().strftime("%A")

    # POPRAVLJEN IN OPTIMIZIRAN PROMPT
    prompt = f"""
    Deluješ kot strokovni, realistični slovenski lokalni vodič. 
    Tvoja edina naloga je predlagati natanko 3 resnične, obstoječe ideje za izlet ali aktivnost na podlagi spodnjih parametrov. Ne piši uvodnih ali zaključnih pozdravov.

    PODATKI UPORABNIKA:
    - Izhodiščni kraj: {lokacija}
    - Družba: {druzba}
    - Proračun: {proracun}
    - Čas na voljo: {trajanje}
    - Želeno razpoloženje: {mood}
    
    TRENUTNO STANJE (ZELO POMEMBNO):
    - Trenutni dan: {trenutni_dan}
    - Trenutna ura: {trenutni_cas}

    STROGA PRAVILA (Upoštevaj jih brez izjem!):
    1. PREVERJENA RESNIČNOST: Predlagaj SAMO dejansko obstoječe, znane lokacije, restavracije, parke ali znamenitosti v Sloveniji. PREPOVEDANO je izmišljevanje imen. Če ne poznaš specifičnega lokala v izbranem kraju, predlagaj najbolj znano naravno znamenitost ali javen trg v tem kraju.
    2. ČAS IN ODPIRALNOST: Upoštevaj, da je danes {trenutni_dan} in ura {trenutni_cas}. Če je večer/noč (po 20:00), NE predlagaj muzejev, zaprtih parkov, gozdov ali jutranjih kavarn. Predlagaj izključno nočne aktivnosti, odprte bare ali varno dostopne večerne razglede.
    3. LOGIKA ODDALJENOSTI: Če je čas "{trajanje}" kratek (npr. "Do 2 uri"), morajo biti lokacije v neposredni bližini kraja {lokacija} (maksimalno 15 minut stran).
    4. PRORAČUN: Če je izbran proračun "0€ (BREZPLAČNO)", so restavracije, lokali s pijačo in plačljive vstopnine strogo prepovedani. Predlagaj samo brezplačno naravo, javne sprehajalne poti ali razgledne točke.

    ZAHTEVAN FORMAT ODGOVORA (Vrni samo ta format, ničesar drugega):
    **1. Ime resnične lokacije, Kraj**
    Kratek opis (1-2 stavka o tem, zakaj je lokacija super izbira glede na družbo in počutje).
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **2. Ime resnične lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **3. Ime resnične lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    """

    try:
        # Pripravimo URL in GLAVE za Google API klic
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        res = requests.post(url, headers=headers, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            print(f"Google API napaka: {res_data['error']}")
            # Varno preberemo sporočilo napake, če obstaja
            error_msg = res_data['error'].get('message', 'Neznana API napaka')
            return jsonify({"error": error_msg}), 500

        if res_data and 'candidates' in res_data and len(res_data['candidates']) > 0:
            odgovor_ai = res_data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"odgovor": odgovor_ai})
        else:
            return jsonify({"error": "AI ni vrnil odgovora."}), 500

    except Exception as e:
        print(f"Sistemska napaka: {str(e)}")
        return jsonify({"error": "Nekaj je šlo narobe na strežniku."}), 500

if __name__ == '__main__':
    print("-----------------------------------------")
    print("STREŽNIK TEČE NA: http://127.0.0.1:5005")
    print("-----------------------------------------")
    app.run(host='127.0.0.1', port=5005, debug=True)
