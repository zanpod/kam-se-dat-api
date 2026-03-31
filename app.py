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

    # ---- OD TUKAJ NAPREJ PRILEPIŠ NOVO KODO ----
    # Pridobimo trenutni čas in dan (da AI ne pošilja v zaprte gostilne)
    trenutni_cas = datetime.now().strftime("%H:%M")
    trenutni_dan = datetime.now().strftime("%A")

    prompt = f"""
    Deluješ kot vrhunski, realistični slovenski lokalni vodič. 
    Uporabnik išče idejo za aktivnost. Strogo upoštevaj spodnje parametre in trenutni čas!

    PODATKI UPORABNIKA:
    - Izhodiščni kraj: {lokacija}
    - Družba: {druzba}
    - Proračun: {proracun}
    - Čas na voljo: {trajanje}
    - Želeno razpoloženje: {mood}
    
    TRENUTNO STANJE (ZELO POMEMBNO):
    - Trenutni dan: {trenutni_dan}
    - Trenutna ura: {trenutni_cas}

    STROGA PRAVILA ZA GENERIRANJE (Če jih prekršiš, bo aplikacija neuporabna):
    1. BREZ HALUCINACIJ: Predlagaj SAMO 3 resnične, obstoječe lokacije v Sloveniji. Ne izmišljuj si imen lokalov ali naravnih znamenitosti. Če nisi 100% prepričan, predlagaj splošno znano točko.
    2. LOKACIJSKA LOGIKA ('{trajanje}'):
       - Če je čas "Do 2 uri", predlagaj lokacije, ki so od izhodišča oddaljene MAX 15-20 minut.
       - Če je čas "Pol dneva" ali več, lahko predlagaš zanimivosti v širši regiji (do 1 ure vožnje).
    3. URNIK IN ODPIRALNI ČASI:
       - Poglej "Trenutno uro". Če je ura zvečer ali ponoči (npr. po 21:00), NE predlagaj muzejev, parkov, ki se zaklepajo, ali dnevnih kavarn. Predlagaj večerne aktivnosti (bare, nočne sprehode, odprte razglede).
       - Zjutraj predlagaj kavo, zajtrk, jutranje pohode.
    4. PRORAČUN ('{proracun}'): Če je 0€, strogo prepovedano predlagati restavracije, vstopnine ali plačljiva parkirišča.

    FORMAT ODGOVORA (za vsako izmed 3 točk):
    **Ime realne lokacije**
    Kratek in jedrnat opis (povej, zakaj je to primerno glede na družbo in čas).
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query={{ime_lokacije_in_kraj}})
    ---
    """
    # ---- TUKAJ SE NOVA KODA KONČA ----

    # Spodaj ostane tvoja stara koda, ki pošlje zahtevek na Google:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    # ... itd ...

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
