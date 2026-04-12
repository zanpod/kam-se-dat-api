import os
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

        # Očistimo vhodne podatke
        surova_lokacija = data.get('lokacija', 'Slovenija')
        lokacija = surova_lokacija.strip().capitalize()
        
        druzba = data.get('druzba', 'S prijatelji')
        proracun = data.get('proracun', 'Zmerno')
        mood = data.get('mood', 'Vesel')
        ze_predlagano = data.get('zePredlagano', [])

        trenutni_cas = datetime.now().strftime("%H:%M")

        sponzorski_tekst = ""
        stevilo_ai_idej = 3
        format_odgovora = """
**1. Ime lokacije, Kraj**
Kratek opis...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
---
**2. Ime lokacije, Kraj**
Kratek opis...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
---
**3. Ime lokacije, Kraj**
Kratek opis...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
"""

        # ====================== SPONZOR LOGIKA ======================
        if proracun != "0€ (BREZPLAČNO)" and supabase:
            try:
                res = supabase.table('sponzorji').select('*').eq('lokacija', lokacija).eq('aktiven', True).execute()
                if res.data and len(res.data) > 0:
                    sponzor = res.data[0]
                    if sponzor['ime'] not in ze_predlagano:
                        maps_q = f"{sponzor['ime']}, {lokacija}".replace(" ", "+")
                        opis = sponzor.get('opis', "Odlična lokalna izbira!")
                        
                        sponzorski_tekst = f"**1. {sponzor['ime']}, {lokacija}**\n{opis}\n[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query={maps_q})\n---\n"
                        
                        stevilo_ai_idej = 2
                        format_odgovora = """
**2. Ime lokacije, Kraj**
Kratek opis...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
---
**3. Ime lokacije, Kraj**
Kratek opis...
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query=Ime+Lokacije,+Kraj)
"""
                        print(f"✅ Sponzor dodan: {sponzor['ime']}")
            except Exception as e:
                print(f"🚨 Napaka pri branju sponzorjev: {e}")

        # ====================== AI PROMPT ======================
        prompt = f"""
Deluješ kot slovenski lokalni insider. Predlagaj {stevilo_ai_idej} ideje za izlet.
Lokacija: {lokacija}, Družba: {druzba}, Proračun: {proracun}, Mood: {mood}, Ura: {trenutni_cas}.
Ne ponavljaj lokacij: {ze_predlagano}. Uporabi točna imena obstoječih lokacij (max 20 min vožnje).

FORMAT:
{format_odgovora}
"""

        # ====================== AI KLIC ======================
        if not API_KEY:
            return jsonify({"error": "Strežnik nima API ključa za Google Gemini."}), 500

        # UPORABA STABILNEGA MODELA
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_data = res.json()

        # PAMETNO LOVLJENJE NAPAK (Prepreči [object Object])
        if 'error' in res_data:
            error_msg = res_data['error'].get('message', str(res_data['error']))
            print(f"🚨 GOOGLE API NAPAKA: {error_msg}")
            return jsonify({"error": f"Napaka Googla: {error_msg}"}), 500

        if 'candidates' not in res_data or not res_data['candidates']:
            return jsonify({"error": "AI ni vrnil odgovora."}), 500

        ai_odgovor = res_data['candidates'][0]['content']['parts'][0]['text']
        koncni_odgovor = sponzorski_tekst + ai_odgovor

        return jsonify({"odgovor": koncni_odgovor.strip()})

    except Exception as e:
        print(f"❌ KRITIČNA NAPAKA STREŽNIKA: {str(e)}")
        return jsonify({"error": "Prišlo je do napake na strežniku."}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5005))
    app.run(host='0.0.0.0', port=port)import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Supabase (optional safe import)
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

# ====================== INIT ======================
load_dotenv()

app = Flask(__name__)
CORS(app)

# ====================== ENV ======================
API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

print("DEBUG ENV:")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", "OK" if SUPABASE_KEY else None)
print("GEMINI:", "OK" if API_KEY else None)

# ====================== SUPABASE INIT (SAFE) ======================
supabase = None

if SUPABASE_URL and SUPABASE_KEY and create_client:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase povezan")
    except Exception as e:
        print("❌ Napaka pri Supabase:", e)
else:
    print("⚠️ Supabase ni nastavljen - fallback mode")

# ====================== ROUTE ======================
@app.route('/generiraj', methods=['POST'])
def generiraj_predloge():
    try:
        data = request.json or {}

        lokacija = data.get('lokacija')
        druzba = data.get('druzba')
        proracun = data.get('proracun')
        trajanje = data.get('trajanje')
        mood = data.get('mood')
        ze_predlagano = data.get('zePredlagano', [])

        trenutni_cas = datetime.now().strftime("%H:%M")

        # ====================== SPONZOR ======================
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

        if proracun != "0€ (BREZPLAČNO)" and supabase:
            try:
                odgovor_baze = supabase.table('sponzorji') \
                    .select('*') \
                    .eq('lokacija', lokacija) \
                    .eq('aktiven', True) \
                    .execute()

                if odgovor_baze.data:
                    sponzor = odgovor_baze.data[0]

                    if sponzor['ime'] not in ze_predlagano:
                        maps_query = f"{sponzor['ime']}, {lokacija}".replace(" ", "+")
                        opis = sponzor.get('opis', "Odlična lokalna izbira!")

                        sponzorski_tekst = f"""**1. {sponzor['ime']}, {lokacija}**
{opis}
[📍 Prikaži na zemljevidu](https://www.google.com/maps/search/?api=1&query={maps_query})
---
"""

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
                        print("✅ Sponzor dodan:", sponzor['ime'])

            except Exception as e:
                print("❌ Napaka Supabase:", e)

        # ====================== PROMPT ======================
        prompt = f"""
Deluješ kot vrhunski slovenski lokalni insider.
Tvoja naloga je predlagati natanko {stevilo_ai_idej} ideje za izlet.

PODATKI:
- Lokacija: {lokacija}
- Družba: {druzba}
- Proračun: {proracun}
- Mood: {mood}
- Ura: {trenutni_cas}

PRAVILA:
- Realne lokacije
- Max 20 min od {lokacija}
- Brez ponavljanja

FORMAT:
{format_odgovora}
"""

        # ====================== GEMINI ======================
        if not API_KEY:
            return jsonify({"error": "Manjka GEMINI_API_KEY"}), 500

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

        res = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )

        res_data = res.json()

        if 'error' in res_data:
            return jsonify({"error": res_data['error']}), 500

        ai_odgovor = res_data['candidates'][0]['content']['parts'][0]['text']

        koncni_odgovor = sponzorski_tekst + ai_odgovor

        return jsonify({"odgovor": koncni_odgovor.strip()})

    except Exception as e:
        print("❌ GLOBAL ERROR:", str(e))
        return jsonify({"error": "Server crash"}), 500


# ====================== RUN ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
