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

if not API_KEY:
    print("🚨 KRITIČNA NAPAKA: API ključ ni najden!")

@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    data = request.json
    lokacija = data.get('lokacija')
    druzba = data.get('druzba')
    proracun = data.get('proracun')
    trajanje = data.get('trajanje')
    mood = data.get('mood')

    trenutni_cas = datetime.now().strftime("%H:%M")
    trenutni_dan = datetime.now().strftime("%A")

   prompt = f"""
    Deluješ kot strokovni, realistični in ustvarjalni slovenski lokalni vodič. 
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
    1. PREVERJENA RESNIČNOST: Predlagaj SAMO dejansko obstoječe in odprte lokacije. NE ugibaj komercialnih zabavišč (kot so stari bowling centri), ki so morda zaprti. Izbiraj preverjene točke, a bodi izjemno lokalno specifičen.
    2. RAZNOLIKOST IN SPECIFIČNOST (KLJUČNO!): Vseh 3 predlogov mora biti med seboj popolnoma različnih. Nikoli ne ponudi treh enakih aktivnosti (npr. ne treh sprehodov ali treh restavracij). Kombiniraj! Ponudi npr. 1x specifično kavarno z znano sladico (Uporabi TOČNO ime lokala, npr. "Kavarna Zvezda", ne "neka kavarna"), 1x skrit lokalni kotiček v naravi in 1x kulturni ali urbani utrip.
    3. ČAS IN ODPIRALNOST: Upoštevaj, da je danes {trenutni_dan} in ura {trenutni_cas}. Če je večer/noč (po 20:00), predlagaj večerne sprehode, nočne razglede ali odprte pube/lokale, ki dejansko delajo pozno.
    4. LOGIKA ODDALJENOSTI: Če je čas "{trajanje}" kratek (npr. "Do 2 uri"), morajo biti lokacije v neposredni bližini kraja {lokacija} (maksimalno 15 minut stran).
    5. PRORAČUN: Če je izbran proračun "0€ (BREZPLAČNO)", so kavarne in restavracije strogo prepovedane. V tem primeru raznolikost dosezi drugače: 1x specifična gozdna pot/hrib, 1x zanimiva arhitektura/ulica in 1x klopca z najboljšim razgledom v tistem kraju.

    ZAHTEVAN FORMAT ODGOVORA (Vrni samo ta format, ničesar drugega):
    **1. Ime resnične lokacije/lokala, Kraj**
    Kratek opis (1-2 stavka o tem, zakaj je to super izbira in kaj točno naj tam počnejo ali poskusijo).
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **2. Ime resnične lokacije/lokala, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **3. Ime resnične lokacije/lokala, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        res = requests.post(url, headers=headers, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            print(f"Google API napaka: {res_data['error']}")
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
    app.run(host='0.0.0.0', port=5005, debug=True)
