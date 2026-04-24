# Waqt App — Architecture Knowledge File
_Last updated: April 22, 2026_

---

## 1. Overview

A mosque prayer time display application deployed across multiple mosques, each with 2-5 dedicated display machines. Each machine may show a different aspect of content (prayer times, announcements, etc.). The app is self-contained per mosque but managed centrally.

---

## 2. Tech Stack

| Layer | Choice |
|---|---|
| Language | Python |
| Frontend/UI | PyQt6 |
| Packaging | PyInstaller (.exe) |
| Database | PostgreSQL (hosted) |
| API Framework | FastAPI |
| File Sync | Syncthing |
| Prayer Times Source | Aladhan API |
| Update Mechanism | GitHub Releases |

---

## 3. Deployment Model

- Same `.exe` binary deployed on every machine across all mosques
- Each machine is configured on first launch as either a **display machine** or an **admin machine**
- A mosque has 2-5 display machines, each with a designated screen role (prayer times, announcements, etc.)
- Admin machine can be any device (including a personal laptop) — not dedicated hardware
- Machines are set up once by the developer and not physically accessed again
- Internet connection required for updates, data sync, and API calls

### First Launch Setup Screen
On first launch the app presents two options:

**Display Machine:**
- Enter mosque ID
- Enter machine number (1–5)
- App starts in display mode, reads synced config for its role

**Admin Machine:**
- Enter mosque ID
- App starts in full admin dashboard mode
- Sees all data scoped to that mosque ID

### Syncthing Setup
- Developer configures Syncthing on every machine (display and admin) during the setup visit
- Admin cannot do this themselves — it is the one manual step per mosque
- If admin gets a new laptop, a brief remote/in-person session is needed to reconfigure Syncthing
- After initial setup, admin is fully independent

---

## 4. App Update Strategy

- App has a hardcoded version number (e.g. `v1.0.0`)
- On every launch, app calls GitHub Releases API to check for a newer version
- If outdated, downloads the new `.exe` from the release assets, replaces itself, and restarts
- No third-party update library (e.g. PyUpdater) needed — handled with `requests`
- Developer workflow: make changes → build new `.exe` → publish GitHub Release → all machines update on next launch

---

## 5. Central Server

- Hosted on a cheap VPS (e.g. DigitalOcean, ~$5/month)
- Runs PostgreSQL + FastAPI
- Machines interact with it via JSON API calls (similar to how they call Aladhan)
- Handles all mosques and all years in one DB — data is small (timestamps only), easily handles 1000+ mosques across multiple years

### Key API Endpoints (conceptual)
```
GET  /prayer-times?mosque_id=1&date=2026-04-22   ← returns prayer + iqamah times
GET  /prayer-times?mosque_id=1&year=2028          ← checks if year data exists
POST /load-year                                    ← app triggers server to fetch + store new year
POST /heartbeat                                    ← machine reports health status
```

---

## 6. Prayer Times Architecture

### Source
- **Aladhan API** for raw prayer start times
- Base URL: `https://api.aladhan.com/v1`
- Used endpoint: `GET /calendar/{year}/{month}` (coordinates-based)
- No API key required for standard use

### Aladhan API Parameters Used

| Parameter | Description | Notes |
|---|---|---|
| `latitude` + `longitude` | Location coordinates | Preferred over city/address |
| `method` | Calculation method ID (1–15, or 99 for custom) | See method list below |
| `shafaq` | Shafaq type for Isha (Moonsighting Committee only) | `general`, `ahmer`, `abyad` |
| `school` | Juristic school for Asr | `0` = Shafi, `1` = Hanafi |
| `tune` | Per-prayer minute offsets | Comma-separated: Imsak,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Sunset,Isha,Midnight |
| `timezonestring` | Timezone string | e.g. `America/Toronto` |
| `methodSettings` | Custom method angles | Only when `method=99`: FajrAngle,MaghribAngle,IshaAngle |

**Not used:** `latitudeAdjustmentMethod` — left at default (Angle Based)

### Calculation Methods

| ID | Name |
|---|---|
| 1 | Muslim World League |
| 2 | Islamic Society of North America (ISNA) |
| 3 | Egyptian General Authority of Survey |
| 4 | Umm Al-Qura, Makkah |
| 5 | University of Islamic Sciences, Karachi |
| 6 | Institute of Geophysics, Tehran |
| 7 | Shia Ithna-Ashari, Leva Institute, Qum |
| 8 | Gulf Region |
| 9 | Kuwait |
| 10 | Qatar |
| 11 | Singapore |
| 12 | Union Organization Islamic de France |
| 13 | Diyanet, Turkey |
| 14 | Russia |
| 15 | Moonsighting Committee |
| 99 | Custom (use `methodSettings`) |

### Database
- PostgreSQL hosted on central server
- Stores 2-3 years of data per mosque
- Tables: `prayer_times`, `mosques`, `screens`

### Yearly Data Loading
- Each machine checks on launch if the next year's data exists in the DB
- If not, the first machine to detect this sends a `POST /load-year` request with:
  - `mosque_id`
  - `year`
  - Calculation method / coordinates
  - Iqamah config
- Server calls Aladhan, computes iqamah times, stores everything
- Subsequent machines skip this — server detects data already exists
- No server-side cron jobs needed
- If Aladhan API is down during load, app keeps retrying until successful

### Internet Outage Handling
- Display machines cache today's prayer times locally
- If server is unreachable, machine continues displaying cached data for the rest of the day
- If server is still unreachable the next day, app displays an error screen / screensaver

---

## 7. Iqamah Time Algorithm

- Iqamah = prayer start time + offset, snapped within a configurable window
- Default windows:
  - Fajr: 30–45 min after start
  - Dhuhr: 25–40 min after start
  - Asr: 30–45 min after start
  - Maghrib: short fixed offset (near immediate)
  - Isha: 30–45 min after start
- Mosque admin can override all windows via admin mode
- Additional constraints available per prayer (under Advanced in admin UI):
  - Earliest allowed time
  - Latest allowed time
  - Round to nearest X minutes (e.g. nearest 5)
- Seasonal override rules:
  - Admin can define a date range (e.g. May 1 – Jun 1) with different window and constraints
  - Multiple override rules can stack
- Iqamah config is sent to the server when loading new year data

---

## 8. Special Prayer Times

### Ramadan Mode
- Tarawih and Tahajjud times added during Ramadan
- Suhoor time displayed
- Potentially different Iqamah windows during Ramadan
- Configurable via admin mode

### Eid Prayers
- Eid prayer times configurable via admin mode
- Displayed on relevant days

### Jumuah
- Configured in Prayer & Iqamah Settings page
- Number of khutbahs (1 or 2), time for each

---

## 9. Display Features

- **Hijri date** — returned by Aladhan API, displayed on screen
- **Next prayer countdown** — live ticker showing time until next prayer
- **Adhan/Iqamah alerts** — display flashes or changes appearance at prayer time

---

## 10. File Sync (Syncthing)

- Runs as a background service on every machine (display and admin), starts before the app
- Syncs a shared folder across all machines within a mosque
- Shared folder path: `C:/waqt/sync/`

```
C:/waqt/sync/
  ├── config.json        ← machine roles, names
  └── announcements/     ← images and slides
```

- Config and prayer data are NOT synced via Syncthing — they come from the central server
- Conflict resolution: last-write-wins
- Option to move to auto-configured Syncthing with server relay in the future without changing app code

### Startup Sequence
1. Syncthing starts and syncs latest files
2. App launches, reads local config (mosque ID, machine type, machine number)
3. App checks GitHub for update
4. App checks server for missing prayer time data, triggers load if needed
5. Display starts (or admin dashboard opens)

---

## 11. Machine Configuration

### Local config file (unique per machine):
```json
{
  "mosque_id": 1,
  "server_url": "https://...",
  "machine_type": "display",
  "machine_number": 2
}
```

### Synced config file (shared across all machines via Syncthing):
```json
{
  "machines": {
    "1": { "name": "Front Lobby", "role": "prayer_times" },
    "2": { "name": "Prayer Hall", "role": "announcements" }
  }
}
```

- `machine_number` is the stable identifier — never changes
- `display_name` is editable from admin mode anytime
- `screen_role` determines what the machine displays
- App reads its own machine number from local config, looks itself up in synced config

### Screen Roles (current)
- `prayer_times` — main prayer time display
- `announcements` — image/slide show

---

## 12. Admin Mode

Built into the app itself. Opened when app is configured as an admin machine. Structured as a multi-page dashboard. Admin sees only their mosque's data based on mosque ID.

### Page 1 — Mosque Setup
- Mosque name
- Latitude / Longitude (with map picker)
- Timezone
- Calculation method (dropdown with all named methods)
- Shafaq — only shown when Moonsighting Committee (method 15) is selected: General / Ahmer / Abyad
- School (Shafi / Hanafi)
- Advanced: per-prayer tune offsets (minute adjustments sent directly to Aladhan)

### Page 2 — Prayer & Iqamah Settings
- Covers all prayers including Jumuah, Ramadan special times, and Eid
- Per prayer: min/max offset window after adhan start
- Jumuah: number of khutbahs (1 or 2), time for each
- Advanced per prayer:
  - Earliest allowed iqamah time
  - Latest allowed iqamah time
  - Round to nearest X minutes
- Seasonal override rules:
  - Date range + different window/constraints for that period
  - Multiple rules supported
- Live preview panel showing today's calculated iqamah times as settings are adjusted

### Page 3 — Database Preview & Editor
- Full table view of all prayer + iqamah times stored in DB
- Filter by date range
- Inline editing of any single cell
- CSV / XLSX download (full DB or filtered range)
- CSV / XLSX upload to bulk overwrite values

### Page 4 — Announcements
- Upload images/slides
- Set display duration per slide
- Enable/disable individual slides
- Syncthing handles propagation to other screens

### Page 5 — Display Themes
- Select from hardcoded premade themes
- Themes apply globally across all screens in the mosque
- Each theme defines: background, primary color, accent color, font family, table/card styling
- Preview of display before applying
- Initial theme ideas: Classic Dark, Midnight Green, Clean Light, Warm Earth, Deep Purple, Mosque Background variants
- Themes are hardcoded in the app — new themes require an app update

### Page 6 — Machine Management
- Lists all machines defined in the synced config
- Edit name for each machine
- Set screen role for each machine
- Add or remove machines
- Writes directly to synced config file — no server involvement

### Page 7 — Machine Health
- Shows all display machines for the mosque
- Per machine: name, number, online/offline status, last seen timestamp, app version
- Server receives heartbeat pings from all machines every X minutes
- If a machine hasn't pinged in 15+ minutes it is marked offline
- Developer has a separate view of all mosques and all machines

---

## 13. Open / Unresolved Items

- Exact PostgreSQL schema
- Map picker implementation for lat/lon in admin UI
- Announcements format — images only, or also text slides/video
- Admin mode UX — sidebar navigation or other
- Exact heartbeat interval and offline threshold
- Alert mechanism for offline machines (email, SMS)
- Error screen / screensaver design for internet outage
- Ramadan mode — how does app know Ramadan has started (calculated vs manual trigger)
- Mosque onboarding flow — self-serve registration via API on first launch
