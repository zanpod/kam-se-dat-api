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
    ze_predlagano = data.get('zePredlagano', []) # NOVO: Preberemo zgodovino iz brskalnika!

    trenutni_cas = datetime.now().strftime("%H:%M")
    trenutni_dan = datetime.now().strftime("%A")

    # ==========================================
    # LOGIKA ZA ZGODOVINO (Da se AI ne ponavlja)
    # ==========================================
    zgodovina_navodilo = ""
    if ze_predlagano and len(ze_predlagano) > 0:
        zgodovina_navodilo = f"\nOPOZORILO: Temu uporabniku si danes ŽE PREDLAGAL naslednje lokacije: {', '.join(ze_predlagano)}. TEH LOKACIJ NE SMEŠ VEČ OMENITI! Najdi 3 popolnoma nove.\n"

    # ==========================================
    # LOGIKA ZA BAZO SPONZORJEV (MONETIZACIJA)
    # ==========================================
    sponzorsko_navodilo = ""
    
    if proracun != "0€ (BREZPLAČNO)":
        try:
            odgovor_baze = supabase.table('sponzorji').select('*').eq('lokacija', lokacija).eq('aktiven', True).execute()
            podatki = odgovor_baze.data

            if podatki and len(podatki) > 0:
                sponzor = podatki[0] 
                
                # Preverimo, da nismo sponzorja slučajno že predlagali prejšnjič
                if sponzor['ime'] not in ze_predlagano:
                    sponzorsko_navodilo = f"""
    *** VIP SPONZORSKA ZAHTEVA (ABSOLUTNA PRIORITETA) ***
    Za 1. IDEJO (na prvem mestu) MORAŠ obvezno predlagati točno to lokacijo: '{sponzor['ime']}'. 
    Dodatne informacije naročnika (vključi jih v privlačen opis): '{sponzor.get('opis', '')}'.
    Prilagodi opis te lokacije tako, da se bo popolnoma ujemal z moodom '{mood}' in družbo '{druzba}'.
    Ostali 2 ideji najdita sama, a naj bosta iz preostalih kategorij.
                    """
        except Exception as e:
            print(f"Napaka pri branju iz baze: {e}")

    # ==========================================
    # PROMPT ZA UMETNO INTELIGENCO
    # ==========================================
    prompt = f"""
    Deluješ kot vrhunski slovenski 'lokalni insider' in kurator doživetij. Ne ponujaš dolgočasnih, generičnih turističnih nasvetov, ampak izjemno specifične, preverjene in butične ideje, prilagojene trenutnemu počutju in družbi.
    Tvoja naloga je predlagati natanko 3 resnične, obstoječe ideje za izlet ali aktivnost na podlagi spodnjih parametrov. Ne piši uvodnih ali zaključnih pozdravov.

    PODATKI UPORABNIKA:
    - Izhodiščni kraj: {lokacija}
    - Družba: {druzba}
    - Proračun: {proracun}
    - Čas na voljo: {trajanje}
    - Želeno razpoloženje: {mood}
    
    TRENUTNO STANJE (ZELO POMEMBNO):
    - Trenutni dan: {trenutni_dan}
    - Trenutna ura: {trenutni_cas}
    {zgodovina_navodilo}
    {sponzorsko_navodilo}

    EKSTREMNO STROGA PRAVILA ZA PROFESIONALNO KAKOVOST:
    1. PRAVILO TREH KATEGORIJ (ABSOLUTNA RAZNOLIKOST): Vseh 3 predlogov mora biti iz popolnoma različnih svetov. NIKOLI ne ponudi dveh istih tipov aktivnosti.
       - Če proračun NI 0€, strukturiraj tako: 
         * 1. ideja: KULINARIKA / HEDONIZEM (specifična kavarna, slaščičarna, vinska klet ali restavracija - navedi točno ime!).
         * 2. ideja: NARAVA / AKTIVNOST (točno določena sprehajalna pot, jezero, hrib ali razgledna točka).
         * 3. ideja: DOŽIVETJE / URBANI UTRIP (kultura, muzej, grad, wellness, ali specifičen trg v mestu).
       - Če proračun JE "0€ (BREZPLAČNO)", strukturiraj tako: 
         * 1. ideja: SKRIT NARAVNI KOTIČEK (ne najbolj znana pot, ampak nekaj bolj lokalnega in mirnega).
         * 2. ideja: URBANI SPREHOD / ARHITEKTURA (zanimiv del mesta, trg, stare uličice).
         * 3. ideja: NAJBOLJŠI LOKALNI RAZGLED (specifična točka za opazovanje sončnega zahoda ali mesta).
         
    2. SPECIFIČNOST "LOKALCA": Ne piši "Pojdite v eno izmed lokalnih kavarn". Piši "Naročite domačo torto v Kavarni Zvezda". Ne piši "Sprehodite se ob reki". Piši "Sprehodite se po levem bregu Savinje do mostu...". Navedi TOČNA IN RESNIČNA IMENA lokalov in lokacij.

    3. PRILAGODITEV MOODU IN DRUŽBI: Odgovor mora vibrirati z izbranim počutjem. Če je mood "{mood}" in družba "{druzba}", mora opis jasno odražati, zakaj je to popolna izbira za točno to situacijo.

    4. PREVERJENA RESNIČNOST IN URA: Ne ugibaj in ne haluciniraj imen! Upoštevaj {trenutni_dan} in {trenutni_cas}. Če je ura po 20:00, ponujaj izključno varne, odprte večerne lokacije (osvetljene poti, nočni razgledi, odprti pubi).

    5. GEOGRAFSKA FLEKSIBILNOST: Če izhodiščni kraj {lokacija} nima dovolj specifičnih opcij, samodejno in inteligentno poišči najboljše ideje v sosednjih vaseh ali mestih, ki so oddaljena maksimalno 15-20 minut vožnje.

    ZAHTEVAN FORMAT ODGOVORA (Vrni samo ta format, ničesar drugega, ohrani zvezdice in ločila zaradi frontend parserja):
    **1. Ime točno določene lokacije, Kraj**
    Kratek opis (2-3 stavki, pisan doživljajsko, prodajno in privlačno. Razloži, KAJ točno naj tam počnejo, jedo ali vidijo, ter zakaj ustreza njihovemu počutju).
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
