```python
import os
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
        trenutni_dan = datetime.now().strftime("%A")

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
```
