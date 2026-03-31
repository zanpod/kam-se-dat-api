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
    try:
        data = request.json
        lokacija = data.get('lokacija', 'Slovenija')
        druzba = data.get('druzba', 'kdorkoli')
        proracun = data.get('proracun', 'zmerno')
        trajanje = data.get('trajanje', 'pol dneva')
        mood = data.get('mood', 'veselo')

        # Pridobimo trenutni čas in dan
        trenutni_cas = datetime.now().strftime("%H:%M")
        trenutni_dan = datetime.now().strftime("%A")

        # Optimiziran prompt za Gemini
        prompt = f"""
        Deluješ kot vrhunski slovenski lokalni vodič. Predlagaj natanko 3 REALNE lokacije.
        
        PARAMETRI:
        - Izhodišče: {lokacija}
        - Družba: {druzba}
        - Proračun: {proracun}
        - Čas: {trajanje}
        - Razpoloženje: {mood}
        - Trenutno: {trenutni_dan}, ob {trenutni_cas}

        PRAVILA:
        1. BREZ HALUCINACIJ. Samo resnični kraji v Sloveniji.
        2. Če je ura po 21:00, predlagaj le stvari, ki so takrat odprte ali dostopne (razgledi, bari, sprehodi).
        3. Če je proračun 0€, ne predlagaj ničesar s plačilom.
        4. Če je čas "Do 2 uri", naj bo lokacija max 20 min stran od {lokacija}.

        FORMAT ODGOVORA:
        **1. Ime lokacije, Kraj**
        Opis v enem ali dveh stavkih.
        [📍 Zemljevid](https://www.google.com/maps/search/?api=1&query=1)
        ---
        """

        # Google Gemini API klic (Uporabljamo 1.5 Flash model)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
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
        return jsonify({"error": "Napaka na strežniku."}), 500

if __name__ == '__main__':
    print("-----------------------------------------")
    print("STREŽNIK TEČE NA: http://127.0.0.1:5005")
    print("-----------------------------------------")
    app.run(host='127.0.0.1', port=5005, debug=True)
