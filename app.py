import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Naložimo nastavitve iz .env datoteke
load_dotenv()

app = Flask(__name__)
CORS(app)

# 2. Varno preberemo ključe iz .env datoteke (ali Render okolja)
API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    print("🚨 KRITIČNA NAPAKA: Manjkajo API ključi ali Supabase podatki!")

# 3. Inicializacija Supabase baze
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"🚨 Napaka pri inicializaciji Supabase: {e}")

@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    data = request.json
    lokacija = data.get('lokacija')
    druzba = data.get('druzba')
    proracun = data.get('proracun')
    trajanje = data.get('trajanje')
    mood = data.get('mood')
    ze_predlagano = data.get('zePredlagano', [])

    trenutni_cas = datetime.now().strftime("%H:%M")
    trenutni_dan = datetime.now().strftime("%A")

    zgodovina_navodilo = ""
    if ze_predlagano and len(ze_predlagano) > 0:
        zgodovina_navodilo = f"\nOPOZORILO: Ne ponujaj teh lokacij, ker so že bile predlagane: {', '.join(ze_predlagano)}.\n"

    # ==========================================
    # "NUKLEARNA OPCIJA" - PRISILNO LEPLJENJE OGLASA
    # ==========================================
    sponzorski_tekst_za_vrh = ""
    stevilo_ai_idej = 3
    
    # Privzet format, če NI sponzorja
    format_odgovora = """
    **1. Ime točno določene lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **2. Ime točno določene lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **3. Ime točno določene lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    """

    print(f"--- DEBUG: Začenjam preverjanje baze ---")
    print(f"--- DEBUG: Izbrani proračun je: '{proracun}' ---")
    print(f"--- DEBUG: Iskana lokacija je: '{lokacija}' ---")

    if proracun != "0€ (BREZPLAČNO)":
        try:
            odgovor_baze = supabase.table('sponzorji').select('*').eq('lokacija', lokacija).eq('aktiven', True).execute()
            podatki = odgovor_baze.data
            print(f"--- DEBUG: Baza je vrnila podatke: {podatki} ---")

            if podatki and len(podatki) > 0:
                sponzor = podatki[0] 
                print(f"--- DEBUG: Našli smo sponzorja: {sponzor['ime']} ---")
                
                if sponzor['ime'] not in ze_predlagano:
                    print("--- DEBUG: VSE JE OK! Sponzor se bo prilepil na vrh! ---")
                    
                    # 1. PYTHON SAM ZGRADI KARTICO ZA SPONZORJA
                    opis_stranke = sponzor.get('opis', f"Odlična lokalna izbira in preverjeno najboljša izkušnja za vaš izlet!")
                    sponzorski_tekst_za_vrh = f"**1. {sponzor['ime']}, {lokacija}**\n{opis_stranke}\n[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)\n---\n"
                    
                    # 2. SPREMENIMO PRAVILA ZA AI - Zgenerira naj samo točko 2 in 3
                    stevilo_ai_idej = 2
                    format_odgovora = """
    **2. Ime točno določene lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    ---
    **3. Ime točno določene lokacije, Kraj**
    Kratek opis...
    [📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
    """
                else:
                    print("--- DEBUG: Sponzor blokiran, ker je že v zgodovini! ---")
            else:
                print("--- DEBUG: Baza prazna ali sponzor ni aktiven! ---")
        except Exception as e:
            print(f"--- DEBUG NAPAKA PRI BAZI: {e} ---")
    else:
        print("--- DEBUG: Preskakujem bazo zaradi 0€ proračuna! ---")

    # ==========================================
    # PROMPT ZA UMETNO INTELIGENCO
    # ==========================================
    prompt = f"""
    Deluješ kot vrhunski slovenski 'lokalni insider'. 
    Tvoja naloga je predlagati natanko {stevilo_ai_idej} resnične, obstoječe ideje za izlet na podlagi spodnjih parametrov. Ne piši uvodnih ali zaključnih pozdravov.

    PODATKI UPORABNIKA:
    - Izhodiščni kraj: {lokacija}
    - Družba: {druzba}
    - Proračun: {proracun}
    - Želeno razpoloženje: {mood}
    {zgodovina_navodilo}

    STROGA PRAVILA:
    1. ABSOLUTNA RAZNOLIKOST: Predlogi si morajo biti različni (npr. ena narava/aktivnost, eno kulturno/urbano doživetje).
    2. SPECIFIČNOST "LOKALCA": Piši točna imena! Ne piši "Sprehodite se ob reki", ampak "Sprehod ob reki Savinji do mestnega parka".
    3. PREVERJENA RESNIČNOST IN URA: Upoštevaj, da je ura {trenutni_cas}. Po 20:00 uri predlagaj samo varne in odprte večerne lokacije.
    4. GEOGRAFSKA FLEKSIBILNOST: Če kraj nima dovolj opcij, poišči najboljše ideje v sosednjih vaseh/mestih (maks 15 min vožnje).

    ZAHTEVAN FORMAT ODGOVORA (Strogo se drži tega formata oštevilčenja):
    {format_odgovora}
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
            
            # ==========================================
            # ZDRUŽITEV: NAŠ OGLAS + AI ODGOVOR
            # ==========================================
            koncni_odgovor = sponzorski_tekst_za_vrh + odgovor_ai
            
            return jsonify({"odgovor": koncni_odgovor})
        else:
            return jsonify({"error": "AI ni vrnil odgovora."}), 500

    except Exception as e:
        print(f"Sistemska napaka: {str(e)}")
        return jsonify({"error": "Nekaj je šlo narobe na strežniku."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
