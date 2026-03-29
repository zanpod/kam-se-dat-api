import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# 1. Naložimo nastavitve iz .env datoteke
load_dotenv()

app = Flask(__name__)
CORS(app)

# 2. Varno preberemo ključ iz .env datoteke
API_KEY = os.getenv("GEMINI_API_KEY")

# Varnostno preverjanje, da takoj veš, če .env ne deluje
if not API_KEY:
    print("🚨 KRITIČNA NAPAKA: API ključ ni najden! Preveri, če imaš datoteko .env in v njej GEMINI_API_KEY=...")

@app.route('/generiraj', methods=['POST'])
def generiraj():
    try:
        podatki = request.json
        mood = podatki.get('mood', 'aktivno')
        lokacija = podatki.get('lokacija', 'Neznana lokacija')
        druzba = podatki.get('druzba', 'SAM')
        proracun = podatki.get('proracun', 'ZMERNO')
        trajanje = podatki.get('trajanje', 'CEL DAN')
        
        # UPORABLJAMO ZMAGOVALNI MODEL, ki ga tvoj ključ dejansko podpira
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"""
        Uporabnik je na lokaciji {lokacija}.
        Uporabnik se počuti {mood}.
        Uporabnik gre na aktivnost s to družbo: {druzba}.
        Proračun za aktivnost: {proracun}.
        Razpoložljiv čas: {trajanje}.

        Na podlagi teh podrobnosti predlagaj 3 specifične in zabavne aktivnosti v Sloveniji (najbolje v bližini uporabnikove lokacije), ki bi mu ustrezale.
        Odgovori v slovenščini, bodi kratek in uporabi alineje.
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        res = requests.post(url, headers=headers, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            print(f"Google API napaka: {res_data['error']}")
            return jsonify({"error": res_data['error']['message']}), 500

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