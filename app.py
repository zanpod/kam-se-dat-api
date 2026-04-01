import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("🚨 KRITIČNA NAPAKA: API ključ ni najden!")

@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    data = request.json
    lokacija = data.get('lokacija', 'Slovenija')
    druzba = data.get('druzba', 'neznano')
    proracun = data.get('proracun', 'zmerno')
    trajanje = data.get('trajanje', 'pol dneva')
    mood = data.get('mood', 'nevtralno')

    trenutni_cas = datetime.now().strftime("%H:%M")
    trenutni_dan = datetime.now().strftime("%A")

    prompt = f"""
    Deluješ kot strokovni slovenski lokalni vodič. 
    Predlagaj natanko 3 resnične, obstoječe ideje za izlet ali aktivnost.

    PODATKI UPORABNIKA:
    - Izhodiščni kraj: {lokacija}
    - Družba: {druzba}
    - Proračun: {proracun}
    - Čas na voljo: {trajanje}
    - Želeno razpoloženje: {mood}
    
    TRENUTNO STANJE:
    - Trenutni dan: {trenutni_dan}
    - Trenutna ura: {trenutni_cas}

    STROGA PRAVILA:
    1. PREVERJENA RESNIČNOST: Predlagaj SAMO dejansko obstoječe lokacije v Sloveniji.
    2. ČAS IN ODPIRALNOST: Upoštevaj trenutni dan in uro. Če je večer/noč, predlagaj le odprte ali zunanje lokacije primerne za noč.
    3. ODDALJENOST: Če je čas kratki, predlagaj lokacije blizu izhodišča.
    4. PRORAČUN: Če je izbrano '0€', so plačljive vstopnine strogo prepovedane.

    ZAHTEVAN FORMAT ODGOVORA (Vrni samo to, ničesar drugega):
    **1. Ime resnične lokacije, Kraj**
    Kratek opis (1-2 stavka).
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query={lokacija})
    ---
    """

    try:
        # TUKAJ JE NASTAVLJEN GEMINI 2.5 FLASH
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        res = requests.post(url, headers=headers, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            return jsonify({"error": res_data['error'].get('message', 'API napaka')}), 500

        if res_data and 'candidates' in res_data:
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
    app.run(host='0.0.0.0', port=5005, debug=True)
