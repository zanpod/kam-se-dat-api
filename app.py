import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Naložimo nastavitve
load_dotenv()
app = Flask(__name__)
CORS(app)

# 2. API ključi
API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    print("🚨 KRITIČNA NAPAKA: Manjkajo API ključi ali Supabase podatki!")

# 3. Supabase klient
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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

    # ====================== SPONZOR LOGIKA ======================
    sponzorski_tekst = ""
    stevilo_ai_idej = 3
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

    if proracun != "0€ (BREZPLAČNO)":
        try:
            odgovor_baze = supabase.table('sponzorji') \
                .select('*') \
                .eq('lokacija', lokacija) \
                .eq('aktiven', True) \
                .execute()

            if odgovor_baze.data and len(odgovor_baze.data) > 0:
                sponzor = odgovor_baze.data[0]

                # Ne ponavljamo sponzorja, če je že bil predlagan
                if sponzor['ime'] not in ze_predlagano:
                    # Dinamična Google Maps povezava
                    maps_query = f"{sponzor['ime']}, {lokacija}".replace(" ", "+")
                    opis = sponzor.get('opis', "Odlična lokalna izbira in preverjeno najboljša izkušnja!")

                    sponzorski_tekst = f"""**1. {sponzor['ime']}, {lokacija}**
{opis}
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query={maps_query})
---
"""

                    # AI naj generira samo še 2 ideji (številki 2 in 3)
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
                    print(f"✅ Sponzor prilepljen: {sponzor['ime']}")
                else:
                    print("⚠️ Sponzor že v zgodovini – preskočen")
            else:
                print("ℹ️ Ni aktivnega sponzorja za to lokacijo")
        except Exception as e:
            print(f"❌ Napaka pri branju sponzorjev: {e}")

    # ====================== PROMPT ZA GEMINI ======================
    prompt = f"""
Deluješ kot vrhunski slovenski lokalni insider.
Tvoja naloga je predlagati natanko {stevilo_ai_idej} resnične ideje za izlet.

PODATKI UPORABNIKA:
- Izhodiščni kraj: {lokacija}
- Družba: {druzba}
- Proračun: {proracun}
- Razpoloženje: {mood}
- Ura: {trenutni_cas}

{zgodovina_navodilo if 'zgodovina_navodilo' in locals() else ''}
OPOZORILO: {sponzor['ime'] if 'sponzor' in locals() else ''} je že uporabljen kot prva ideja. NE ponovi ga!

STROGA PRAVILA:
1. Predlogi morajo biti med seboj popolnoma različni.
2. Uporabi točna imena lokacij (ne generičnih opisov).
3. Upoštevaj uro {trenutni_cas}.
4. Maksimalna razdalja: 15–20 minut vožnje od {lokacija}.

VRNI SAMO naslednji format (brez uvodov, brez zaključkov):

{format_odgovora}
"""

    # ====================== KLIČ GEMINI ======================
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        res = requests.post(url, headers=headers, json=payload)
        res_data = res.json()

        if 'error' in res_data:
            return jsonify({"error": res_data['error'].get('message', 'API napaka')}), 500

        if res_data and 'candidates' in res_data and len(res_data['candidates']) > 0:
            ai_odgovor = res_data['candidates'][0]['content']['parts'][0]['text']

            # Združimo sponzor + AI
            koncni_odgovor = sponzorski_tekst + ai_odgovor

            return jsonify({"odgovor": koncni_odgovor.strip()})
        else:
            return jsonify({"error": "AI ni vrnil odgovora"}), 500

    except Exception as e:
        print(f"❌ Sistemska napaka: {str(e)}")
        return jsonify({"error": "Napaka na strežniku"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
