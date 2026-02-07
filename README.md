# 🔋 Battery Monitor per Home Assistant

Integrazione personalizzata per **monitorare tutte le entità batteria** presenti in Home Assistant e avere un colpo d’occhio immediato su:
- quante batterie stai monitorando
- quante sono **sotto soglia**
- quante sono a **0%**
- qual è la **batteria più scarica**
- una **lista pronta** dei dispositivi sotto soglia

> Perfetta per impianti Zigbee (ZHA / Zigbee2MQTT), Wi-Fi e qualsiasi integrazione che esponga sensori di batteria.

![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue)
![Platform](https://img.shields.io/badge/Platform-Home%20Assistant-41BDF5)
![Maintainer](https://img.shields.io/badge/Maintainer-DomoticaFacile-blueviolet)
[![Donate](https://img.shields.io/badge/Buy_Me_A_Coffee-%E2%98%95-yellow)](https://www.buymeacoffee.com/domoticafacile)
![GitHub stars](https://img.shields.io/github/stars/DomoticaFacile/battery_monitor?style=social)


[![Gruppo Facebook](https://img.shields.io/badge/Gruppo-Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://www.facebook.com/groups/domoticafacile)
[![Pagina Facebook](https://img.shields.io/badge/Pagina-Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://www.facebook.com/domoticafacile)
[![YouTube](https://img.shields.io/badge/YouTube-Channel-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@DomoticaFacile-it)

[![Instagram](https://img.shields.io/badge/Instagram-Profilo-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/domoticafacile.it)
[![TikTok](https://img.shields.io/badge/TikTok-Profilo-000000?style=for-the-badge&logo=tiktok&logoColor=white)](https://www.tiktok.com/@domoticafacile)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Canale-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://whatsapp.com/channel/0029Vb5qW5O4o7qPGrFbRm1T)

<p align="center">
  <img width="400" height="400" alt="icon" src="https://github.com/user-attachments/assets/a6da43c2-e5eb-422d-aba3-9c42e908a043" />
</p>

📣 Ti piace questa integrazione? ⭐ Metti una stella al repository per supportare il progetto!

---

## 🎯 Funzionalità

✅ Scansione automatica delle entità “batteria” (device_class battery + euristica)  
✅ Filtri avanzati: domini, include/exclude (pattern)  
✅ **Selezione multipla da elenco a discesa** per includere/escludere sensori (più facile di scrivere pattern)  
✅ Sensori di riepilogo (conteggi + percentuali + lista)  
✅ Stato “semaforo”: **OK / WARNING / CRITICAL**  
✅ Opzione per **ignorare 0%** nel calcolo della batteria più scarica  
✅ Opzione per **notifica automatica** quando compare uno 0%  
✅ Low List pulita: non include i sensori creati dall’integrazione Battery Monitor

---

## ⚙️ Installazione tramite HACS

> Se non hai HACS, segui la guida ufficiale: https://hacs.xyz

1. Apri **HACS**
2. Vai sui 3 pallini in alto a destra
3. Clicca su "Archivi digitali personalizzati"
4. Copia e incolla l'indirizzo di questo repo: https://github.com/DomoticaFacile/battery_monitor
5. Seleziona "Integrazione"
6. Clicca "Aggiungi"
7. Cerca l'integrazione nell'elenco di HACS, clicca e poi installa

---

## 🧩 Configurazione

Dopo l’installazione:

1. Vai su **Impostazioni → Dispositivi e servizi**
2. Clicca **Aggiungi integrazione**
3. Cerca **Battery Monitor**
4. Completa il setup

📌 La configurazione principale è via UI e le opzioni sono modificabili dal tasto **ingranaggio** dell’integrazione.

---

## 🛠️ Opzioni disponibili (Impostazioni → Integrazioni → Battery Monitor → Opzioni)

### 🔻 Soglia Batteria Bassa (%)
- Imposta la percentuale sotto cui una batteria viene considerata “bassa”.
- Esempio: soglia 20 → tutte le batterie **≤ 20%** entrano nella lista “Low”.

### 🔻 Soglia Batteria Critica (%)
- Imposta la percentuale sotto cui una batteria viene considerata “critica”.
- Esempio: soglia 10 → tutte le batterie **≤ 10%** entrano nella lista “critica”.

### 🧠 Usa euristica (include_heuristic)
Se attiva, oltre alle entità con `device_class: battery`, prova a riconoscere le batterie anche quando:
- nel nome/entity_id compare “battery/batter”
- o il valore ha unità “%” e sembra un livello batteria

### 🧭 Domini da scansionare (scan_domains)
Di default è `sensor`.
Puoi aggiungere altri domini separati da virgola se necessario.

### ✅ Include / ❌ Exclude (selezione multipla)
- **include_entities**: se selezioni uno o più sensori, Battery Monitor considera **solo** quelli.
- **exclude_entities**: i sensori selezionati vengono **sempre esclusi**.
  
📌 Sono presenti anche i filtri pattern (fnmatch) per utenti avanzati.

### 🧯 Ignora 0% per batteria più scarica (ignore_zero_for_lowest)
Quando attivo, il sensore **Battery Monitor Lowest** ignora i valori 0% nel calcolo.
Utile perché alcuni dispositivi (soprattutto Zigbee) a volte riportano 0% in modo errato o fisso.

### 🔔 Notifica quando compare uno 0% (notify_on_zero)
Quando attivo, Battery Monitor genera una notifica persistente quando viene rilevato almeno un sensore batteria a 0%.

---

## 📟 Sensori creati dall’integrazione (cosa fanno e a cosa servono)

Di seguito l’elenco completo dei sensori e il loro utilizzo pratico.

### ✅ Battery Monitor Status (`sensor.battery_monitor_status`)
**Stato generale** dell’impianto batterie:
- **OK** → nessuna batteria sotto soglia e nessun 0%
- **WARNING** → almeno una batteria sotto soglia (ma nessun 0%)
- **CRITICAL** → almeno una batteria a 0%

🔧 Utile per: automazioni “semaforo”, dashboard immediate.

---

### 🔢 Battery Monitor Total (`sensor.battery_monitor_total`)
Numero totale di **batterie monitorate** (entità batteria valide trovate).

🔧 Utile per: controllare che la scansione funzioni (es. “mi vede davvero tutte le batterie?”).

---

### ⚠️ Battery Monitor Low (`sensor.battery_monitor_low`)
Numero di entità batteria **sotto soglia**.

🔧 Utile per: trigger automazioni e alert (es. notifica se > 0).

---

### 🔌 Battery Monitor Low Devices (`sensor.battery_monitor_low_devices`)
Numero di **dispositivi** con almeno una batteria sotto soglia.

✅ Differenza con “Low”:
- **Low** conta le entità
- **Low Devices** conta i device (evita duplicati se un device espone più entità)

---

### 🔻 Battery Monitor Lowest (`sensor.battery_monitor_lowest`)
Mostra la **batteria più scarica** trovata (in percentuale).

📌 Se `ignore_zero_for_lowest` è attivo, ignora i valori 0% nel calcolo.

---

### 🧾 Battery Monitor Low List (`sensor.battery_monitor_low_list`)
Lista testuale pronta dei dispositivi sotto soglia (es. `Nome: 12% | Nome2: 18%`).

🔧 Utile per:
- card Lovelace “lista rapida”
- notifiche già pronte senza template complessi

---

### 🚨 Battery Monitor Zero Count (`sensor.battery_monitor_zero_count`)
Conta quante batterie sono **esattamente a 0%**.

🔧 Utile per: alert urgenti (batterie finite / sensori bloccati su 0).

---

### 📉 Battery Monitor Low Percent (`sensor.battery_monitor_low_percent`)
Percentuale di batterie sotto soglia rispetto al totale.

Formula: `Low / Total * 100`

---

### 📉 Battery Monitor Zero Percent (`sensor.battery_monitor_zero_percent`)
Percentuale di batterie a 0% rispetto al totale.

Formula: `Zero Count / Total * 100`

---

### 🧩 Battery Monitor Overview (`sensor.battery_monitor_overview`)
Sensore “tecnico” di riepilogo: il valore è un totale, ma negli **attributi** trovi spesso:
- elenco completo batterie (entity_id, nome, valore, disponibile)
- soglia e conteggi
- dettagli utili per card avanzate o debug

---

## 📊 Dashboard Lovelace (semplice e pulita)

Esempio base (nativa):

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: sensor.battery_monitor_status
    show_state: false
    show_name: false
    state_image:
      OK: /local/images/battery_monitor/status_ok.png
      CRITICAL: /local/images/battery_monitor/status_critical.png
      WARNING: /local/images/battery_monitor/status_warning.png
    image: /local/images/battery_monitor/status_ok.png
    card_mod:
      style: |
        ha-card {
          width: 100px;
          max-width: 100px;
          margin: 0 auto;
        }
        #image {
          height: 100px;
          object-fit: contain;
        }
  - type: entities
    title: Stato Batterie
    entities:
      - entity: sensor.battery_monitor_status
      - entity: sensor.battery_monitor_total
      - entity: sensor.battery_monitor_low
      - entity: sensor.battery_monitor_low_devices
      - entity: sensor.battery_monitor_lowest
      - entity: sensor.battery_monitor_low_list
      - entity: sensor.battery_monitor_overview
```
---
🇮🇹 Guida rapida: come tradurre Battery Monitor in altre lingue

Home Assistant gestisce le traduzioni tramite i file nella cartella translations/.
La lingua usata dipende automaticamente dalla lingua impostata in Home Assistant (Impostazioni → Sistema → Generale).

✅ Struttura delle cartelle

Assicurati che la tua integrazione abbia questa struttura:
```yaml
custom_components/battery_monitor/
  strings.json
  translations/
    it.json
    en.json
    de.json
    fr.json
```

strings.json contiene le chiavi e i testi base.

translations/ contiene le traduzioni per ogni lingua.

1) Aggiungere una nuova lingua

Crea un nuovo file nella cartella translations/ con il codice lingua:

Inglese: en.json

Tedesco: de.json

Francese: fr.json

Spagnolo: es.json

Copia la struttura di translations/it.json dentro il nuovo file.

Traduci solo i testi (valori), senza cambiare le chiavi.

✅ Esempio:

```yaml
{
  "options": {
    "step": {
      "init": {
        "title": "Battery Monitor Options",
        "data": {
          "threshold": "Low battery threshold (%)"
        }
      }
    }
  }
}
```
2) Non cambiare mai le chiavi

Le chiavi devono combaciare esattamente con quelle usate nel codice (config flow e options flow).
Se una chiave non esiste o è diversa, Home Assistant mostrerà il nome grezzo (es. scan_domains).

3) Troubleshooting

Se vedi errori tipo JSONDecodeError, il file non è un JSON valido (attenzione a virgole e parentesi).

Se le traduzioni non compaiono, verifica i percorsi:

custom_components/battery_monitor/strings.json

custom_components/battery_monitor/translations/<lang>.json

---

👨‍💻 Sviluppatore

Realizzato con ❤️ da www.domoticafacile.it

Hai suggerimenti o vuoi contribuire?
Apri una issue, una pull request o contattaci tramite i nostri canali social che trovi sul sito.

---

## 📄 Licenza

Questo progetto è distribuito sotto licenza **MIT**.  
Puoi usarlo, modificarlo e distribuirlo liberamente, purché venga mantenuto il copyright originario.

Leggi il file [LICENSE](LICENSE) per i dettagli completi.

---

❤️ Supporta Domotica Facile

Se questa integrazione ti è stata utile e ti ha fatto risparmiare tempo (e batterie 😄), puoi darci una mano concreta a continuare 💪🏡

Ogni guida, integrazione e test richiede tempo, studio e tanta passione.
Con un piccolo contributo puoi supportare lo sviluppo di nuovi progetti, articoli e integrazioni come questa.

☕ Offrici un caffè e sostieni Domotica Facile

[![Buy Me A Coffee](https://github.com/appcraftstudio/buymeacoffee/raw/master/Images/snapshot-bmc-button.png)](https://www.buymeacoffee.com/domoticafacile)

Anche un gesto simbolico fa la differenza.
Grazie di cuore per il tuo supporto ❤️🔋

---
ENGLISH
# 🔋 Battery Monitor for Home Assistant

A custom integration to **monitor all battery entities** in Home Assistant and get an instant overview of:
- how many batteries you’re monitoring
- how many are **below the threshold**
- how many are at **0%**
- which one is the **lowest battery**
- a **ready-to-use list** of devices below the threshold

> Perfect for Zigbee setups (ZHA / Zigbee2MQTT), Wi-Fi devices, and any integration that exposes battery sensors.

![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue)
![Platform](https://img.shields.io/badge/Platform-Home%20Assistant-41BDF5)
![Maintainer](https://img.shields.io/badge/Maintainer-DomoticaFacile-blueviolet)
[![Donate](https://img.shields.io/badge/Buy_Me_A_Coffee-%E2%98%95-yellow)](https://www.buymeacoffee.com/domoticafacile)
![GitHub stars](https://img.shields.io/github/stars/DomoticaFacile/battery_monitor?style=social)

[![Facebook Group](https://img.shields.io/badge/Group-Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://www.facebook.com/groups/domoticafacile)
[![Facebook Page](https://img.shields.io/badge/Page-Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white)](https://www.facebook.com/domoticafacile)
[![YouTube](https://img.shields.io/badge/YouTube-Channel-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@DomoticaFacile-it)

[![Instagram](https://img.shields.io/badge/Instagram-Profile-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/domoticafacile.it)
[![TikTok](https://img.shields.io/badge/TikTok-Profile-000000?style=for-the-badge&logo=tiktok&logoColor=white)](https://www.tiktok.com/@domoticafacile)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Channel-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://whatsapp.com/channel/0029Vb5qW5O4o7qPGrFbRm1T)

<p align="center">
  <img width="400" height="400" alt="icon" src="https://github.com/user-attachments/assets/a6da43c2-e5eb-422d-aba3-9c42e908a043" />
</p>

📣 Do you like this integration? ⭐ Star the repository to support the project!

---

## 🎯 Features

✅ Automatic discovery of “battery” entities (`device_class: battery` + heuristic)  
✅ Advanced filters: domains, include/exclude (patterns)  
✅ **Multi-select dropdown** to include/exclude sensors (easier than writing patterns)  
✅ Summary sensors (counts + percentages + list)  
✅ Traffic-light status: **OK / WARNING / CRITICAL**  
✅ Option to **ignore 0%** when calculating the lowest battery  
✅ Option for **automatic notification** when a 0% battery appears  
✅ Clean Low List: it does not include sensors created by the Battery Monitor integration

---

## ⚙️ Installation via HACS

> If you don’t have HACS, follow the official guide: https://hacs.xyz

1. Open **HACS**
2. Click the **three dots** in the top-right corner
3. Select **Custom repositories**
4. Copy & paste this repository URL: https://github.com/DomoticaFacile/battery_monitor
5. Select **Integration**
6. Click **Add**
7. Find the integration in the HACS list, click it and then install it.

---

## 🧩 Configuration

After installation:

1. Go to **Settings → Devices & services**
2. Click **Add integration**
3. Search for **Battery Monitor**
4. Complete the setup

📌 The main configuration is done via UI, and options can be changed via the integration **gear icon**.

---

## 🛠️ Available Options (Settings → Integrations → Battery Monitor → Options)

### 🔻 Low Battery Threshold (%)
- Set the percentage under which a battery is considered “low”.
- Example: threshold 20 → all batteries **≤ 20%** will appear in “Low”.

### 🔻 Critical Battery Threshold (%)
- Sets the percentage below which a battery is considered "critical."
- Example: threshold 10 → all batteries **≤ 10%** enter the "critical" list.

### 🧠 Use heuristic (include_heuristic)
If enabled, in addition to entities with `device_class: battery`, it tries to detect batteries when:
- “battery/batter” appears in the name/entity_id
- or the value has “%” and looks like a battery level

### 🧭 Domains to scan (scan_domains)
Default is `sensor`.
You can add other domains separated by commas if needed.

### ✅ Include / ❌ Exclude (multi-select)
- **include_entities**: if you select one or more sensors, Battery Monitor will scan **only** those.
- **exclude_entities**: selected sensors are **always excluded**.

📌 Pattern filters (fnmatch) are also available for advanced users.

### 🧯 Ignore 0% for lowest battery (ignore_zero_for_lowest)
When enabled, the **Battery Monitor Lowest** sensor ignores 0% values.
Useful because some devices (especially Zigbee) may sometimes report a wrong or “stuck” 0%.

### 🔔 Notify when a 0% appears (notify_on_zero)
When enabled, Battery Monitor creates a persistent notification when at least one battery sensor is detected at 0%.

---

## 📟 Sensors created by the integration (what they do)

Below is the complete list of sensors and their practical use.

### ✅ Battery Monitor Status (`sensor.battery_monitor_status`)
Overall battery system status:
- **OK** → no battery below threshold and no 0%
- **WARNING** → at least one battery below threshold (but no 0%)
- **CRITICAL** → at least one battery at 0%

🔧 Useful for: “traffic light” automations and quick dashboards.

---

### 🔢 Battery Monitor Total (`sensor.battery_monitor_total`)
Total number of **monitored batteries** (valid battery entities found).

🔧 Useful for: verifying discovery/scanning (e.g., “does it see all my batteries?”).

---

### ⚠️ Battery Monitor Low (`sensor.battery_monitor_low`)
Number of battery entities **below the threshold**.

🔧 Useful for: triggers and alerts (e.g., notify when > 0).

---

### 🔌 Battery Monitor Low Devices (`sensor.battery_monitor_low_devices`)
Number of **devices** with at least one battery below threshold.

✅ Difference vs “Low”:
- **Low** counts entities
- **Low Devices** counts devices (avoids duplicates if a device exposes multiple battery entities)

---

### 🔻 Battery Monitor Lowest (`sensor.battery_monitor_lowest`)
Shows the **lowest battery level** found (percentage).

📌 If `ignore_zero_for_lowest` is enabled, it ignores 0% values in the calculation.

---

### 🧾 Battery Monitor Low List (`sensor.battery_monitor_low_list`)
Ready-to-use text list of devices below threshold (e.g., `Name: 12% | Name2: 18%`).

🔧 Useful for:
- quick Lovelace list cards
- notifications without complex templates

---

### 🚨 Battery Monitor Zero Count (`sensor.battery_monitor_zero_count`)
Counts how many batteries are **exactly at 0%**.

🔧 Useful for: urgent alerts (dead batteries / sensors stuck at 0).

---

### 📉 Battery Monitor Low Percent (`sensor.battery_monitor_low_percent`)
Percentage of batteries below threshold compared to the total.

Formula: `Low / Total * 100`

---

### 📉 Battery Monitor Zero Percent (`sensor.battery_monitor_zero_percent`)
Percentage of batteries at 0% compared to the total.

Formula: `Zero Count / Total * 100`

---

### 🧩 Battery Monitor Overview (`sensor.battery_monitor_overview`)
Technical summary sensor: the state is a total, but the real value is in the **attributes**, which may include:
- full battery list (entity_id, name, value, availability)
- threshold and counts
- useful details for advanced cards or debugging

---

## 📊 Lovelace Dashboard (simple and clean)

Basic example (native):

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Battery Status
    entities:
      - entity: sensor.battery_monitor_status
      - entity: sensor.battery_monitor_total
      - entity: sensor.battery_monitor_low
      - entity: sensor.battery_monitor_low_devices
      - entity: sensor.battery_monitor_lowest
      - entity: sensor.battery_monitor_low_list
      - entity: sensor.battery_monitor_overview
```
EN Quick guide: how to translate Battery Monitor into other languages

Home Assistant handles translations using the files inside the translations/ folder.
The language is automatically selected based on the language set in Home Assistant (Settings → System → General).

✅ Folder structure

Make sure your integration follows this structure:

```yaml
custom_components/battery_monitor/
  strings.json
  translations/
    it.json
    en.json
    de.json
    fr.json
```
strings.json contains the translation keys and base strings.

translations/ contains the translations for each language.

1) Add a new language

Create a new file inside translations/ using the language code:

English: en.json

German: de.json

French: fr.json

Spanish: es.json

Copy the structure from translations/it.json into the new file.

Translate only the text values, without changing the keys.

✅ Example:

```yaml
{
  "options": {
    "step": {
      "init": {
        "title": "Battery Monitor Options",
        "data": {
          "threshold": "Low battery threshold (%)"
        }
      }
    }
  }
}
```
2) Never change the keys

Keys must match exactly what is used in the code (config flow and options flow).
If a key is missing or different, Home Assistant will show the raw key (e.g., scan_domains).

3) Troubleshooting

If you see errors like JSONDecodeError, the file is not valid JSON (check commas and braces).

If translations do not appear, verify the file paths:

custom_components/battery_monitor/strings.json

custom_components/battery_monitor/translations/<lang>.json

---
👨‍💻 Developer

Created with ❤️ by www.domoticafacile.it

Do you have suggestions or want to contribute?
Open an issue, a pull request, or contact us through our social channels listed on the website.
---

📄 License

This project is distributed under the MIT license.
You may use, modify, and distribute it freely, as long as the original copyright is preserved.

Read the LICENSE file for full details.

[![Buy Me A Coffee](https://github.com/appcraftstudio/buymeacoffee/raw/master/Images/snapshot-bmc-button.png)](https://www.buymeacoffee.com/domoticafacile)
